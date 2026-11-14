"""Read the answer options again from the scans the first pass left without clean text.

`prepare_m3kang.py` writes `options: {}` when it cannot find a clean A..E sequence in the OCR
boxes, and the student page then cuts the options out of the scan as pictures. On many scans
the options are plain text ("A) 110°") and the first parser lost them for one reason: a figure
label on the same row ("110°" far to the right) was glued to option E, or a stray box split a
value. This script reads those scans again with RapidOCR (laptop only) and a parser that keeps
only the boxes near each marker, and writes what came out clean to `data/options_ocr.jsonl`:

    {"key": "lvl-3_2024_29|cat", "options": {"A": "110°", ...}}

The web server overlays that file on the problems it shows (`copilot/webapp.py`); the splits
themselves are not rewritten, so the predictor sees the same data as before. The file holds
M3Kang text: it stays out of git like the rest of `data/`.

Usage, from the repository root, in a venv with laptop/requirements.txt:

    python laptop/reocr_options.py                # data/train.jsonl + data/val.jsonl, data/images
    python laptop/reocr_options.py --only lvl-3_2024_29_cat --show   # one scan, boxes printed

The OCR boxes are cached in data/.reocr_boxes.jsonl, so a change to the parser re-runs in
seconds (`--reparse`).
"""

import argparse
import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prepare_m3kang import LETTERS, is_marker  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The page's own acceptance test (assets/app.js: CLEAN, NOISY, tidyOption), in Python, so the
# file only holds options the page will show as text.
CLEAN_EXTRA = set(" .,:;%°€$'\"/+-=<>!?…×√·—–{}∞≤≥÷*′″＇（）#^_|[]~±≠≈π∈→")
NOISY = re.compile(r"\d\s+\d|[^\W\d_]\d\s*$|[²³]\d")


# fullwidth punctuation to ASCII; the CJK characters the (Chinese) OCR model gives a π
FULLWIDTH = str.maketrans("：，．（）；％元兀斤", ":,.();%πππ")
EDGE_OPERATOR = re.compile(r"^[+×÷=/·)]|[+\-−×÷=/·(]$")


def tidy(value):
    value = str(value).translate(FULLWIDTH)
    value = re.sub(r"\s[—–]\s", " - ", value)   # a dash between two terms is a minus
    value = re.sub(r"V(?=\s?\d)", "√", value)
    value = re.sub(r"^(.*\d.*?)\s+[A-E]$", r"\1", value)
    return value.strip()


def is_clean_value(value):
    value = value.strip()
    return bool(value) and all(ch.isalnum() or ch.isspace() or ch in CLEAN_EXTRA for ch in value) and not NOISY.search(value)


def options_clean(options):
    """The page's test, plus what a lost fraction leaves behind: a value repeated (its numerator
    read for two options), a value without a digit among values with digits (the unit alone),
    a value ending or starting with an operator (the fraction after "6 +" is gone)."""
    values = [v.strip() for v in options.values()]
    if len(options) < 2 or not all(is_clean_value(v) for v in values):
        return False
    if len(set(values)) < len(values):
        return False
    digits = [bool(re.search(r"\d", v)) for v in values]
    if any(digits) and not all(digits):
        return False
    return not any(EDGE_OPERATOR.search(v) for v in values)


def reading_order(boxes):
    """prepare_m3kang.reading_order with the box's right edge kept: rows top to bottom, then left to right."""
    items = []
    for box, text, _score in boxes:
        ys = [pt[1] for pt in box]
        xs = [pt[0] for pt in box]
        items.append({"x": min(xs), "x2": max(xs), "y": (min(ys) + max(ys)) / 2, "h": max(ys) - min(ys), "text": text})
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


