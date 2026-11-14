"""Measure the Catalan/English pairs of a split and their length in tokens (rung 0, docs/bilingual-rung.md).

    python3 laptop/measure_bilingual.py --input data/val.jsonl [--out results/bilingual-val.csv]

For every id with both languages it counts the tokens of the problem block the prompts use
(text, then "A) option" lines) with llama-server's /tokenize (the same tokenizer the board
runs), and turns them into board prefill seconds with copilot.board_clock.estimate_tokens.
Prints Markdown tables; the CSV has ids and counts only, never text. Laptop only.
"""
import argparse
import collections
import csv
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot.board_clock import estimate_tokens  # noqa: E402
from copilot.client import post  # noqa: E402
from copilot.config import CONFIG  # noqa: E402

TOKENIZE_URL = f"http://{CONFIG['LLM_HOST']}:{CONFIG['LLM_PORT']}/tokenize"


def block(problem):
    lines = [problem["text"].strip()]
    options = problem.get("options") or {}
    for letter in "ABCDE":
        if letter in options:
            lines.append(f"{letter}) {options[letter]}")
    return "\n".join(lines)


def tokens(text):
    return len(post(TOKENIZE_URL, {"content": text}, timeout=30)["tokens"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/val.jsonl")
    ap.add_argument("--out", default=None, help="CSV with id, level, tokens_cat, tokens_eng, chars_cat, chars_eng")
    args = ap.parse_args()

    by_id = collections.defaultdict(dict)
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                p = json.loads(line)
                by_id[p["id"]][p["language"]] = p
    pairs = {i: v for i, v in by_id.items() if "cat" in v and "eng" in v}
    same_label = sum(1 for v in pairs.values() if v["cat"].get("label") == v["eng"].get("label"))
    both_options = sum(1 for v in pairs.values() if v["cat"].get("options") and v["eng"].get("options"))

    rows = []
    for pid, v in sorted(pairs.items()):
        rows.append({"id": pid, "level": v["cat"].get("level"),
                     "tokens_cat": tokens(block(v["cat"])), "tokens_eng": tokens(block(v["eng"])),
                     "chars_cat": len(block(v["cat"])), "chars_eng": len(block(v["eng"]))})
    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    cat = [r["tokens_cat"] for r in rows]
    eng = [r["tokens_eng"] for r in rows]
    diff = [c - e for c, e in zip(cat, eng)]
    ratio = sum(cat) / sum(eng)
    print(f"Pairs: {len(pairs)}/{len(by_id)} ids with both languages; same label {same_label}/{len(pairs)}; "
          f"options read in both {both_options}/{len(pairs)}")
    print()
    print("| measure (problem block: text + options) | Catalan | English | Catalan / English |")
    print("|---|---|---|---|")
    print(f"| mean tokens | {statistics.mean(cat):.1f} | {statistics.mean(eng):.1f} | {ratio:.3f} |")
    print(f"| median tokens | {statistics.median(cat):.0f} | {statistics.median(eng):.0f} | |")
    print(f"| max tokens | {max(cat)} | {max(eng)} | |")
    print(f"| mean characters | {statistics.mean(r['chars_cat'] for r in rows):.0f} | {statistics.mean(r['chars_eng'] for r in rows):.0f} | "
          f"{sum(r['chars_cat'] for r in rows) / sum(r['chars_eng'] for r in rows):.3f} |")
    print(f"| mean board prefill seconds (estimate_tokens) | {statistics.mean(estimate_tokens(c) for c in cat):.2f} | "
          f"{statistics.mean(estimate_tokens(e) for e in eng):.2f} | {ratio:.3f} |")
    print(f"| mean difference, tokens (cat - eng) | {statistics.mean(diff):+.1f} | | |")
    print(f"| pairs where Catalan is longer | {sum(1 for d in diff if d > 0)}/{len(diff)} | | |")
    print()
    print("| level | n | mean tokens cat | mean tokens eng | ratio |")
    print("|---|---|---|---|---|")
    by_level = collections.defaultdict(list)
    for r in rows:
        by_level[r["level"]].append(r)
    for level in sorted(by_level):
        rs = by_level[level]
        c, e = sum(r["tokens_cat"] for r in rs), sum(r["tokens_eng"] for r in rs)
        print(f"| {level} | {len(rs)} | {c / len(rs):.1f} | {e / len(rs):.1f} | {c / e:.3f} |")


if __name__ == "__main__":
    main()
