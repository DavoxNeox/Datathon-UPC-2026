"""Error signatures: what a wrong Kangaroo option says about the student's mistake.

The five options of a Kangaroo problem are designed: every distractor captures one
concrete slip (counting both ends, doubling, a dropped zero, swapped digits...). When
the student picks a wrong option we compare, in code, the value of the chosen option
with the value of the correct one, both read from the OCR `options`, and name the slip
with a bilingual diagnostic that never states the correct value or letter.

    diagnose(problem, "B") -> None | {"signature": key, "text_ca": ..., "text_en": ..., "evidence": {...}}

`None` means there is nothing to diagnose: the answer is right, the letter is not an
option, or one of the two options is not a single number (pictures, sets, ratios,
OCR noise such as "77 2"). A numeric pair that matches no signature returns the key
"none" with a generic "start again from the statement" text, so the caller can always
show something after a failure.

Order of the signatures, most specific first (the first match wins; a tie between two
signatures is documented in tests/test_signatures.py):

    1. sum_vs_product / product_vs_sum   two statement numbers explain both values
    2. digits_swapped                    same digits, another order
    3. sign                              chosen == -correct
    4. times_10 / div_10                 a factor of 10, 100 or 1000
    5. double / half                     a factor of 2 (never for the pair 1 <-> 2: off by one)
    6. plus_one / minus_one              |difference| == 1
    7. missing_add / missing_subtract    |difference| == a number of the statement (>= 2)
    8. statement_number                  the chosen value is written in the statement
    9. none                              nothing fits

Every text goes through copilot.leak_filter before it is returned: a text that happens to
contain the correct value (the Catalan "dues" when the answer is 2, a statement number
equal to the answer) is dropped and the next matching signature is tried. The Catalan
texts avoid "un"/"una" wherever they can, because the filter reads them as the number 1.
The last resort text of "none" carries no digit and no number word, so it always passes.

The `evidence` dict carries the correct value and the difference for logs and the
teacher page: never send it to the student's browser.

Board code: Python standard library only.
"""
import re
from fractions import Fraction

from .leak_filter import leaks
from .solvers.common import LETTERS, fmt, parse_number

# Units that carry a digit (cm3, m², km2): removed before counting the numbers of an option
_UNIT_WITH_DIGIT = re.compile(r"(?<=\d)\s*(?:cm|dm|mm|km|m)[23²³](?!\d)", re.IGNORECASE)
_NUMBER_TOKEN = re.compile(r"-?\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?")
# "13. For 3 days..." -> the leading problem number is not a number of the statement
_LEADING_INDEX = re.compile(r"^\s*\d{1,2}\s*[.)]\s*")

_POWERS_OF_TEN = (10, 100, 1000)
_ZEROS_EN = {10: "one zero", 100: "two zeros", 1000: "three zeros"}

NONE_TEXT = {
    "text_ca": "El teu resultat no s'assembla al correcte per cap relliscada típica: "
               "torna a llegir l'enunciat i planteja el problema des del principi.",
    "text_en": "Your result is not a typical slip away from the right one: "
               "read the statement again and set the problem up from scratch.",
}


def option_value(text):
    """The value of an option that is a single number (units allowed), else None.

    Strict on purpose: "18 cm" -> 18, "17,5cm" -> 17.5, "3/4" -> 3/4, "80 cm²" -> 80,
    but "77 2" (OCR noise), "{2,3,5,7}", "3 : 4", "1 1/2" and "m+n" -> None.
    """
    if text is None:
        return None
    clean = _UNIT_WITH_DIGIT.sub("", str(text).replace("−", "-"))
    tokens = _NUMBER_TOKEN.findall(clean)
    if len(tokens) != 1:
        return None
    return parse_number(tokens[0])


