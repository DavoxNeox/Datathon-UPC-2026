#!/usr/bin/env python3
"""Official entry point: answer every problem with one letter, A to E.

    python3 predict.py --input problems.jsonl --output predictions.csv
    python3 predict.py --input problems.jsonl --output predictions.csv --rag 1

Input: one JSON object per line with at least "id" and "text", plus
"options" ({"A": ..., "E": ...}) and "language" when available.
Output: a CSV with id, language, answer, seconds, status.

Rules: runs offline, at most 60 seconds per problem, deterministic.

Every input line gets exactly one output row, whatever it contains: a line that is
not a JSON object, a problem without an id, or a problem that makes the pipeline
raise still gets a row (the fallback letter, status "error:<reason>"), and the run
goes on with the next line. An exam is scored on the rows that exist.

The run resumes: when --output already exists, the rows it holds are kept and only the
input lines without a row are answered, appended in input order. A board reset in the
middle of a long exam costs the problem in flight, not the file. --fresh starts over.
"""
import argparse
import csv
import json
import os
import sys
import time

from copilot.config import CONFIG
from copilot.pipeline import solve

FALLBACK = str(CONFIG.get("FALLBACK_ANSWER", "D")).strip().upper()[:1] or "D"
LETTERS = ("A", "B", "C", "D", "E")


def read_problems(path):
    """Yield (line_number, problem_dict_or_None, parse_error) for every non-blank line."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except ValueError as e:
                yield n, None, "error:json:%s" % type(e).__name__
                continue
            if not isinstance(obj, dict):
                yield n, None, "error:not-an-object"
                continue
            yield n, obj, ""


def row_id(problem, line_number):
    """The id to write: the problem's own when it has one, else the line number."""
    if isinstance(problem, dict):
        for key in ("id", "ID", "Id", "problem_id"):
            value = problem.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
    return "line-%d" % line_number


def answer_one(problem, index, k):
    """solve() guarded: always a letter, the seconds spent, a status and a board estimate."""
    t0 = time.time()
    try:
        result = solve(problem, index=index, k=k)
        answer = str(result.get("answer", "")).strip().upper()[:1]
        if answer not in LETTERS:
            answer, status = FALLBACK, "error:no-letter"
        else:
            status = result.get("status", "ok")
        return answer, float(result.get("seconds", time.time() - t0)), status, float(result.get("board_seconds", 0.0))
    except Exception as e:  # noqa: BLE001 - one bad row must not end the exam
        return FALLBACK, time.time() - t0, "error:%s" % type(e).__name__, 0.0


def rows_already_written(path):
    """The ids with a row in an existing output, or None when there is no usable output yet."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header != ["id", "language", "answer", "seconds", "status"]:
                return None
            return {row[0] for row in reader if row}
    except (OSError, csv.Error):
        return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--rag", type=int, default=0, metavar="K", help="add K similar solved problems")
    p.add_argument("--index", default="data/index.db")
    p.add_argument("--fresh", action="store_true", help="ignore an existing --output and start over")
    args = p.parse_args()

    index = None
    if args.rag:
        if not os.path.exists(args.index):
            sys.exit(f"{args.index} not found. Build it first: python3 build_index.py")
        from copilot.rag import Index
        index = Index(args.index)

    rows = list(read_problems(args.input))
    done = None if args.fresh else rows_already_written(args.output)
    if done:
        print(f"resuming: {len(done)} rows already in {args.output}", file=sys.stderr)
    with open(args.output, "a" if done is not None else "w", newline="") as out:
        writer = csv.writer(out)
        if done is None:
            done = set()
            writer.writerow(["id", "language", "answer", "seconds", "status"])
        for n, (line_number, problem, parse_error) in enumerate(rows, 1):
            pid = row_id(problem, line_number)
            if pid in done:
                continue
            done.add(pid)
            language = str(problem.get("language", "") or "") if problem else ""
            if parse_error:
                answer, seconds, status, board = FALLBACK, 0.0, parse_error, 0.0
            else:
                answer, seconds, status, board = answer_one(problem, index, args.rag)
            writer.writerow([pid, language, answer, round(seconds, 2), status])
            out.flush()
            print(f"[{n}/{len(rows)}] {pid} -> {answer} in {seconds:.1f} s, board est. {board:.1f} s ({status})",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
