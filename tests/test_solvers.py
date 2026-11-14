import unittest
from fractions import Fraction

from copilot import solvers
from copilot.solvers import common, consecutive

OPTIONS = {"A": "19", "B": "21", "C": "23", "D": "25", "E": "27"}


class CommonTest(unittest.TestCase):
    def test_parse_number_formats(self):
        self.assertEqual(common.parse_number("18"), 18)
        self.assertEqual(common.parse_number("-3"), -3)
        self.assertEqual(common.parse_number("2.5"), Fraction(5, 2))
        self.assertEqual(common.parse_number("2,5 cm"), Fraction(5, 2))
        self.assertEqual(common.parse_number("3/4"), Fraction(3, 4))
        self.assertEqual(common.parse_number("36 cm²"), 36)
        self.assertIsNone(common.parse_number("a square"))
        self.assertIsNone(common.parse_number(None))

    def test_match_option_requires_exactly_one_hit(self):
        self.assertEqual(common.match_option(23, OPTIONS), "C")
        self.assertIsNone(common.match_option(24, OPTIONS))
        self.assertIsNone(common.match_option(23, {"A": "23", "B": "23"}))
        self.assertIsNone(common.match_option(23, {}))
        self.assertEqual(common.match_option(Fraction(1, 2), {"A": "0.5", "B": "1/3"}), "A")

    def test_try_options_lists_the_letters_that_satisfy_the_condition(self):
        self.assertEqual(common.try_options(OPTIONS, lambda v: v % 3 == 0), ["B", "E"])
        self.assertEqual(common.try_options(OPTIONS, lambda v: 1 / (v - 23) > 0), ["D", "E"])  # ZeroDivision skipped

    def test_fmt(self):
        self.assertEqual(common.fmt(Fraction(18)), "18")
        self.assertEqual(common.fmt(Fraction(5, 2)), "2.5")
        self.assertEqual(common.fmt(Fraction(1, 3)), "1/3")


class ConsecutiveTest(unittest.TestCase):
    def test_classify_by_keywords(self):
        self.assertEqual(solvers.classify({"text": "The sum of five consecutive numbers is 105."}), "consecutive")
        self.assertIsNone(solvers.classify({"text": "How many apples are left?"}))
        self.assertIsNone(solvers.classify({"text": "Three consecutive days of rain."}))  # no sum

    def test_compute_largest_of_five(self):
        value, trace = consecutive.compute({"count": 5, "sum": 105, "step": 1, "asked": 3}, {})
        self.assertEqual(value, 23)
        self.assertGreaterEqual(len(trace), 3)
        self.assertEqual(trace[-1]["value"], "23")
        for step in trace:
            self.assertIn("text_ca", step)
            self.assertIn("text_en", step)

    def test_compute_consecutive_even_smallest(self):
        value, _ = consecutive.compute({"count": 3, "sum": 36, "step": 2, "asked": 1}, {})
        self.assertEqual(value, 10)  # 10 + 12 + 14

    def test_no_integer_solution_raises(self):
        with self.assertRaises(ValueError):
            consecutive.compute({"count": 4, "sum": 15, "step": 1, "asked": 3}, {})  # 4 consecutive sum to 2 mod 4

    def test_unknown_asked_uses_the_options(self):
        value, _ = consecutive.compute({"count": 5, "sum": 105, "step": 1, "asked": 0}, {"A": "22", "B": "30"})
        self.assertEqual(value, 22)

    def test_solve_returns_none_without_a_family(self):
        self.assertIsNone(solvers.solve({"id": "x", "text": "How many apples?", "options": OPTIONS}))

    def test_solve_keeps_the_sample_fixture(self):
        r = solvers.solve({"id": "sample-1", "text": "x", "options": {}})
        self.assertEqual(r["answer"], "C")


if __name__ == "__main__":
    unittest.main()
