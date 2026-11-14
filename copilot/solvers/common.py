"""Shared pieces for every solver family: numbers, options and the "try the options" strategy."""
import re
from fractions import Fraction

LETTERS = "ABCDE"
_NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?")


def parse_number(text):
    """The first number in an option text, as a Fraction, or None.

    Handles "18", "-3", "2.5", "2,5", "3/4", "18 cm", "1 1/2" is NOT handled (returns 1).
    """
    if text is None:
        return None
    m = _NUMBER.search(str(text).replace("−", "-"))
    if not m:
        return None
    raw = m.group(0).replace(" ", "")
    try:
        if "/" in raw:
            num, den = raw.split("/")
            return Fraction(int(num), int(den))
        return Fraction(raw.replace(",", "."))
    except (ValueError, ZeroDivisionError):
        return None


def match_option(value, options):
    """The one letter whose option equals value, or None when zero or several match.

    "Exactly one" is the safety net: when the extraction went wrong the computed value
    usually matches no option, and the caller falls back to the normal pipeline.
    """
    if value is None or not options:
        return None
    try:
        target = Fraction(value)
    except (TypeError, ValueError):
        return None
    hits = [l for l in LETTERS if l in options and parse_number(options[l]) == target]
    return hits[0] if len(hits) == 1 else None


def try_options(options, holds):
    """Letters whose numeric option satisfies holds(value) (the "test every option" strategy).

    Kangaroo options are designed to be checked: when a problem gives conditions rather
    than a direct computation, evaluating each option against them is both a solver and
    a strategy we teach. Returns the list of letters that pass, in order.
    """
    passing = []
    for l in LETTERS:
        if l not in options:
            continue
        v = parse_number(options[l])
        if v is None:
            continue
        try:
            if holds(v):
                passing.append(l)
        except (ArithmeticError, ValueError, TypeError):
            continue
    return passing


def fmt(value):
    """A Fraction as the student sees it: 18, -3, 2.5 or 3/4."""
    f = Fraction(value)
    if f.denominator == 1:
        return str(f.numerator)
    as_float = float(f)
    if as_float == round(as_float, 2):
        return f"{as_float:g}"
    return f"{f.numerator}/{f.denominator}"
