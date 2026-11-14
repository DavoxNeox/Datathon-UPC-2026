#!/usr/bin/env python3
"""Learn the option prior (copilot/prior.py) on the training problems and write data_curated/option_prior.json.

    python3 laptop/learn_prior.py                         # learn on data/train.jsonl (English), print the tables, write the json
    python3 laptop/learn_prior.py --cv 5                  # 5-fold cross-validation INSIDE train of several stratifications
    python3 laptop/learn_prior.py --validate              # also score the learned policy ONCE on data/val.jsonl, with a bootstrap
    python3 laptop/learn_prior.py --strata level,picture,kind --min-gain 10

Protocol (docs/reason-experiments.md, experiment 5). A stratification is a list of dimensions (level 0-7,
picture/text, kind of options, order of the values, ...). For every stratum the script counts how many
training problems each candidate rule gets right, where a rule that does not apply to a problem falls back
to the current policy (middle value for five distinct numeric options, else FALLBACK_ANSWER). A stratum
keeps the best rule only when it beats the current policy by at least --min-gain problems there; every
other stratum keeps the current policy (chosen = null). Several stratifications may be learned, finest
first (--strata "level,picture,kind;kind,order;kind"): the first stratum with a rule that applies answers.
The json holds counts and rule names only, never a problem text.
"""
import argparse
import json
import os
import random
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from copilot import prior  # noqa: E402
from copilot.config import CONFIG  # noqa: E402

LETTERS = "ABCDE"
RANKS = ["min", "second_smallest", "middle", "second_largest", "max"]
RULES = list(LETTERS) + RANKS + ["none_option"]
FALLBACK = CONFIG.get("FALLBACK_ANSWER", "D")
MAIN = "level,picture,kind"
# The stratifications the cross-validation compares (each alone and the hierarchy of all of them)
CANDIDATES = [MAIN, "level,kind", "picture,kind", "level", "kind", "picture", "kind,order", "kind,fraction",
              "kind,pi_root", "kind,none_text", "kind,distinct", "language,kind"]


def parse_strata(text):
    return [tuple(d.strip() for d in part.split(",") if d.strip()) for part in text.split(";") if part.strip()]


def read(path, languages):
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    rows = [r for r in rows if not languages or r.get("language") in languages]
    return [(r, prior.features(r)) for r in rows]


def hits_of(rule, rows):
    """How many rows the rule gets right, the current policy answering where it abstains."""
    right = 0
    for problem, feats in rows:
        letter = prior.apply_rule(rule, problem, feats) if rule else None
        if letter is None:
            letter = prior.default_letter(problem, feats, FALLBACK)
        right += letter == problem["label"]
    return right


def learn_one(rows, dims, min_gain):
    """{"dims": [...], "strata": {key: {...}}} for one stratification."""
    strata = {}
    for problem, feats in rows:
        key = prior.stratum_key(feats, dims)
        if key is not None:
            strata.setdefault(key, []).append((problem, feats))
    table = {}
    for key in sorted(strata, key=lambda k: [int(v) if v.lstrip("-").isdigit() else v for v in (p.split("=")[1] for p in k.split("|"))]):
        group = strata[key]
        letters = Counter(p["label"] for p, _ in group)
        default = hits_of(None, group)
        scores = {rule: hits_of(rule, group) for rule in RULES}
        best = max(scores, key=lambda r: (scores[r], -RULES.index(r)))
        gain = scores[best] - default
        table[key] = {"n": len(group), "letters": {l: letters.get(l, 0) for l in LETTERS},
                      "most_frequent_letter": letters.most_common(1)[0][0], "default_hits": default,
                      "best_rule": best, "best_hits": scores[best], "gain": gain,
                      "chosen": best if gain >= min_gain else None, "rules": scores}
    return {"dims": list(dims), "strata": table}


def learn(rows, stratifications, min_gain):
    return {"stratifications": [learn_one(rows, dims, min_gain) for dims in stratifications]}


