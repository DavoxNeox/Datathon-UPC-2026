#!/usr/bin/env python3
"""Phase 3b: combine the keyword topics with k-means clusters of the index embeddings.

Laptop only, pure Python (no numpy): the vectors come from data/index.db (English rows).

    python3 laptop/cluster_topics.py --k 12 --out data_curated/topics.json
    python3 laptop/cluster_topics.py --k 12 --manual data_curated/topics_manual.json   # report agreement

Method:
1. k-means (k-means++ seeding, seed 42, cosine on unit vectors) over the English vectors.
2. Every cluster is labelled with the majority keyword topic of its members.
3. A problem keeps its keyword topic when the keywords are confident (best score >= MIN_SCORE
   and a margin >= MIN_MARGIN over the runner-up); otherwise it takes its cluster's label.
4. visual flag per topic = most of its problems have text_only == false.

With --manual, the script reports the agreement of the keyword-only and the combined
assignment with the hand labels, which is the number Phase 3b is judged by.
"""
import argparse
import json
import os
import random
import sqlite3
import sys
from array import array
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_topics import TOPIC_KEYS, PRIORITY, keyword_scores, keyword_topic, visual_flags  # noqa: E402

MIN_SCORE = 4
MIN_MARGIN = 2


def load_vectors(db_path, language="eng"):
    db = sqlite3.connect(db_path)
    rows = {}
    for key, problem, blob in db.execute("SELECT key, problem, vec FROM problems"):
        p = json.loads(problem)
        if p.get("language") != language:
            continue
        vec = array("f")
        vec.frombytes(blob)
        rows[p["id"]] = (p, list(vec))
    db.close()
    return rows


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def kmeans(vectors, k, iterations=30, seed=42):
    """Return (assignments, centroids). Vectors are unit length, so cosine = dot."""
    rnd = random.Random(seed)
    ids = list(vectors)
    # k-means++ seeding
    centroids = [vectors[rnd.choice(ids)]]
    while len(centroids) < k:
        dists = [min(1 - dot(vectors[i], c) for c in centroids) for i in ids]
        total = sum(dists) or 1.0
        r, acc = rnd.random() * total, 0.0
        for i, d in zip(ids, dists):
            acc += d
            if acc >= r:
                centroids.append(vectors[i])
                break
    assign = {}
    for _ in range(iterations):
        new_assign = {i: max(range(k), key=lambda c: dot(vectors[i], centroids[c])) for i in ids}
        if new_assign == assign:
            break
        assign = new_assign
        sums = [[0.0] * len(centroids[0]) for _ in range(k)]
        counts = [0] * k
        for i, c in assign.items():
            counts[c] += 1
            v = vectors[i]
            s = sums[c]
            for d in range(len(v)):
                s[d] += v[d]
        for c in range(k):
            if counts[c]:
                norm = sum(x * x for x in sums[c]) ** 0.5 or 1.0
                centroids[c] = [x / norm for x in sums[c]]
    return assign, centroids


def combine(rows, assign):
    """{id: topic} from keywords, with the cluster label where the keywords are weak."""
    kw_topic = {pid: keyword_topic(p["text"]) for pid, (p, _v) in rows.items()}
    cluster_label = {}
    members = defaultdict(list)
    for pid, c in assign.items():
        members[c].append(pid)
    for c, ids in members.items():
        votes = Counter(kw_topic[i] for i in ids)
        best = max(votes.values())
        cluster_label[c] = next(t for t in PRIORITY if votes.get(t) == best)
    final, source = {}, Counter()
    for pid, (p, _v) in rows.items():
        scores = keyword_scores(p["text"])
        ranked = scores.most_common(2)
        best = ranked[0][1] if ranked else 0
        second = ranked[1][1] if len(ranked) > 1 else 0
        if best >= MIN_SCORE and best - second >= MIN_MARGIN:
            final[pid] = kw_topic[pid]
            source["keywords"] += 1
        else:
            final[pid] = cluster_label[assign[pid]]
            source["cluster"] += 1
    return final, kw_topic, cluster_label, members, source


def agreement(auto, manual):
    both = [i for i in manual if i in auto]
    hits = sum(1 for i in both if auto[i] == manual[i])
    return hits, len(both)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=os.path.join(ROOT, "data", "index.db"))
    p.add_argument("--extra", nargs="*", default=[os.path.join(ROOT, "data", "val.jsonl")],
                   help="jsonl files whose English rows get a topic too (keywords only, no vector)")
    p.add_argument("--k", type=int, default=12)
    p.add_argument("--out", default="", help="write topics.json here (ids and keys only)")
    p.add_argument("--manual", default="", help="hand labels {id: topic} to report the agreement")
    args = p.parse_args()

    rows = load_vectors(args.db)
    vectors = {pid: v for pid, (_p, v) in rows.items()}
    print(f"{len(rows)} English vectors from {args.db}; k-means k={args.k} ...", flush=True)
    assign, _centroids = kmeans(vectors, args.k)
    final, kw_topic, cluster_label, members, source = combine(rows, assign)

    print(f"\nClusters (label = majority keyword topic of the members):")
    for c in sorted(members, key=lambda c: -len(members[c])):
        votes = Counter(kw_topic[i] for i in members[c])
        visual = sum(1 for i in members[c] if not rows[i][0].get("text_only")) / len(members[c])
        top3 = ", ".join(f"{t} {n}" for t, n in votes.most_common(3))
        print(f"  cluster {c:2} n={len(members[c]):4} needs figure {100 * visual:3.0f}%  -> {cluster_label[c]:11} [{top3}]")
    print(f"\nAssignment source: {dict(source)}")
    changed = sum(1 for i in final if final[i] != kw_topic[i])
    print(f"Changed by the clusters: {changed}/{len(final)} ({100 * changed / len(final):.1f}%)")

    # Problems outside the index (validation) get the keyword topic
    english = {pid: p for pid, (p, _v) in rows.items()}
    for path in args.extra:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    if r.get("language") == "eng" and r["id"] not in final:
                        final[r["id"]] = keyword_topic(r["text"])
                        english[r["id"]] = r
    counts = Counter(final.values())
    flags = visual_flags(final, english)
    print(f"\nTopics over {len(final)} ids:")
    for key in TOPIC_KEYS:
        print(f"  {key:11} {counts[key]:5} {100 * counts[key] / len(final):5.1f}%  visual={flags[key]}")

    if args.manual:
        with open(args.manual, encoding="utf-8") as f:
            manual = json.load(f)["topics"]
        kw_all = {i: kw_topic.get(i) or keyword_topic(english[i]["text"]) for i in manual if i in english}
        h1, n1 = agreement(kw_all, manual)
        h2, n2 = agreement(final, manual)
        print(f"\nAgreement with {len(manual)} hand labels:")
        print(f"  keywords only : {h1}/{n1} = {100 * h1 / max(1, n1):.0f}%")
        print(f"  keywords+kmeans: {h2}/{n2} = {100 * h2 / max(1, n2):.0f}%")
        confusion = Counter((manual[i], final[i]) for i in manual if i in final and final[i] != manual[i])
        if confusion:
            print("  disagreements (manual -> auto):", ", ".join(f"{m}->{a} x{n}" for (m, a), n in confusion.most_common()))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"method": f"keywords on the English text + k-means (k={args.k}, seed 42) on the index embeddings "
                                 f"(laptop/cluster_topics.py); ids only, no problem text",
                       "n": len(final), "visual": flags, "topics": dict(sorted(final.items()))}, f, indent=0)
            f.write("\n")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
