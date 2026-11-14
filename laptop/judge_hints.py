#!/usr/bin/env python3
"""Generate, measure and judge the LLM hints of the ladder (rung 3b), topic by topic.

    python3 laptop/judge_hints.py generate --input data/val.jsonl --per-topic 10
        Writes results/hints_<name>.jsonl (gitignored: it holds hint texts) and prints the
        measurements: leak rate (first hint rejected by the filter), rejection after the retry,
        prompt_n and board seconds with and without prefetch, rung 1 and 2 latency.
    python3 laptop/judge_hints.py judge --judge "your name"
        Shows the hints one at a time (problem, image path, correct answer, hint) and records
        good/bad + reason in data_curated/hint_quality.json: only ids, topic, verdict and the
        percentage per topic. No problem text is written there.
    python3 laptop/judge_hints.py report
        The quality table per topic, and which topics the ladder may ask the LLM for.

Runs on the laptop against the same llama-server flags as the board. Standard library only.
"""
import argparse
import contextlib
import datetime
import io
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot import hints, topics  # noqa: E402
from copilot.config import ROOT  # noqa: E402

RESULTS = os.path.join(ROOT, "results")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--input", default="data/val.jsonl" if os.path.exists(os.path.join(ROOT, "data", "val.jsonl"))
                   else "data/sample_problems.jsonl")
    g.add_argument("--per-topic", type=int, default=10, help="problems per topic (0 = all)")
    g.add_argument("--lang", default="eng", help="language of the problems to take from --input (any = all)")
    g.add_argument("--prefetch-per-topic", type=int, default=3,
                   help="on this many problems per topic, measure prompt_n again after a prefetch")
    g.add_argument("--name", default=None, help="results/hints_<name>.jsonl; default: the input's basename")
    j = sub.add_parser("judge")
    j.add_argument("--name", default=None)
    j.add_argument("--judge", default=os.environ.get("USER", "team"))
    j.add_argument("--per-topic", type=int, default=10)
    j.add_argument("--open-images", action="store_true", help="open the problem image with the OS viewer")
    sub.add_parser("report")
    return p.parse_args()


def load_problems(path, lang):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    rows = [r for r in rows if r.get("options") and r.get("label") in r["options"]]
    same = [r for r in rows if lang == "any" or r.get("language") == lang]
    return same or rows


def topic_of(problem):
    return problem.get("topic") or topics.get_topic(problem["id"])


def results_path(name, input_path=None):
    name = name or os.path.splitext(os.path.basename(input_path or "hints"))[0]
    return os.path.join(RESULTS, f"hints_{name}.jsonl")


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


