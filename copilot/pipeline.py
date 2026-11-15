"""The baseline copilot: one problem in, one letter out.

This is the file to change first. predict.py and eval.py both call solve(),
so whatever you build here is exactly what the official run measures.
"""
import socket
import time
import urllib.error

from . import bias, ladder, prior, solvers, think, votes
from .board_clock import Clock
from .config import CONFIG
from .llm import URL, answer_letter, letter_scores

TIME_LIMIT = float(CONFIG["TIME_LIMIT_SECONDS"])
FALLBACK = CONFIG["FALLBACK_ANSWER"]
MARGIN = 3.0  # seconds kept free for Python and for writing the answer
# Letter-bias calibration from calibrate_bias.py. None = the raw baseline (one letter, no logprobs).
BIAS = bias.load()
# Family solvers run first (copilot/solvers). Set SOLVERS=0 in the environment to measure without them.
USE_SOLVERS = CONFIG.get("SOLVERS", "1") != "0"
# When no solver applies: LETTER_MODEL=1 asks the model for a letter, LETTER_MODEL=0 answers
# FALLBACK_ANSWER at once. Measured on 281 English validation problems: the model's letter is
# 21.7% right, always D 23.1%, and its confidence is anti-correlated with being right, so the
# default is 0. Turn it on to collect the letter logprobs for analysis.
USE_LETTER_MODEL = CONFIG.get("LETTER_MODEL", "0") != "0"
# MIDDLE_VALUE=1 (default): when the five options are distinct numbers, answer the middle value
# (copilot/ladder.py) instead of the fallback letter; every other problem still gets FALLBACK_ANSWER.
# Measured on 281 English validation problems: 27.4% against 23.1% for always D, at no cost.
USE_MIDDLE_VALUE = CONFIG.get("MIDDLE_VALUE", "1") != "0"
# MIDDLE_VALUE_SKIP_ORDERED=1: the rule abstains (D answers) when the five values are printed in ascending or
# descending order, where it is "always C". Measured on data v2 (docs/reason-experiments.md, Data v2): off by default.
MIDDLE_SKIP_ORDERED = CONFIG.get("MIDDLE_VALUE_SKIP_ORDERED", "0") != "0"
# OPTION_PRIOR=1: the learned option prior (copilot/prior.py, data_curated/option_prior.json) answers before the
# middle-value rule where its stratum has a learned rule. Off by default: 80/281 against 77 on validation,
# bootstrap 95% [-4, +11] (docs/reason-experiments.md, experiment 5).
USE_OPTION_PRIOR = CONFIG.get("OPTION_PRIOR", "0") != "0"
# Experiments on the options (copilot/votes.py), off by default. VOTE_SHIFTS=5 asks for a letter once per
# cyclic shift of the options and takes a strict majority; VALUE_MODEL=1 asks for the option's value with
# a grammar limited to the five strings. Both run only when the problem has options, after the solvers
# and before the middle-value rule, and fall through when they abstain. Neither beat always D on the 281
# validation problems, and five shifts put 6 of 281 problems over 60 s, so both skip a problem whose
# board estimate would pass EXPERIMENT_BUDGET seconds (copilot/votes.py).
VOTE_SHIFTS = int(CONFIG.get("VOTE_SHIFTS", "0") or 0)
VOTE_MIN = int(CONFIG.get("VOTE_MIN", "3") or 3)
USE_VALUE_MODEL = CONFIG.get("VALUE_MODEL", "0") != "0"
EXPERIMENT_BUDGET = float(CONFIG.get("EXPERIMENT_BUDGET_SECONDS", "50") or 50)
# Estimated board seconds a solver's extraction may cost (its real time ran at 1.33x the estimate on the board).
SOLVER_BUDGET = float(CONFIG.get("SOLVER_BUDGET_SECONDS", "42") or 42)
# Brief reasoning by the 0.8B (copilot/think.py): THINK_LEVELS lists the levels on which the model writes a
# few lines of working before the letter (empty = off, "all" = every level); THINK_TEXT_ONLY=1 keeps it to
# problems without a figure. It runs after the solvers and before the middle-value rule, only when the
# board estimate leaves at least THINK_MIN_TOKENS of output inside THINK_BUDGET_SECONDS, and it
# abstains (the rest of the policy answers) on a budget skip, a timeout, a server error or unreadable working.
THINK_LEVELS = think.levels_from_config()
THINK_TEXT_ONLY = CONFIG.get("THINK_TEXT_ONLY", "1") != "0"
# THINK_NUMERIC=0 keeps the stage to problems whose options are not five distinct numbers (the middle-value
# prior answers those); 1 runs it on every problem with five options.
THINK_NUMERIC = CONFIG.get("THINK_NUMERIC", "1") != "0"


