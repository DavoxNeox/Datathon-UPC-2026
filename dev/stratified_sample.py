#!/usr/bin/env python3
"""Pick a stratified sample of problem ids for eval.py --ids (docs/reason-experiments.md, Experiment 6).

    python3 dev/stratified_sample.py --input data/train.jsonl --languages eng --size 300 > results/train-strat300.ids

Strata: level (0 to 7) x figure (text_only) x numeric options (copilot/ladder.numeric_options).
Proportional allocation, at least one problem per non-empty stratum, seed 42. Ids only: no problem text.
"""
import argparse
import json
import random
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from copilot import ladder  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default="data/train.jsonl")
    p.add_argument("--languages", default="eng")
    p.add_argument("--size", type=int, default=300)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    languages = set(filter(None, args.languages.split(",")))
    with open(args.input) as f:
        problems = [json.loads(line) for line in f if line.strip()]
    problems = [x for x in problems if not languages or x["language"] in languages]
    strata = defaultdict(list)
    for x in problems:
        key = (x["level"], bool(x.get("text_only")), ladder.numeric_options(x.get("options") or {}) is not None)
        strata[key].append(x["id"])
    rng = random.Random(args.seed)
    total = len(problems)
    quotas = {k: max(1, round(args.size * len(v) / total)) for k, v in strata.items()}
    chosen = []
    for key in sorted(strata):
        ids = sorted(strata[key])
        rng.shuffle(ids)
        chosen.extend(ids[:quotas[key]])
        print(f"level {key[0]} text_only {int(key[1])} numeric {int(key[2])}: {len(ids):4} -> {min(quotas[key], len(ids))}",
              file=sys.stderr)
    print(f"{len(chosen)} ids from {total} problems", file=sys.stderr)
    print("\n".join(chosen))


if __name__ == "__main__":
    main()
