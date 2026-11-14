"""Family: ages. Three sub-templates, chosen by the model as a letter:

A. "The ages of n people add up to S. What did/will they add up to k years ago/from now?"
     -> S - n*k (ago) or S + n*k (from now). The classic trap, a member not yet born k years
        ago, gives a value that matches no option, so solve() abstains.
B. "X is d years older than Y. In k years their ages will add up to S. How old is Y now?"
     -> Y = (S - 2k - d) / 2
C. "The mother is M. The children are a1, a2, ... In how many years will the children's ages
    add up to the mother's age?" -> x = (M - sum) / (count - 1)
"""
import re
import sys
from fractions import Fraction

from .. import llm
from . import common, register

KEY = "ages"
_MATCH = re.compile(r"\b(ages?|years? old|older|younger)\b", re.I)
_SUM = re.compile(r"\b(add up|sum|total|older|younger|exceed)", re.I)
GRAMMAR = llm.json_grammar({"kind": "letter", "n": "int", "total": "int", "years": "int", "direction": "letter",
                            "difference": "int", "parent": "int", "children_sum": "int", "children": "int",
                            "comparison": "letter"})
HINT = ('kind = "A" if the sum of several ages now is given and the question asks that sum some years ago or later; '
        '"B" if one person is some years older than another and the sum of their ages at some future time is given; '
        '"C" if a parent\'s age and the children\'s ages are given and the question asks in how many years the '
        'children\'s ages will add up to the parent\'s age. n = how many people (0 if not relevant); total = the sum of '
        'ages given (0 if none); years = the number of years mentioned (0 if none); direction = "A" for years ago, '
        '"B" for years from now; difference = how many years older (0 if none); parent = the parent\'s age (0 if none); '
        'children_sum = the sum of the children\'s ages now (0 if none); children = how many children (0 if none); '
        'comparison = "A" if the question says EXCEED or MORE THAN, "B" if it says EQUAL or THE SAME')


def matches(text):
    return bool(_MATCH.search(text)) and bool(_SUM.search(text))


def extract(problem):
    return llm.extract_json(problem["text"], GRAMMAR, HINT)


def compute(params, options):
    kind = str(params["kind"]).strip('"')
    if kind == "A":
        n, total, k = int(params["n"]), int(params["total"]), int(params["years"])
        ago = str(params["direction"]).strip('"') == "A"
        if n <= 0 or k <= 0:
            raise ValueError("bad parameters")
        value = Fraction(total - n * k if ago else total + n * k)
        when_ca, when_en = ("fa", "ago") if ago else ("d'aquí a", "from now")
        trace = [
            {"text_ca": f"Ara les {n} edats sumen {total}.", "text_en": f"Now the {n} ages add up to {total}."},
            {"text_ca": f"Cada persona té {k} anys {'menys' if ago else 'més'} {when_ca} {k} anys: la suma canvia en {n}·{k} = {n * k}.",
             "text_en": f"Each person is {k} years {'younger' if ago else 'older'} {k} years {when_en}: the sum changes by {n}·{k} = {n * k}."},
            {"text_ca": f"La suma és {common.fmt(value)}. Comprova que tothom ja havia nascut!",
             "text_en": f"The sum is {common.fmt(value)}. Check that everyone was already born!", "value": common.fmt(value)},
        ]
    elif kind == "B":
        d, k, total = int(params["difference"]), int(params["years"]), int(params["total"])
        value = Fraction(total - 2 * k - d, 2)
        if value.denominator != 1 or value <= 0:
            raise ValueError("no whole positive age")
        trace = [
            {"text_ca": f"Si el més jove té y anys, l'altre en té y + {d}.", "text_en": f"If the younger one is y, the other is y + {d}."},
            {"text_ca": f"D'aquí a {k} anys sumaran (y + {k}) + (y + {d} + {k}) = {total}.",
             "text_en": f"In {k} years they add up to (y + {k}) + (y + {d} + {k}) = {total}."},
            {"text_ca": f"Per tant 2y = {total - 2 * k - d} i y = {common.fmt(value)}.",
             "text_en": f"So 2y = {total - 2 * k - d} and y = {common.fmt(value)}.", "value": common.fmt(value)},
        ]
    elif kind == "C":
        parent, csum, c = int(params["parent"]), int(params["children_sum"]), int(params["children"])
        if c < 2:
            raise ValueError("needs at least two children")
        exact = Fraction(parent - csum, c - 1)
        if exact < 0:
            raise ValueError("already past")
        exceed = str(params.get("comparison", "B")).strip('"') == "A"
        if exceed:
            value = Fraction(exact.numerator // exact.denominator + 1)  # first whole year strictly past the parent
        elif exact.denominator == 1:
            value = exact
        else:
            raise ValueError("the sums are never equal in a whole year")
        trace = [
            {"text_ca": f"Ara els {c} fills sumen {csum} anys i la mare en té {parent}.",
             "text_en": f"Now the {c} children add up to {csum} years and the parent is {parent}."},
            {"text_ca": f"Cada any la suma dels fills creix {c} i la mare 1: la diferència {parent - csum} es redueix {c - 1} per any.",
             "text_en": f"Each year the children's sum grows by {c} and the parent by 1: the gap of {parent - csum} closes by {c - 1} a year."},
            {"text_ca": f"La igualtat exacta seria als {common.fmt(exact)} anys; {'la supera' if exceed else 'la iguala'} als {common.fmt(value)}.",
             "text_en": f"Exact equality would come at {common.fmt(exact)} years; it {'exceeds' if exceed else 'equals'} at {common.fmt(value)}.",
             "value": common.fmt(value)},
        ]
    else:
        raise ValueError("unknown kind")
    return value, trace


register(sys.modules[__name__])
