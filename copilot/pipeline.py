"""The baseline copilot: one problem in, one letter out.

This is the file to change first. predict.py and eval.py both call solve(),
so whatever you build here is exactly what the official run measures.
"""
import socket
import time
import urllib.error

from . import bias
from .board_clock import Clock
from .config import CONFIG
from .llm import URL, answer_letter, letter_scores

TIME_LIMIT = float(CONFIG["TIME_LIMIT_SECONDS"])
FALLBACK = CONFIG["FALLBACK_ANSWER"]
MARGIN = 3.0  # seconds kept free for Python and for writing the answer
# Letter-bias calibration from calibrate_bias.py. None = the raw baseline (one letter, no logprobs).
BIAS = bias.load()


def solve(problem, index=None, k=0, exclude_id=None, image_b64=None, llm_url=URL,
          time_limit=TIME_LIMIT):
    """Return {"answer", "seconds", "board_seconds", "status", ...} for one problem.

    seconds is measured here; board_seconds is the estimate for the UNO Q from the
    token counts (copilot/board_clock.py). On the board they should agree.

    index and k turn on retrieval: the k most similar solved problems are
    added to the prompt as examples. Each example costs reading time.
    image_b64 and llm_url send the problem image to a vision server.

    With a letter-bias calibration (data_curated/letter_prior.json) the model is
    asked once for the log probabilities of A to E and the answer is the letter
    with the best corrected score (copilot/bias.py). Same request size, no extra
    tokens. raw_letter is what the model would have answered on its own.
    """
    start = time.perf_counter()
    clock = Clock()
    result = {"answer": FALLBACK, "status": "ok", "prompt_tokens": 0, "retrieved": "", "examples": [],
              "board_seconds": 0.0, "raw_letter": "", "margin": None}
    try:
        examples = []
        if index is not None and k > 0:
            hits = index.search(problem, k=k, exclude_id=exclude_id)
            examples = [p for _score, p in hits]
            result["examples"] = hits
            result["retrieved"] = ";".join(f"{p['id']}:{s:.2f}" for s, p in hits)
            clock.add_embeddings(1)  # the query is embedded once
        remaining = time_limit - (time.perf_counter() - start) - MARGIN
        if BIAS is not None and image_b64 is None:
            raw, scores, timings = letter_scores(problem, examples, timeout=max(remaining, 1.0), url=llm_url)
            letter, margin = bias.choose(scores, BIAS["prior"], BIAS["alpha"], BIAS["min_margin"], BIAS["fallback"])
            result["raw_letter"] = raw
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
