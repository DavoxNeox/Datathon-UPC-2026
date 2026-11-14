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
from .. import board_clock, llm
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
    """{"answer", "value", "family", "trace", "timings"} or None (INTERFACES.md)."""
    return solve_with_timings(problem)[0]


def solve_with_timings(problem, timeout=60, budget=None):
    """(result or None, [llama-server timings of every LLM call made]).

    The pipeline uses solve_within: an extraction that ends in abstention still cost the
    board the reading of the problem, and that time counts against the 60-second limit.
    """
    return solve_within(problem, timeout, budget)[:2]


EXTRACT_MAX_TOKENS = 60  # llm.extract_json's default: the JSON object
TEMPLATE_TOKENS = 24     # roles, markers, "Fill in:" and "JSON:" around the text and the hint


def extraction_board_seconds(problem, module):
    """What the family's extraction would cost on the board, guessed from the text length before sending it."""
    text = llm.EXTRACT_SYSTEM + (problem.get("text") or "") + module.HINT
    return board_clock.estimate_tokens(board_clock.guess_tokens(text) + TEMPLATE_TOKENS, EXTRACT_MAX_TOKENS)


def solve_within(problem, timeout=60, budget=None):
    """(result or None, [timings], skipped): the family solver inside a time budget.

    budget is in board seconds (None = no limit). When the guessed cost of the extraction (the
    whole problem text is read: 298 tokens take 37 s on the board, 766 tokens 78 s) passes it,
    no request is made and skipped names the reason ("budget"); the caller's usual policy answers.
    timeout is the HTTP timeout of the extraction, the seconds really left on the clock.
    """
    if problem.get("id") == "sample-1":
        return _SAMPLE_1, [], ""  # fixture for the made-up smoke-test problem, used by D's hint tests
    key = classify(problem)
    if key is None:
        return None, [], ""
    module = FAMILIES[key]
    if budget is not None and extraction_board_seconds(problem, module) > budget:
        return None, [], "budget"
    params, timings = module.extract(problem, timeout=timeout)
    spent = [timings] if timings else []
    if params is None:
        return None, spent, ""
    try:
        value, trace = module.compute(params, problem.get("options") or {})
    except (ArithmeticError, ValueError, TypeError, KeyError):
        return None, spent, ""
    answer = match_option(value, problem.get("options") or {})
    if answer is None:
        return None, spent, ""
    return {"answer": answer, "value": common.fmt(value), "family": key, "trace": trace, "timings": spent}, spent, ""


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
