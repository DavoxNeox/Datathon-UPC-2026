#!/usr/bin/env python3
"""Measure copilot/lineage.lineage() on the validation problems.

    python3 laptop/measure_lineage.py                         # tables for docs/lineage.md (ids only)
    python3 laptop/measure_lineage.py --thresholds 0.5,0.6,0.7,0.8 --min-levels 3
    python3 laptop/measure_lineage.py --judge 15 --out /path/outside/the/repo.txt   # chains with texts, to judge by hand
    python3 laptop/measure_lineage.py --judge 15 --judge-seed 11 --judge-exclude id1,id2 --out ...   # a clean second round

For every English validation problem the chain is built once with max_links=8 (every other
level that passes the lowest threshold), then cut at each threshold. Reported: the share of
problems whose chain has at least --min-levels links, the mean chain length, the mean
similarity, and the same per topic at the main threshold. Board cost: a validation id costs
one embedding (BOARD_EMBED_SECONDS, measured on the board) plus the Python part, which is
timed here on the laptop and reported as is (a lower bound on the board's CPU). Training ids
reuse their stored vector: 0 embeddings; a sample of them is timed too.

The judge file holds problem texts, so it must live outside the repository.
"""
import argparse
import json
import os
import random
import statistics
import sys
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from copilot import lineage, retrieval, topics  # noqa: E402
from copilot.board_clock import EMBED_SECONDS  # noqa: E402


def rows_from(path, language="eng"):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip() and f'"{language}"' in l]


def build_chains(problems, floor, lang="eng"):
    """{id: (chain at threshold `floor` with every level, python ms)}."""
    out = {}
    for row in problems:
        t0 = time.perf_counter()
        chain = lineage.lineage(row["id"], lang=lang, min_similarity=floor, max_links=8)
        out[row["id"]] = (chain, 1000 * (time.perf_counter() - t0))
    return out


def cut(chain, threshold, max_links=8):
    kept = sorted((l for l in chain if l["similarity"] >= threshold), key=lambda l: -l["similarity"])[:max_links]
    return sorted(kept, key=lambda l: l["level"])


def summarise(chains, threshold, min_levels, max_links=8):
    lengths = [len(cut(c, threshold, max_links)) for c in chains]
    sims = [l["similarity"] for c in chains for l in cut(c, threshold, max_links)]
    n = len(lengths)
    return {"n": n,
            "with_min": sum(1 for x in lengths if x >= min_levels),
            "mean_len": statistics.mean(lengths) if lengths else 0.0,
            "mean_sim": statistics.mean(sims) if sims else 0.0,
            "full": sum(1 for x in lengths if x == 7)}


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "-"


def report(problems, chains_by_id, thresholds, mains, min_levels, label):
    chains = [chains_by_id[r["id"]][0] for r in problems]
    print(f"\n### {label}: n={len(problems)} problems, chain = best same-topic problem at each other level\n")
    mean, sd, n = random_baseline(problems)
    print(f"Floor: a random same-topic problem of another level scores {mean:.3f} (sd {sd:.3f}, n={n}); "
          f"the best per level scores {summarise(chains, 0.0, min_levels)['mean_sim']:.3f} on average.\n")
    print(f"| threshold | >= {min_levels} links | mean links (of 7) | all 7 levels | mean similarity |")
    print("|---|---|---|---|---|")
    for th in thresholds:
        s = summarise(chains, th, min_levels)
        print(f"| {th:.2f} | {s['with_min']}/{s['n']} = {pct(s['with_min'], s['n'])} | {s['mean_len']:.2f} | "
              f"{pct(s['full'], s['n'])} | {s['mean_sim']:.3f} |")
    for main in mains:
        s5 = summarise(chains, main, min_levels, max_links=5)
        print(f"\nWith the default max_links=5 at {main:.2f}: mean {s5['mean_len']:.2f} links, "
              f">= {min_levels} links {pct(s5['with_min'], s5['n'])}.")

    by_topic = defaultdict(list)
    for r in problems:
        by_topic[topics.get_topic(r["id"])].append(chains_by_id[r["id"]][0])
    print(f"\nPer topic, at thresholds {' and '.join(f'{m:.2f}' for m in mains)}:\n")
    print("| topic | n | " + " | ".join(f">= {min_levels} links @{m:.2f} | mean links @{m:.2f}" for m in mains) + " | mean similarity |")
    print("|---|---|" + "---|---|" * len(mains) + "---|")
    for key in topics.TOPIC_KEYS:
        group = by_topic.get(key, [])
        if not group:
            continue
        cells = []
        for main in mains:
            s = summarise(group, main, min_levels)
            cells.append(f"{s['with_min']}/{s['n']} = {pct(s['with_min'], s['n'])} | {s['mean_len']:.2f}")
        print(f"| {key} | {len(group)} | " + " | ".join(cells) + f" | {summarise(group, 0.0, min_levels)['mean_sim']:.3f} |")

    by_level = defaultdict(list)
    for r in problems:
        by_level[int(r["level"])].append(chains_by_id[r["id"]][0])
    print(f"\nPer level of the query problem, at thresholds {' and '.join(f'{m:.2f}' for m in mains)}:\n")
    print("| level | n | " + " | ".join(f">= {min_levels} links @{m:.2f} | mean links @{m:.2f}" for m in mains) + " |")
    print("|---|---|" + "---|---|" * len(mains))
    for lvl in sorted(by_level):
        cells = []
        for main in mains:
            s = summarise(by_level[lvl], main, min_levels)
            cells.append(f"{pct(s['with_min'], s['n'])} | {s['mean_len']:.2f}")
        print(f"| {lvl} | {len(by_level[lvl])} | " + " | ".join(cells) + " |")


