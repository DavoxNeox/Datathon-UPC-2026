#!/usr/bin/env python3
"""Coverage and distribution of the error signatures (copilot/signatures.py) on M3Kang.

For every problem whose correct option is a single number, every distractor is diagnosed
as if the student had picked it. The report gives, by topic (data_curated/topics.json) and
by level, how many distractors get a signature other than "none" and how many problems
have at least one signed distractor; then the distribution of signatures in two ways:
simulating a student who picks each numeric distractor once, and over the wrong answers
of the evaluation runs in results/eval-*.csv (the copilot's own errors: `answer` vs `label`).

    python3 laptop/measure_signatures.py                                   # val + train, eng rows
    python3 laptop/measure_signatures.py --out docs/error-signatures-coverage.md
    python3 laptop/measure_signatures.py --sample 20 --seed 1 --sample-out results/signatures_sample.tsv

Markdown only, ids only, never a word of problem text. The sample file (for the manual
judgement, git-ignored under results/) carries the option values, so it stays out of git.
"""
import argparse
import csv
import glob
import json
import os
import random
import sys
from collections import Counter, OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from copilot.signatures import SIGNATURE_KEYS, diagnose, option_value  # noqa: E402
from copilot.topics import TOPIC_KEYS, get_topic  # noqa: E402

LETTERS = "ABCDE"


def load_problems(paths, lang):
    rows = OrderedDict()
    for path in paths:
        if not os.path.exists(path):
            print(f"missing {path}, skipped", file=sys.stderr)
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("language", lang) == lang and r["id"] not in rows:
                    r["_source"] = os.path.basename(path)
                    rows[r["id"]] = r
    return rows


def diagnose_all(problems):
    """[(problem, letter, result)] for every distractor of every problem with a numeric label."""
    out = []
    for p in problems.values():
        options = p.get("options") or {}
        label = p.get("label")
        if label not in options or option_value(options[label]) is None:
            continue
        for letter in LETTERS:
            if letter == label or letter not in options:
                continue
            out.append((p, letter, diagnose(p, letter)))
    return out


def pct(hits, n):
    return f"{100 * hits / n:.0f}%" if n else "-"


