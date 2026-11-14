#!/usr/bin/env python3
"""Measure accuracy and latency on the board, the way the official run does.

    python3 eval.py --limit 50                    # baseline on 50 validation problems
    python3 eval.py --limit 50 --rag 1 --name rag1
    python3 eval.py --languages cat --limit 100

Every run writes per-problem results to results/ and adds one line to
results/ablations.csv, so you can build your ablation table as you go.
"""
import argparse
import csv
import json
import os
import random
import statistics
import subprocess
import time
from collections import Counter, defaultdict

from copilot import board_clock
from copilot.config import CONFIG
from copilot.pipeline import TIME_LIMIT, solve


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def table(title, groups):
    print(f"\n{title}")
    for key in sorted(groups, key=str):
        hits = groups[key]
        print(f"  {str(key):12} {sum(hits):4}/{len(hits):<4} {100 * sum(hits) / len(hits):5.1f}%")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default="data/val.jsonl")
    p.add_argument("--limit", type=int, default=50, help="0 means every problem")
    p.add_argument("--languages", default="", help="e.g. eng,cat")
    p.add_argument("--rag", type=int, default=0, metavar="K")
    p.add_argument("--index", default="data/index.db")
    p.add_argument("--name", default="", help="a label for this experiment in ablations.csv")
    p.add_argument("--simulate-latency", action="store_true",
                   help="on a laptop, wait after each problem until the board estimate has passed")
    args = p.parse_args()

    with open(args.input) as f:
        problems = [json.loads(line) for line in f if line.strip()]
    languages = set(filter(None, args.languages.split(",")))
    if languages:
        problems = [x for x in problems if x["language"] in languages]
    random.Random(42).shuffle(problems)  # the same sample every run, so runs compare
    if args.limit:
        problems = problems[:args.limit]

    index = None
    if args.rag:
        from copilot.rag import Index
        index = Index(args.index)

    os.makedirs("results", exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = args.name or (f"rag{args.rag}" if args.rag else "baseline")
    detail_path = f"results/eval-{stamp}-{name}.csv"

    rows = []
    with open(detail_path, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["id", "language", "level", "has_options", "label", "answer",
                         "correct", "seconds", "board_seconds", "status", "prompt_tokens", "retrieved",
                         "raw_letter", "margin", "family"])
        for n, problem in enumerate(problems, 1):
            result = solve(problem, index=index, k=args.rag, exclude_id=problem["id"])
            if args.simulate_latency and result["board_seconds"] > result["seconds"]:
                time.sleep(result["board_seconds"] - result["seconds"])
            correct = result["answer"] == problem["label"]
            row = {**problem, **result, "correct": correct, "has_options": bool(problem.get("options"))}
            rows.append(row)
            writer.writerow([problem["id"], problem["language"], problem["level"], row["has_options"],
                             problem["label"], result["answer"], int(correct), result["seconds"],
                             result["board_seconds"], result["status"], result["prompt_tokens"], result["retrieved"],
                             result.get("raw_letter", ""), result.get("margin", ""), result.get("family", "")])
            out.flush()
            running = 100 * sum(r["correct"] for r in rows) / len(rows)
            print(f"[{n}/{len(problems)}] {problem['id']} {problem['language']}: "
                  f"{result['answer']} (truth {problem['label']}) {result['seconds']:.1f} s "
                  f"(board est. {result['board_seconds']:.1f} s), "
                  f"running accuracy {running:.1f}%", flush=True)

    hits = [r["correct"] for r in rows]
    seconds = [r["seconds"] for r in rows]
    board = [r["board_seconds"] for r in rows]
    floor = sum(r["label"] == CONFIG["FALLBACK_ANSWER"] for r in rows)
    sim = board_clock.runtime() == "sim"
    # In sim the limit is checked against the board estimate: the laptop is not the board
    over = sum(s > TIME_LIMIT for s in (board if sim else seconds))
    accuracy = 100 * sum(hits) / len(hits)

    print("\n" + "=" * 60)
    print(f"Accuracy: {sum(hits)}/{len(hits)} = {accuracy:.1f}%")
    print(f"  floor, always {CONFIG['FALLBACK_ANSWER']}: {100 * floor / len(rows):.1f}%   random guess: 20.0%")
    where = "laptop, real" if sim else "board, real"
    print(f"Latency ({where}): mean {statistics.mean(seconds):.1f} s, median {statistics.median(seconds):.1f} s, "
          f"worst {max(seconds):.1f} s")
    print(f"Board estimate from token counts: mean {statistics.mean(board):.1f} s, "
          f"median {statistics.median(board):.1f} s, worst {max(board):.1f} s, over {TIME_LIMIT:.0f} s: {over}"
          + ("   (ESTIMATE: constants from the README, not yet calibrated on the board)" if sim else ""))
    print(f"Status: {dict(Counter(r['status'] for r in rows))}")
    solved = [r for r in rows if r.get("family")]
    if solved:
        print(f"Family solvers: {len(solved)}/{len(rows)} problems routed, "
              f"{sum(r['correct'] for r in solved)}/{len(solved)} correct, by family "
              f"{dict(Counter(r['family'] for r in solved))}")

    for field, title in (("language", "By language"), ("level", "By level"),
                         ("has_options", "By whether OCR found the options")):
        groups = defaultdict(list)
        for r in rows:
            groups[r[field]].append(r["correct"])
        table(title, groups)

    predicted = Counter(r["answer"] for r in rows)
    truth = Counter(r["label"] for r in rows)
    print("\nLetters   " + "  ".join(f"{l}:{predicted[l]:>3}/{truth[l]:<3}" for l in "ABCDE"))
    print("          (predicted/true; a model that loves one letter shows up here)")

    log = "results/ablations.csv"
    new = not os.path.exists(log)
    with open(log, "a", newline="") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(["time", "name", "commit", "runtime", "input", "languages", "n", "rag_k",
                             "accuracy", "mean_s", "worst_s", "board_mean_s", "board_worst_s", "over_limit"])
        writer.writerow([stamp, name, git_commit(), board_clock.runtime(), args.input, args.languages or "all",
                         len(rows), args.rag, f"{accuracy:.1f}", f"{statistics.mean(seconds):.1f}",
                         f"{max(seconds):.1f}", f"{statistics.mean(board):.1f}", f"{max(board):.1f}", over])
    print(f"\nDetails: {detail_path}\nAblation log: {log}")


if __name__ == "__main__":
    main()
