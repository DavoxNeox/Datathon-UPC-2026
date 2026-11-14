#!/usr/bin/env python3
"""Measure the model's letter bias on TRAINING problems and write data_curated/letter_prior.json.

    python3 calibrate_bias.py                       # 100 training problems
    python3 calibrate_bias.py --limit 200
    python3 calibrate_bias.py --input data/sample_problems.jsonl --limit 0   # dry run

For each problem it asks the model once (one letter, grammar A to E, logprobs) and keeps
the log probabilities of the five letters. Then it computes the prior (the model's mean
probability of each letter) and tries a small grid of alpha (how much prior to remove)
and min_margin (below which we answer the most common letter), keeping the pair with
the best accuracy ON THESE TRAINING PROBLEMS. The honest number is eval.py on
validation, afterwards. Standard library only: it also runs on the board.

The output file holds five numbers, the chosen alpha and min_margin, and how they were
measured. No problem text: it is safe to commit.
"""
import argparse
import json
import os
import random
import sys
import time
from collections import Counter

from copilot import bias
from copilot.board_clock import estimate
from copilot.llm import letter_scores

ALPHAS = (0.0, 0.5, 0.75, 1.0, 1.25)
MARGINS = (0.0, 0.1, 0.25, 0.5, 1.0)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default="data/train.jsonl")
    p.add_argument("--limit", type=int, default=100, help="0 means every problem")
    p.add_argument("--languages", default="eng", help="e.g. eng or eng,cat")
    p.add_argument("--out", default=bias.DEFAULT_PATH)
    p.add_argument("--dry-run", action="store_true", help="measure and print, but don't write the file")
    args = p.parse_args()

    with open(args.input, encoding="utf-8") as f:
        problems = [json.loads(line) for line in f if line.strip()]
    languages = set(filter(None, args.languages.split(",")))
    if languages:
        problems = [x for x in problems if x.get("language") in languages] or problems
    random.Random(42).shuffle(problems)
    if args.limit:
        problems = problems[:args.limit]

    runs, labels, raw, board = [], [], [], []
    start = time.perf_counter()
    for n, problem in enumerate(problems, 1):
        letter, scores, timings = letter_scores(problem)
        runs.append(scores)
        labels.append(problem["label"])
        raw.append(letter)
        board.append(estimate(timings))
        print(f"\r[{n}/{len(problems)}] raw accuracy {100 * sum(a == b for a, b in zip(raw, labels)) / n:.1f}%  "
              f"board est. {sum(board) / n:.1f} s/problem", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)

    prior = bias.prior_from_runs(runs)
    fallback = Counter(labels).most_common(1)[0][0]
    print(f"Calibration set: {len(runs)} problems from {args.input} ({args.languages or 'all'}), "
          f"{time.perf_counter() - start:.0f} s on this machine, {sum(board) / len(board):.1f} s/problem estimated on the board")
    print("Model prior over letters (mean probability): " +
          "  ".join(f"{l}: {100 * 2.718281828 ** prior[l]:.1f}%" for l in bias.LETTERS))
    print("True labels:                                 " +
          "  ".join(f"{l}: {100 * labels.count(l) / len(labels):.1f}%" for l in bias.LETTERS))
    print(f"Raw model: {100 * sum(a == b for a, b in zip(raw, labels)) / len(labels):.1f}%, "
          f"letters chosen {dict(sorted(Counter(raw).items()))}")

    best = None
    print("\nalpha  margin  accuracy  fallbacks  letters chosen")
    for alpha in ALPHAS:
        for margin in MARGINS:
            chosen = [bias.choose(s, prior, alpha, margin, fallback)[0] for s in runs]
            acc = sum(a == b for a, b in zip(chosen, labels)) / len(labels)
            fallbacks = sum(bias.choose(s, prior, alpha, margin, fallback)[1] < margin for s in runs)
            print(f"{alpha:5.2f}  {margin:6.2f}  {100 * acc:7.1f}%  {fallbacks:9d}  {dict(sorted(Counter(chosen).items()))}")
            key = (acc, -margin, -abs(alpha - 1.0))  # prefer simpler settings on ties
            if best is None or key > best[0]:
                best = (key, alpha, margin, acc)
    _, alpha, margin, acc = best
    print(f"\nBest on calibration: alpha {alpha}, min_margin {margin}, accuracy {100 * acc:.1f}% "
          f"(always {fallback}: {100 * labels.count(fallback) / len(labels):.1f}%). "
          "Confirm on validation with eval.py before believing it.")

    if args.dry_run:
        return
    out = {
        "prior": {l: round(prior[l], 6) for l in bias.LETTERS},
        "alpha": alpha, "min_margin": margin, "fallback": fallback,
        "calibration": {"input": os.path.basename(args.input), "languages": args.languages or "all",
                        "n": len(runs), "raw_accuracy": round(100 * sum(a == b for a, b in zip(raw, labels)) / len(labels), 1),
                        "corrected_accuracy": round(100 * acc, 1), "board_seconds_per_problem": round(sum(board) / len(board), 1),
                        "date": time.strftime("%Y-%m-%d")},
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
