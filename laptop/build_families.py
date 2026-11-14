#!/usr/bin/env python3
"""Tag text problems with a solver family, from keywords in the English text.

Laptop only. Writes data_curated/families.json as {id: family} (ids and family keys only,
no problem text) and prints how often each family appears in train and val, so the
controller can pick the most frequent ones for copilot/solvers/.

    python3 laptop/build_families.py
    python3 laptop/build_families.py --show ages 10      # sample problems of one family

A problem gets the family with the highest keyword score; problems with no family hit
are left out of the file. The report splits the counts by text_only and by whether OCR
read the options, because a solver can only check its value against read options.
"""
import argparse
import hashlib
import json
import os
import random
import re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# family key -> (name_en, [(weight, regex)])
FAMILIES = {
    "ages": ("Ages now and in n years", [
        (3, r"\byears? old\b|\bages?\b|\baged\b|\bolder\b|\byounger\b|\bborn\b|\bbirthday\b"),
        (1, r"\bmother\b|\bfather\b|\bgrand(?:mother|father|ma|pa)\b|\bson\b|\bdaughter\b|\bsister\b|\bbrother\b"),
    ]),
    "speed_time": ("Speed, time and distance", [
        (3, r"\bspeed\b|\bkm/h\b|\bkm per hour\b|\bmet(?:er|re)s? per (?:second|minute)\b|\bm/s\b|\bfaster\b|\bslower\b"),
        (2, r"\bkm\b|\bkilomet|\bwalks?\b|\bruns?\b|\bcycl|\bdriv|\btrain\b|\bcar\b|\bbus\b|\bjourney\b|\btravel|\blaps?\b|\brace\b"),
        (1, r"\bhours?\b|\bminutes?\b|\bseconds?\b|\bdistance\b|\barrive|\bdepart|\bmeet\b"),
    ]),
    "percent": ("Percentages and discounts", [
        (4, r"%|\bpercent|\bper cent\b"),
        (2, r"\bdiscount|\bincrease[sd]? by\b|\bdecrease[sd]? by\b|\bprice\b|\bcheaper\b|\bmore expensive\b"),
    ]),
    "consecutive": ("Consecutive integers", [
        (4, r"\bconsecutive (?:positive |natural |whole |even |odd )?(?:integers|numbers)\b|\bconsecutive\b"),
    ]),
    "cryptarithm": ("Letters standing for digits", [
        (4, r"\b(?:different|distinct|same) letters?\b|\bletters? (?:represent|stand|denote|correspond)|\beach letter\b|\brepresents? (?:a |the same |a different )?digit"),
        (2, r"(?-i:\b[A-Z]{2,5}\s*[+×−-]\s*[A-Z]{2,5}\b)|\bcode\b|\bencod|\bsymbols? (?:represent|stand)|\bsame symbol\b"),
    ]),
    "liars": ("Liars and truth-tellers", [
        (4, r"\blies?\b|\bliars?\b|\blying\b|\btells? the truth\b|\btruthful\b|\bhonest\b|\bknights?\b|\bknaves?\b|\balways (?:lie|tell)"),
        (2, r"\bstatements?\b|\btrue\b|\bfalse\b|\bsays?\b|\bsaid\b|\bclaims?\b"),
    ]),
    "average": ("Averages and means", [
        (4, r"\baverage\b|\bmean\b|\barithmetic mean\b|\bmedian\b"),
    ]),
    "clock": ("Clocks and calendar", [
        (3, r"\bo'clock\b|\bclock\b|\bwatch\b|\b\d{1,2}:\d{2}\b|\ba\.?m\.?\b|\bp\.?m\.?\b|\bnoon\b|\bmidnight\b"),
        (3, r"\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b|\bsaturday\b|\bsunday\b|\bcalendar\b|\bday of the week\b|\bleap year\b|\bjanuary\b|\bfebruary\b|\bmarch\b|\bapril\b|\bjune\b|\bjuly\b|\baugust\b|\bseptember\b|\boctober\b|\bnovember\b|\bdecember\b"),
    ]),
    "money": ("Money, prices and change", [
        (3, r"\beuros?\b|€|\bcents?\b|\bcoins?\b|\bbanknotes?\b|\bprice\b|\bcost|\bpays?\b|\bpaid\b|\bbuys?\b|\bbought\b|\bsells?\b|\bsold\b|\bmoney\b|\bchange\b"),
    ]),
    "sharing": ("Sharing and ratios of quantities", [
        (3, r"\bshares?\b|\bshared\b|\bdivide[sd]? (?:equally |them )?(?:among|between)\b|\bratio\b|\btwice as (?:many|much)\b|\bthree times as (?:many|much)\b|\bhalf as (?:many|much)\b|\bas many .* as\b|\beach (?:of them )?(?:gets?|receives?|has)\b"),
        (1, r"\bapples?\b|\bcandies|\bsweets\b|\bmarbles\b|\bballs\b|\bcards\b|\bcoins\b|\bchildren\b|\bfriends\b"),
    ]),
    "digit_sum": ("Digits of a number", [
        (3, r"\bdigits?\b|\b(?:two|three|four|five|2|3|4|5)[- ]digit\b|\bsum of (?:its|the) digits\b|\bunits? digit\b|\btens digit\b|\blast digit\b"),
    ]),
    "divisibility": ("Divisibility, primes and remainders", [
        (3, r"\bdivisible\b|\bprimes?\b|\bmultiples? of\b|\bremainders?\b|\bdivisors?\b|\bfactors?\b|\bgcd\b|\blcm\b|\bleast common\b|\bgreatest common\b"),
    ]),
    "weights": ("Weights and balances", [
        (3, r"\bweighs?\b|\bweight\b|\bweighing\b|\bbalance\b|\bscales?\b|\bkg\b|\bkilogram|\bgrams?\b|\bheavier\b|\blighter\b"),
    ]),
    "arrangements": ("Ways to arrange or choose", [
        (3, r"\bin how many (?:different )?ways\b|\bhow many (?:different )?(?:ways|arrangements|orders|possibilities)\b|\bnumber of (?:different )?ways\b"),
        (1, r"\barrange|\border\b|\bchoose\b|\bpick\b|\bselect\b"),
    ]),
    "work_rate": ("Work rates and filling", [
        (3, r"\bfills?\b|\bfilled\b|\bempt(?:y|ies|ied)\b|\btap\b|\bpipe\b|\bpump\b|\bmachines?\b|\bworkers?\b|\bpainters?\b|\btogether they\b|\bper (?:day|hour|minute)\b"),
    ]),
    "sum_equations": ("Sums and differences with unknowns", [
        (2, r"\bthe sum of\b|\bthe difference\b|\bthe product of\b|\bsum of (?:two|three|four|five|all)\b|\btotal of\b|\baltogether\b|\bin total\b|\bmore than\b|\bless than\b|\bfewer than\b"),
    ]),
}
COMPILED = {key: (name, [(w, re.compile(rx, re.IGNORECASE)) for w, rx in rules])
            for key, (name, rules) in FAMILIES.items()}


