"""The 8x13 LED matrix: tick/cross, mastery map, path animation.

Owner: A (branch `infra`). Backend chosen by RUNTIME: `sim` prints ASCII and keeps the
last frame; `board` sends it over the App Lab Bridge. Callers never know which runs.
"""
import os

from ..config import CONFIG
from ..topics import TOPIC_KEYS

ROWS, COLS = 8, 13
_last_frame = [[0] * COLS for _ in range(ROWS)]

TICK = ["......###....", "......##.....", ".....###.....", ".#...##......",
        ".##.###......", "..####.......", "...##........", "............."]
CROSS = [".............", "...##...##...", "....##.##....", ".....###.....",
         ".....###.....", "....##.##....", "...##...##...", "............."]


def runtime():
    return os.environ.get("RUNTIME", CONFIG.get("RUNTIME", "sim"))


def _frame_from_ascii(lines):
    return [[7 if ch == "#" else 0 for ch in line.ljust(COLS, ".")[:COLS]] for line in lines[:ROWS]]


def last_frame():
    """The last frame drawn, as 8 rows of 13 brightness values (0..7). For the sim web page."""
    return [row[:] for row in _last_frame]


def _draw(frame):
    global _last_frame
    _last_frame = [row[:] for row in frame]
    if runtime() == "board":
        _draw_board(frame)
    else:
        _draw_sim(frame)


def _draw_sim(frame):
    print("\n".join("".join("#" if v else "." for v in row) for row in frame))


def _draw_board(frame):
    try:
        from arduino.app_utils import Bridge  # provided by App Lab, only on the board
    except ImportError:
        _draw_sim(frame)
        return
    Bridge.call("draw", bytes(v for row in frame for v in row))


def show_result(ok):
    _draw(_frame_from_ascii(TICK if ok else CROSS))


def show_mastery(mastery):
    """One row per topic (LED order), a bar of 0..13 LEDs for mastery 0..5."""
    frame = []
    for key in TOPIC_KEYS:
        lit = round(13 * max(0, min(5, int(mastery.get(key, 0)))) / 5)
        frame.append([7 if c < lit else 0 for c in range(COLS)])
    _draw(frame)


def show_path(grid):
    """Light the cells of a path-count grid (rows of ints); non-zero cells are on."""
    frame = [[0] * COLS for _ in range(ROWS)]
    for r, row in enumerate(grid[:ROWS]):
        for c, v in enumerate(row[:COLS]):
            frame[r][c] = 7 if v else 0
    _draw(frame)