def generate(args):
    problems = load_problems(args.input, args.lang)
    by_topic = {}
    for p in problems:
        by_topic.setdefault(topic_of(p), []).append(p)
    chosen = []
    for key in topics.TOPIC_KEYS:
        rows = by_topic.get(key, [])
        chosen += rows[:args.per_topic] if args.per_topic else rows
    print(f"{len(problems)} problems with options in {args.input}; generating hints for {len(chosen)} "
          f"({', '.join(f'{k}:{len(by_topic.get(k, []))}' for k in topics.TOPIC_KEYS)})", flush=True)
    os.makedirs(RESULTS, exist_ok=True)
    out_path = results_path(args.name, args.input)
    rows, seen_prefetch = [], {}
    for i, p in enumerate(chosen, 1):
        hints.register_problem(p)
        topic = topic_of(p)
        t = time.perf_counter(); hints.reset(p["id"]); r1 = quiet(hints.get_hint, p["id"], 1, "cat"); ms1 = (time.perf_counter() - t) * 1000
        t = time.perf_counter(); r2 = quiet(hints.get_hint, p["id"], 2, "cat"); ms2 = (time.perf_counter() - t) * 1000
        # cold: the slot holds the previous problem's prompt, as on the board without prefetch
        t = time.perf_counter(); cold = hints.llm_hint(p, "cat"); laptop_s = time.perf_counter() - t
        row = {"id": p["id"], "language": p.get("language"), "level": p.get("level"), "topic": topic,
               "label": p["label"], "value": p["options"].get(p["label"]),
               "ok": cold["ok"], "attempts": cold["attempts"], "rejected": cold["rejected"],
               "text_ca": cold["text_ca"], "text_en": cold["text_en"],
               "prompt_n_cold": cold["prompt_n"], "predicted_n": cold["predicted_n"],
               "board_s_cold": round(cold["estimated_board_seconds"], 2), "laptop_s": round(laptop_s, 2),
               "rung1_ms": round(ms1, 2), "rung2_ms": round(ms2, 2), "rung1_neighbour": (r1.get("problem") or {}).get("id"),
               "rung2_manipulative": r2.get("manipulative")}
        if seen_prefetch.get(topic, 0) < args.prefetch_per_topic:
            seen_prefetch[topic] = seen_prefetch.get(topic, 0) + 1
            warm = hints.warm(p["id"], "cat")
            t = time.perf_counter(); hot = hints.llm_hint(p, "cat"); hot_s = time.perf_counter() - t
            row.update(warm_prompt_n=warm.get("prompt_n"), prompt_n_warm=hot["prompt_n"],
                       board_s_warm=round(hot["estimated_board_seconds"], 2), laptop_s_warm=round(hot_s, 2),
                       same_text_after_prefetch=hot["text_ca"] == cold["text_ca"])
        rows.append(row)
        flag = "ok " if cold["ok"] else "REJ"
        print(f"[{i}/{len(chosen)}] {p['id']} {topic:10s} {flag} tries={cold['attempts']} prompt_n={cold['prompt_n']}"
              f"{' warm=' + str(row['prompt_n_warm']) if 'prompt_n_warm' in row else ''} "
              f"gen={cold['predicted_n']} board={cold['estimated_board_seconds']:.1f}s | {cold['text_ca'][:70]}", flush=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\nWrote {out_path}")
    summarize(rows)


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else float("nan")


def summarize(rows):
    n = len(rows)
    if not n:
        return
    first_leak = sum(1 for r in rows if r["rejected"] and not r["rejected"][0].startswith("error"))
    final_reject = sum(1 for r in rows if not r["ok"])
    warm_rows = [r for r in rows if "prompt_n_warm" in r]
    print(f"\n=== LLM hints, n={n}")
    print(f"first hint rejected by the leak filter : {first_leak}/{n} = {100 * first_leak / n:.0f}%")
    print(f"still rejected after the strict retry  : {final_reject}/{n} = {100 * final_reject / n:.0f}%")
    print(f"rejection reasons                      : {sorted(set(x for r in rows for x in r['rejected']))}")
    print(f"prompt_n without prefetch (2 calls)    : mean {mean([r['prompt_n_cold'] for r in rows]):.0f}")
    if warm_rows:
        print(f"prompt_n with prefetch    (2 calls)    : mean {mean([r['prompt_n_warm'] for r in warm_rows]):.0f}  (n={len(warm_rows)})")
    print(f"generated tokens (both languages)      : mean {mean([r['predicted_n'] for r in rows]):.0f}")
    print(f"board seconds, rung 3 without prefetch : mean {mean([r['board_s_cold'] for r in rows]):.1f}  max {max(r['board_s_cold'] for r in rows):.1f}")
    if warm_rows:
        print(f"board seconds, rung 3 with prefetch    : mean {mean([r['board_s_warm'] for r in warm_rows]):.1f}  max {max(r['board_s_warm'] for r in warm_rows):.1f}")
    print(f"laptop seconds, rung 3 (shared server) : mean {mean([r['laptop_s'] for r in rows]):.1f}")
    print(f"rung 1 ms: mean {mean([r['rung1_ms'] for r in rows]):.2f}   rung 2 ms: mean {mean([r['rung2_ms'] for r in rows]):.2f}")
    print("\nper topic: n  first-leak  final-reject  board_s_cold")
    for key in topics.TOPIC_KEYS:
        t = [r for r in rows if r["topic"] == key]
        if t:
            print(f"  {key:10s} {len(t):3d}  {sum(1 for r in t if r['rejected']):3d}        {sum(1 for r in t if not r['ok']):3d}        {mean([r['board_s_cold'] for r in t]):.1f}")


def load_quality():
    if os.path.exists(hints.QUALITY_FILE):
        with open(hints.QUALITY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"topics": {}}


def save_quality(data):
    for key, row in data["topics"].items():
        row["n"] = len(row["judgements"])
        row["good"] = sum(1 for j in row["judgements"] if j["verdict"] == "good")
        row["percent"] = round(100 * row["good"] / row["n"], 1) if row["n"] else 0
    data["min_percent"] = hints.QUALITY_MIN
    data["updated"] = datetime.date.today().isoformat()
    with open(hints.QUALITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def judge(args):
    path = results_path(args.name)
    if not args.name:
        candidates = sorted((f for f in os.listdir(RESULTS) if f.startswith("hints_")), key=lambda f: os.path.getmtime(os.path.join(RESULTS, f)))
        if not candidates:
            sys.exit("No results/hints_*.jsonl yet: run `generate` first")
        path = os.path.join(RESULTS, candidates[-1])
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    data = load_quality()
    data["judge"] = args.judge
    done = {(t, j["id"]) for t, row in data["topics"].items() for j in row["judgements"]}
    print(f"Judging {path}. Keys: g = good (helps without giving it away), b = bad, s = skip, q = quit.")
    count = {}
    for row in rows:
        if not row["ok"] or (row["topic"], row["id"]) in done or count.get(row["topic"], 0) >= args.per_topic:
            continue
        problem = hints.problem_for(row["id"], row["language"] or "eng") or {}
        image = hints._image_path(row["id"], row["language"] or "eng")
        print("\n" + "=" * 78)
        print(f"{row['id']} · topic {row['topic']} · level {row['level']} · {row['language']}")
        print(problem.get("text", "(text not found: link data/*.jsonl)"))
        if problem.get("options"):
            print("   " + "  ".join(f"{k}) {v}" for k, v in sorted(problem["options"].items())))
        if image:
            print(f"   image: {image}")
            if args.open_images:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", os.path.join(ROOT, image)])
        print(f"   correct: {row['label']} ({row['value']})")
        print(f"   HINT ca: {row['text_ca']}")
        print(f"   HINT en: {row['text_en']}")
        while True:
            answer = input("   good / bad / skip / quit [g/b/s/q]: ").strip().lower()
            if answer in ("g", "b", "s", "q"):
                break
        if answer == "q":
            break
        if answer == "s":
            continue
        reason = input("   reason (short): ").strip()
        verdict = "good" if answer == "g" else "bad"
        data["topics"].setdefault(row["topic"], {"judgements": []})["judgements"].append(
            {"id": row["id"], "verdict": verdict, "reason": reason})
        count[row["topic"]] = count.get(row["topic"], 0) + 1
        save_quality(data)
    save_quality(data)
    report(args)


def report(_args):
    data = load_quality()
    print(f"\nHint quality by topic (data_curated/hint_quality.json, judge: {data.get('judge', '?')}, "
          f"updated {data.get('updated', '?')}, LLM allowed from {hints.QUALITY_MIN:.0f}%)")
    print(f"{'topic':12s} {'n':>3s} {'good':>5s} {'percent':>8s}  LLM")
    for key in topics.TOPIC_KEYS:
        row = data["topics"].get(key)
        if row and row.get("n"):
            allowed = "yes" if row["percent"] >= hints.QUALITY_MIN else "no"
            print(f"{key:12s} {row['n']:3d} {row['good']:5d} {row['percent']:7.0f}%  {allowed}")
        else:
            print(f"{key:12s}   0     -        -  no (not judged)")


def main():
    args = parse_args()
    {"generate": generate, "judge": judge, "report": report}[args.command](args)


if __name__ == "__main__":
    main()