def family_scores(text):
    """{family: score}. Rules ignore case, except the (?-i:...) group for capital-letter cryptarithms."""
    scores = Counter()
    for key, (_name, rules) in COMPILED.items():
        for weight, regex in rules:
            hits = len(regex.findall(text))
            if hits:
                scores[key] += weight * min(hits, 3)
    return scores


def family_of(text, min_score=3):
    scores = family_scores(text)
    if not scores:
        return None
    key, score = scores.most_common(1)[0]
    return key if score >= min_score else None


def load(paths):
    rows = []
    for path in paths:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                rows.extend(json.loads(line) for line in f if line.strip())
    return rows


def split_of(pid, val_fraction=0.15):
    """The same id hash as laptop/prepare_m3kang.py, so the report can name the split."""
    bucket = int(hashlib.sha256(pid.encode()).hexdigest(), 16) % 1000
    return "val" if bucket < val_fraction * 1000 else "train"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inputs", nargs="+", default=[os.path.join(ROOT, "data", "train.jsonl"),
                                                   os.path.join(ROOT, "data", "val.jsonl")])
    p.add_argument("--out", default=os.path.join(ROOT, "data_curated", "families.json"))
    p.add_argument("--all", action="store_true", help="tag every problem, not only text_only ones")
    p.add_argument("--show", nargs=2, metavar=("FAMILY", "N"))
    args = p.parse_args()

    english = {r["id"]: r for r in load(args.inputs) if r["language"] == "eng"}
    pool = {i: r for i, r in english.items() if args.all or r.get("text_only")}
    families = {}
    for pid, row in pool.items():
        fam = family_of(row["text"])
        if fam:
            families[pid] = fam

    if args.show:
        fam, n = args.show[0], int(args.show[1])
        ids = [i for i, f in families.items() if f == fam]
        random.Random(1).shuffle(ids)
        for pid in ids[:n]:
            r = english[pid]
            print("-", pid, "opts" if r.get("options") else "----", dict(family_scores(r["text"]).most_common(2)),
                  "|", r["text"][:140].replace("\n", " "))
        return

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"method": "keywords on the English text of text_only problems (laptop/build_families.py); ids only",
                   "pool": "text_only" if not args.all else "all", "n_pool": len(pool), "n_tagged": len(families),
                   "names_en": {k: v[0] for k, v in FAMILIES.items()},
                   "families": dict(sorted(families.items()))}, f, indent=0, ensure_ascii=False)
        f.write("\n")

    # Frequency table: train / val, and how many of those have OCR options (a solver can check its value)
    table = defaultdict(Counter)
    for pid, fam in families.items():
        split = split_of(pid)
        table[fam][split] += 1
        if english[pid].get("options"):
            table[fam][split + "_opts"] += 1
    print(f"Wrote {args.out}: {len(families)}/{len(pool)} problems tagged "
          f"({'all' if args.all else 'text_only'} pool, English rows)")
    print(f"\n{'family':14} {'name':36} {'train':>6} {'(opts)':>7} {'val':>5} {'(opts)':>7} {'% pool':>7}")
    for fam, c in sorted(table.items(), key=lambda kv: -(kv[1]['train'] + kv[1]['val'])):
        n = c["train"] + c["val"]
        print(f"{fam:14} {FAMILIES[fam][0]:36} {c['train']:6} {c['train_opts']:7} {c['val']:5} {c['val_opts']:7} "
              f"{100 * n / len(pool):6.1f}%")
    untagged = len(pool) - len(families)
    print(f"{'(none)':14} {'no family matched':36} {'':6} {'':7} {'':5} {'':7} {100 * untagged / len(pool):6.1f}%")


if __name__ == "__main__":
    main()
