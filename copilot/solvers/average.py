"""Family: arithmetic means. Three sub-templates, chosen by the model as a letter:

A. "The mean of n numbers is m. A value v is added. New mean?"           -> (n*m + v) / (n + 1)
B. "The mean of n numbers is m. One more value makes the mean m2. Which?" -> (n+1)*m2 - n*m
C. "After n tests the mean is m. Each new test scores p. How many more tests for a mean of b?"
                                                                         -> k = n*(b - m) / (p - b)
"""
import re
import sys
from fractions import Fraction

from .. import llm
from . import common, register

KEY = "average"
_MATCH = re.compile(r"\b(average|arithmetic mean|mean score|mean of)\b", re.I)
GRAMMAR = llm.json_grammar({"kind": "letter", "n": "int", "mean": "number", "value": "number",
                            "new_mean": "number", "score": "number", "target": "number"})
HINT = ('kind = "A" if a value is added and the question asks the NEW mean; "B" if the new mean is given and the '
        'question asks the added value; "C" if the question asks HOW MANY more items are needed to reach a target '
        'mean; n = how many values there are at first; mean = their mean; value = the value added (0 if unknown); '
        'new_mean = the mean after adding (0 if unknown); score = the score of each new item (0 if none); '
        'target = the mean to reach (0 if none)')


def matches(text):
    return bool(_MATCH.search(text)) and "geometric" not in text


def extract(problem):
    return llm.extract_json(problem["text"], GRAMMAR, HINT)


def _f(x):
    return Fraction(str(x))


def compute(params, options):
    kind = str(params["kind"]).strip('"')
    n, mean = int(params["n"]), _f(params["mean"])
    if n <= 0:
        raise ValueError("bad n")
    total = n * mean
    if kind == "A":
        v = _f(params["value"])
        value = (total + v) / (n + 1)
        trace = [
            {"text_ca": f"La suma dels {n} valors és {n}·{common.fmt(mean)} = {common.fmt(total)}.",
             "text_en": f"The {n} values add up to {n}·{common.fmt(mean)} = {common.fmt(total)}."},
            {"text_ca": f"Afegim {common.fmt(v)}: ara són {n + 1} valors.", "text_en": f"Add {common.fmt(v)}: now there are {n + 1} values."},
            {"text_ca": f"La nova mitjana és {common.fmt(value)}.", "text_en": f"The new mean is {common.fmt(value)}.", "value": common.fmt(value)},
        ]
    elif kind == "B":
        m2 = _f(params["new_mean"])
        value = (n + 1) * m2 - total
        trace = [
            {"text_ca": f"Abans, la suma era {n}·{common.fmt(mean)} = {common.fmt(total)}.",
             "text_en": f"Before, the total was {n}·{common.fmt(mean)} = {common.fmt(total)}."},
            {"text_ca": f"Després, {n + 1} valors amb mitjana {common.fmt(m2)} sumen {common.fmt((n + 1) * m2)}.",
             "text_en": f"After, {n + 1} values with mean {common.fmt(m2)} add up to {common.fmt((n + 1) * m2)}."},
            {"text_ca": f"La diferència és el valor afegit: {common.fmt(value)}.",
             "text_en": f"The difference is the added value: {common.fmt(value)}.", "value": common.fmt(value)},
        ]
    elif kind == "C":
        p, b = _f(params["score"]), _f(params["target"])
        if p == b:
            raise ValueError("no solution")
        value = n * (b - mean) / (p - b)
        if value.denominator != 1 or value < 0:
            raise ValueError("not a whole number of items")
        trace = [
            {"text_ca": f"Ara la suma és {n}·{common.fmt(mean)} = {common.fmt(total)}.",
             "text_en": f"Now the total is {n}·{common.fmt(mean)} = {common.fmt(total)}."},
            {"text_ca": f"Amb k proves més de {common.fmt(p)} punts, la mitjana és ({common.fmt(total)} + {common.fmt(p)}k)/({n} + k) = {common.fmt(b)}.",
             "text_en": f"With k more tests of {common.fmt(p)} points, the mean is ({common.fmt(total)} + {common.fmt(p)}k)/({n} + k) = {common.fmt(b)}."},
            {"text_ca": f"Si ho resols, k = {common.fmt(value)}.", "text_en": f"Solving, k = {common.fmt(value)}.", "value": common.fmt(value)},
        ]
    else:
        raise ValueError("unknown kind")
    return value, trace


register(sys.modules[__name__])
