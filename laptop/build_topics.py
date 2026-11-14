#!/usr/bin/env python3
"""Assign one of the eight topics to every M3Kang problem, from its English text.

Laptop only (it reads the problem texts). The board never sees the texts: it reads
data_curated/topics.json, which holds only problem ids and topic keys, and is committed.

    python3 laptop/build_topics.py                       # data/train.jsonl + data/val.jsonl
    python3 laptop/build_topics.py --inputs data/train.jsonl data/val.jsonl --out data_curated/topics.json
    python3 laptop/build_topics.py --show spatial 15     # print 15 problems of one topic, to tune the rules

Method (Phase 3a): weighted keyword rules on the English text. Each rule adds
weight x min(hits, 3) to its topic; the topic with the highest score wins; ties go
to the more specific topic (PRIORITY order); no hit at all means "arithmetic".
Phase 3b adds the embedding clusters (laptop/cluster_topics.py) on top of this.
"""
import argparse
import json
import os
import random
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC_KEYS = ["arithmetic", "logic", "digits", "counting", "areas", "angles", "spatial", "boards"]
# Ties go to the earlier topic: the specific geometric ones before the catch-all
PRIORITY = ["angles", "areas", "spatial", "boards", "counting", "digits", "logic", "arithmetic"]

# (topic, weight, regex on the lowercased English text)
RULES = [
    ("angles", 3, r"\bangles?\b|\bdegrees?\b|°|\bbisect"),
    ("angles", 2, r"\bisosceles\b|\bequilateral\b|\bright[- ]angled?\b|\bperpendicular\b|\bparallel\b|\brhombus"),
    ("areas", 3, r"\bareas?\b|\bperimeters?\b|\bshaded\b|\bfractions?\b|\bradius\b|\bradii\b|\bdiameter\b|\bcircumference\b"),
    ("areas", 2, r"\bcm\s*[²2]|\bm\s*[²2]|\bsquare (?:centi)?met|\brectangles?\b|\bsemicircle|\bquarter\b|\bhalf of\b"
                 r"|\bthird of\b|\bpart of the\b|\bdivided into\b|\barcs?\b|\btangent\b|\bdiagonals?\b|\bsegments?\b"),
    ("areas", 1, r"\bcircles?\b|\btriangles?\b|\blengths?\b|\bwidth\b|\bside\b|\bsides\b|\bmidpoints?\b|\bhexagon\b"
                 r"|\bpolygon\b|\bquadrilateral\b|\btrapez|\bpentagon\b|\boctagon\b"),
    ("spatial", 3, r"\bcubes?\b|\bdice\b|\bdie\b|\bfold|\bunfold|\bnets?\b|\bmirror\b|\breflect|\brotat|\bfrom above\b"
                   r"|\bfrom the (?:front|top|side|left|right|back)\b|\bturn(?:ed|s)? (?:it )?(?:over|around|upside)|\bsymmetr"),
    ("spatial", 2, r"\bpieces?\b|\bcut\b|\bcuts\b|\bpaper\b|\bsheet\b|\bbuilt?\b|\bblocks?\b|\bbricks?\b|\bsolid\b|\bviews?\b"
                   r"|\bshapes?\b|\bglued?\b|\bstack|\bfaces?\b|\bvertices\b|\bvertex\b|\bedges?\b|\bthree[- ]dimensional\b"
                   r"|\b3d\b|\bprism\b|\bpyramid\b|\bsphere\b|\bcylinder\b|\bvolume\b|\bjigsaw\b|\bpuzzle\b|\bmissing piece\b"),
    ("spatial", 1, r"\bfigure\b|\bpicture\b|\bdrawing\b|\bimage\b|\bdiagram\b|\bbox(?:es)?\b|\bcolou?red\b|\bpainted?\b"
                   r"|\bwhite\b|\bblack\b|\bgray\b|\bgrey\b"),
    ("boards", 3, r"\bgrid\b|\bboards?\b|\bchess|\bcells?\b|\btiles?\b|\btiled\b|\bdominos?\b|\bdominoes\b|\bmagic square\b"
                  r"|\bsudoku\b|\brows? and (?:each )?columns?\b|\bcolumns?\b|\btokens?\b|\bcounters?\b|\bcheckered\b"),
    ("boards", 2, r"\brows?\b|\btable\b|\bsquares? of the\b|\bneighbou?ring\b|\badjacent\b|\bempty squares?\b|\bfilled?\b"
                  r"|\bpattern\b|\barrange(?:d|ment)?\b|\bcorner\b|\bswap"),
    ("counting", 3, r"\bhow many (?:different )?(?:ways|paths|routes|possibilities|arrangements|combinations)\b"
                    r"|\bin how many ways\b|\bnumber of (?:different )?(?:ways|paths|routes)\b|\bprobability\b"
                    r"|\bat least how many\b|\bminimum number of\b|\bmaximum number of\b|\bsmallest number of\b"
                    r"|\blargest number of\b|\bhandshake|\bshake hands\b|\broutes?\b"),
    ("counting", 2, r"\bhow many (?:different|possible)\b|\bchoose\b|\bchosen\b|\bselect|\bdifferent (?:orders?|ways)\b"
                    r"|\bpossible\b|\bat most\b|\bat least\b|\bguarantee|\bbe sure\b|\bcertain(?:ly)? that\b"
                    r"|\bwithout looking\b|\bdraws? (?:out|from)\b|\bpaths?\b"),
    ("digits", 3, r"\bdigits?\b|\b(?:two|three|four|five|six|2|3|4|5|6)[- ]digit\b|\bdivisible\b|\bprime\b|\bmultiples?\b"
                  r"|\bremainder\b|\bconsecutive\b|\bpositive integers?\b|\bintegers?\b|\bnatural numbers?\b"
                  r"|\bwhole numbers?\b|\beven\b|\bodd\b|\bsquare number\b|\bperfect square\b|\bfactors?\b|\bdivisors?\b"
                  r"|\bsum of the (?:digits|numbers)\b|\bproduct of\b"),
    ("digits", 2, r"\bnumbers? (?:from|between) \d|\bwritten\b|\bwrite[sn]?\b|\bsequence\b|\bcalculat|\bvalue of\b"
                  r"|\bexpression\b|\bresult of\b|\boperation|\bequation|\bequal(?:s)? to\b|\babcd?\b"
                  r"|\bletters? (?:represent|stand)|\bdifferent letters\b|\bsame letters?\b|\b\d{4,}\b|\bpower|\^"),
    ("logic", 3, r"\blies?\b|\bliars?\b|\blying\b|\btruth\b|\btruthful\b|\bhonest\b|\bknights?\b|\bknaves?\b|\bstatements?\b"
                 r"|\btrue\b|\bfalse\b|\bsays?\b|\bsaid\b|\bclaims?\b|\bsentences?\b|\bwho (?:is|was|has|won|owns|lives)\b"),
    ("logic", 2, r"\bexactly one\b|\beach of (?:the|them)\b|\bolder\b|\byounger\b|\btaller\b|\bshorter\b|\bheavier\b"
                 r"|\blighter\b|\bnext to\b|\bsit|\bseat|\bnames?\b|\bfriends?\b|\btournament\b|\bmatch(?:es)?\b"
                 r"|\bwon\b|\blost\b|\bwins?\b|\beither\b|\bnever\b|\balways\b|\bimpossible\b|\bcannot\b"),
    ("arithmetic", 3, r"\beuros?\b|€|\bcents?\b|\bprice\b|\bcost|\bpay|\bbuy|\bbought|\bsold?\b|\bmoney\b|\bkilogram|\bkg\b"
                      r"|\bgrams?\b|\blit(?:re|er)s?\b|\bkm\b|\bkilomet|\bmet(?:re|er)s?\b|\bspeed\b|\bkm/h\b|\bhours?\b"
                      r"|\bminutes?\b|\bseconds?\b|\bo'clock\b|\bclock\b|\bwatch\b|\bage[sd]?\b|\byears? old\b|\baverage\b"
                      r"|\bmean\b|\bpercent|%|\bweigh|\btwice as\b|\bthree times as\b|\bhalf as\b|\bmore than\b|\bless than\b"
                      r"|\bfewer\b|\baltogether\b|\bin total\b|\btotal\b|\beach (?:day|week|month|year|hour|minute)\b"
                      r"|\bper (?:day|hour|minute|kg|litre|liter)\b|\bjumps?\b"),
    ("arithmetic", 2, r"\bapples?\b|\bcandies|\bsweets\b|\bcakes?\b|\bbottles?\b|\bglass(?:es)?\b|\bjar\b|\bbag\b|\bbaskets?\b"
                      r"|\bbox(?:es)? of\b|\bchildren\b|\bstudents?\b|\bclass\b|\bbirthday\b|\bgave\b|\bgives?\b|\bgets?\b"
                      r"|\bgot\b|\breceive|\bshares?\b|\bdivide[sd]? (?:equally|among|between)\b|\bate\b|\beats?\b|\bdrinks?\b"
                      r"|\bfills?\b|\bempt(?:y|ies)\b|\btank\b|\bwater\b|\bjourney\b|\btrain\b|\bbus\b|\bcar\b|\bwalk|\bruns?\b"
                      r"|\bcycl|\bswim|\btravel|\bdistance\b|\barrive|\bleave|\bleft\b|\bstart(?:ed|s)?\b|\bfinish|\bbegan\b"
                      r"|\bmother\b|\bfather\b|\bgrandm|\bgrandf|\bbrother|\bsister|\bson\b|\bdaughter\b"),
]
COMPILED = [(topic, weight, re.compile(pattern)) for topic, weight, pattern in RULES]


