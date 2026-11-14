#!/usr/bin/env python3
"""Measure the board's real speed and propose the BOARD_* constants of config.env.

    python3 board/calibrate_speed.py             # measure and print
    python3 board/calibrate_speed.py --write     # also update BOARD_* in config.env

Runs on the board (standard library only), against the two servers from step 7. It sends
a few representative requests and reads the rates llama-server itself reports:
`timings.prompt_per_second` (reading), `timings.predicted_per_second` (writing), and the
wall time of a batch of embeddings. copilot/board_clock.py turns those constants into the
"board estimate" every eval prints, so this is what makes the laptop numbers honest.

Run it with nothing else using the servers. On a laptop it measures the laptop, which is
only useful to check that the script works.
"""
import argparse
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from copilot.client import post  # noqa: E402
from copilot.config import CONFIG, ROOT  # noqa: E402
from copilot.embed import embed  # noqa: E402

LLM = f"http://127.0.0.1:{CONFIG['LLM_PORT']}/v1/chat/completions"
SYSTEM = ("You solve multiple-choice math competition problems for school students. "
          "Read the problem and the options, then reply with the letter of the correct option.")
# A problem-sized text, repeated to make prompts of 1x, 2x and 3x (about 90, 180, 270 tokens)
PROBLEM = ("Anna has 3 bags with 4 apples in each bag. She eats 2 apples and gives 3 to Ben. "
           "Ben already had 5 apples. How many apples do they have together now?\n"
           "A) 12\nB) 15\nC) 17\nD) 20\nE) 22\nAnswer:")
TEXTS = ["How many apples are left?", "A triangle has three sides.", "The sum of five consecutive numbers is 105.",
         "Three friends share 24 marbles equally.", "A square has a perimeter of 36 cm."] * 4


def chat(user, max_tokens, grammar=None, cache=False):
    payload = {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
               "max_tokens": max_tokens, "temperature": 0, "seed": int(CONFIG["SEED"]), "cache_prompt": cache}
    if grammar:
        payload["grammar"] = grammar
    t = time.perf_counter()
    r = post(LLM, payload, timeout=300)
    return r["timings"], time.perf_counter() - t


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true", help="update BOARD_PREFILL_TPS, BOARD_GEN_TPS, BOARD_EMBED_SECONDS in config.env")
    p.add_argument("--rounds", type=int, default=2)
    args = p.parse_args()

    prefill, gen, overhead = [], [], []
    print("Reading speed (prefill), prompts of 1x, 2x, 3x a problem, one letter out:")
    for _ in range(args.rounds):
        for k in (1, 2, 3):
            t, wall = chat("\n\n".join([PROBLEM] * k), 1, grammar="root ::= [A-E]", cache=False)
            prefill.append(t["prompt_per_second"])
            overhead.append(wall - t["prompt_ms"] / 1000 - t["predicted_ms"] / 1000)
            print(f"  {t['prompt_n']:4d} tokens read at {t['prompt_per_second']:6.1f} tok/s, wall {wall:.2f} s")
    print("Writing speed (generation), short prompt, 60 tokens out:")
    for _ in range(args.rounds):
        t, wall = chat("Count from one to thirty in words, separated by commas.", 60, cache=False)
        gen.append(t["predicted_per_second"])
        print(f"  {t['predicted_n']:4d} tokens written at {t['predicted_per_second']:6.1f} tok/s, wall {wall:.2f} s")
    print(f"Embeddings, {len(TEXTS)} short texts:")
    secs = []
    for _ in range(args.rounds):
        t0 = time.perf_counter()
        embed(TEXTS)
        secs.append((time.perf_counter() - t0) / len(TEXTS))
        print(f"  {secs[-1] * 1000:.0f} ms per text")

    P, G, E = statistics.median(prefill), statistics.median(gen), statistics.median(secs)
    print("\nMeasured medians:")
    print(f"  BOARD_PREFILL_TPS={P:.1f}      (config.env now: {CONFIG['BOARD_PREFILL_TPS']})")
    print(f"  BOARD_GEN_TPS={G:.1f}          (config.env now: {CONFIG['BOARD_GEN_TPS']})")
    print(f"  BOARD_EMBED_SECONDS={E:.3f}    (config.env now: {CONFIG['BOARD_EMBED_SECONDS']})")
    print(f"  HTTP + Python overhead per request: {statistics.median(overhead) * 1000:.0f} ms (not in the estimate)")
    if not args.write:
        print("\nRun with --write to put these values in config.env, then commit it.")
        return
    path = os.path.join(ROOT, "config.env")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for key, value in (("BOARD_PREFILL_TPS", f"{P:.1f}"), ("BOARD_GEN_TPS", f"{G:.1f}"), ("BOARD_EMBED_SECONDS", f"{E:.3f}")):
        text, n = re.subn(rf"^{key}=.*$", f"{key}={value}", text, flags=re.M)
        if n != 1:
            sys.exit(f"{key} not found exactly once in config.env")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nWrote {path}. Commit it with the date and the board it was measured on.")


if __name__ == "__main__":
    main()
