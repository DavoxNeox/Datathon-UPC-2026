"""Estimate how long a request takes on the Arduino UNO Q, from llama-server timings.

The laptop is many times faster than the board, but the token counts are the same:
`timings.prompt_n` (tokens read, after the prompt cache) and `timings.predicted_n`
(tokens written). The board reads about BOARD_PREFILL_TPS tokens per second and writes
about BOARD_GEN_TPS, and one embedding costs BOARD_EMBED_SECONDS (config.env).

    seconds = prompt_n / BOARD_PREFILL_TPS + predicted_n / BOARD_GEN_TPS + embeddings * BOARD_EMBED_SECONDS

These constants are the README's measurements until Phase 10 calibrates them on the board.
Until then, every "board seconds" number in results/ is an estimate.
"""
import os
import time

from .config import CONFIG

PREFILL_TPS = float(CONFIG.get("BOARD_PREFILL_TPS", 11))
GEN_TPS = float(CONFIG.get("BOARD_GEN_TPS", 5.5))
EMBED_SECONDS = float(CONFIG.get("BOARD_EMBED_SECONDS", 0.25))


# The device tree names the board ("Arduino SA,Imola" on the UNO Q). On the host it is under
# /proc; inside the App Lab app container only the /sys path is bind-mounted.
BOARD_MODEL_FILE = "/proc/device-tree/model"
BOARD_MODEL_FILES = (BOARD_MODEL_FILE, "/sys/firmware/devicetree/base/model")


def on_board():
    """True on the Arduino UNO Q, on the host or inside its App Lab container. False on any laptop."""
    for path in (BOARD_MODEL_FILE,) + tuple(p for p in BOARD_MODEL_FILES if p != BOARD_MODEL_FILE):
        try:
            with open(path, "rb") as f:
                if b"Arduino" in f.read():
                    return True
        except OSError:
            continue
    return bool(os.environ.get("APP_HOME")) and os.path.isdir("/app")  # the App Lab container itself


def runtime():
    """"sim" on a laptop, "board" on the UNO Q.

    RUNTIME in the environment wins, then config.env. The default, "auto", detects the
    board from the device tree, so the same config.env runs unchanged in both places.
    """
    value = os.environ.get("RUNTIME", CONFIG.get("RUNTIME", "auto")).strip().lower()
    if value in ("", "auto"):
        return "board" if on_board() else "sim"
    return value


def estimate_tokens(prompt_tokens, output_tokens=0, embeddings=0, python_seconds=0.0):
    """Board seconds for a request of this size. Use it BEFORE trying a prompt."""
    return prompt_tokens / PREFILL_TPS + output_tokens / GEN_TPS + embeddings * EMBED_SECONDS + python_seconds


def estimate(timings, embeddings=0, python_seconds=0.0):
    """Board seconds for a request that already ran, from the server's `timings` object."""
    return estimate_tokens(timings.get("prompt_n", 0) or 0, timings.get("predicted_n", 0) or 0,
                           embeddings, python_seconds)


class Clock:
    """Adds up the board estimate of one problem: every LLM call and every embedding.

        clock = Clock()
        ... letter, timings = answer_letter(...); clock.add_llm(timings)
        ... clock.add_embeddings(1)
        clock.board_seconds()   # estimate on the board
        clock.real_seconds()    # measured here
    """

    def __init__(self):
        self.start = time.perf_counter()
        self.prompt_tokens = 0
        self.output_tokens = 0
        self.embeddings = 0

    def add_llm(self, timings):
        self.prompt_tokens += int(timings.get("prompt_n", 0) or 0)
        self.output_tokens += int(timings.get("predicted_n", 0) or 0)

    def add_embeddings(self, count=1):
        self.embeddings += count

    def real_seconds(self):
        return time.perf_counter() - self.start

    def board_seconds(self):
        """Estimate: the model work at board speed, plus the Python time measured here.

        Python on the laptop is faster than on the board too, but it is a small share
        of the total, so it is counted as measured.
        """
        return estimate_tokens(self.prompt_tokens, self.output_tokens, self.embeddings)

    def seconds(self):
        """What the time limit is checked against: the estimate in sim, the real time on the board."""
        return self.board_seconds() if runtime() == "sim" else self.real_seconds()


def sleep_to_board_time(clock):
    """Wait until the real time reaches the board estimate (eval.py --simulate-latency)."""
    gap = clock.board_seconds() - clock.real_seconds()
    if gap > 0:
        time.sleep(gap)
    return max(gap, 0.0)