def statement_numbers(text):
    """The distinct numbers written in the statement, as Fractions, in order of appearance."""
    if not text:
        return []
    body = _LEADING_INDEX.sub("", str(text).replace("−", "-"))
    seen, out = set(), []
    for tok in _NUMBER_TOKEN.findall(body):
        v = parse_number(tok)
        if v is not None and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _digits(value):
    """Digit string of a non-negative integer Fraction, or None."""
    if value.denominator != 1:
        return None
    return str(abs(value.numerator))


def _candidates(correct, chosen, numbers):
    """Every signature that explains chosen from correct, most specific first: [(key, texts, evidence)]."""
    out = []
    diff = chosen - correct

    # 1. Two statement numbers: the student added where the product was needed, or the reverse
    for i, a in enumerate(numbers):
        for b in numbers[i + 1:]:
            if a * b == correct and a + b == chosen:
                out.append(("sum_vs_product", {
                    "text_ca": f"Has sumat {fmt(a)} i {fmt(b)} quan calia multiplicar-los.",
                    "text_en": f"You added {fmt(a)} and {fmt(b)} where they had to be multiplied.",
                }, {"a": fmt(a), "b": fmt(b)}))
            elif a + b == correct and a * b == chosen:
                out.append(("product_vs_sum", {
                    "text_ca": f"Has multiplicat {fmt(a)} i {fmt(b)} quan calia sumar-los.",
                    "text_en": f"You multiplied {fmt(a)} and {fmt(b)} where they had to be added.",
                }, {"a": fmt(a), "b": fmt(b)}))

    # 2. Same digits in another order (integers of two or more digits)
    dc, dw = _digits(correct), _digits(chosen)
    if dc and dw and len(dc) >= 2 and dc != dw and sorted(dc) == sorted(dw) \
            and (correct >= 0) == (chosen >= 0):
        out.append(("digits_swapped", {
            "text_ca": "Has intercanviat les xifres: tens les xifres bones però en un altre ordre. "
                       "Torna a escriure el nombre amb calma.",
            "text_en": "You swapped the digits: right digits, wrong order. "
                       "Write the number again carefully.",
        }, {}))

    # 3. Sign
    if correct != 0 and chosen == -correct:
        out.append(("sign", {
            "text_ca": "Has canviat el signe: revisa què es resta de què.",
            "text_en": "You changed the sign: check what is subtracted from what.",
        }, {}))

    # 4. A power of ten
    if correct != 0:
        for p in _POWERS_OF_TEN:
            if chosen == correct * p:
                out.append(("times_10", {
                    "text_ca": "Se t'ha escapat la coma o algun zero: el teu resultat és massa gran. "
                               "Revisa les unitats i la coma decimal.",
                    "text_en": f"You have {_ZEROS_EN[p]} too many: your result is too big. "
                               "Check the units and the decimal point.",
                }, {"factor": p}))
            elif chosen * p == correct:
                out.append(("div_10", {
                    "text_ca": "Se t'ha escapat la coma o algun zero: el teu resultat és massa petit. "
                               "Revisa les unitats i la coma decimal.",
                    "text_en": f"You dropped {_ZEROS_EN[p]}: your result is too small. "
                               "Check the units and the decimal point.",
                }, {"factor": p}))

    # 5. Double / half (1 <-> 2 is off by one, not a doubling)
    if correct != 0 and chosen == 2 * correct and not (correct == 1 and chosen == 2):
        out.append(("double", {
            "text_ca": "Has comptat cada cas dues vegades: el teu resultat és el doble del que toca. "
                       "Pensa quins casos són en realitat el mateix.",
            "text_en": "You counted every case twice: your result is double the right one. "
                       "Think about which cases are really the same.",
        }, {}))
    if chosen != 0 and correct == 2 * chosen and not (chosen == 1 and correct == 2):
        out.append(("half", {
            "text_ca": "T'has deixat la meitat: el teu resultat és la meitat del que toca. "
                       "Hi ha casos que no has comptat.",
            "text_en": "You left half out: your result is half the right one. "
                       "There are cases you did not count.",
        }, {}))

    # 6. Off by one
    if diff == 1:
        out.append(("plus_one", {
            "text_ca": "Et sobra el primer o el darrer: revisa els extrems del recompte.",
            "text_en": "You counted one too many: check the end points, one of them does not belong.",
        }, {}))
    elif diff == -1:
        out.append(("minus_one", {
            "text_ca": "Et falta el primer o el darrer: revisa els extrems del recompte.",
            "text_en": "You left an end point out: there is one more than you counted.",
        }, {}))

    # 7. The difference is a number of the statement
    for x in numbers:
        if x >= 2 and abs(diff) == x:
            if diff < 0:
                out.append(("missing_add", {
                    "text_ca": f"El teu resultat es queda curt: torna a mirar què fas amb el {fmt(x)} de l'enunciat, "
                               "potser l'havies de sumar.",
                    "text_en": f"Your result falls short: look again at what you do with the {fmt(x)} of the statement, "
                               "maybe it had to be added.",
                }, {"x": fmt(x)}))
            else:
                out.append(("missing_subtract", {
                    "text_ca": f"El teu resultat es passa: torna a mirar què fas amb el {fmt(x)} de l'enunciat, "
                               "potser l'havies de restar.",
                    "text_en": f"Your result overshoots: look again at what you do with the {fmt(x)} of the statement, "
                               "maybe it had to be subtracted.",
                }, {"x": fmt(x)}))
            break

    # 8. The chosen option is a number copied from the statement
    if chosen in numbers:
        out.append(("statement_number", {
            "text_ca": "La teva resposta és una dada de l'enunciat, no el resultat: encara falta fer-hi alguna operació.",
            "text_en": "Your answer is a number given in the statement, not the result: an operation is still missing.",
        }, {}))
    return out


