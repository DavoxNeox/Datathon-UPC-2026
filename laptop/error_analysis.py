#!/usr/bin/env python3
"""Error analysis of eval runs: accuracy by topic, family, language, level and text_only.

Joins results/eval-*.csv (one row per problem: id, language, label, answer, ...) with
data/val.jsonl on id + language (for text_only and the OCR options), with
data_curated/topics.json (id -> topic) and data_curated/families.json (id -> family).
Prints Markdown tables with the number of problems next to every percentage, and never
a word of problem text, so the output can go straight into the README.

    python3 laptop/error_analysis.py                                   # the newest results/eval-*.csv
    python3 laptop/error_analysis.py results/eval-*-B-eng50.csv --out docs/error-analysis.md
    python3 laptop/error_analysis.py results/eval-*.csv --merge         # all runs as one sample

Besides the accuracy, each row shows what guessing would score on the same problems:
`always D` (the share of D labels in the group) and `random` (20%). A topic whose accuracy
sits between the two is at chance level, whatever the headline number says.
"""
import argparse
import csv
import glob
import json
import os
import sys
from collections import Counter, OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from copilot.topics import TOPICS, TOPIC_KEYS  # noqa: E402

FALLBACK = "D"
VISUAL = {t["key"]: t["visual"] for t in TOPICS}
NAME_EN = {t["key"]: t["name_en"] for t in TOPICS}


def load_jsonl(path):
    rows = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    rows[(r["id"], r.get("language", ""))] = r
    return rows


def load_json(path, key):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f).get(key, {})


def load_run(path, val, topics, families):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            problem = val.get((r["id"], r["language"]), {})
            text_only = problem.get("text_only")
            rows.append({
                "id": r["id"], "language": r["language"], "level": int(r.get("level") or problem.get("level") or 0),
                "label": r["label"], "answer": r["answer"], "correct": r["correct"] in ("1", "True", "true"),
                "status": r.get("status", ""), "solver_family": r.get("family") or "",
                "has_options": (r.get("has_options") or str(bool(problem.get("options")))) in ("True", "true", "1"),
                "text_only": "unknown" if text_only is None else bool(text_only),
                "topic": topics.get(r["id"], "arithmetic"), "family": families.get(r["id"], "(none)"),
                "board_seconds": float(r.get("board_seconds") or 0),
            })
    return rows


def pct(hits, n):
    return f"{100 * hits / n:.0f}%" if n else "-"


def table(title, rows, key, order=None, extra=None):
    """One Markdown table: group | n | correct | accuracy | always D | random, plus optional extra columns."""
    groups = defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    keys = [k for k in (order or sorted(groups, key=str)) if k in groups]
    keys += [k for k in sorted(groups, key=str) if k not in keys]
    lines = [f"### {title}", "",
             "| " + title.split(" (")[0] + " | n | correct | accuracy | always D | random |" + ("".join(f" {c} |" for c in extra) if extra else ""),
             "| --- | ---: | ---: | ---: | ---: | ---: |" + (" ---: |" * len(extra) if extra else "")]
    for k in keys:
        g = groups[k]
        hits = sum(r["correct"] for r in g)
        floor = sum(r["label"] == FALLBACK for r in g)
        cells = [str(k), str(len(g)), str(hits), pct(hits, len(g)), pct(floor, len(g)), "20%"]
        if extra:
            cells += [fn(g) for fn in extra.values()]
        lines.append("| " + " | ".join(cells) + " |")
    hits = sum(r["correct"] for r in rows)
    floor = sum(r["label"] == FALLBACK for r in rows)
    cells = ["**all**", str(len(rows)), str(hits), pct(hits, len(rows)), pct(floor, len(rows)), "20%"]
    if extra:
        cells += [fn(rows) for fn in extra.values()]
    lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def topic_label(r):
    return f"{r['topic']} ({'visual' if VISUAL.get(r['topic']) else 'text'})"


