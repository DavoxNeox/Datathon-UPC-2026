#!/usr/bin/env python3
"""Validate data_curated/demo_set.json (the hand-written demo problems).

    python3 laptop/validate_demo_set.py data_curated/demo_set.json [--data data/val.jsonl data/train.jsonl]

Checks: ids exist in the prepared data when it is available, every step has Catalan and
English text, the last step is the only one that may name the answer, the topic is one of the
eight keys, and no field copies the problem statement (M3Kang is research-only).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from copilot.topics import TOPIC_KEYS  # noqa: E402

LETTERS = "ABCDE"


def load_problems(paths):
    found = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    found.setdefault(r["id"], {})[r["language"]] = r
    return found


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("path", nargs="?", default="data_curated/demo_set.json")
    p.add_argument("--data", nargs="*", default=["data/val.jsonl", "data/train.jsonl"])
    args = p.parse_args()
    with open(args.path, encoding="utf-8") as f:
        data = json.load(f)
    problems = data.get("problems", [])
    known = load_problems(args.data)
    errors = []
    for i, item in enumerate(problems):
        tag = f"#{i + 1} {item.get('id', '?')}"
        for key in ("id", "topic", "figure_ca", "figure_en", "steps"):
            if key not in item:
                errors.append(f"{tag}: missing {key}")
        if item.get("topic") not in TOPIC_KEYS:
            errors.append(f"{tag}: topic {item.get('topic')!r} is not one of {TOPIC_KEYS}")
        steps = item.get("steps") or []
        if len(steps) < 2:
            errors.append(f"{tag}: at least two steps")
        for n, step in enumerate(steps):
            if not step.get("text_ca") or not step.get("text_en"):
                errors.append(f"{tag} step {n + 1}: needs text_ca and text_en")
        if known and item.get("id") in known:
            rows = known[item["id"]]
            label = next(iter(rows.values()))["label"]
            answer_value = next(iter(rows.values())).get("options", {}).get(label)
            for n, step in enumerate(steps[:-1]):
                text = (step.get("text_ca", "") + " " + step.get("text_en", ""))
                if re.search(rf"\b(opci[oó]n?|option)\s*{label}\b", text, re.I):
                    errors.append(f"{tag} step {n + 1}: names the correct option before the last step")
                if answer_value and re.search(rf"(?<![\d.,]){re.escape(answer_value)}(?![\d.,])", text) and n < len(steps) - 2:
                    errors.append(f"{tag} step {n + 1}: contains the answer value {answer_value!r} too early")
            for lang, r in rows.items():
                statement = r["text"].strip()
                for key in ("figure_ca", "figure_en"):
                    if statement and statement[:60] in item.get(key, ""):
                        errors.append(f"{tag}: {key} copies the statement (research-only data)")
        elif known:
            errors.append(f"{tag}: id not found in {args.data}")
    print(f"{len(problems)} demo problems, {len(errors)} problem(s)")
    for e in errors:
        print("  -", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
