"""Family: consecutive integers. "The sum of five consecutive numbers is 105. The largest is?"

The model copies two numbers (how many, their sum); Python finds the sequence. Also
handles even/odd consecutive numbers (step 2) and "smallest/largest/middle".
"""
import re
import sys
from fractions import Fraction

from .. import llm
from . import common, register

KEY = "consecutive"
_KEYWORDS = re.compile(r"\bconsecutive (whole |positive |natural |even |odd )?(numbers|integers)\b")
GRAMMAR = llm.json_grammar({"count": "int", "sum": "int", "step": "int", "asked": "int"})
HINT = ("count = how many consecutive numbers; sum = their total; "
        "step = 1 for consecutive integers, 2 for consecutive even or odd numbers; "
        "asked = 1 if the question asks for the smallest, 2 for the middle, 3 for the largest, 0 otherwise")


def matches(text):
    # "the sum of N consecutive numbers": the sum must be about the sequence, not about digits
    return bool(_KEYWORDS.search(text)) and bool(re.search(r"\bsum of (the )?(\w+ )?consecutive", text))


def extract(problem, timeout=60):
    return llm.extract_json(problem["text"], GRAMMAR, HINT, timeout=timeout)


def compute(params, options):
    n, total, step, asked = (int(params[k]) for k in ("count", "sum", "step", "asked"))
    if n <= 0 or step not in (1, 2):
        raise ValueError("bad parameters")
    # first + (first + step) + ... = n*first + step*n*(n-1)/2
    first = (Fraction(total) - Fraction(step * n * (n - 1), 2)) / n
    if first.denominator != 1:
        raise ValueError("no integer solution")
    numbers = [first + step * i for i in range(n)]
    value = {1: numbers[0], 2: numbers[n // 2], 3: numbers[-1]}.get(asked)
    trace = [
        {"text_ca": f"Són {n} nombres consecutius que sumen {total}. Anomena el més petit x.",
         "text_en": f"There are {n} consecutive numbers adding up to {total}. Call the smallest one x."},
        {"text_ca": f"La suma és {n}·x més els salts: {n}·x + {step * n * (n - 1) // 2} = {total}.",
         "text_en": f"The sum is {n}·x plus the gaps: {n}·x + {step * n * (n - 1) // 2} = {total}."},
        {"text_ca": f"Per tant x = {common.fmt(first)}, i els nombres són {', '.join(common.fmt(v) for v in numbers)}.",
         "text_en": f"So x = {common.fmt(first)}, and the numbers are {', '.join(common.fmt(v) for v in numbers)}.",
         "value": common.fmt(first)},
    ]
    if value is None:
        # The question asks for something else: let the options decide which one fits
        candidates = [l for l in common.LETTERS if l in options and common.parse_number(options[l]) in numbers]
        if len(candidates) != 1:
            raise ValueError("cannot tell which number is asked")
        value = common.parse_number(options[candidates[0]])
    trace.append({"text_ca": f"La resposta és {common.fmt(value)}.", "text_en": f"The answer is {common.fmt(value)}.",
                  "value": common.fmt(value)})
    return value, trace


register(sys.modules[__name__])