def parse_options_near(boxes):
    """{"A": ..., "E": ...} from OCR boxes, or {}. Like prepare_m3kang.parse_options, but a box
    only continues an option when it sits near it: before the next marker, and no further to the
    right than one marker spacing. A figure label on the options' row is left out. A box that
    overlaps the marker's box and repeats its value ("A) 1" then "10") replaces it: the OCR read
    the first digit twice."""
    items = reading_order(boxes)
    starts = [i for i, it in enumerate(items) if is_marker(it["text"], "A", strict=True) is not None]
    for start in reversed(starts):
        markers = []   # (index, letter, rest)
        letter_iter = iter(LETTERS)
        letter = next(letter_iter)
        for i in range(start, len(items)):
            rest = is_marker(items[i]["text"], letter, strict=(letter == "A")) if letter else None
            if rest is not None:
                markers.append((i, letter, rest))
                letter = next(letter_iter, None)
        if len(markers) < 5:
            continue
        xs = [items[i]["x"] for i, _, _ in markers]
        spacing = statistics.median(b - a for a, b in zip(xs, xs[1:]))
        options = {}
        for n, (i, letter, rest) in enumerate(markers):
            end = markers[n + 1][0] if n + 1 < len(markers) else len(items)
            x0, y0, h0 = items[i]["x"], items[i]["y"], items[i]["h"]
            value, right = rest, items[i]["x2"]
            for j in range(i + 1, end):
                it = items[j]
                if it["x"] > x0 + 1.5 * spacing or abs(it["y"] - y0) > max(h0, it["h"]):
                    break
                text = it["text"].strip()
                if it["x"] < right and value and text.startswith(value):
                    value = text
                else:
                    value = (value + " " + text).strip()
                right = max(right, it["x2"])
            options[letter] = value.lstrip(")）] ").strip()
        if all(options.values()):
            return options
        return {}   # five markers, but the options are pictures
    return {}


def load_bank(paths):
    bank = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    p = json.loads(line)
                    bank[f"{p['id']}|{p.get('language', 'cat')}"] = p
    return bank


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    ap.add_argument("--only", help="one scan, e.g. lvl-3_2024_29_cat")
    ap.add_argument("--show", action="store_true", help="print the OCR boxes")
    ap.add_argument("--reparse", action="store_true", help="parse the cached boxes again without OCR")
    ap.add_argument("--all", action="store_true", help="also the versions whose options were already clean (a check)")
    args = ap.parse_args()

    bank = load_bank([os.path.join(args.data, n) for n in ("train.jsonl", "val.jsonl")])
    images = os.path.join(args.data, "images")
    cache_path = os.path.join(args.data, ".reocr_boxes.jsonl")
    out_path = os.path.join(args.data, "options_ocr.jsonl")

    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    cache[row["key"]] = row["boxes"]

    keys = sorted(bank)
    if args.only:
        pid, lang = args.only.rsplit("_", 1)
        keys = [f"{pid}|{lang}"]
    elif not args.all:
        keys = [k for k in keys if not options_clean(bank[k].get("options") or {})]

    ocr = None
    results, t0 = {}, time.time()
    with open(cache_path, "a", encoding="utf-8") as cache_file:
        for n, key in enumerate(keys, 1):
            pid, lang = key.split("|")
            path = os.path.join(images, f"{pid}_{lang}.png")
            if key in cache and not args.only:
                boxes = cache[key]
            elif os.path.exists(path) and not args.reparse:
                if ocr is None:
                    from rapidocr_onnxruntime import RapidOCR
                    ocr = RapidOCR()
                raw, _ = ocr(path)
                boxes = [[[[float(x), float(y)] for x, y in box], text, float(score)] for box, text, score in (raw or [])]
                cache[key] = boxes
                cache_file.write(json.dumps({"key": key, "boxes": boxes}, ensure_ascii=False) + "\n")
                cache_file.flush()
            else:
                continue
            if args.show:
                for box, text, score in boxes:
                    ys = [p[1] for p in box]
                    xs = [p[0] for p in box]
                    print(f"  y={min(ys):4.0f}-{max(ys):4.0f} x={min(xs):4.0f}-{max(xs):4.0f} {score:.2f} {text!r}")
            options = {k: tidy(v) for k, v in parse_options_near(boxes).items()}
            results[key] = options
            if n % 100 == 0:
                print(f"  {n}/{len(keys)} scans, {n / (time.time() - t0):.1f}/s", flush=True)

    clean = {k: v for k, v in results.items() if options_clean(v)}
    if args.only:
        key = keys[0]
        print(f"{key}: bank {bank[key].get('options')} -> {results.get(key)} ({'clean' if key in clean else 'not clean'})")
        return
    if args.all:
        same = sum(1 for k, v in clean.items() if v == (bank[k].get("options") or {}))
        print(f"{len(keys)} versions read, {len(clean)} clean, {same} identical to the bank")
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            for key in sorted(clean):
                f.write(json.dumps({"key": key, "options": clean[key]}, ensure_ascii=False) + "\n")
        was_empty = sum(1 for k in clean if not bank[k].get("options"))
        print(f"{len(keys)} versions without clean options read again: {len(clean)} now clean "
              f"({was_empty} had none, {len(clean) - was_empty} were noisy); written to {os.path.relpath(out_path, ROOT)}")
        for key in sorted(clean)[:12]:
            print(f"  {key}: {bank[key].get('options')} -> {clean[key]}")


if __name__ == "__main__":
    main()
