#!/usr/bin/env python3
"""Phase 7: does searching with the Catalan text find the same neighbours as the English text?

    python3 laptop/catalan_bridge.py --n 60 --k 5

For a sample of validation ids, the Catalan and the English text of the SAME problem are
embedded (bge-small is English-only) and the k nearest English training problems are
retrieved with each. The report gives the overlap of the two neighbour sets, how often
the top-1 neighbour is the same, and how often the neighbours share the problem's topic.
Pair it with `eval.py --languages cat` vs `--languages eng` on the same --limit.
"""
import argparse
import json
import os
import random
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from copilot import retrieval, topics  # noqa: E402
from copilot.embed import embed  # noqa: E402
from copilot.llm import format_problem  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n", type=int, default=60)
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--input", default=os.path.join(ROOT, "data", "val.jsonl"))
    args = p.parse_args()

    by_id = {}
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            by_id.setdefault(r["id"], {})[r["language"]] = r
    ids = sorted(i for i, langs in by_id.items() if "eng" in langs and "cat" in langs)
    sample = random.Random(42).sample(ids, min(args.n, len(ids)))

    catalog = retrieval._catalog()
    overlaps, same_top1, topic_eng, topic_cat, topic_agree_top1 = [], 0, [], [], 0
    for pid in sample:
        eng, cat = by_id[pid]["eng"], by_id[pid]["cat"]
        v_eng, v_cat = embed([format_problem(eng), format_problem(cat)])
        topic = topics.get_topic(pid)
        all_levels = list(retrieval.LEVELS)
        # no level or topic filter: pure retrieval quality
        pool = [(i, vec) for i, _l, _t, vec in catalog.english if i != pid]
        def top(v):
            scored = sorted(((sum(a * b for a, b in zip(v, vec)), i) for i, vec in pool), reverse=True)
            return [i for _s, i in scored[:args.k]]
        n_eng, n_cat = top(v_eng), top(v_cat)
        overlaps.append(len(set(n_eng) & set(n_cat)) / args.k)
        same_top1 += n_eng[0] == n_cat[0]
        topic_eng.append(sum(topics.get_topic(i) == topic for i in n_eng) / args.k)
        topic_cat.append(sum(topics.get_topic(i) == topic for i in n_cat) / args.k)
        topic_agree_top1 += topics.get_topic(n_eng[0]) == topics.get_topic(n_cat[0])

    n = len(sample)
    print(f"Catalan vs English query on the same {n} validation ids, k={args.k}, English training index")
    print(f"  overlap of the k neighbours (cat ∩ eng / k): mean {100 * statistics.mean(overlaps):.0f}%")
    print(f"  same top-1 neighbour:                        {same_top1}/{n} = {100 * same_top1 / n:.0f}%")
    print(f"  top-1 neighbours share a topic (cat vs eng):  {topic_agree_top1}/{n} = {100 * topic_agree_top1 / n:.0f}%")
    print(f"  neighbours with the problem's own topic:      eng query {100 * statistics.mean(topic_eng):.0f}%, "
          f"cat query {100 * statistics.mean(topic_cat):.0f}%")


if __name__ == "__main__":
    main()