def random_baseline(problems, seed=42):
    """Mean similarity of a query to ONE random same-topic training problem of another level.

    The chain keeps the best candidate per level, so its similarities must be read
    against this floor, not against 0.
    """
    rnd = random.Random(seed)
    catalog = retrieval._catalog()
    sims = []
    for r in problems:
        found = retrieval.query_vector(r["id"], catalog)
        if found is None:
            continue
        vec, level, _e = found
        topic = topics.get_topic(r["id"])
        pool = [v for pid, lvl, top, v in catalog.english if top == topic and lvl != level and pid != r["id"]]
        if pool:
            other = rnd.choice(pool)
            sims.append(sum(a * b for a, b in zip(vec, other)))
    return statistics.mean(sims), statistics.pstdev(sims), len(sims)


def cost(problems, chains_by_id, label):
    ms = [chains_by_id[r["id"]][1] for r in problems]
    embeds = [lineage.embeddings_needed(r["id"]) for r in problems]
    e = statistics.mean(embeds)
    print(f"\n{label}: {e:.0f} embedding(s) per chain x {EMBED_SECONDS} s + Python {statistics.mean(ms):.1f} ms mean "
          f"/ {max(ms):.1f} ms worst on the laptop (n={len(ms)}, first call includes the embedding request) "
          f"-> board estimate {e * EMBED_SECONDS + statistics.mean(ms) / 1000:.2f} s per chain.")


def judge_file(problems, chains_by_id, n, threshold, out, seed=7, exclude=()):
    """n chains with at least 3 links, spread over the topics, with the texts: for the hand judgement.

    `exclude` keeps ids judged in an earlier round out, so a second round is a clean sample.
    """
    rnd = random.Random(seed)
    good = [r for r in problems if len(cut(chains_by_id[r["id"]][0], threshold)) >= 3 and r["id"] not in exclude]
    by_topic = defaultdict(list)
    for r in good:
        by_topic[topics.get_topic(r["id"])].append(r)
    picked = []
    keys = [k for k in topics.TOPIC_KEYS if by_topic.get(k)]
    while len(picked) < n and any(by_topic[k] for k in keys):
        for k in keys:
            if by_topic[k] and len(picked) < n:
                picked.append(by_topic[k].pop(rnd.randrange(len(by_topic[k]))))
    lines = []
    for r in picked:
        chain = cut(chains_by_id[r["id"]][0], threshold, max_links=5)
        lines.append(f"==== QUERY {r['id']} level {r['level']} year {r['year']} topic {topics.get_topic(r['id'])} "
                     f"text_only={r.get('text_only')}")
        lines.append(r["text"].strip().replace("\n", " ")[:600])
        for l in chain:
            lines.append(f"-- link level {l['level']} year {l['year']} {l['id']} sim {l['similarity']} text_only={l.get('text_only')}")
            lines.append(l["text"].strip().replace("\n", " ")[:600])
        lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"{len(picked)} chains with texts written to {out} (keep it out of the repo)")
    json_out = os.path.splitext(out)[0] + ".json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump([{"id": r["id"], "level": r["level"], "topic": topics.get_topic(r["id"]),
                    "links": [{"id": l["id"], "level": l["level"], "year": l["year"], "similarity": l["similarity"]}
                              for l in cut(chains_by_id[r["id"]][0], threshold, max_links=5)]}
                   for r in picked], f, indent=1)
    print(f"ids only: {json_out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(ROOT, "data", "val.jsonl"))
    ap.add_argument("--thresholds", default="0.50,0.60,0.70,0.75,0.80,0.85")
    ap.add_argument("--main", default="0.60,0.75",
                    help="thresholds of the per-topic tables: the signature default and the hand-calibrated one")
    ap.add_argument("--judge-threshold", type=float, default=0.75, help="threshold of the chains written by --judge")
    ap.add_argument("--judge-seed", type=int, default=7)
    ap.add_argument("--judge-exclude", default="", help="comma-separated ids judged before (round 1 used seed 7 at 0.6)")
    ap.add_argument("--min-levels", type=int, default=3)
    ap.add_argument("--train-sample", type=int, default=100, help="training ids timed for the 0-embedding cost")
    ap.add_argument("--judge", type=int, default=0, help="write this many chains with texts for the hand judgement")
    ap.add_argument("--out", default=None, help="judge file (outside the repo)")
    args = ap.parse_args()
    thresholds = [float(t) for t in args.thresholds.split(",")]
    mains = [float(t) for t in args.main.split(",")]
    floor = min(thresholds + mains + [args.judge_threshold])

    val = rows_from(args.input)
    lineage.lineage(val[0]["id"])  # load the catalog outside the timing
    t0 = time.perf_counter()
    val_chains = build_chains(val, floor)
    print(f"{len(val)} validation chains built in {time.perf_counter() - t0:.1f} s on the laptop "
          f"(index: {len(retrieval._catalog().english)} English training vectors).")
    report(val, val_chains, thresholds, mains, args.min_levels, "Validation problems (one embedding each)")
    cost(val, val_chains, "Validation id")

    if args.train_sample:
        train = rows_from(os.path.join(ROOT, "data", "train.jsonl"))
        sample = random.Random(42).sample(train, min(args.train_sample, len(train)))
        train_chains = build_chains(sample, floor)
        report(sample, train_chains, thresholds, mains, args.min_levels, "Training problems, random sample (stored vector)")
        cost(sample, train_chains, "Training id")

    if args.judge:
        out = args.out or os.path.join(os.path.expanduser("~"), "m3kang-data", "judge_lineage.txt")
        exclude = {i.strip() for i in args.judge_exclude.split(",") if i.strip()}
        judge_file(val, val_chains, args.judge, args.judge_threshold, out, args.judge_seed, exclude)


if __name__ == "__main__":
    main()
