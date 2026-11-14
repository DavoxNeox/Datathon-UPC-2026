#!/usr/bin/env python3
"""Phase 3 bis measurements for copilot/retrieval.neighbors().

    python3 laptop/measure_retrieval.py --timing 30          # ms per query, train ids vs val ids
    python3 laptop/measure_retrieval.py --judge 20 --out /path/judge.txt   # texts to judge by hand (NOT in the repo)

Timing: train ids reuse the stored vector (no embedding); val ids embed the English text
once (BOARD_EMBED_SECONDS each). The Python part is measured on the laptop and reported
as is: the board's CPU is slower, so it is a lower bound there.
"""
import argparse
import json
import os
import random
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from copilot import retrieval, topics  # noqa: E402
from copilot.board_clock import EMBED_SECONDS  # noqa: E402


def ids_from(path, language="eng"):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip() and f'"{language}"' in l]


def timing(n):
    rnd = random.Random(42)
    train = [r["id"] for r in ids_from(os.path.join(ROOT, "data", "train.jsonl"))]
    val = [r["id"] for r in ids_from(os.path.join(ROOT, "data", "val.jsonl"))]
    retrieval.neighbors(train[0])  # load the catalog once, outside the timing
    for name, pool, embeds in (("train id (stored vector)", train, 0), ("val id (one embedding)", val, 1)):
        sample = rnd.sample(pool, n)
        times = []
        for pid in sample:
            retrieval._QUERY_CACHE.pop(pid, None)
            t0 = time.perf_counter()
            hits = retrieval.neighbors(pid, level_delta=-1, same_topic=True, lang="cat", k=1)
            times.append(1000 * (time.perf_counter() - t0))
            assert all(h["id"] != pid for h in hits)
        mean, worst = statistics.mean(times), max(times)
        print(f"{name:26} n={n}: laptop mean {mean:6.1f} ms, median {statistics.median(times):6.1f} ms, worst {worst:6.1f} ms"
              f" | board estimate: {embeds} embedding x {EMBED_SECONDS} s + Python = {embeds * EMBED_SECONDS + mean / 1000:.2f} s"
              f" (Python part measured on the laptop)")
    t0 = time.perf_counter()
    retrieval._INDEX = None
    retrieval._catalog()
    print(f"catalog load: {time.perf_counter() - t0:.2f} s ({len(retrieval._INDEX.by_key)} rows, "
          f"{len(retrieval._INDEX.english)} English vectors)")


def judge(n, out):
    rnd = random.Random(7)
    val = ids_from(os.path.join(ROOT, "data", "val.jsonl"))
    val = [r for r in val if r["level"] >= 1]
    sample = rnd.sample(val, n)
    lines, rows = [], []
    for r in sample:
        hits = retrieval.neighbors(r["id"], level_delta=-1, same_topic=True, lang="eng", k=1)
        h = hits[0] if hits else None
        rows.append({"id": r["id"], "level": r["level"], "topic": topics.get_topic(r["id"]),
                     "neighbor": h and h["id"], "n_level": h and h["level"], "n_topic": h and h["topic"],
                     "similarity": h and h["similarity"]})
        lines.append(f"=== {r['id']} L{r['level']} {topics.get_topic(r['id'])} text_only={r['text_only']}\n{r['text']}\n"
                     f"--- neighbour {h and h['id']} L{h and h['level']} {h and h['topic']} sim={h and h['similarity']}\n"
                     f"{h and h['text']}\n")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"{n} pairs written to {out} (problem texts: keep it out of the repo)")
    print(json.dumps(rows, indent=0))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--timing", type=int, default=0)
    p.add_argument("--judge", type=int, default=0)
    p.add_argument("--out", default="")
    args = p.parse_args()
    if args.timing:
        timing(args.timing)
    if args.judge:
        judge(args.judge, args.out or os.path.join(os.path.expanduser("~"), "m3kang-data", "judge_neighbors.txt"))


if __name__ == "__main__":
    main()
