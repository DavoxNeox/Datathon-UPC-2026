"""Brief reasoning by the 0.8B itself, inside the board's time budget (flag THINK_LEVELS, off by default).

Every policy so far asked the model for one token (a letter, a value, five letters) with the
reasoning switched off (`--reasoning off --reasoning-budget 0` in math-llm.service). This stage
lets the model write a few lines of working before the letter. What the server at commit 2cbe0ec
allows, checked against the running server, not assumed (probe of 14 Nov 2026):

- The Qwen3.5 chat template honours `chat_template_kwargs: {"enable_thinking": true}` per request
  (`/apply-template` ends the prompt with `<think>\\n`), but `--reasoning-budget 0` closes the block
  at once: the completion is the same as without it (same content, no reasoning_content).
- Real thinking mode, through `/completion` with a hand-edited prompt, spent 250 tokens on the
  simplest sample problem and had not reached an answer ("Evaluate options: A) 8, B) 9, ...").
  At 5.6 tokens per second on the board that is already 45 s. Unusable.
- With the think block closed, the model still writes a short solution when asked ("Anna starts
  with 3 bags ... The correct answer is C) 10", 63 tokens). That is what this module uses: ONE chat
  completion whose `max_tokens` is computed from the board clock, with the letter read from the text.

Why one call and not reasoning + a grammar-forced letter: llama-server restores this hybrid
model's cache only at the start of the last user message (docs/results-A.md), so a second request
that sees the reasoning re-reads problem and reasoning (about 300 tokens, 26 s on the board).
The letter is parsed instead: "Answer: C" (the prompt asks for that line), "the answer is C",
"**C)**", or, when the model ends with a value and the options are distinct numbers, the option
with that value. Anything else abstains and the caller falls through to its usual policy
(family solvers already ran; middle value, then FALLBACK_ANSWER).

Budget: the pipeline passes THINK_BUDGET_SECONDS (45) minus what the problem has already cost.
The prompt is counted with the server's /tokenize (one cheap request; chars / CHARS_PER_TOKEN if it
fails), the system prompt is added when the cache is cold, and the output is capped so that prompt
plus output fit the budget at BOARD_PREFILL_TPS / BOARD_GEN_TPS. Fewer than THINK_MIN_TOKENS of
output left: no call at all. The real request also carries the caller's timeout; a timeout or a
server error abstains too. Determinism: temperature 0, SEED. The server's cache restore can change
a token or two of the working between a cold and a warm run (observed: 63 against 68 tokens for
the same prompt); the letter read from it did not change in our probes, but it is not guaranteed.
"""
import math
import re
import urllib.parse

from . import board_clock
from .client import post
from .config import CONFIG
from .ladder import numeric_options
from .llm import URL, format_problem
from .solvers.common import parse_number
from .votes import CHARS_PER_TOKEN

LETTERS = "ABCDE"
# Stable text first: the start of the prompt is read once per run as long as it does not change.
THINK_SYSTEM = ("You solve multiple-choice math competition problems for school students. "
                "Reason in English in a few short steps, then give the letter of the correct option.")
INSTRUCTIONS = {
    # steps: the first prompt measured (Experiment 6). 60% of the workings hit the 200-token cap.
    "steps": ("\n\nSolve it step by step in English, briefly: at most 6 short lines. "
              "End with a line \"Answer: X\" where X is the letter of the correct option."),
    # short: the same, asking for plain text and a word limit, to cut the LaTeX and the cut-offs.
    "short": ("\n\nSolve it in English in plain text, no LaTeX, at most 60 words. "
              "End with a line \"Answer: X\" where X is the letter of the correct option."),
    # match: the same, telling the model to pick the letter by comparing its result with the option values
    # (it often computes the right value and then names the wrong letter).
    "match": ("\n\nSolve it in English in plain text, no LaTeX, at most 60 words. "
              "Then compare your result with the five options and answer with the letter of the option "
              "whose value equals your result. End with a line \"Answer: X\"."),
}
STYLE = CONFIG.get("THINK_STYLE", "steps") or "steps"
INSTRUCTION = INSTRUCTIONS.get(STYLE, INSTRUCTIONS["steps"])
TEMPLATE_TOKENS = 16  # <|im_start|>, roles, <|im_end|>, the closed think block
SYSTEM_TOKENS = 40    # THINK_SYSTEM, paid when the cache is cold (a different stage ran just before)

MAX_TOKENS = int(CONFIG.get("THINK_MAX_TOKENS", "200") or 200)
# Board seconds one problem may spend here, minus what it already cost (the pipeline subtracts). 45, not the
# experiments' 50: on the board one request estimated at 49.5 s ran into the 57 s HTTP timeout (Experiment 7).
BUDGET = float(CONFIG.get("THINK_BUDGET_SECONDS", "45") or 45)
MIN_TOKENS = int(CONFIG.get("THINK_MIN_TOKENS", "80") or 80)


