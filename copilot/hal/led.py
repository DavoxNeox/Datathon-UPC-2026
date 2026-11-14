"""The 8x13 LED matrix: a small animator over the frame the sketch draws.

Owner: A (branch `infra`). Backend chosen by RUNTIME: `sim` prints the key frames as ASCII and
keeps the last frame for the web page; `board` sends every frame over the App Lab Bridge to
`sketch/sketch.ino`, which only copies the 104 bytes into the matrix. Callers never know which runs.

What the matrix shows (the web app calls these; nothing here reads the trainer or the hints):

- `show_mastery(mastery)`     rest frame: one row per topic, a bar of 0..13 LEDs for mastery 0..5,
                              grown over half a second. An empty map breathes slowly instead of
                              staying dark, so the matrix never looks dead.
- `show_hints_left(left, n)`  while a problem is open: `n` blocks on the bottom rows, the spent
                              ones dimmed; the top rows keep the mastery bars, dimmed.
- `pulse(True/False)`         a dot runs along the bottom row while the model writes a hint or the
                              solution is being prepared; the frame underneath stays.
- `show_answer(letter, ok)`   the letter the student chose, big, then the tick or the cross.
- `show_result(ok)`           tick or cross at once (kept for the contract).
- `show_path(grid)`           the path-count grid of the manipulative, non-zero cells lit.
- `last_frame()`              the frame on the matrix right now, for the web page's canvas.

Every call returns at once: a daemon thread advances the animation at `FPS` frames per second and
only sends a frame when it changed. `LED_ANIMATE=0` (config.env or environment) draws the final
frame synchronously with no thread, which is what the tests use.
"""
import logging
import os
import threading
import time

from .. import board_clock
from ..config import CONFIG
from ..topics import TOPIC_KEYS

ROWS, COLS = 8, 13
FPS = 12
FULL, DIM = 7, 2                 # brightness levels, 0..7 (the sketch uses 3 grayscale bits)
LETTER_SECONDS = 0.8             # the chosen letter before the tick or the cross
GROW_SECONDS = 0.5               # the mastery bars growing
BREATH_SECONDS = 2.4             # one breath of the empty rest frame
PULSE_SECONDS = 1.0              # one run of the thinking dot

log = logging.getLogger(__name__)

TICK = ["......###....", "......##.....", ".....###.....", ".#...##......",
        ".##.###......", "..####.......", "...##........", "............."]
CROSS = [".............", "...##...##...", "....##.##....", ".....###.....",
         ".....###.....", "....##.##....", "...##...##...", "............."]
# 5x7 glyphs, drawn centred (columns 4..8)
GLYPHS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
}
# the breath: a soft diamond in the middle, brightness scaled 1..4
BREATH = [".............", "......#......", ".....###.....", "....#####....",
          ".....###.....", "......#......", ".............", "............."]


def runtime():
    return board_clock.runtime()  # "auto" detects the board from the device tree


def _animate_enabled():
    value = os.environ.get("LED_ANIMATE", CONFIG.get("LED_ANIMATE", "1"))
    return str(value).strip() not in ("0", "", "off", "false")


def _frame_from_ascii(lines, level=FULL):
    return [[level if ch == "#" else 0 for ch in line.ljust(COLS, ".")[:COLS]] for line in lines[:ROWS]]


def _blank():
    return [[0] * COLS for _ in range(ROWS)]


def _is_blank(frame):
    return not any(v for row in frame for v in row)


def _scale(frame, level):
    """The lit cells of `frame` at brightness `level` (0 stays 0)."""
    return [[level if v else 0 for v in row] for row in frame]


def _mastery_frame(mastery, fraction=1.0, level=FULL):
    frame = []
    for key in TOPIC_KEYS:
        lit = round(13 * max(0, min(5, int(mastery.get(key, 0)))) / 5 * fraction)
        frame.append([level if c < lit else 0 for c in range(COLS)])
    return frame


# ----------------------------------------------------------------- the animator

_lock = threading.RLock()
_last_frame = _blank()
_rest = _blank()                 # the frame to come back to when nothing else is going on
_rest_breathes = True            # breathe when the rest frame is blank
_sequence = []                   # [(frame, seconds)] still to show, in order
_sequence_until = 0.0            # when the current sequence frame expires
_grow = None                     # (mastery, started) while the bars grow
_pulsing = False
_thread = None
_bridge_failures = 0


def last_frame():
    """The frame on the matrix right now, as 8 rows of 13 brightness values (0..7)."""
    with _lock:
        return [row[:] for row in _last_frame]


def _send(frame, key=False):
    """Draw one frame. `key` frames are the ones callers asked for: the sim prints those only."""
    global _last_frame
    with _lock:
        if frame == _last_frame and not key:
            return
        _last_frame = [row[:] for row in frame]
    if runtime() == "board":
        _draw_board(frame)
    elif key:
        _draw_sim(frame)


def _draw_sim(frame):
    print("\n".join("".join("#" if v else "." for v in row) for row in frame))


def _draw_board(frame):
    global _bridge_failures
    try:
        from arduino.app_utils import Bridge  # provided by App Lab, only on the board
    except ImportError:
        _draw_sim(frame)
        return
    try:
        Bridge.call("draw", bytes(v for row in frame for v in row))
        _bridge_failures = 0
    except Exception as e:  # noqa: BLE001 - the matrix must never take the web app down
        _bridge_failures += 1
        if _bridge_failures in (1, 10, 100):
            log.warning("LED matrix: draw failed %d times (%s: %s)", _bridge_failures, type(e).__name__, e)
        if _bridge_failures >= 3:
            time.sleep(min(5.0, 0.5 * _bridge_failures))


