#!/usr/bin/env python3
"""Prepare M3Kang for the Arduino UNO Q, on your laptop.

M3Kang stores each problem as text plus an image. The text has the question
but not the five answer options: those only appear in the image. This script:

1. downloads the parquet shards you ask for from Hugging Face,
2. keeps the languages you ask for,
3. reads the options A to E from each image with OCR (RapidOCR, offline),
4. splits the problems into train and validation by problem ID, so a
   problem and its translations never land on both sides,
5. writes small JSONL files (no images) that you copy to the board.

Reading the options (step 3) has four fallbacks, in this order: the markers may be "A)",
"(A)", "a)" or "A" alone; when A is missing but B..E are there, the box before B is A; when
the full image gives nothing, the bottom 40 % of the image is read again at twice the size in
grey; when exactly four options are found, the fifth is taken from the box that follows the
last one. After OCR the translations of one problem vote: the options are the same numbers in
every language, so a language whose scan failed takes them from a language whose scan worked
(only for options without words, which do change with the language).

The OCR boxes are cached in `<out>/.ocr_boxes.v2.jsonl` (one line per image and pass), so a
parser change re-reads nothing. The old `.ocr_cache.jsonl` (options only, parser v1) is
ignored and can be deleted. `--reparse` reports coverage without touching the files.

Usage:
    python3 laptop/prepare_m3kang.py                      # English and Catalan
    python3 laptop/prepare_m3kang.py --languages eng,cat,esp
    python3 laptop/prepare_m3kang.py --val-years 2024     # hold out a whole year
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
from collections import Counter

DATASET = "qualcomm/M3Kang"
SHARD = "data/{split}-{index:05d}-of-{total:05d}.parquet"
SHARDS = {"high_quality": 4, "standard": 10}
LETTERS = "ABCDE"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--split", default="high_quality", choices=sorted(SHARDS))
    p.add_argument("--shards", default="0",
                   help="comma-separated shard numbers, or 'all'. Shard 0 of high_quality has "
                        "eng, cat, fra, esp, ind, deu, swh, vie, tur, zho, kor, arb, jpn, lit")
    p.add_argument("--parquet", nargs="*", help="use local parquet files instead of downloading")
    p.add_argument("--languages", default="eng,cat", help="M3Kang language codes, e.g. eng,cat,esp")
    p.add_argument("--val-fraction", type=float, default=0.15, help="share of problem IDs held out")
    p.add_argument("--val-years", default="", help="hold out these years instead, e.g. 2023,2024")
    p.add_argument("--out", default="data", help="output folder")
    p.add_argument("--no-ocr", action="store_true", help="skip OCR; options will be empty")
    p.add_argument("--save-images", action="store_true", help="also save problem images as PNG")
    p.add_argument("--limit", type=int, default=0, help="only process the first N rows (for testing)")
    p.add_argument("--no-vote", action="store_true", help="do not copy options between translations")
    p.add_argument("--sample", type=int, default=20, help="print N random extractions for manual review")
    p.add_argument("--seed", type=int, default=42, help="seed of the printed sample")
    p.add_argument("--reparse", action="store_true",
                   help="only re-parse the cached boxes and print the coverage; write nothing")
    return p.parse_args()


def shard_paths(args):
    if args.parquet:
        return args.parquet
    from huggingface_hub import hf_hub_download
    total = SHARDS[args.split]
    indexes = range(total) if args.shards == "all" else [int(s) for s in args.shards.split(",")]
    paths = []
    for i in indexes:
        name = SHARD.format(split=args.split, index=i, total=total)
        print(f"Downloading {name} (cached after the first time)...", flush=True)
        paths.append(hf_hub_download(DATASET, name, repo_type="dataset"))
    return paths


# --- Reading the options from the image -------------------------------------
#
# OCR returns text boxes. The options are the last A..E sequence in reading
# order, usually on one row at the bottom. OCR noise we handle, seen on real
# M3Kang images: "A)21" (no space), "E16" (lost parenthesis), "C" and "13" in
# separate boxes, and ")768351" (parenthesis attached to the value).

# "A) 12", "(A) 12", "A. 12", "A: 12", "a) 12" and "A12" (lost parenthesis); a lower-case
# letter counts only with a closing parenthesis, so words are never markers.
MARKER = re.compile(r"^\s*[\(（\[]?\s*([A-Ea-e])\s*([\)）\]:.]?)\s*(.*)$")
PARSER_VERSION = 2
CACHE_NAME = ".ocr_boxes.v2.jsonl"
OLD_CACHE_NAME = ".ocr_cache.jsonl"
BOTTOM_SHARE = 0.40    # the second OCR pass reads this share of the image, from the bottom
BOTTOM_SCALE = 2.0     # ... scaled by this factor, in grey


def reading_order(boxes):
    """Sort OCR boxes into rows (top to bottom), then left to right."""
    items = []
    for box, text, _score in boxes:
        ys = [pt[1] for pt in box]
        xs = [pt[0] for pt in box]
        items.append({"x": min(xs), "y": (min(ys) + max(ys)) / 2, "h": max(ys) - min(ys), "text": text})
    items.sort(key=lambda it: it["y"])
    rows, current = [], []
    for it in items:
        if current and abs(it["y"] - current[-1]["y"]) > 0.6 * max(it["h"], current[-1]["h"]):
            rows.append(current)
            current = []
        current.append(it)
    if current:
        rows.append(current)
    return [it for row in rows for it in sorted(row, key=lambda it: it["x"])]


def is_marker(text, letter, strict):
    m = MARKER.match(text)
    if not m or m.group(1).upper() != letter:
        return None
    paren, rest = m.group(2), m.group(3)
    if m.group(1).islower() and not paren:
        return None
    if paren:
        return rest
    if strict:
        return None
    # Without a parenthesis, only accept "C" alone or "E16"-style values,
    # so words such as "ADA" or figure labels with text are not markers.
    if rest == "" or re.match(r"^[-+−\d]", rest):
        return rest
    return None


def _clean(value):
    return value.lstrip(")）] ").strip()


def _walk(items, start, first_rest):
    """From the A marker at items[start], collect the boxes of each option in reading order.

    Returns {letter: [box texts]} with the marker's own remainder as the first text. A letter
    whose marker never appears is absent (its boxes end up appended to the previous letter).
    """
    pieces, current = {"A": [first_rest]}, "A"
    remaining = list(LETTERS[1:])
    for it in items[start + 1:]:
        rest, found = None, None
        if remaining:
            rest = is_marker(it["text"], remaining[0], strict=False)
            found = remaining[0]
            if rest is None and len(remaining) > 1:
                # the OCR lost one marker: the next letter's marker, with its parenthesis, still counts
                rest = is_marker(it["text"], remaining[1], strict=True)
                found = remaining[1]
        if rest is not None:
            current = found
            pieces[current] = [rest]
            remaining = remaining[remaining.index(found) + 1:]
        else:
            pieces[current].append(it["text"])
    return pieces


def _five_from_pieces(pieces):
    """Five non-empty options from the collected boxes, or None.

    With exactly four letters, the fifth is taken laxly: the missing letter's text is the
    second box of the letter before it (an option's value is one box; a second box after it
    is the next option whose marker the OCR lost), or the first box of the letter after it.
    """
    if len(pieces) == 5:
        options = {k: _clean(" ".join(v)) for k, v in pieces.items()}
        return options if all(options.values()) else None
    if len(pieces) != 4:
        return None
    missing = next(l for l in LETTERS if l not in pieces)
    before = LETTERS[LETTERS.index(missing) - 1] if missing != "A" else None
    after = LETTERS[LETTERS.index(missing) + 1] if missing != "E" else None
    options = {}
    if before and len(pieces[before]) >= 2:
        texts = [t for t in pieces[before] if _clean(t)]
        if len(texts) >= 2:
            options = {k: _clean(" ".join(v)) for k, v in pieces.items() if k != before}
            options[before] = _clean(texts[0])
            options[missing] = _clean(" ".join(texts[1:]))
    elif after and len(pieces[after]) >= 2:
        texts = [t for t in pieces[after] if _clean(t)]
        if len(texts) >= 2:
            options = {k: _clean(" ".join(v)) for k, v in pieces.items() if k != after}
            options[missing] = _clean(texts[0])
            options[after] = _clean(" ".join(texts[1:]))
    if len(options) == 5 and all(options.values()):
        return dict(sorted(options.items()))
    return None


def parse_options(boxes):
    """Return {"A": "12", ..., "E": "24"}, or {} when the options are not text."""
    items = reading_order(boxes)
    starts = [i for i, it in enumerate(items) if is_marker(it["text"], "A", strict=True) is not None]
    for start in reversed(starts):  # the options are the last A..E sequence
        pieces = _walk(items, start, is_marker(items[start]["text"], "A", strict=True))
        options = _five_from_pieces(pieces)
        if options:
            return options
        if len(pieces) == 5:
            return {}  # five markers, but the options are pictures
    # No "A)" marker, but "B)".."E)" in a row: the box right before B is the A option.
    b_starts = [i for i, it in enumerate(items) if i > 0 and is_marker(it["text"], "B", strict=True) is not None]
    for b in reversed(b_starts):
        a_text = items[b - 1]["text"]
        a_rest = is_marker(a_text, "A", strict=False)
        first = a_rest if a_rest is not None else a_text
        pieces = _walk(items, b - 1, first)
        if all(l in pieces for l in "BCD"):
            options = _five_from_pieces(pieces)
            if options and options["A"] and not re.search(r"[^\W\d_]{4,}", options["A"]):
                return options
    return {}


def _bottom_crop(image_bytes):
    """The bottom BOTTOM_SHARE of the image, BOTTOM_SCALE times bigger, in grey (numpy array)."""
    import numpy as np
    import cv2
    img = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    top = int(img.shape[0] * (1 - BOTTOM_SHARE))
    crop = img[top:, :]
    return cv2.resize(crop, None, fx=BOTTOM_SCALE, fy=BOTTOM_SCALE, interpolation=cv2.INTER_CUBIC)


def read_options(ocr, image_bytes, cached, remember):
    """Options of one image: parse the full image's boxes; when that fails, the bottom crop's.

    `cached[pass]` holds the OCR boxes already read for this image; `remember(pass, boxes)`
    stores new ones. Returns (options, pass_used) with pass_used "full", "bottom" or "".
    """
    for name in ("full", "bottom"):
        if name in cached:
            boxes = cached[name]
        else:
            if ocr is None:
                return {}, ""
            source = image_bytes if name == "full" else _bottom_crop(image_bytes)
            boxes = []
            if source is not None:
                raw, _ = ocr(source)
                boxes = [[[[float(x), float(y)] for x, y in box], text, float(score)] for box, text, score in (raw or [])]
            remember(name, boxes)
        options = parse_options(boxes)
        if options:
            return options, name
    return {}, ""


WORD = re.compile(r"[^\W\d_]{3,}", re.UNICODE)
UNITS = {"cm", "km", "mm", "dm", "kg", "min", "cm2", "cm3", "km2", "m2", "m3", "ml", "deg", "euro", "euros"}


def language_neutral(options):
    """True when no option holds a word (units apart): such options are the same in every language."""
    for value in options.values():
        for word in WORD.findall(value):
            if word.lower().strip("²³") not in UNITS:
                return False
    return True


def vote_options(rows):
    """Translations of one problem share their options.

    For every problem id, the languages whose scan gave five options vote letter by letter;
    a language with no options takes the winner, and one whose five options disagree with the
    winner is corrected, in both cases only when the winner is language-neutral (numbers,
    fractions, units). Returns the number of rows changed.
    """
    by_id = {}
    for r in rows:
        by_id.setdefault(r["id"], []).append(r)
    changed = 0
    for group in by_id.values():
        full = [r["options"] for r in group if len(r["options"]) == 5]
        if not full:
            continue
        winner = {}
        for letter in LETTERS:
            votes = Counter(o[letter] for o in full)
            winner[letter] = votes.most_common(1)[0][0]
        if not language_neutral(winner):
            continue
        for r in group:
            if r["options"] != winner and (not r["options"] or language_neutral(r["options"])):
                r["options"] = dict(winner)
                r["options_source"] = "vote"
                changed += 1
    return changed


def load_box_cache(path):
    """{image key: {pass: boxes}} from the v2 cache."""
    cache = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                row = json.loads(line)
                cache.setdefault(row["key"], {})[row["pass"]] = row["boxes"]
    return cache


def coverage(rows):
    """(versions with 5 options, versions, problem ids whose every language has 5, problem ids)."""
    by_id = {}
    for r in rows:
        by_id.setdefault(r["id"], []).append(len(r["options"]) == 5)
    five = sum(1 for r in rows if len(r["options"]) == 5)
    ids_all = sum(1 for flags in by_id.values() if all(flags))
    return five, len(rows), ids_all, len(by_id)


def read_existing(out):
    rows = []
    for split in ("train", "val"):
        path = os.path.join(out, f"{split}.jsonl")
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        r["split"] = split
                        rows.append(r)
    return rows


def print_coverage(title, rows):
    print(title)
    for split in ("train", "val"):
        part = [r for r in rows if r["split"] == split]
        if not part:
            continue
        five, n, ids_all, ids = coverage(part)
        print(f"  {split:5}: versions with 5 options {five}/{n} ({100 * five / n:.1f}%), "
              f"problems with 5 in every language {ids_all}/{ids} ({100 * ids_all / ids:.1f}%)")


def main():
    args = parse_args()
    import random
    import pyarrow.parquet as pq

    languages = set(args.languages.split(","))
    val_years = set(y for y in args.val_years.split(",") if y)
    os.makedirs(args.out, exist_ok=True)
    if args.save_images:
        os.makedirs(os.path.join(args.out, "images"), exist_ok=True)

    before = read_existing(args.out)

    ocr = None
    if not args.no_ocr and not args.reparse:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()

    old_cache = os.path.join(args.out, OLD_CACHE_NAME)
    if os.path.exists(old_cache):
        print(f"Ignoring {old_cache}: options of parser v1. The boxes now live in {CACHE_NAME}; delete the old file.")
    cache_path = os.path.join(args.out, CACHE_NAME)
    cache = load_box_cache(cache_path)
    cache_file = None if args.reparse else open(cache_path, "a")

    rows, passes = [], Counter()
    t0 = time.time()
    for path in shard_paths(args):
        table = pq.read_table(path, columns=["language"])
        wanted = [i for i, lang in enumerate(table.column(0).to_pylist()) if lang in languages]
        if not wanted:
            continue
        full = pq.read_table(path).take(wanted)
        for i in range(full.num_rows):
            if args.limit and len(rows) >= args.limit:
                break
            r = {c: full.column(c)[i].as_py() for c in ("id", "language", "level", "text_only", "label", "text")}
            key = f"{r['id']}|{r['language']}"
            image = full.column("image")[i].as_py()["bytes"]
            if args.save_images:
                with open(os.path.join(args.out, "images", key.replace("|", "_") + ".png"), "wb") as f:
                    f.write(image)
            cached = cache.setdefault(key, {})

            def remember(name, boxes, key=key, cached=cached):
                cached[name] = boxes
                if cache_file:
                    cache_file.write(json.dumps({"key": key, "pass": name, "boxes": boxes}, ensure_ascii=False) + "\n")
                    cache_file.flush()

            options, used = read_options(ocr, image, cached, remember)
            passes[used or "none"] += 1
            year = r["id"].split("_")[1]
            if val_years:
                split = "val" if year in val_years else "train"
            else:
                bucket = int(hashlib.sha256(r["id"].encode()).hexdigest(), 16) % 1000
                split = "val" if bucket < args.val_fraction * 1000 else "train"
            rows.append({
                "id": r["id"], "language": r["language"], "level": r["level"], "year": int(year),
                "text_only": r["text_only"], "text": r["text"].strip(), "options": options,
                "label": r["label"], "split": split, "options_source": used,
            })
            if len(rows) % 100 == 0:
                rate = len(rows) / (time.time() - t0)
                print(f"  {len(rows)} rows, {rate:.1f} rows/s", flush=True)
    if cache_file:
        cache_file.close()

    voted = 0 if args.no_vote else vote_options(rows)

    if not args.reparse:
        for split in ("train", "val"):
            out = os.path.join(args.out, f"{split}.jsonl")
            with open(out, "w") as f:
                for r in rows:
                    if r["split"] == split:
                        f.write(json.dumps({k: v for k, v in r.items() if k not in ("split", "options_source")},
                                           ensure_ascii=False) + "\n")

    report(rows, args.out, before, passes, voted, args.sample, args.seed, args.reparse)


def report(rows, out, before, passes, voted, sample, seed, reparse):
    import random
    if not rows:
        sys.exit("No rows matched. Check --languages and --shards.")
    by = Counter((r["split"], r["language"]) for r in rows)
    text_only = [r for r in rows if r["text_only"]]
    labels = Counter(r["label"] for r in rows if r["split"] == "train")
    top, count = labels.most_common(1)[0]
    print()
    print(("Coverage only, nothing written. " if reparse else f"Wrote {out}/train.jsonl and {out}/val.jsonl. ") +
          f"Parser v{PARSER_VERSION}.")
    for (split, lang), n in sorted(by.items()):
        print(f"  {split:5} {lang}: {n}")
    if before:
        print_coverage("Before (the files that were in the output folder):", before)
    print_coverage("After:", rows)
    print(f"Where the options came from: full image {passes.get('full', 0)}, bottom crop {passes.get('bottom', 0)}, "
          f"copied or corrected by the translation vote {voted}, none {passes.get('none', 0) - voted}")
    if text_only:
        ok = sum(1 for r in text_only if r["options"])
        print(f"  text-only problems with options: {ok}/{len(text_only)} ({100 * ok / len(text_only):.0f}%)")
    print(f"Most common answer in train: {top} ({100 * count / sum(labels.values()):.1f}%). "
          f"Always answering {top} is the floor to beat.")
    if sample:
        rng = random.Random(seed)
        with_options = [r for r in rows if r["options"]]
        print(f"\n{min(sample, len(with_options))} random extractions for a manual check (id | language | source | options):")
        for r in rng.sample(with_options, min(sample, len(with_options))):
            src = "vote" if r.get("options_source") == "vote" else (r.get("options_source") or "?")
            print(f"  {r['id']} | {r['language']} | {src:6} | " + "  ".join(f"{k}) {v}" for k, v in sorted(r["options"].items())))


if __name__ == "__main__":
    main()