def levels_from_config(value=None):
    """THINK_LEVELS: comma-separated levels (0 to 7) on which the stage runs; empty = off; 'all' = every level."""
    if value is None:
        value = CONFIG.get("THINK_LEVELS", "")
    value = (value or "").strip().lower()
    if not value:
        return set()
    if value == "all":
        return set(range(8))
    levels = set()
    for part in value.split(","):
        part = part.strip()
        if part.isdigit():
            levels.add(int(part))
    return levels


def applies(problem, levels, text_only_only=True, numeric_too=True):
    """Whether the stage runs on this problem: a text, five options, a selected level, (by default) no figure,
    and, with numeric_too=False, only when the options are not five distinct numbers (where the
    middle-value prior already answers)."""
    if not (problem.get("text") or "").strip():
        return False  # nothing to reason about: a request on the options alone answered A in the review
    options = problem.get("options") or {}
    if len(options) != 5:
        return False
    if not numeric_too and numeric_options(options) is not None:
        return False
    level = problem.get("level")
    try:
        level = int(level)
    except (TypeError, ValueError):
        return False
    if level not in levels:
        return False
    if text_only_only and not problem.get("text_only", False):
        return False
    return True


def build_messages(problem):
    return [{"role": "system", "content": THINK_SYSTEM},
            {"role": "user", "content": format_problem(problem) + INSTRUCTION}]


def tokenize_url(url):
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, "/tokenize", "", ""))


def count_prompt_tokens(text, url=URL, timeout=5):
    """Tokens the server would read for this text: /tokenize, or a pessimistic guess if it fails."""
    try:
        return len(post(tokenize_url(url), {"content": text}, timeout=timeout)["tokens"])
    except Exception:  # any failure here must not cost the letter: guess high
        return int(len(text) / (CHARS_PER_TOKEN * 0.8)) + 1


def output_budget(prompt_tokens, budget, cold=False, max_tokens=MAX_TOKENS):
    """How many output tokens fit after reading the prompt, within budget board seconds (0 = none)."""
    tokens = prompt_tokens + TEMPLATE_TOKENS + (SYSTEM_TOKENS if cold else 0)
    seconds_left = budget - board_clock.estimate_tokens(tokens)
    if seconds_left <= 0:
        return 0
    return max(0, min(max_tokens, math.floor(seconds_left * board_clock.GEN_TPS)))


_ANSWER_LINE = re.compile(r"answer\s*(?:is)?\s*[:\-]?\s*[*_(\[]*\s*([A-E])(?![a-z])", re.I)
_BOLD_LETTER = re.compile(r"\*\*\s*\(?([A-E])\)?[^*\n]{0,40}\*\*")
_PAREN_LETTER = re.compile(r"(?:^|[\s(])([A-E])\)")
_LAST_NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?(?:/\d+)?")


def parse_letter(content, options=None, finished=True):
    """(letter or None, how) from the model's working. how names the pattern that matched, for the CSV.

    finished=False (the output hit max_tokens): only an explicit "Answer: X" counts. A cut-off
    working ends in the middle of a case analysis, and its last letter or number is not an answer
    (smoke run: "If a = 7" matched an option's value, "Comparing this to the options: A) 16" gave A).
    """
    text = (content or "").replace("−", "-")
    hits = _ANSWER_LINE.findall(text)
    if hits:
        return hits[-1].upper(), "answer_line"
    if not finished:
        return None, ""
    hits = _BOLD_LETTER.findall(text)
    if hits:
        return hits[-1].upper(), "bold"
    tail = "\n".join(text.strip().splitlines()[-2:])
    hits = _PAREN_LETTER.findall(tail)
    if len(set(hits)) == 1:
        return hits[0].upper(), "paren"
    values = numeric_options(options or {})
    if values:
        numbers = _LAST_NUMBER.findall(tail)
        if numbers:
            target = parse_number(numbers[-1])
            matches = [l for l in LETTERS if values[l] == target]
            if len(matches) == 1:
                return matches[0], "value"
    return None, ""


def think_letter(problem, timeout=60, url=URL, budget=None, cold=False, max_tokens=MAX_TOKENS,
                 min_tokens=MIN_TOKENS):
    """(letter or None, info, timings). info records tokens, finish reason and the working for the CSV."""
    messages = build_messages(problem)
    info = {"skipped": "", "n_predict": 0, "finish": "", "how": "", "text": ""}
    prompt_tokens = count_prompt_tokens(messages[1]["content"], url=url)
    n_predict = max_tokens if budget is None else output_budget(prompt_tokens, budget, cold, max_tokens)
    info["prompt_guess"] = prompt_tokens + TEMPLATE_TOKENS + (SYSTEM_TOKENS if cold else 0)
    if n_predict < min_tokens:
        info["skipped"] = "budget"
        return None, info, {}
    response = post(url, {
        "messages": messages,
        "max_tokens": n_predict,
        "temperature": 0,
        "seed": int(CONFIG["SEED"]),
        "cache_prompt": True,
    }, timeout=timeout)
    choice = response["choices"][0]
    content = choice["message"].get("content") or ""
    info.update(n_predict=n_predict, finish=choice.get("finish_reason", ""), text=content)
    letter, how = parse_letter(content, problem.get("options"), finished=choice.get("finish_reason") == "stop")
    info["how"] = how
    return letter, info, response.get("timings", {})