def policy_letter(problem, feats, table):
    letter = prior.choose(problem, table)
    return letter if letter is not None else prior.default_letter(problem, feats, FALLBACK)


def score(rows, table):
    """(policy hits, current-policy hits, per-problem (policy right, current right) pairs) on rows."""
    pairs = [(policy_letter(p, f, table) == p["label"], prior.default_letter(p, f, FALLBACK) == p["label"]) for p, f in rows]
    return sum(a for a, _ in pairs), sum(b for _, b in pairs), pairs


def bootstrap(pairs, resamples=1000, seed=42):
    """Paired bootstrap of the gain (policy hits minus current-policy hits) over the problems."""
    rng = random.Random(seed)
    n = len(pairs)
    gains = sorted(sum(a - b for a, b in (pairs[rng.randrange(n)] for _ in range(n))) for _ in range(resamples))
    return {"resamples": resamples, "seed": seed, "mean": round(sum(gains) / resamples, 2),
            "p2.5": gains[int(0.025 * resamples)], "p97.5": gains[min(resamples - 1, int(0.975 * resamples))],
            "at_or_under_zero": sum(g <= 0 for g in gains) / resamples}


def cross_validate(rows, stratifications, min_gain, folds, seeds=(42, 43, 44)):
    """Mean out-of-fold gain of the learning procedure over the whole training set, per seed."""
    gains = []
    for seed in seeds:
        order = list(range(len(rows)))
        random.Random(seed).shuffle(order)
        gain = 0
        for k in range(folds):
            held = set(order[k::folds])
            train = [rows[i] for i in range(len(rows)) if i not in held]
            test = [rows[i] for i in sorted(held)]
            table = learn(train, stratifications, min_gain)
            hits, default, _ = score(test, table)
            gain += hits - default
        gains.append(gain)
    return gains


