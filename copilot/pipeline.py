"""The baseline copilot: one problem in, one letter out.

This is the file to change first. predict.py and eval.py both call solve(),
so whatever you build here is exactly what the official run measures.
"""
import socket
import time
import urllib.error

from . import bias, ladder, solvers, votes
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
# MIDDLE_VALUE=1: when the five options are distinct numbers, answer the middle value (copilot/ladder.py)
# instead of the fallback letter. Measured on 281 English validation problems: 27.4% against 23.1% for
# always D, at no cost. Off by default until the controller adopts it.
USE_MIDDLE_VALUE = CONFIG.get("MIDDLE_VALUE", "0") != "0"
# Experiments on the options (copilot/votes.py), off by default. VOTE_SHIFTS=5 asks for a letter once per
# cyclic shift of the options and takes a strict majority; VALUE_MODEL=1 asks for the option's value with
# a grammar limited to the five strings. Both run only when the problem has options, after the solvers
# and before the middle-value rule, and fall through when they abstain.
VOTE_SHIFTS = int(CONFIG.get("VOTE_SHIFTS", "0") or 0)
VOTE_MIN = int(CONFIG.get("VOTE_MIN", "3") or 3)
USE_VALUE_MODEL = CONFIG.get("VALUE_MODEL", "0") != "0"


def solve(problem, index=None, k=0, exclude_id=None, image_b64=None, llm_url=URL,
          time_limit=TIME_LIMIT):
    """Return {"answer", "seconds", "board_seconds", "status", ...} for one problem.

    seconds is measured here; board_seconds is the estimate for the UNO Q from the
    token counts (copilot/board_clock.py). On the board they should agree.

    index and k turn on retrieval: the k most similar solved problems are
    added to the prompt as examples. Each example costs reading time.
    image_b64 and llm_url send the problem image to a vision server.

    Order: a family solver when one applies (the model only copies numbers, Python
    computes, the value must match exactly one option), then the middle-value rule when
    MIDDLE_VALUE=1 and the options are numbers, else the letter model below.

    With a letter-bias calibration (data_curated/letter_prior.json) the model is
    asked once for the log probabilities of A to E and the answer is the letter
    with the best corrected score (copilot/bias.py). Same request size, no extra
    tokens. raw_letter is what the model would have answered on its own.
    """
    start = time.perf_counter()
    clock = Clock()
    result = {"answer": FALLBACK, "status": "ok", "prompt_tokens": 0, "retrieved": "", "examples": [],
              "board_seconds": 0.0, "raw_letter": "", "margin": None, "family": "", "letter_logprobs": None,
              "rule": "", "extra": {}}
    try:
        if USE_SOLVERS and image_b64 is None:
            solved, spent = solvers.solve_with_timings(problem)
            for timings in spent:  # counted even when the solver abstains: the board still read the problem
                clock.add_llm(timings)
                result["prompt_tokens"] += int(timings.get("prompt_n", 0) or 0)
            if solved is not None:
                result.update(answer=solved["answer"], family=solved["family"],
                              seconds=round(time.perf_counter() - start, 2), board_seconds=round(clock.board_seconds(), 2))
                return result
        remaining = time_limit - (time.perf_counter() - start) - MARGIN
        if VOTE_SHIFTS > 0 and image_b64 is None and len(problem.get("options") or {}) == 5:
            letter, tally, spent = votes.vote_letter(problem, votes.SHIFTS[:VOTE_SHIFTS], timeout=max(remaining, 1.0),
                                                     url=llm_url, min_votes=VOTE_MIN)
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
            letter, value, timings = votes.value_letter(problem, timeout=max(remaining, 1.0), url=llm_url)
            clock.add_llm(timings)
            result["prompt_tokens"] += int(timings.get("prompt_n", 0) or 0)
            result["extra"]["value"] = value
            if letter is not None:
                result.update(answer=letter, rule="value", seconds=round(time.perf_counter() - start, 2),
                              board_seconds=round(clock.board_seconds(), 2))
                return result
        if USE_MIDDLE_VALUE and image_b64 is None:
            middle = ladder.middle_letter(problem)
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
            result["status"] = "ok"
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
