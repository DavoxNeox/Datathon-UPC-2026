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


class DigitCountTest(unittest.TestCase):
    def test_product_zero_four_digit(self):
        from copilot.solvers import digit_count
        value, trace = digit_count.compute({"digits": 4, "measure": "B", "equals": 0}, {})
        self.assertEqual(value, 2439)  # lvl-6_2018_11
        self.assertEqual(trace[-1]["value"], "2439")

    def test_two_digit_sum_five(self):
        from copilot.solvers import digit_count
        self.assertEqual(digit_count.compute({"digits": 2, "measure": "A", "equals": 5}, {})[0], 5)  # 14 23 32 41 50

    def test_classify(self):
        self.assertEqual(solvers.classify({"text": "How many four-digit numbers have the property that the product of their digits is zero?"}), "digit_count")


class AverageTest(unittest.TestCase):
    def test_kinds(self):
        from copilot.solvers import average
        self.assertEqual(average.compute({"kind": "A", "n": 4, "mean": 5, "value": 10, "new_mean": 0, "score": 0, "target": 0}, {})[0], 6)
        self.assertEqual(average.compute({"kind": "B", "n": 4, "mean": 5, "value": 0, "new_mean": 6, "score": 0, "target": 0}, {})[0], 10)
        # lvl-6_2008_11: one test with 1 point, then perfect 5s, mean 4 -> 3 more tests
        self.assertEqual(average.compute({"kind": "C", "n": 1, "mean": 1, "value": 0, "new_mean": 0, "score": 5, "target": 4}, {})[0], 3)

    def test_geometric_mean_is_not_this_family(self):
        self.assertIsNone(solvers.classify({"text": "The geometric mean of three numbers is 3. What is the mean of all six?"}))


class AgesTest(unittest.TestCase):
    def test_sum_years_ago_and_later(self):
        from copilot.solvers import ages
        base = {"kind": "A", "n": 5, "total": 80, "years": 7, "direction": "A", "difference": 0, "parent": 0, "children_sum": 0, "children": 0}
        self.assertEqual(ages.compute(base, {})[0], 45)  # the naive value: the real answer 46 is not it, so solve() would abstain
        self.assertEqual(ages.compute({**base, "direction": "B"}, {})[0], 115)

    def test_older_sum_in_k_years(self):
        from copilot.solvers import ages
        p = {"kind": "B", "n": 0, "total": 31, "years": 5, "direction": "B", "difference": 3, "parent": 0, "children_sum": 0, "children": 0}
        self.assertEqual(ages.compute(p, {})[0], 9)  # Ben 9, Anna 12: in 5 years 14 + 17 = 31

    def test_children_catch_the_parent(self):
        from copilot.solvers import ages
        p = {"kind": "C", "n": 0, "total": 0, "years": 0, "direction": "A", "difference": 0, "parent": 36, "children_sum": 23, "children": 3}
        self.assertEqual(ages.compute({**p, "comparison": "A"}, {})[0], 7)   # lvl-1_2020_23: exceed -> first whole year past 6.5
        with self.assertRaises(ValueError):
            ages.compute({**p, "comparison": "B"}, {})                        # never exactly equal in a whole year
        self.assertEqual(ages.compute({**p, "parent": 35, "comparison": "B"}, {})[0], 6)
        self.assertEqual(ages.compute({**p, "parent": 35, "comparison": "A"}, {})[0], 7)

    def test_classify(self):
        self.assertEqual(solvers.classify({"text": "The ages of a family of five add up to 80 years. What was the sum 7 years ago?"}), "ages")
