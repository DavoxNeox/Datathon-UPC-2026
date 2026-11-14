"""The LED matrix animator (copilot/hal/led.py): frames, sequences and the two modes.

With LED_ANIMATE=0 every call draws its final frame synchronously. With LED_ANIMATE=1 a daemon
thread advances the animation; the tests wait a few frames and look at last_frame().
"""
import contextlib
import io
import os
import time
import unittest

from copilot.hal import led

TOPICS8 = led.TOPIC_KEYS


def lit(frame):
    return sum(1 for row in frame for v in row if v)


class SyncMode(unittest.TestCase):
    def setUp(self):
        os.environ["LED_ANIMATE"] = "0"
        self.out = contextlib.redirect_stdout(io.StringIO())
        self.out.__enter__()

    def tearDown(self):
        self.out.__exit__(None, None, None)
        os.environ.pop("LED_ANIMATE", None)

    def test_mastery_bars(self):
        led.show_mastery({TOPICS8[0]: 5, TOPICS8[1]: 2})
        frame = led.last_frame()
        self.assertEqual(frame[0], [7] * 13)
        self.assertEqual(sum(1 for v in frame[1] if v), 5)   # 13 * 2 / 5 = 5.2 -> 5
        self.assertEqual(lit(frame[2:]), 0)

    def test_empty_mastery_is_dark_in_sync_mode(self):
        led.show_mastery({})
        self.assertEqual(lit(led.last_frame()), 0)

    def test_hints_left_blocks(self):
        led.show_mastery({TOPICS8[0]: 5})
        led.show_hints_left(2, 4)
        frame = led.last_frame()
        self.assertEqual(frame[0], [led.DIM] * 13)              # the bars, dimmed
        bottom = frame[7]
        self.assertEqual(bottom[0], led.FULL)                    # first block available
        self.assertEqual(bottom[3], led.FULL)                    # second block available
        self.assertEqual(bottom[6], led.DIM)                     # third spent
        self.assertEqual(bottom[9], led.DIM)                     # fourth spent
        self.assertEqual(bottom[2], 0)                           # a gap between blocks

    def test_hints_left_clamps(self):
        led.show_hints_left(9, 4)
        self.assertEqual(led.last_frame()[7][9], led.FULL)
        led.show_hints_left(-1, 4)
        self.assertEqual(led.last_frame()[7][0], led.DIM)

    def test_answer_draws_the_verdict(self):
        led.show_answer("C", True)
        self.assertEqual(led.last_frame(), led._frame_from_ascii(led.TICK))
        led.show_answer("A", False)
        self.assertEqual(led.last_frame(), led._frame_from_ascii(led.CROSS))

    def test_result_and_path(self):
        led.show_result(False)
        self.assertEqual(led.last_frame(), led._frame_from_ascii(led.CROSS))
        led.show_path([[1, 1, 1], [1, 2, 3], [1, 3, 6]])
        self.assertEqual(led.last_frame()[0][:3], [7, 7, 7])
        self.assertEqual(led.last_frame()[2][3], 0)

    def test_pulse_is_a_no_op_in_sync_mode(self):
        led.show_result(True)
        led.pulse(True)
        self.assertEqual(led.last_frame(), led._frame_from_ascii(led.TICK))
        led.pulse(False)

    def test_frame_shape_and_levels(self):
        led.show_hints_left(1, 3)
        frame = led.last_frame()
        self.assertEqual((len(frame), len(frame[0])), (8, 13))
        self.assertTrue(all(0 <= v <= 7 for row in frame for v in row))


class AnimatedMode(unittest.TestCase):
    def setUp(self):
        os.environ["LED_ANIMATE"] = "1"
        self.out = contextlib.redirect_stdout(io.StringIO())
        self.out.__enter__()

    def tearDown(self):
        led.pulse(False)
        led.show_result(True)
        self.out.__exit__(None, None, None)
        os.environ.pop("LED_ANIMATE", None)

    def wait_until(self, predicate, seconds=2.0):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(0.03)
        return predicate()

    def test_empty_mastery_breathes(self):
        led.show_mastery({})
        self.assertTrue(self.wait_until(lambda: lit(led.last_frame()) > 0))
        frame = led.last_frame()
        self.assertEqual(frame[3][6], max(v for row in frame for v in row))   # the centre of the diamond
        self.assertTrue(all(v <= 4 for row in frame for v in row))

    def test_mastery_grows_to_its_bars(self):
        led.show_mastery({TOPICS8[0]: 5})
        self.assertTrue(self.wait_until(lambda: led.last_frame()[0] == [7] * 13))

    def test_answer_shows_the_letter_then_the_verdict(self):
        led.show_answer("B", True)
        first = led.last_frame()
        self.assertEqual(first[0][4:9], [7, 7, 7, 7, 0])         # the top of a B, columns 4..8
        self.assertTrue(self.wait_until(lambda: led.last_frame() == led._frame_from_ascii(led.TICK), 3.0))

    def test_pulse_runs_a_dot_on_the_bottom_row(self):
        led.show_hints_left(4, 4)
        led.pulse(True)
        seen = set()

        def collect():
            row = led.last_frame()[7]
            full = [c for c, v in enumerate(row) if v == led.FULL]
            if len(full) == 1:
                seen.add(full[0])
            return len(seen) >= 3
        self.assertTrue(self.wait_until(collect, 3.0))
        led.pulse(False)
        self.assertTrue(self.wait_until(lambda: led.last_frame()[7][0] == led.FULL and led.last_frame()[7][2] == 0))


if __name__ == "__main__":
    unittest.main()