def _ensure_thread():
    global _thread
    if not _animate_enabled():
        return False
    with _lock:
        if _thread is None or not _thread.is_alive():
            _thread = threading.Thread(target=_run, name="led-animator", daemon=True)
            _thread.start()
    return True


def _current_frame(now):
    """The frame the matrix should show at `now`, from the state under the lock."""
    global _sequence, _sequence_until, _grow
    while _sequence and now >= _sequence_until:
        _sequence.pop(0)
        if _sequence:
            _sequence_until = now + _sequence[0][1]
    if _sequence:
        return _sequence[0][0]
    if _grow:
        mastery, started = _grow
        fraction = min(1.0, (now - started) / GROW_SECONDS)
        if fraction >= 1.0:
            _grow = None
        else:
            return _mastery_frame(mastery, fraction)
    base = [row[:] for row in _rest]
    if _pulsing:
        pos = int((now % PULSE_SECONDS) / PULSE_SECONDS * COLS)
        for c in range(COLS):
            base[ROWS - 1][c] = FULL if c == pos else (DIM if c == pos - 1 else 0)
        return base
    if _rest_breathes and _is_blank(base):
        phase = (now % BREATH_SECONDS) / BREATH_SECONDS       # 0..1
        level = 1 + round(3 * (1 - abs(2 * phase - 1)))      # 1..4..1
        return _frame_from_ascii(BREATH, level)
    return base


def _run():
    period = 1.0 / FPS
    while True:
        with _lock:   # compute and send together, so a caller's synchronous frame is never overtaken by an older one
            _send(_current_frame(time.monotonic()))
        time.sleep(period)


def _show(frame_now, key_frame=True):
    """Draw `frame_now` at once (synchronously), then let the thread carry on."""
    _send(frame_now, key=key_frame)
    _ensure_thread()


# ----------------------------------------------------------------- public API

def show_mastery(mastery):
    """Rest frame: one row per topic (LED order), a bar of 0..13 LEDs for mastery 0..5, grown."""
    global _rest, _grow, _sequence, _rest_breathes
    final = _mastery_frame(mastery)
    with _lock:
        _rest, _rest_breathes, _sequence = final, True, []
        _grow = (dict(mastery), time.monotonic()) if _animate_enabled() and not _is_blank(final) else None
        _send(final, key=True)   # the sim prints the bars once; on the board the thread grows them from here
    _ensure_thread()


def show_hints_left(left, maximum):
    """While a problem is open: the mastery bars dimmed on top, `maximum` blocks on the bottom
    two rows, the ones still available at full brightness, the spent ones dimmed."""
    global _rest, _grow, _sequence, _rest_breathes
    maximum = max(1, int(maximum))
    left = max(0, min(maximum, int(left)))
    with _lock:
        frame = _scale(_rest if not _grow else _mastery_frame(_grow[0]), DIM)
        width = COLS // maximum
        for i in range(maximum):
            level = FULL if i < left else DIM
            for c in range(i * width, i * width + width - 1):
                frame[ROWS - 2][c] = level
                frame[ROWS - 1][c] = level
        _rest, _rest_breathes, _grow, _sequence = frame, False, None, []
    _show(frame)


def pulse(on):
    """A dot running along the bottom row while something is being prepared."""
    global _pulsing
    with _lock:
        _pulsing = bool(on) and _animate_enabled()
        frame = _current_frame(time.monotonic())
    _show(frame, key_frame=False)


def show_answer(letter, ok):
    """The chosen letter, big, for LETTER_SECONDS, then the tick or the cross, which stays."""
    global _sequence, _sequence_until, _rest, _rest_breathes, _grow, _pulsing
    verdict = _frame_from_ascii(TICK if ok else CROSS)
    glyph = GLYPHS.get(str(letter).upper()[:1])
    with _lock:
        _pulsing, _grow = False, None
        _rest, _rest_breathes = verdict, False
        if glyph and _animate_enabled():
            frame = _blank()
            for r, line in enumerate(glyph):
                for c, ch in enumerate(line):
                    if ch == "#":
                        frame[r][4 + c] = FULL
            _sequence = [(frame, LETTER_SECONDS)]
            _sequence_until = time.monotonic() + LETTER_SECONDS
            first = frame
        else:
            _sequence, first = [], verdict
    _show(first)


def show_result(ok):
    """Tick or cross at once, kept as the rest frame."""
    global _sequence, _rest, _rest_breathes, _grow, _pulsing
    verdict = _frame_from_ascii(TICK if ok else CROSS)
    with _lock:
        _pulsing, _grow, _sequence = False, None, []
        _rest, _rest_breathes = verdict, False
    _show(verdict)


def show_path(grid):
    """Light the cells of a path-count grid (rows of ints); non-zero cells are on."""
    global _sequence, _rest, _rest_breathes, _grow, _pulsing
    frame = _blank()
    for r, row in enumerate(grid[:ROWS]):
        for c, v in enumerate(row[:COLS]):
            frame[r][c] = FULL if v else 0
    with _lock:
        _pulsing, _grow, _sequence = False, None, []
        _rest, _rest_breathes = frame, False
    _show(frame)
