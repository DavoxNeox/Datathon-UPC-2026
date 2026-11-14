"""Find (pseudonym, level) pairs whose first diagnostic problems suit the live demo.

The trainer is deterministic: the first problem a fresh student sees depends only on
SEED, the pseudonym and the level chosen on the start screen (copilot/trainer.py,
_choose_diagnostic). This script replays that choice for many pseudonyms and levels,
scores the problem it yields (Catalan text, readable options, picture when visual, a
useful rung-1 neighbour) and prints the best pairs. Ids only: no problem text is printed
unless --show is given (for the team's eyes, never for a committed file).

    python3 dev/demo_pick.py                 # table of candidates
    python3 dev/demo_pick.py --show ID       # the problem and its rung-1 neighbour, in Catalan
    python3 dev/demo_pick.py --chain NAME L  # the first 3 diagnostic problems of NAME at level L

Needs data/train.jsonl, data/val.jsonl, data/index.db and data/images linked (docs/deploy-board.md).
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from copilot import hints, trainer, topics  # noqa: E402
from copilot.topics import TOPIC_KEYS  # noqa: E402

NAMES = ("Mar Pol Jan Aina Arnau Laia Biel Júlia Nil Ona Pau Martina Marc Clàudia Roc Bruna Guillem "
         "Carla Oriol Noa Èric Abril Jordi Núria Gerard Mireia Quim Alba Ferran Berta Adrià Emma Lluc "
         "Irene Marcel Anna Joel Paula Àlex Rita Hugo Greta Bernat Lia Dídac Vinyet Enric Elna Sergi Ivet "
         "Ot Ariadna Max Olívia Teo Mia Iu Elsa Kai Lola Roger Judit Víctor Gal·la Ignasi Nora Aleix Jana "
         "Ramon Sara Pere Maria Joan Montse Xavier Rosa Josep Carme Marta Toni Eva Lluís Neus Albert Eli "
         "prova demo alumne alumna jurat Kangaroo Qualcomm UPC FME datathon copilot Edge mates Arduino "
         "Èlia Mariona Blai Txell Pep Gina Ricard Isona Tomàs Ivó Aitana Genís Mercè Nico Dani Jofre Queralt "
         "Lluna Martí Valentina Arlet Leo Mila Pol2 Mar2 a1 a2 a3 b1 b2 b3 c1 c2 c3 d1 d2 d3 e1 e2 e3").split()

MAX_TEXT = 360        # Catalan characters: fits the page without scrolling on a projector
MAX_OPTION = 14       # characters per option: readable from the back of the room
MAX_SIM = 0.95        # above this the "neighbour" is the same problem posed one level lower: no hint
# An option as OCR should have read it: a number, a fraction, a unit, a short word or a letter sequence
CLEAN_OPTION = re.compile(r"^(\d+([.,]\d+)?(\s?(cm²|cm2|cm|m²|m|km|°|%|€|kg|g|h|min))?|\d+/\d+|[A-Za-zÀ-ÿ·'’ -]{1,12}|[\d\-]{3,12})$")


def options_clean(options):
    return len(options) == 5 and all(CLEAN_OPTION.match(str(v).strip()) and len(str(v)) <= MAX_OPTION
                                     for v in options.values())


def first_problems(student, level, n=3):
    """The first n diagnostic problem ids of a fresh student, in order, without touching the database."""
    levels = trainer.diagnostic_levels(level)
    order = list(TOPIC_KEYS)
    trainer._rng(student, "diagnostic-topics").shuffle(order)
    seen, out = set(), []
    for i in range(n):
        lvl = levels[min(i, len(levels) - 1)]
        topic = order[i % len(order)]
        ids = trainer.bank().candidates(lvl, topic, exclude=seen) or trainer.bank().candidates(lvl, None, exclude=seen)
        pid = trainer._pick(trainer._rng(student, i), ids)
        seen.add(pid)
        out.append(pid)
    return out


def describe(pid):
    """Features of a problem for the demo, ids only."""
    p = trainer.bank().get(pid)
    if not p or p.get("language") != "cat":
        return None
    topic = topics.get_topic(pid)
    visual = topics.is_visual(topic)
    options = p.get("options") or {}
    image = hints._image_path(pid, "cat")
    hint = hints.get_hint(pid, 1, "cat")
    nb = hint.get("problem")
    nb_img = nb.get("image") if nb else None
    ok = (options_clean(options) and len(p["text"]) <= MAX_TEXT and (image or not visual) and nb is not None
          and hint.get("easier") and (nb_img or not visual) and options_clean(nb.get("options") or {})
          and (nb.get("similarity") or 0) < MAX_SIM and bool(p.get("text_only")) != visual)
    return {"id": pid, "level": p.get("level"), "topic": topic, "visual": visual, "text_len": len(p["text"]),
            "options_ok": options_clean(options), "text_only": bool(p.get("text_only")),
            "image": bool(image), "neighbour": nb["id"] if nb else None,
            "nb_level": nb.get("level") if nb else None, "nb_sim": nb.get("similarity") if nb else None,
            "nb_image": bool(nb_img), "nb_options": bool(nb and nb.get("options")), "ok": bool(ok)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", help="print a problem and its rung-1 neighbour (Catalan)")
    ap.add_argument("--chain", nargs=2, metavar=("NAME", "LEVEL"))
    ap.add_argument("--find", help="which (pseudonym, level) pairs serve this id as 1st, 2nd or 3rd problem")
    ap.add_argument("--levels", default="0,1,2,3,4,5", help="start levels to try")
    ap.add_argument("--all", action="store_true", help="print also pairs whose first problem fails a check")
    args = ap.parse_args()
    hints.PREFETCH = "off"
    if args.show:
        p = trainer.bank().get(args.show)
        print(p["id"], "L", p["level"], topics.get_topic(p["id"]), "label", p["label"])
        print(p["text"]); print(p.get("options"))
        h = hints.get_hint(args.show, 1, "cat")
        print("--- rung 1:", h.get("text_ca"))
        if h.get("problem"):
            n = h["problem"]
            print(n["id"], "L", n["level"], "sim", n.get("similarity"), "image", n.get("image"))
            print(n["text"]); print(n.get("options"))
        return
    if args.find:
        for level in range(8):
            for name in NAMES:
                chain = first_problems(name, level)
                if args.find in chain:
                    print(name, level, "position", chain.index(args.find) + 1, chain)
        return
    if args.chain:
        name, lvl = args.chain[0], int(args.chain[1])
        for i, pid in enumerate(first_problems(name, lvl)):
            print(i + 1, describe(pid))
        return
    rows = []
    for level in (int(x) for x in args.levels.split(",")):
        for name in NAMES:
            chain = first_problems(name, level, n=2)
            d1, d2 = describe(chain[0]), describe(chain[1])
            if d1 and (d1["ok"] or args.all):
                rows.append((name, level, d1, d2))
    rows.sort(key=lambda r: (-(r[2]["ok"] + (r[3]["ok"] if r[3] else 0)), r[2]["topic"], -(r[2]["nb_sim"] or 0)))
    print("name level | p1 id topic L vis txt nb nbL sim nbimg ok | p2 id topic L ok")
    for name, level, d1, d2 in rows:
        p2 = f"{d2['id']} {d2['topic']} L{d2['level']} {'OK' if d2['ok'] else '--'}" if d2 else "-"
        print(f"{name:10} {level} | {d1['id']:16} {d1['topic']:10} L{d1['level']} {'V' if d1['visual'] else 'T'}{'t' if d1['text_only'] else 'f'} "
              f"{d1['text_len']:3} {d1['neighbour']} L{d1['nb_level']} {d1['nb_sim']} {'img' if d1['nb_image'] else '   '} "
              f"{'OK' if d1['ok'] else '--'} | {p2}")


if __name__ == "__main__":
    main()