def strata_report(stratification):
    lines = [f"Stratification {'/'.join(stratification['dims'])}",
             "| stratum | n | letters A B C D E | current policy | best rule | hits | gain | chosen |",
             "| --- | ---: | --- | ---: | --- | ---: | ---: | --- |"]
    for key, row in stratification["strata"].items():
        letters = " ".join(str(row["letters"][l]) for l in LETTERS)
        chosen = f"`{row['chosen']}`" if row["chosen"] else ""
        lines.append(f"| {key} | {row['n']} | {letters} | {row['default_hits']} | `{row['best_rule']}` | {row['best_hits']} | "
                     f"{row['gain']:+d} | {chosen} |")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--train", default=os.path.join(ROOT, "data", "train.jsonl"))
    p.add_argument("--val", default=os.path.join(ROOT, "data", "val.jsonl"))
    p.add_argument("--languages", default="eng", help="comma-separated; empty = all")
    p.add_argument("--min-gain", type=int, default=prior.MIN_GAIN)
    p.add_argument("--strata", default=MAIN, help='stratifications, finest first, e.g. "level,picture,kind;kind,order"')
    p.add_argument("--out", default=os.path.join(ROOT, prior.DEFAULT_PATH))
    p.add_argument("--cv", type=int, default=0, metavar="FOLDS", help="cross-validate the candidate stratifications inside train")
    p.add_argument("--validate", action="store_true", help="score the learned policy on --val (the one look)")
    p.add_argument("--resamples", type=int, default=1000)
    args = p.parse_args()
    languages = set(filter(None, args.languages.split(",")))
    stratifications = parse_strata(args.strata)

    train = read(args.train, languages)
    print(f"Training: {len(train)} problems ({','.join(sorted(languages)) or 'all languages'}), min gain {args.min_gain}")

    if args.cv:
        print(f"\n{args.cv}-fold cross-validation inside train, out-of-fold gain over the current policy, seeds 42/43/44 "
              f"(min gain {args.min_gain}):")
        print("| stratification | strata on all train | chosen on all train | out-of-fold gain per seed | mean |")
        print("| --- | ---: | ---: | --- | ---: |")
        for text in CANDIDATES + [";".join(CANDIDATES)]:
            strata = parse_strata(text)
            table = learn(train, strata, args.min_gain)
            n_strata = sum(len(s["strata"]) for s in table["stratifications"])
            chosen = sum(1 for s in table["stratifications"] for row in s["strata"].values() if row["chosen"])
            gains = cross_validate(train, strata, args.min_gain, args.cv)
            label = text if len(strata) == 1 else "all of the above, finest first"
            print(f"| {label} | {n_strata} | {chosen} | {' / '.join(f'{g:+d}' for g in gains)} | {sum(gains) / len(gains):+.1f} |")

    table = learn(train, stratifications, args.min_gain)
    for stratification in table["stratifications"]:
        print()
        print(strata_report(stratification))
    policy_hits, default_hits, pairs = score(train, table)
    boot_train = bootstrap(pairs, args.resamples)
    chosen = [(s["dims"], k, r["chosen"]) for s in table["stratifications"] for k, r in s["strata"].items() if r["chosen"]]
    print(f"\nChosen rules: {chosen if chosen else 'none (the learned policy is the current policy)'}")
    print(f"Train: learned policy {policy_hits}/{len(train)} = {100 * policy_hits / len(train):.1f}% against the current "
          f"policy {default_hits} = {100 * default_hits / len(train):.1f}% ({policy_hits - default_hits:+d}); "
          f"bootstrap of the gain: 95% [{boot_train['p2.5']:+d}, {boot_train['p97.5']:+d}], "
          f"{100 * boot_train['at_or_under_zero']:.1f}% of resamples at or under zero")

    output = {
        "description": "Learned option prior (docs/reason-experiments.md, experiment 5): per stratum, the rule that beat the "
                       "current policy (middle value, else FALLBACK_ANSWER) by at least min_gain training problems; "
                       "stratifications finest first. Counts and rule names only.",
        "learned_on": {"file": os.path.basename(args.train), "languages": sorted(languages), "n": len(train)},
        "min_gain": args.min_gain,
        "fallback": FALLBACK,
        "rules": RULES,
        "train": {"policy_hits": policy_hits, "default_hits": default_hits, "bootstrap": boot_train},
    }
    if args.validate:
        val = read(args.val, languages)
        v_hits, v_default, v_pairs = score(val, table)
        boot = bootstrap(v_pairs, args.resamples)
        print(f"Validation (ONE look): learned policy {v_hits}/{len(val)} = {100 * v_hits / len(val):.1f}% against the current "
              f"policy {v_default} = {100 * v_default / len(val):.1f}% ({v_hits - v_default:+d}); bootstrap of the gain: "
              f"95% [{boot['p2.5']:+d}, {boot['p97.5']:+d}], {100 * boot['at_or_under_zero']:.1f}% of resamples at or under zero")
        fired = {}
        for problem, feats in val:
            letter = prior.choose(problem, table)
            if letter is None:
                continue
            for stratification in table["stratifications"]:
                key = prior.stratum_key(feats, stratification["dims"])
                if key and (stratification["strata"].get(key) or {}).get("chosen"):
                    row = fired.setdefault(key, {"n": 0, "learned_hits": 0, "default_hits": 0, "rule": stratification["strata"][key]["chosen"]})
                    row["n"] += 1
                    row["learned_hits"] += letter == problem["label"]
                    row["default_hits"] += prior.default_letter(problem, feats, FALLBACK) == problem["label"]
                    break
        for key, row in sorted(fired.items()):
            print(f"  {key}: `{row['rule']}` fired on {row['n']}, right {row['learned_hits']}, current policy right {row['default_hits']}")
        output["validation"] = {"file": os.path.basename(args.val), "n": len(val), "policy_hits": v_hits,
                                "default_hits": v_default, "bootstrap": boot, "fired": fired}
    output["stratifications"] = table["stratifications"]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {os.path.relpath(args.out, ROOT)}")


if __name__ == "__main__":
    main()
