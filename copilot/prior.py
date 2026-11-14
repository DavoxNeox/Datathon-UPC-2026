"""A learned prior on the options: per stratum, the rule that beat the middle-value rule on training.

Experiment 5 of docs/reason-experiments.md. Like copilot/ladder.py this is a prior on how Kangaroo
options are built, not reasoning: it reads the five option strings, the level and whether the
problem has a picture, never the problem text. laptop/learn_prior.py measures every candidate rule
on the training problems, stratum by stratum (level 0-7, with or without picture, kind of options),
and keeps a rule only where it beats the current policy (middle value when the five options are
distinct numbers, else FALLBACK_ANSWER) by at least MIN_GAIN problems in that stratum. The table
goes to data_curated/option_prior.json: counts and rule names only, no problem text.

A stratification is a choice of dimensions (level, picture, kind of options, order of the values, ...)
and the json may hold several, finest first. choose(problem) answers a letter only for a stratum with a
learned rule that applies; everywhere else it returns None and the pipeline continues with the
middle-value rule and the fallback letter. No model call, no time, no RAM.
"""
import json
import os
import re
from fractions import Fraction

from .config import CONFIG
from .ladder import numeric_options
from .solvers.common import parse_number

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join("data_curated", "option_prior.json")
LETTERS = "ABCDE"
MIN_GAIN = 10

# Lenient numeric option: an OCR'd option may start with a stray digit that repeats the number's first
# digit ("1 10", "4 40cm", "6 600 g") and may carry junk after the number and its unit ("88 616",
# "15 2 3", "300 g 400g 100g 2"). The number must be followed by a space or the end, so "1S0S", "7: 9" and
# "3∈" still abstain. Dates ("15/4/2015") have two slashes and abstain too.
_STRAY_PREFIX = re.compile(r"^(\d)\s+(?=\1\d)")
_LENIENT = re.compile(r"^(-?\d+(?:[.,]\d+)?(?:/\d+)?\s*(?:%|€|\$|°|[A-Za-z]{1,7}(?:[²³2]|/[A-Za-z]{1,3})?)?)(?=\s|$)")
_NONE_TEXT = re.compile(r"\b(none|neither|impossible|cannot|can't|not possible|no answer|cap|ningun|ninguna|"
                        r"no es pot|no (?:se|es) pot|no hi ha|no n'hi ha|no es possible)\b", re.IGNORECASE)
_PI_ROOT = re.compile(r"π|√|\bpi\b|\bsqrt\b")
_FRACTION = re.compile(r"\d\s*/\s*\d")


def lenient_number(text):
    """The Fraction of a noisy numeric option, or None."""
    if text is None:
        return None
    text = str(text).replace("−", "-").strip()
    if text.count("/") > 1:
        return None
    text = _STRAY_PREFIX.sub("", text)
    m = _LENIENT.match(text)
    return parse_number(m.group(1)) if m else None


def lenient_options(options):
    """{letter: Fraction} when the five options parse leniently as distinct numbers, else None."""
    if not options:
        return None
    values = {}
    for letter in LETTERS:
        value = lenient_number(options.get(letter))
        if value is None:
            return None
        values[letter] = value
    return values if len(set(values.values())) == 5 else None


def none_letters(options):
    """Letters whose option text says "none", "impossible", "cannot" (English or Catalan)."""
    return [l for l in LETTERS if l in (options or {}) and _NONE_TEXT.search(str(options[l]))]


def features(problem):
    """What the rules and strata read: level, picture, language, kind of options and the option patterns."""
    options = problem.get("options") or {}
    strict = numeric_options(options)
    lenient = lenient_options(options) if strict is None else None
    values = strict if strict is not None else lenient
    if strict is not None:
        kind = "numeric"
    elif lenient is not None:
        kind = "noisy_numeric"
    elif len(options) == 5:
        kind = "words"
    else:
        kind = "no_options"
    texts = " ".join(str(v) for v in options.values())
    level = problem.get("level")
    image = (not problem.get("text_only")) if "text_only" in problem else None
    return {
        "level": int(level) if level is not None and str(level).lstrip("-").isdigit() else None,
        "picture": None if image is None else ("picture" if image else "text"),
        "language": problem.get("language"),
        "kind": kind,
        "values": values,
        "order": None if values is None else ("ascending" if [values[l] for l in LETTERS] == sorted(values.values()) else "unsorted"),
        "distinct": len({str(v).strip() for v in options.values()}) if options else 0,
        "fraction": values is not None and (any(v.denominator != 1 for v in values.values()) or bool(_FRACTION.search(texts))),
        "pi_root": bool(_PI_ROOT.search(texts)),
        "none_text": bool(none_letters(options)),
    }


# The dimensions a stratification may use; "level/picture/kind" is the main one of the experiment
DIMENSIONS = ("level", "picture", "language", "kind", "order", "distinct", "fraction", "pi_root", "none_text")


def stratum_key(feats, dims=("level", "picture", "kind")):
    """The problem's stratum for these dimensions, e.g. "level=3|picture=text|kind=numeric"; None if one is unknown."""
    parts = []
    for dim in dims:
        value = feats.get(dim)
        if value is None:
            return None
        parts.append(f"{dim}={value}")
    return "|".join(parts)


def _by_rank(values, rank):
    order = sorted(LETTERS, key=lambda l: (values[l], l))
    return order[rank]


def apply_rule(rule, problem, feats=None):
    """The letter rule gives for the problem, or None when it does not apply.

    Rules: a fixed letter "A".."E"; a rank of the numeric values "min", "second_smallest", "middle",
    "second_largest", "max" (strict or lenient numeric options); "none_option" (the single option that
    says none/impossible).
    """
    feats = feats if feats is not None else features(problem)
    if rule in LETTERS:
        return rule
    if rule == "none_option":
        letters = none_letters(problem.get("options") or {})
        return letters[0] if len(letters) == 1 else None
    ranks = {"min": 0, "second_smallest": 1, "middle": 2, "second_largest": 3, "max": 4}
    if rule in ranks:
        return _by_rank(feats["values"], ranks[rule]) if feats["values"] is not None else None
    return None


def default_letter(problem, feats=None, fallback=None):
    """What the current policy answers without the prior: the middle value, else the fallback letter."""
    feats = feats if feats is not None else features(problem)
    if feats["kind"] == "numeric":
        return _by_rank(feats["values"], 2)
    return fallback or CONFIG.get("FALLBACK_ANSWER", "D")


def load(path=None):
    """The learned table, or None when the file is missing or malformed."""
    path = path or CONFIG.get("OPTION_PRIOR_FILE") or DEFAULT_PATH
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data.get("stratifications"), list):
        return None
    return data


PRIOR = load()


def choose(problem, prior=None):
    """The learned rule's letter for the problem, or None (the pipeline continues).

    prior["stratifications"] is a list of {"dims": [...], "strata": {key: {"chosen": rule, ...}}}, finest
    first: the first stratum with a chosen rule that applies to the problem answers.
    """
    prior = prior if prior is not None else PRIOR
    if prior is None:
        return None
    feats = features(problem)
    for stratification in prior["stratifications"]:
        key = stratum_key(feats, stratification.get("dims") or ())
        if key is None:
            continue
        rule = (stratification.get("strata", {}).get(key) or {}).get("chosen")
        if not rule:
            continue
        letter = apply_rule(rule, problem, feats)
        if letter is not None and letter in LETTERS:
            return letter
    return None
