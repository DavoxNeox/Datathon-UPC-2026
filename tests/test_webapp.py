"""copilot/webapp.py: the session behind the page, with the trainer mocked where the contract is optional."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from copilot import hints, webapp


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


BI_CAT = {"id": "bi-web", "language": "cat", "level": 1, "topic": "arithmetic", "text": "Quants cromos li queden?",
          "options": {"A": "6", "B": "8", "C": "9", "D": "11", "E": "21"}, "label": "C"}
BI_ENG = {**BI_CAT, "language": "eng", "text": "How many cards are left?"}


class Rung0Test(unittest.TestCase):
    """Rung 0 on the page: the other language by id, counted, never a hint for mastery."""

    def setUp(self):
        hints.register_problem(BI_CAT)
        hints.register_problem(BI_ENG)
        self.rungs = []
        self.trainer = mock.MagicMock(wraps=webapp.trainer)
        self.trainer.next_problem = lambda student: dict(BI_CAT)
        self.trainer.record_answer = lambda student, pid, letter, rung: self.rungs.append(rung) or {
            "correct": letter == "C", "label": "C", "topic": "arithmetic", "mastery_before": 0, "mastery_after": 0, "review": False}
        self.trainer.mastery_map = lambda student: {}
        self.trainer.start_student = lambda student, level=None: {}
        self.trainer.reset_student = lambda student: None
        del self.trainer.teacher_report
        self.patch = mock.patch.object(webapp, "trainer", self.trainer)
        self.patch.start()
        self.s = webapp.Session()
        quiet(self.s.start, "Mar", "1")

    def tearDown(self):
        self.patch.stop()
        if self.s._timer:
            self.s._timer.cancel()

    def test_show_puts_the_english_version_without_label_in_the_state(self):
        before = quiet(self.s.state)
        self.assertTrue(before["translation_available"])
        self.assertEqual(before["other_language"], "eng")
        self.assertIsNone(before["translation"])
        state = quiet(self.s.translate, "show")
        tr = state["translation"]
        self.assertEqual(tr["language"], "eng")
        self.assertEqual(tr["text"], "How many cards are left?")
        self.assertEqual(tr["options"]["C"], "9")
        self.assertNotIn("label", tr)
        self.assertNotIn("label", json.dumps(state["translation"]))
        self.assertNotIn("label", state["problem"])

    def test_show_is_a_timeline_row_with_zero_board_seconds_and_leaves_rung_at_0(self):
        state = quiet(self.s.translate, "show")
        rows = [r for r in state["timeline"] if r["action"] == "rung0:translation"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["board_s"], 0.0)
        self.assertEqual(state["rung"], 0)
        self.assertEqual(state["hints"], [])
        self.assertEqual(state["rung0"]["uses"], 1)

    def test_hide_keeps_the_count_and_a_second_show_counts_again(self):
        quiet(self.s.translate, "show")
        hidden = quiet(self.s.translate, "hide")
        self.assertIsNone(hidden["translation"])
        self.assertEqual(hidden["rung0"]["uses"], 1)
        again = quiet(self.s.translate, "show")
        self.assertEqual(again["rung0"]["uses"], 2)
        self.assertEqual(again["rung0"]["session"]["uses"], 2)
        self.assertEqual(again["rung0"]["session"]["problems"], 1)  # the same problem, counted once

    def test_record_answer_receives_rung_0_after_using_only_rung_0(self):
        quiet(self.s.translate, "show")
        state = quiet(self.s.answer_letter, "C")
        self.assertEqual(self.rungs, [0])
        self.assertTrue(state["answer"]["correct"])
        report = self.s.teacher()["rung0"]
        self.assertEqual(report["students_using"], 1)
        self.assertEqual(report["students_total"], 1)
        self.assertEqual(report["with"], {"answers": 1, "correct": 1})
        self.assertEqual(report["without"], {"answers": 0, "correct": 0})
        self.assertEqual(report["by_student"]["Mar"]["uses"], 1)

    def test_answers_without_rung_0_are_counted_apart(self):
        quiet(self.s.answer_letter, "A")
        report = self.s.teacher()["rung0"]
        self.assertEqual(self.rungs, [0])
        self.assertEqual(report["students_using"], 0)
        self.assertEqual(report["students_total"], 1)
        self.assertEqual(report["without"], {"answers": 1, "correct": 0})

    def test_rung_0_then_a_real_hint_keeps_the_hint_rung(self):
        quiet(self.s.translate, "show")
        with self.s.lock:
            self.s.rung = 2  # as _compute_hint would leave it after rung 2
        quiet(self.s.answer_letter, "C")
        self.assertEqual(self.rungs, [2])
        self.assertEqual(self.s.teacher()["rung0"]["with"]["answers"], 1)

    def test_next_problem_forgets_the_shown_translation(self):
        quiet(self.s.translate, "show")
        state = quiet(self.s.next)
        self.assertIsNone(state["translation"])
        self.assertEqual(state["rung0"]["uses"], 0)
        self.assertEqual(state["rung0"]["session"]["uses"], 1)

    def test_english_page_offers_the_catalan_version(self):
        quiet(self.s.set_lang, "eng")
        state = quiet(self.s.translate, "show")
        self.assertEqual(state["shown_language"], "eng")
        self.assertEqual(state["other_language"], "cat")
        self.assertEqual(state["translation"]["text"], "Quants cromos li queden?")

    def test_no_other_language_is_an_error_and_counts_nothing(self):
        self.trainer.next_problem = lambda student: {"id": "sample-4", "language": "cat", "level": 1, "text": "x",
                                                     "options": {}, "label": "B"}
        quiet(self.s.next)
        self.assertFalse(quiet(self.s.state)["translation_available"])
        out = quiet(self.s.translate, "show")
        self.assertIn("error", out)
        self.assertEqual(self.s.teacher()["rung0"]["uses"], 0)

    def test_reset_forgets_the_student_counters(self):
        quiet(self.s.translate, "show")
        quiet(self.s.answer_letter, "C")
        quiet(self.s.reset)
        self.assertEqual(self.s.teacher()["rung0"]["students_total"], 0)


class Rung0StatsTest(unittest.TestCase):
    def test_counters_survive_a_restart_through_the_json_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rung0.json")
            stats = webapp.Rung0Stats(path)
            stats.use("Pau", first_on_this_problem=True)
            stats.answer("Pau", used_rung0=True, correct=False)
            stats.answer("Pau", used_rung0=False, correct=True)
            again = webapp.Rung0Stats(path)
            self.assertEqual(again.report()["by_student"]["Pau"],
                             {"uses": 1, "problems": 1, "with": {"answers": 1, "correct": 0}, "without": {"answers": 1, "correct": 1}})
            self.assertEqual(again.session["uses"], 0)  # the session counters start afresh
            again.forget("Pau")
            self.assertEqual(webapp.Rung0Stats(path).report()["students_total"], 0)

    def test_without_a_path_nothing_is_written(self):
        stats = webapp.Rung0Stats(None)
        stats.use("x", True)
        self.assertEqual(stats.report()["students_using"], 1)


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


class HintCapTest(unittest.TestCase):
    """The hint button works at most HINT_MAX_USES times per problem; rung 0 and the solution do not count."""

    def setUp(self):
        self.s = webapp.Session()
        self.s.start("cap-test", "auto")
        self.assertIsNotNone(self.s.problem)

    def _hint(self):
        # Run the hint synchronously: call the handler, then the worker it would have started
        with mock.patch.object(webapp.threading, "Thread") as thread:
            result = self.s.hint()
        if result.get("ok"):
            rung = thread.call_args.kwargs.get("args", thread.call_args[1].get("args"))[0]
            self.s._compute_hint(rung)
        return result

    def test_three_hints_then_refused(self):
        self.assertEqual(self.s.state()["hints_left"], webapp.HINT_MAX_USES)
        for n in range(webapp.HINT_MAX_USES):
            self.assertTrue(self._hint().get("ok"), f"hint {n + 1} should be accepted")
        self.assertEqual(self.s.state()["hints_left"], 0)
        refused = self._hint()
        self.assertEqual(refused.get("error"), "no hints left")
        self.assertIn("pistes", self.s.state()["message"]["ca"])
        self.assertEqual(len(self.s.hints), webapp.HINT_MAX_USES)

    def test_rung_0_and_solution_do_not_count(self):
        self.s.translate("show")
        self.assertEqual(self.s.state()["hints_left"], webapp.HINT_MAX_USES)
        with mock.patch.object(webapp.threading, "Thread"):
            self.assertTrue(self.s.solution().get("ok"))
        self.assertEqual(self.s.state()["hints_left"], webapp.HINT_MAX_USES)

    def test_cap_resets_on_the_next_problem(self):
        for _ in range(webapp.HINT_MAX_USES):
            self._hint()
        self.s.answer_letter("A")
        self.s.next()
        self.assertEqual(self.s.state()["hints_left"], webapp.HINT_MAX_USES)
