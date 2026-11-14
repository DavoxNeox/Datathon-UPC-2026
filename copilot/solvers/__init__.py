"""Solvers by problem family: classify, extract parameters, solve in Python.

Owner: A (branch `infra`). Phase 0 stub: solves only sample-1, by hand.
See INTERFACES.md for the contract. `solve` returns None when no family applies.
"""


def solve(problem):
    """{"answer", "value", "family", "trace"} or None."""
    if problem.get("id") != "sample-1":
        return None
    # Hand-written trace for the made-up sample problem: 3 bags x 4 apples - 2 eaten
    return {
        "answer": "C",
        "value": "10",
        "family": "arithmetic_words",
        "trace": [
            {"text_ca": "Primer compta quantes pomes hi ha en total a les bosses.",
             "text_en": "First count how many apples the bags hold in total.", "value": "12"},
            {"text_ca": "Després treu les que s'ha menjat.",
             "text_en": "Then take away the ones she ate."},
            {"text_ca": "Queden 10 pomes: opció C.",
             "text_en": "10 apples are left: option C.", "value": "10"},
        ],
    }
