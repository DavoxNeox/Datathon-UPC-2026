"""copilot/webapp.py: the session behind the page, with the trainer mocked where the contract is optional."""
import contextlib
import io
import unittest
from unittest import mock

from copilot import webapp


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


class StartResetTest(unittest.TestCase):
    def setUp(self):
        self.s = webapp.Session()

    def test_start_screen_until_the_student_begins(self):
        state = quiet(self.s.state)
        self.assertFalse(state["started"])
        self.assertIsNone(state["problem"])

    def test_start_with_level_calls_start_student_when_the_trainer_has_it(self):
        calls = []
        fake_trainer = mock.MagicMock(wraps=webapp.trainer)
        fake_trainer.start_student = lambda student, level=None: calls.append((student, level)) or {}
        with mock.patch.object(webapp, "trainer", fake_trainer):
            state = quiet(self.s.start, "Mar", "2")
        self.assertEqual(calls, [("Mar", 2)])
        self.assertTrue(state["started"])
        self.assertEqual(state["level"], 2)
        self.assertEqual(state["student"], "Mar")
        self.assertIsNotNone(state["problem"])
        self.assertNotIn("label", state["problem"])

    def test_start_without_start_student_falls_back_to_the_current_flow(self):
        fake_trainer = mock.MagicMock(wraps=webapp.trainer)
        del fake_trainer.start_student
        with mock.patch.object(webapp, "trainer", fake_trainer):
            state = quiet(self.s.start, "Pau", "auto")
        self.assertTrue(state["started"])
        self.assertIsNone(state["level"])
        self.assertIsNotNone(state["problem"])

    def test_reset_calls_reset_student_and_returns_to_the_start_screen(self):
        calls = []
        fake_trainer = mock.MagicMock(wraps=webapp.trainer)
        fake_trainer.reset_student = lambda student: calls.append(student)
        with mock.patch.object(webapp, "trainer", fake_trainer):
            quiet(self.s.start, "Mar", "auto")
            state = quiet(self.s.reset)
        self.assertEqual(calls, ["Mar"])
        self.assertFalse(state["started"])
        self.assertIsNone(state["problem"])
        self.assertEqual(state["hints"], [])
        self.assertTrue(state["reset_supported"])

    def test_reset_without_reset_student_still_returns_to_the_start_screen(self):
        fake_trainer = mock.MagicMock(wraps=webapp.trainer)
        del fake_trainer.reset_student
        with mock.patch.object(webapp, "trainer", fake_trainer):
            quiet(self.s.start, "Mar", "auto")
            state = quiet(self.s.reset)
        self.assertFalse(state["started"])
        self.assertFalse(state["reset_supported"])

    def test_mastery_is_refreshed_right_after_the_answer(self):
        quiet(self.s.start, "test-webapp", "auto")
        fake_trainer = mock.MagicMock(wraps=webapp.trainer)
        fake_trainer.record_answer = lambda *a: {"correct": True, "label": "C", "topic": "arithmetic",
                                                  "mastery_before": 0, "mastery_after": 2, "review": False}
        fake_trainer.mastery_map = lambda student: {"arithmetic": 2}
        with mock.patch.object(webapp, "trainer", fake_trainer):
            state = quiet(self.s.answer_letter, "C")
        self.assertEqual(state["mastery"], {"arithmetic": 2})
        self.assertTrue(state["answer"]["correct"])
        self.s._timer.cancel()


class TeacherReportTest(unittest.TestCase):
    def test_trainer_list_shape_is_normalised_for_the_page(self):
        data = {"topics": [], "students": [
            {"student_id": "Mar", "mastery": {"arithmetic": 3}, "by_level": {2: {"answers": 4, "correct": 3}},
             "base_level": 2, "diagnostic_done": True, "answers": 4, "correct": 3, "reviews": 0}]}
        out = webapp._normalise_report(data, {"students": {}, "by_level": None})
        self.assertEqual(out["students"], {"Mar": {"arithmetic": 3}})
        self.assertEqual(out["by_level"], {"Mar": {"2": {"correct": 3, "total": 4}}})
        self.assertEqual(out["details"]["Mar"]["base_level"], 2)
        self.assertEqual(out["source"], "teacher_report")

    def test_dict_shape_passes_through(self):
        data = {"students": {"Mar": {"arithmetic": 1}}, "by_level": None}
        out = webapp._normalise_report(data, {"students": {}, "by_level": None})
        self.assertEqual(out["students"], {"Mar": {"arithmetic": 1}})


if __name__ == "__main__":
    unittest.main()