def report(name, rows):
    out = [f"## {name}", "", f"{len(rows)} problems, {sum(r['correct'] for r in rows)} correct "
           f"({pct(sum(r['correct'] for r in rows), len(rows))}); always D would score "
           f"{pct(sum(r['label'] == FALLBACK for r in rows), len(rows))}, random 20%. "
           f"Board estimate: mean {sum(r['board_seconds'] for r in rows) / max(1, len(rows)):.1f} s, "
           f"worst {max((r['board_seconds'] for r in rows), default=0):.1f} s.", ""]
    mean_board = {"board s (mean)": lambda g: f"{sum(r['board_seconds'] for r in g) / len(g):.1f}"}
    topic_order = [f"{k} ({'visual' if VISUAL[k] else 'text'})" for k in TOPIC_KEYS]
    out.append(table("Topic (visual = most problems need the figure)", rows, topic_label, topic_order, mean_board))
    visual_rows = [r for r in rows if VISUAL.get(r["topic"])]
    text_rows = [r for r in rows if not VISUAL.get(r["topic"])]
    out.append(table("Visual vs text topics", rows, lambda r: "visual topics" if VISUAL.get(r["topic"]) else "text topics",
                     ["text topics", "visual topics"]))
    if visual_rows:
        v_hits, v_floor = sum(r["correct"] for r in visual_rows), sum(r["label"] == FALLBACK for r in visual_rows)
        acc, floor = v_hits / len(visual_rows), max(v_floor / len(visual_rows), 0.2)
        verdict = ("at or below the guessing floors: chance level" if acc <= floor + 0.02 else
                   f"{100 * (acc - floor):.0f} points above the better guessing floor (check the n before trusting it)")
        out.append(f"On the visual topics the copilot reads a text that describes a picture it cannot see: "
                   f"{pct(v_hits, len(visual_rows))} on {len(visual_rows)} problems against {pct(v_floor, len(visual_rows))} "
                   f"for always D and 20% for random, {verdict}.\n")
    out.append(table("Family (keyword family of text-only problems; (none) = no family)", rows, lambda r: r["family"],
                     [k for k, _ in Counter(r["family"] for r in rows).most_common()]))
    if any(r["solver_family"] for r in rows):
        out.append(table("Answered by (solver family, or no solver)", rows, lambda r: r["solver_family"] or "(no solver)",
                         None, mean_board))
    out.append(table("Language", rows, lambda r: r["language"], ["eng", "cat"]))
    out.append(table("Level (0 = grade 5)", rows, lambda r: r["level"], list(range(8))))
    out.append(table("text_only (M3Kang: the figure is not needed)", rows, lambda r: r["text_only"], [True, False, "unknown"]))
    out.append(table("OCR read the options", rows, lambda r: r["has_options"], [True, False]))
    if any(r["status"] != "ok" for r in rows):
        out.append(table("Status", rows, lambda r: r["status"]))
    predicted = Counter(r["answer"] for r in rows)
    truth = Counter(r["label"] for r in rows)
    out.append("### Letters\n\n| letter | predicted | true |\n| --- | ---: | ---: |")
    for l in "ABCDE":
        out.append(f"| {l} | {predicted[l]} | {truth[l]} |")
    out.append("")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("results", nargs="*", help="eval CSV files (default: the newest results/eval-*.csv)")
    p.add_argument("--val", default=os.path.join(ROOT, "data", "val.jsonl"))
    p.add_argument("--topics", default=os.path.join(ROOT, "data_curated", "topics.json"))
    p.add_argument("--families", default=os.path.join(ROOT, "data_curated", "families.json"))
    p.add_argument("--merge", action="store_true", help="pool every file into one sample")
    p.add_argument("--out", default="", help="write the Markdown here instead of stdout")
    args = p.parse_args()

    files = args.results or sorted(glob.glob(os.path.join(ROOT, "results", "eval-*.csv")))[-1:]
    if not files:
        sys.exit("no results/eval-*.csv found")
    val = load_jsonl(args.val)
    topics = load_json(args.topics, "topics")
    families = load_json(args.families, "families")
    if not val:
        print(f"warning: {args.val} not found, text_only is unknown", file=sys.stderr)

    runs = OrderedDict((os.path.basename(f), load_run(f, val, topics, families)) for f in files)
    if args.merge:
        runs = OrderedDict([(" + ".join(runs), [r for rows in runs.values() for r in rows])])
    parts = ["# Error analysis", "",
             "Accuracy by topic, family, language, level and text_only, from `results/eval-*.csv` joined with "
             "`data/val.jsonl` by id and language. Every percentage has its n next to it; the `always D` column "
             "is what answering the fallback letter scores on the same problems. Problem ids only, no text.", ""]
    parts += [report(name, rows) for name, rows in runs.items()]
    text = "\n".join(parts)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