def diagnose(problem, chosen_letter):
    """Name the slip behind a wrong answer, or None when there is nothing numeric to compare.

    problem: a Problem dict with `options`, `label` and (optionally) `text`.
    chosen_letter: the letter the student picked.
    """
    if not isinstance(problem, dict):
        return None
    options = problem.get("options") or {}
    label = str(problem.get("label") or "").strip().upper()
    chosen_letter = str(chosen_letter or "").strip().upper()
    if label not in LETTERS or chosen_letter not in LETTERS or chosen_letter == label:
        return None
    if label not in options or chosen_letter not in options:
        return None
    correct = option_value(options[label])
    chosen = option_value(options[chosen_letter])
    if correct is None or chosen is None or correct == chosen:
        return None

    numbers = statement_numbers(problem.get("text"))
    candidates = _candidates(Fraction(correct), Fraction(chosen), numbers)
    evidence = {
        "chosen_letter": chosen_letter, "chosen_value": fmt(chosen), "correct_value": fmt(correct),
        "difference": fmt(chosen - correct),
        "ratio": fmt(Fraction(chosen) / correct) if correct != 0 else None,
        "statement_numbers": [fmt(v) for v in numbers],
        "candidates": [key for key, _, _ in candidates],
        "dropped_by_leak_filter": [],
    }
    for key, texts, extra in candidates:
        if leaks(texts["text_ca"], label, options) or leaks(texts["text_en"], label, options):
            evidence["dropped_by_leak_filter"].append(key)
            continue
        evidence.update(extra)
        return {"signature": key, "text_ca": texts["text_ca"], "text_en": texts["text_en"], "evidence": evidence}
    return {"signature": "none", "text_ca": NONE_TEXT["text_ca"], "text_en": NONE_TEXT["text_en"],
            "evidence": evidence}


SIGNATURE_KEYS = ["sum_vs_product", "product_vs_sum", "digits_swapped", "sign", "times_10", "div_10",
                  "double", "half", "plus_one", "minus_one", "missing_add", "missing_subtract",
                  "statement_number", "none"]
