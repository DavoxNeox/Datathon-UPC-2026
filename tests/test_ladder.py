import os
import unittest
from fractions import Fraction
from unittest import mock

from copilot import ladder


class LadderTest(unittest.TestCase):
    def test_middle_of_five_numbers(self):
        self.assertEqual(ladder.middle_letter({"options": {"A": "12", "B": "15", "C": "18", "D": "20", "E": "24"}}), "C")
        # not sorted: the middle VALUE wins, not the middle letter
        self.assertEqual(ladder.middle_letter({"options": {"A": "20", "B": "8", "C": "13", "D": "11", "E": "12"}}), "E")

    def test_units_decimals_and_fractions(self):
        self.assertEqual(ladder.middle_letter({"options": {"A": "48cm", "B": "40 cm", "C": "32cm", "D": "24 cm", "E": "16cm"}}), "C")
        self.assertEqual(ladder.middle_letter({"options": {"A": "165 cm²", "B": "176cm2", "C": "187 cm2", "D": "198 cm²", "E": "215 cm²"}}), "C")
        self.assertEqual(ladder.middle_letter({"options": {"A": "1/2", "B": "0.25", "C": "2,5", "D": "-1", "E": "10%"}}), "A")
        values = ladder.numeric_options({"A": "1/2", "B": "0.25", "C": "2,5", "D": "-1", "E": "10%"})
        self.assertEqual(values["C"], Fraction(5, 2))

    def test_abstains_on_words_noise_duplicates_or_missing_options(self):
        self.assertIsNone(ladder.middle_letter({"options": {}}))
        self.assertIsNone(ladder.middle_letter({}))
        self.assertIsNone(ladder.middle_letter({"options": {"A": "4", "B": "5", "C": "6", "D": "7", "E": "Q"}}))
        self.assertIsNone(ladder.middle_letter({"options": {"A": "1 10", "B": "11", "C": "12", "D": "13", "E": "15"}}))  # OCR noise
        self.assertIsNone(ladder.middle_letter({"options": {"A": "12 m 1m", "B": "8 m", "C": "13 m", "D": "11 m", "E": "10 m"}}))
        self.assertIsNone(ladder.middle_letter({"options": {"A": "3", "B": "3", "C": "4", "D": "5", "E": "6"}}))  # duplicates
        self.assertIsNone(ladder.middle_letter({"options": {"A": "1", "B": "2", "C": "3", "D": "4"}}))  # four options
        self.assertIsNone(ladder.middle_letter({"options": {"A": "15/4/2015", "B": "1/6/2055", "C": "1/5/2050", "D": "25/5/2015", "E": "15/5/2015"}}))

    def test_pipeline_flag_off_by_default_and_on_with_env(self):
        from copilot import pipeline
        self.assertFalse(pipeline.USE_MIDDLE_VALUE)
        problem = {"id": "x", "text": "How many?", "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}}
        with mock.patch.object(pipeline, "USE_MIDDLE_VALUE", True), mock.patch.object(pipeline, "USE_SOLVERS", False):
            result = pipeline.solve(problem)
        self.assertEqual((result["answer"], result["rule"], result["status"]), ("C", "middle_value", "ok"))
        self.assertEqual(result["board_seconds"], 0.0)
        with mock.patch.object(pipeline, "USE_MIDDLE_VALUE", False), mock.patch.object(pipeline, "USE_SOLVERS", False), \
             mock.patch.object(pipeline, "USE_LETTER_MODEL", False):
            result = pipeline.solve(problem)
        self.assertEqual((result["answer"], result["rule"]), (pipeline.FALLBACK, ""))


if __name__ == "__main__":
    unittest.main()
