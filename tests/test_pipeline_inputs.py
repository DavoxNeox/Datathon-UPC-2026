"""solve() takes whatever the exam file carries, and no stage reads a text the clock cannot afford."""
import time
import unittest
from unittest import mock

from copilot import board_clock, llm, pipeline, solvers
from copilot.solvers import ages

NUMBERS = {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}
ODD_OPTIONS = [None, "a string", 42, ["1", "2", "3", "4", "5"], ["1", "2"], {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
               {"A": None, "B": ["x"], "C": {"v": 1}, "D": 4.5, "E": "5"}, {"F": "1", "": "2"}, {}]


class NormaliseTest(unittest.TestCase):
    def test_options_become_a_dict_of_strings_with_letter_keys(self):
        for odd in ODD_OPTIONS:
            clean = pipeline.normalise_problem({"text": "x", "options": odd})["options"]
            self.assertIsInstance(clean, dict, repr(odd))
            self.assertTrue(set(clean) <= set("ABCDE"), repr(odd))
            self.assertTrue(all(isinstance(v, str) for v in clean.values()), repr(odd))
        self.assertEqual(pipeline.normalise_problem({"options": ["1", "2", "3", "4", "5"]})["options"], NUMBERS)
        self.assertEqual(pipeline.normalise_problem({"options": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}})["options"], NUMBERS)
        self.assertEqual(pipeline.normalise_problem({"options": {"A": None, "B": ["x"], "C": {"v": 1}, "D": 4.5, "E": "5"}})["options"],
                         {"A": "", "D": "4.5", "E": "5"})

    def test_text_is_always_a_string_and_the_input_is_not_changed(self):
        for text in (None, 12, ["a"], {"t": 1}):
            self.assertIsInstance(pipeline.normalise_problem({"text": text})["text"], str)
        self.assertEqual(pipeline.normalise_problem({})["text"], "")
        raw = {"id": "k", "options": ["1", "2", "3", "4", "5"]}
        pipeline.normalise_problem(raw)
        self.assertEqual(raw["options"], ["1", "2", "3", "4", "5"])

    def test_solve_answers_a_letter_on_every_odd_input_without_a_server(self):
        def no_server(*args, **kwargs):
            raise AssertionError("no model call expected")
        with mock.patch.object(llm, "post", no_server):
            for odd in ODD_OPTIONS:
                for text in (None, "", "How many apples are left?", 7):
                    result = pipeline.solve({"id": "o", "text": text, "options": odd})
                    self.assertIn(result["answer"], list("ABCDE"), (odd, text))
                    self.assertTrue(result["status"].startswith("ok"), (odd, text))
            # the middle-value rule reads the normalised options: a list of five numbers is still five numbers
            self.assertEqual(pipeline.solve({"id": "o", "text": "x", "options": ["1", "2", "3", "4", "5"]})["answer"], "C")


class SolverBudgetTest(unittest.TestCase):
    LONG = ("The ages of the five people in a family add up to 80 years. " * 55).strip()  # about 1000 tokens

    def test_a_long_text_with_family_keywords_is_classified_but_not_sent(self):
        problem = {"id": "long", "text": self.LONG, "options": NUMBERS}
        self.assertEqual(solvers.classify(problem), "ages")
        self.assertGreater(solvers.extraction_board_seconds(problem, ages), 60)

        def no_server(*args, **kwargs):
            raise AssertionError("the extraction must not be sent")
        with mock.patch.object(llm, "post", no_server):
            result, spent, skipped = solvers.solve_within(problem, timeout=57.0, budget=57.0)
            self.assertEqual((result, spent, skipped), (None, [], "budget"))
            with mock.patch.object(pipeline, "USE_SOLVERS", True):
                start = time.perf_counter()
                answer = pipeline.solve(problem)
            self.assertLess(time.perf_counter() - start, 1.0)
        self.assertEqual(answer["answer"], "C")  # middle value answers instead
        self.assertEqual(answer["status"], "ok (solver skipped: budget)")
        self.assertEqual(answer["board_seconds"], 0.0)

    def test_a_normal_text_fits_and_gets_the_remaining_seconds_as_timeout(self):
        problem = {"id": "ok", "text": "The ages of a family of five add up to 80 years. What was the sum 7 years ago?",
                   "options": {"A": "45", "B": "52", "C": "60", "D": "66", "E": "73"}}
        # the hint of the ages family alone is about 230 tokens, read again on every problem: the cost is real
        self.assertLess(solvers.extraction_board_seconds(problem, ages), 57)
        seen = {}

        def fake_extract(problem, timeout=60):
            seen["timeout"] = timeout
            return None, {"prompt_n": 150, "predicted_n": 20}
        with mock.patch.object(ages, "extract", fake_extract):
            result, spent, skipped = solvers.solve_within(problem, timeout=42.0, budget=57.0)
        self.assertEqual((result, skipped), (None, ""))
        self.assertEqual(seen["timeout"], 42.0)
        self.assertEqual(spent, [{"prompt_n": 150, "predicted_n": 20}])

    def test_the_pipeline_passes_the_solver_budget(self):
        seen = {}

        def fake_within(problem, timeout=60, budget=None):
            seen.update(timeout=timeout, budget=budget)
            return None, [], ""
        with mock.patch.object(solvers, "solve_within", fake_within), mock.patch.object(pipeline, "USE_SOLVERS", True):
            pipeline.solve({"id": "b", "text": "x", "options": NUMBERS})
        self.assertEqual(seen["budget"], pipeline.SOLVER_BUDGET)
        self.assertEqual(seen["timeout"], pipeline.TIME_LIMIT - pipeline.MARGIN)
        self.assertEqual(pipeline.SOLVER_BUDGET, 42.0)

    def test_the_guess_errs_on_the_long_side(self):
        # 3 characters per token is below the measured mean of 3.2, so the guess is never the optimistic one
        self.assertGreaterEqual(board_clock.guess_tokens("x" * 300), 100)
        self.assertEqual(solvers.solve_with_timings({"id": "none", "text": "nothing", "options": {}}), (None, []))


if __name__ == "__main__":
    unittest.main()
