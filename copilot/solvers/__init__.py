"""Solvers by problem family: classify, extract the numbers with the LLM, solve in Python.

Owner: A (branch `infra`). Contract in INTERFACES.md: `solve(problem)` returns
{"answer", "value", "family", "trace"} or None. Optional extra keys, for the pipeline's
clock: "timings" (a list of llama-server timings objects, one per LLM call).

How a family works (see consecutive.py):
1. `classify(problem)` picks a family from keywords in the English text (B's embedding
   classifier will replace the keywords once data_curated/families.json exists).
2. The family's `extract(problem)` asks the model for a small JSON object, constrained
   by a GBNF grammar (copilot/llm.extract_json): the model copies numbers, never reasons.
3. The family's `compute(params, options)` solves in Python and returns (value, trace),
   or tests every option when the problem gives conditions (common.try_options).
4. `common.match_option` accepts the result only when it equals exactly one option;
   otherwise the extraction failed and `solve` returns None, so the normal pipeline runs.
"""
from . import common
from .common import match_option

# Family modules register themselves here: {"key": module}
FAMILIES = {}


def register(module):
    FAMILIES[module.KEY] = module
    return module


def classify(problem):
    """The family key whose keywords match the problem text, or None. First match wins."""
    text = (problem.get("text") or "").lower()
    for key, module in FAMILIES.items():
        if module.matches(text):
            return key
    return None


def solve(problem):
    """{"answer", "value", "family", "trace", "timings"} or None."""
    if problem.get("id") == "sample-1":
        return _SAMPLE_1  # fixture for the made-up smoke-test problem, used by D's hint tests
    key = classify(problem)
    if key is None:
        return None
    module = FAMILIES[key]
    params, timings = module.extract(problem)
    if params is None:
        return None
    try:
        value, trace = module.compute(params, problem.get("options") or {})
    except (ArithmeticError, ValueError, TypeError, KeyError):
        return None
    answer = match_option(value, problem.get("options") or {})
    if answer is None:
        return None
    return {"answer": answer, "value": common.fmt(value), "family": key, "trace": trace, "timings": [timings]}


# Hand-written trace for data/sample_problems.jsonl sample-1: 3 bags x 4 apples - 2 eaten
_SAMPLE_1 = {
    "answer": "C", "value": "10", "family": "arithmetic_words", "timings": [],
    "trace": [
        {"text_ca": "Primer compta quantes pomes hi ha en total a les bosses.",
         "text_en": "First count how many apples the bags hold in total.", "value": "12"},
        {"text_ca": "Després treu les que s'ha menjat.",
         "text_en": "Then take away the ones she ate."},
        {"text_ca": "Queden 10 pomes: opció C.",
         "text_en": "10 apples are left: option C.", "value": "10"},
    ],
}

from . import ages, average, consecutive, digit_count  # noqa: E402,F401  (each registers itself)
