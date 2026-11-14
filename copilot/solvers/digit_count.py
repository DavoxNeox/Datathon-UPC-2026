"""Family: counting numbers by their digits. "How many four-digit numbers have a digit product of 0?"

The model copies three things: how many digits, whether the question is about the sum or
the product of the digits, and the target value. Python enumerates. Counting problems that
ask for something else (distinct digits, swapped digits, a digit appearing k times) are not
this family: the extraction then yields a count that matches no option, and solve() abstains.
"""
import re
import sys
from fractions import Fraction

from .. import llm
from . import common, register

KEY = "digit_count"
_MATCH = re.compile(r"how many .{0,40}\b(two|three|four|five|six|2|3|4|5|6)-digit\b", re.I)
_DIGITS = re.compile(r"\b(sum|product)\b.{0,30}\bdigits?\b|\bdigits?\b.{0,30}\b(sum|product|add|multipl)", re.I)
GRAMMAR = llm.json_grammar({"digits": "int", "measure": "letter", "equals": "int"})
HINT = ('digits = how many digits the numbers have; measure = "A" if the question is about the SUM of the digits, '
        '"B" if about the PRODUCT of the digits; equals = the value that sum or product must be')


def matches(text):
    return bool(_MATCH.search(text)) and bool(_DIGITS.search(text))


def extract(problem, timeout=60):
    return llm.extract_json(problem["text"], GRAMMAR, HINT, timeout=timeout)


def compute(params, options):
    n, target = int(params["digits"]), int(params["equals"])
    measure = str(params["measure"]).strip('"')
    if not 1 <= n <= 7 or measure not in ("A", "B"):
        raise ValueError("bad parameters")
    lo, hi = (10 ** (n - 1) if n > 1 else 0), 10 ** n
    count = 0
    for x in range(lo, hi):
        ds = [int(c) for c in str(x)]
        if measure == "A":
            value = sum(ds)
        else:
            value = 1
            for d in ds:
                value *= d
        count += value == target
    what_ca = "suma" if measure == "A" else "producte"
    what_en = "sum" if measure == "A" else "product"
    trace = [
        {"text_ca": f"Busquem nombres de {n} xifres amb {what_ca} de xifres igual a {target}.",
         "text_en": f"We look for {n}-digit numbers whose digit {what_en} is {target}."},
        {"text_ca": f"Hi ha {hi - lo} nombres de {n} xifres: comprova'ls de manera ordenada, per la primera xifra.",
         "text_en": f"There are {hi - lo} numbers with {n} digits: check them in order, by first digit."},
        {"text_ca": f"En total n'hi ha {count}.", "text_en": f"In total there are {count}.", "value": str(count)},
    ]
    return Fraction(count), trace


register(sys.modules[__name__])
