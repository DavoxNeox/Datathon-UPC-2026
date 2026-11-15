"""The middle-value rule: when the five options are numbers, answer the one in the middle.

This is a prior on how Kangaroo distractors are built, not reasoning about the problem: the
wrong options are made from the right value (one step too many, one too few, double, half),
so the correct value usually has distractors above it and below it and is rarely the
smallest or the largest of the five. Measured on the English training problems whose five
options parse as distinct numbers (654 of 1466): the middle value is right 30.4% of the
time, always D 24.6%. On the 281 English validation problems (the held-out set, used once):
77/281 = 27.4% with this rule and D elsewhere, against 65/281 = 23.1% for always D; a
hidden test can return that gain to zero (docs/reason-experiments.md has the bootstrap).
No model call, no time, no RAM.

A number may carry a short unit ("48 cm", "4 kg", "165 cm²", "25%"); anything else (two
numbers, words, letters, OCR noise such as "1 10") is not a numeric option and the rule
abstains, so the pipeline's normal fallback answers. The five values must be distinct.
"""
import re

from .solvers.common import parse_number

LETTERS = "ABCDE"
# One number, then at most one short unit: letters (cm, kg, hours, km/h, cm², cm2), % € $ °
_OPTION = re.compile(r"^\s*-?\d+(?:[.,]\d+)?(?:/\d+)?\s*(?:%|€|\$|°|[A-Za-z]{1,7}(?:[²³2]|/[A-Za-z]{1,3})?)?\s*$")


def numeric_options(options):
    """{letter: Fraction} when all five options are distinct plain numbers (with a unit at most), else None."""
    if not options:
        return None
    values = {}
    for letter in LETTERS:
        text = options.get(letter)
        if text is None or not _OPTION.match(str(text).replace("−", "-")):
            return None
        value = parse_number(text)
        if value is None:
            return None
        values[letter] = value
    if len(set(values.values())) != 5:
        return None
    return values


def is_ordered(values):
    """True when the five values are printed in ascending or descending order (then the middle value is option C)."""
    seq = [values[l] for l in LETTERS]
    return all(a < b for a, b in zip(seq, seq[1:])) or all(a > b for a, b in zip(seq, seq[1:]))


def middle_letter(problem, skip_ordered=False):
    """The letter of the middle value (third of five, sorted), or None when the rule does not apply.

    skip_ordered=True abstains when the options are printed in order (ascending or descending):
    there the rule is "always C", a positional pick with nothing over always D (data v2, Experiment
    8: train 133 against 132 for D on 465 ordered problems). The gain of the rule lives in the
    unordered option sets, where the middle value is not a position.
    """
    values = numeric_options(problem.get("options") or {})
    if values is None:
        return None
    if skip_ordered and is_ordered(values):
        return None
    order = sorted(LETTERS, key=lambda l: (values[l], l))
    return order[2]