def keyword_scores(text):
    """{topic: score} from the keyword rules. Empty when nothing matches."""
    low = text.lower()
    scores = Counter()
    for topic, weight, regex in COMPILED:
        hits = len(regex.findall(low))
        if hits:
            scores[topic] += weight * min(hits, 3)
    return scores


def keyword_topic(text):
    scores = keyword_scores(text)
    if not scores:
        return "arithmetic"
    best = max(scores.values())
    return next(t for t in PRIORITY if scores[t] == best)


def load_problems(paths):
    problems = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            problems.extend(json.loads(line) for line in f if line.strip())
    return problems


def english_by_id(problems):
    """The English row of every id (bge-small and the keyword rules are English-only)."""
    return {p["id"]: p for p in problems if p["language"] == "eng"}


def visual_flags(topics, english):
    """visual = most problems of the topic need the figure (text_only == False)."""
    flags = {}
    for key in TOPIC_KEYS:
        rows = [english[i] for i, t in topics.items() if t == key and i in english]
        flags[key] = bool(rows) and sum(1 for r in rows if not r.get("text_only", False)) > len(rows) / 2
    return flags


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inputs", nargs="+", default=[os.path.join(ROOT, "data", "train.jsonl"),
                                                   os.path.join(ROOT, "data", "val.jsonl")])
    p.add_argument("--out", default=os.path.join(ROOT, "data_curated", "topics.json"))
    p.add_argument("--show", nargs=2, metavar=("TOPIC", "N"), help="print N sample problems of TOPIC and exit")
    args = p.parse_args()

    english = english_by_id(load_problems(args.inputs))
    topics = {pid: keyword_topic(row["text"]) for pid, row in english.items()}

    if args.show:
        topic, n = args.show[0], int(args.show[1])
        ids = [i for i, t in topics.items() if t == topic]
        random.Random(1).shuffle(ids)
        for pid in ids[:n]:
            row = english[pid]
            print("-", pid, "T" if row.get("text_only") else "V", dict(keyword_scores(row["text"]).most_common(3)),
                  "|", row["text"][:150].replace("\n", " "))
        return

    flags = visual_flags(topics, english)
    counts = Counter(topics.values())
    out = {
        "method": "keywords on the English text (laptop/build_topics.py); ids only, no problem text",
        "n": len(topics),
        "visual": flags,
        "topics": dict(sorted(topics.items())),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=0, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    print(f"Wrote {args.out}: {len(topics)} problems")
    for key in TOPIC_KEYS:
        rows = [english[i] for i, t in topics.items() if t == key]
        visual = 100 * sum(1 for r in rows if not r.get("text_only")) / max(1, len(rows))
        print(f"  {key:11} {counts[key]:5}  {100 * counts[key] / len(topics):5.1f}%   needs the figure: {visual:3.0f}%"
              f"  -> visual={flags[key]}")


if __name__ == "__main__":
    main()