LETTERS = "ABCDE"


def normalise_problem(problem):
    """A copy of the problem with the fields every stage reads in the types it expects.

    The exam file may carry anything. text: a string ("" when missing or null, str() of any other
    type). options: a dict with keys A to E and string values; {} when missing, null or not a
    dict; lower-case keys are upper-cased; a list of five is read as A to E; a nested value
    (list, dict) drops its key. The solvers, ladder.numeric_options and the model stages then
    never see a list, a number or None where they expect text.
    """
    problem = dict(problem) if isinstance(problem, dict) else {"text": str(problem)}
    text = problem.get("text")
    problem["text"] = text if isinstance(text, str) else ("" if text is None else str(text))
    options = problem.get("options")
    if isinstance(options, (list, tuple)):
        options = dict(zip(LETTERS, options))
    clean = {}
    if isinstance(options, dict):
        for key, value in options.items():
            letter = str(key).strip().upper()
            if len(letter) == 1 and letter in LETTERS and not isinstance(value, (dict, list, tuple)):
                clean[letter] = "" if value is None else str(value)
    problem["options"] = clean
    return problem


def solve(problem, index=None, k=0, exclude_id=None, image_b64=None, llm_url=URL,
          time_limit=TIME_LIMIT):
    """Return {"answer", "seconds", "board_seconds", "status", ...} for one problem.

    seconds is measured here; board_seconds is the estimate for the UNO Q from the
    token counts (copilot/board_clock.py). On the board they should agree.

    index and k turn on retrieval: the k most similar solved problems are
    added to the prompt as examples. Each example costs reading time.
    image_b64 and llm_url send the problem image to a vision server.

    Order: a family solver when one applies (the model only copies numbers, Python
    computes, the value must match exactly one option), then brief reasoning by the model
    on the levels in THINK_LEVELS (copilot/think.py), then the learned option prior when
    OPTION_PRIOR=1 and its stratum has a rule, then the middle-value rule when
    MIDDLE_VALUE=1 and the options are numbers, else the letter model below.

    With a letter-bias calibration (data_curated/letter_prior.json) the model is
    asked once for the log probabilities of A to E and the answer is the letter
    with the best corrected score (copilot/bias.py). Same request size, no extra
    tokens. raw_letter is what the model would have answered on its own.
    """
    start = time.perf_counter()
    clock = Clock()
    problem = normalise_problem(problem)
    result = {"answer": FALLBACK, "status": "ok", "prompt_tokens": 0, "retrieved": "", "examples": [],
              "board_seconds": 0.0, "raw_letter": "", "margin": None, "family": "", "letter_logprobs": None,
              "rule": "", "extra": {}}
    try:
        if USE_SOLVERS and image_b64 is None:
            # The extraction reads the whole text: budget it like every other model call (a 766-token
            # exam row would take 78 s on the board), and give it the seconds really left as its timeout.
            try:
                solved, spent, skipped = solvers.solve_within(problem, timeout=max(time_limit - MARGIN, 1.0),
                                                               budget=min(SOLVER_BUDGET, time_limit - MARGIN) - clock.board_seconds())
            except (socket.timeout, TimeoutError, urllib.error.URLError) as error:
                # the extraction never came back (server down, timeout): the normal order answers below
                solved, spent, skipped = None, [], f"error: {getattr(error, 'reason', error)}"
            if skipped:
                result["status"] = f"ok (solver skipped: {skipped})"
            for timings in spent:  # counted even when the solver abstains: the board still read the problem
                clock.add_llm(timings)
                result["prompt_tokens"] += int(timings.get("prompt_n", 0) or 0)
            if solved is not None:
                result.update(answer=solved["answer"], family=solved["family"],
                              seconds=round(time.perf_counter() - start, 2), board_seconds=round(clock.board_seconds(), 2))
                return result
        remaining = time_limit - (time.perf_counter() - start) - MARGIN
        if THINK_LEVELS and image_b64 is None and think.applies(problem, THINK_LEVELS, THINK_TEXT_ONLY, THINK_NUMERIC):
            try:
                letter, info, timings = think.think_letter(problem, timeout=max(remaining, 1.0), url=llm_url,
                                                           budget=think.BUDGET - clock.board_seconds(),
                                                           cold=clock.prompt_tokens > 0)
            except (socket.timeout, TimeoutError, urllib.error.URLError) as error:
                # the working never arrived: the rest of the policy answers, and the time is unknown here
                letter, info, timings = None, {"skipped": f"error: {getattr(error, 'reason', error)}"}, {}
            clock.add_llm(timings)
            result["prompt_tokens"] += int(timings.get("prompt_n", 0) or 0)
            result["extra"]["think"] = info
            if letter is not None:
                result.update(answer=letter, rule="think", seconds=round(time.perf_counter() - start, 2),
                              board_seconds=round(clock.board_seconds(), 2))
                return result
            remaining = time_limit - (time.perf_counter() - start) - MARGIN
        if VOTE_SHIFTS > 0 and image_b64 is None and len(problem.get("options") or {}) == 5:
            letter, tally, spent = votes.vote_letter(problem, votes.SHIFTS[:VOTE_SHIFTS], timeout=max(remaining, 1.0),
                                                     url=llm_url, min_votes=VOTE_MIN,
                                                     budget=EXPERIMENT_BUDGET - clock.board_seconds())
            for timings in spent:
                clock.add_llm(timings)
                result["prompt_tokens"] += int(timings.get("prompt_n", 0) or 0)
            result["extra"]["votes"] = tally
            if letter is not None:
                result.update(answer=letter, rule="vote", seconds=round(time.perf_counter() - start, 2),
                              board_seconds=round(clock.board_seconds(), 2))
                return result
        if USE_VALUE_MODEL and image_b64 is None and problem.get("options"):
            remaining = time_limit - (time.perf_counter() - start) - MARGIN
            letter, value, timings = votes.value_letter(problem, timeout=max(remaining, 1.0), url=llm_url,
                                                        budget=EXPERIMENT_BUDGET - clock.board_seconds())
            clock.add_llm(timings)
            result["prompt_tokens"] += int(timings.get("prompt_n", 0) or 0)
            result["extra"]["value"] = value
            if letter is not None:
                result.update(answer=letter, rule="value", seconds=round(time.perf_counter() - start, 2),
                              board_seconds=round(clock.board_seconds(), 2))
                return result
        if USE_OPTION_PRIOR and image_b64 is None and (chosen := prior.choose(problem)) is not None:
            result.update(answer=chosen, rule="option_prior", seconds=round(time.perf_counter() - start, 2), board_seconds=round(clock.board_seconds(), 2))
            return result
        if USE_MIDDLE_VALUE and image_b64 is None:
            middle = ladder.middle_letter(problem, skip_ordered=MIDDLE_SKIP_ORDERED)
            if middle is not None:
                result.update(answer=middle, rule="middle_value", seconds=round(time.perf_counter() - start, 2),
                              board_seconds=round(clock.board_seconds(), 2))
                return result
        examples = []
        if index is not None and k > 0:
            hits = index.search(problem, k=k, exclude_id=exclude_id)
            examples = [p for _score, p in hits]
            result["examples"] = hits
            result["retrieved"] = ";".join(f"{p['id']}:{s:.2f}" for s, p in hits)
            clock.add_embeddings(1)  # the query is embedded once
        if not USE_LETTER_MODEL and image_b64 is None:
            # status stays as set above ("ok", or the solver skip note): the fallback letter is still an answer
            result["seconds"] = round(time.perf_counter() - start, 2)
            result["board_seconds"] = round(clock.board_seconds(), 2)
            return result  # answer stays FALLBACK
        remaining = time_limit - (time.perf_counter() - start) - MARGIN
        if image_b64 is None:
            # Always ask for the five letters' log probabilities: same request, same single
            # token, no extra cost, and eval.py keeps them for offline analysis.
            raw, scores, timings = letter_scores(problem, examples, timeout=max(remaining, 1.0), url=llm_url)
            result["raw_letter"] = raw
            result["letter_logprobs"] = {l: round(v, 4) for l, v in scores.items()}
            letter = raw
            if BIAS is not None:
                letter, margin = bias.choose(scores, BIAS["prior"], BIAS["alpha"], BIAS["min_margin"], BIAS["fallback"])
                result["margin"] = round(margin, 3)
        else:
            letter, timings = answer_letter(problem, examples, timeout=max(remaining, 1.0),
                                            image_b64=image_b64, url=llm_url)
        result["answer"] = letter
        result["prompt_tokens"] = timings.get("prompt_n", 0)
        clock.add_llm(timings)
    except (socket.timeout, TimeoutError):
        result["status"] = "timeout"
    except urllib.error.URLError as error:
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            result["status"] = "timeout"
        else:
            result["status"] = f"error: {error.reason}"
    result["seconds"] = round(time.perf_counter() - start, 2)
    result["board_seconds"] = round(clock.board_seconds(), 2)
    return result