def coverage_table(title, items, key, order):
    """group | problems (numeric label) | distractors numeric | signed | % | problems with >=1 signed | %"""
    groups = defaultdict(list)
    for item in items:
        groups[key(item[0])].append(item)
    lines = [f"### {title}", "",
             f"| {title} | problems | distractors | numeric | signed | % signed | problems ≥1 signed | % |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]

    def row(name, its):
        ids = {p["id"] for p, _, _ in its}
        numeric = [r for _, _, r in its if r is not None]
        signed = [r for r in numeric if r["signature"] != "none"]
        signed_ids = {p["id"] for p, _, r in its if r is not None and r["signature"] != "none"}
        return (f"| {name} | {len(ids)} | {len(its)} | {len(numeric)} | {len(signed)} | "
                f"{pct(len(signed), len(numeric))} | {len(signed_ids)} | {pct(len(signed_ids), len(ids))} |")

    for k in order:
        if k in groups:
            lines.append(row(k, groups[k]))
    lines.append(row("**all**", items))
    return "\n".join(lines) + "\n"


def distribution_table(title, counter, total_label="all"):
    n = sum(counter.values())
    lines = [f"### {title}", "", "| signature | n | % |", "| --- | ---: | ---: |"]
    for key in SIGNATURE_KEYS + ["(not numeric)"]:
        if counter.get(key):
            lines.append(f"| {key} | {counter[key]} | {pct(counter[key], n)} |")
    lines.append(f"| **{total_label}** | {n} | 100% |")
    return "\n".join(lines) + "\n"


def eval_distribution(csv_paths, problems):
    """Signatures of the copilot's wrong answers in the eval CSVs (answer != label)."""
    counter, files, wrong, seen_rows = Counter(), [], 0, 0
    for path in sorted(csv_paths):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        files.append((os.path.basename(path), len(rows)))
        for r in rows:
            seen_rows += 1
            if r.get("answer") == r.get("label") or not r.get("answer"):
                continue
            wrong += 1
            p = problems.get(r["id"])
            if p is None:
                counter["(not numeric)"] += 1
                continue
            d = diagnose(p, r["answer"])
            counter[d["signature"] if d else "(not numeric)"] += 1
    return counter, files, seen_rows, wrong


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", nargs="+", default=[os.path.join(ROOT, "data", "val.jsonl"),
                                                   os.path.join(ROOT, "data", "train.jsonl")])
    ap.add_argument("--lang", default="eng", help="rows of this language (the options are the same OCR per image)")
    ap.add_argument("--results", default=os.path.join(ROOT, "results", "eval-*.csv"))
    ap.add_argument("--out", help="write the Markdown report here too")
    ap.add_argument("--sample", type=int, default=0, help="also draw N signed distractors for a manual judgement")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sample-out", default=os.path.join(ROOT, "results", "signatures_sample.tsv"))
    ap.add_argument("--pairs", nargs="*", metavar="ID:LETTER",
                    help="only diagnose these (problem id, chosen letter) pairs and print a Markdown table")
    args = ap.parse_args()

    if args.pairs:
        problems = load_problems(args.inputs, args.lang)
        print("| id | level | topic | chosen | signature | candidates |\n| --- | ---: | --- | --- | --- | --- |")
        for pair in args.pairs:
            pid, letter = pair.rsplit(":", 1)
            p = problems.get(pid)
            d = diagnose(p, letter) if p else None
            sig = d["signature"] if d else "(none: not numeric or unknown id)"
            cands = ", ".join(d["evidence"]["candidates"]) if d else ""
            print(f"| {pid} | {p['level'] if p else '-'} | {get_topic(pid)} | {letter} | {sig} | {cands} |")
        return

    problems = load_problems(args.inputs, args.lang)
    items = diagnose_all(problems)
    with_options = sum(1 for p in problems.values() if p.get("options"))
    numeric_label = len({p["id"] for p, _, _ in items})

    out = ["# Error signatures: coverage on M3Kang", "",
           f"Rows: {len(problems)} problems in `{args.lang}` from {', '.join(os.path.basename(x) for x in args.inputs)}; "
           f"{with_options} with OCR options ({pct(with_options, len(problems))}); {numeric_label} whose correct option is a "
           f"single number ({pct(numeric_label, len(problems))}). Every distractor of those is diagnosed as if the student had "
           "picked it. `numeric` = the distractor is a single number too; `signed` = a signature other than `none`.", ""]
    levels = sorted({p["level"] for p in problems.values()})
    out.append(coverage_table("Topic", items, lambda p: get_topic(p["id"]), TOPIC_KEYS))
    out.append(coverage_table("Level", items, lambda p: p["level"], levels))
    out.append(coverage_table("Source", items, lambda p: p["_source"], sorted({p["_source"] for p in problems.values()})))

    simulated = Counter(r["signature"] for _, _, r in items if r is not None)
    out.append(distribution_table("Distribution, simulated student (each numeric distractor picked once)", simulated,
                                  "numeric distractors"))

    csv_paths = glob.glob(args.results)
    if csv_paths:
        counter, files, n_rows, wrong = eval_distribution(csv_paths, problems)
        out.append(f"### Distribution over the copilot's wrong answers in results/\n\n"
                   f"{len(files)} runs, {n_rows} rows, {wrong} wrong answers (`answer` != `label`); `(not numeric)` = the "
                   "problem has no numeric pair to compare (pictures, OCR noise) or is not in the inputs. These are the "
                   "model's errors, not a student's: they say what the web would show if the copilot were the student.\n")
        out.append("| run | rows |\n| --- | ---: |\n" + "\n".join(f"| {name} | {n} |" for name, n in files) + "\n")
        out.append(distribution_table("Signatures of the wrong answers", counter, "wrong answers"))
    else:
        out.append("No results/eval-*.csv found: only the simulated distribution above.\n")

    dropped = Counter(k for _, _, r in items if r is not None for k in r["evidence"]["dropped_by_leak_filter"])
    if dropped:
        out.append("### Candidates dropped by the leak filter\n\nA matching signature whose text would have named the correct "
                   "value (a Catalan number word, a statement number equal to the answer); the next candidate was used.\n\n"
                   "| signature | dropped |\n| --- | ---: |\n" + "\n".join(f"| {k} | {v} |" for k, v in dropped.most_common()) + "\n")

    report = "\n".join(out)
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"written {args.out}", file=sys.stderr)

    if args.sample:
        signed = [(p, letter, r) for p, letter, r in items if r is not None and r["signature"] != "none"]
        rng = random.Random(args.seed)
        picked = rng.sample(signed, min(args.sample, len(signed)))
        with open(args.sample_out, "w", encoding="utf-8") as f:
            f.write("id\tlevel\ttopic\tlabel\tchosen\tsignature\tchosen_value\tcorrect_value\tcandidates\ttext_en\n")
            for p, letter, r in picked:
                e = r["evidence"]
                f.write("\t".join([p["id"], str(p["level"]), get_topic(p["id"]), p["label"], letter, r["signature"],
                                   e["chosen_value"], e["correct_value"], ",".join(e["candidates"]), r["text_en"]]) + "\n")
        print(f"{len(picked)} signed distractors for the manual judgement in {args.sample_out} (git-ignored)",
              file=sys.stderr)


if __name__ == "__main__":
    main()
