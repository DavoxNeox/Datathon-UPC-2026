"""copilot/signatures.py: the slip behind a wrong option, named without giving the answer away.

The problems here are made up (no M3Kang text). Each test says which signature must win
and, for the ties, why: the order in copilot/signatures.py is most specific first.
"""
import json
import os
import unittest

from copilot.leak_filter import leaks
from copilot.signatures import SIGNATURE_KEYS, diagnose, option_value, statement_numbers

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def problem(options, label, text=""):
    return {"id": "made-up", "language": "eng", "level": 0, "text": text, "options": options, "label": label}


FIVE = {"A": "6", "B": "9", "C": "10", "D": "12", "E": "20"}


class NothingToDiagnoseTest(unittest.TestCase):
    def test_right_answer_is_none(self):
        self.assertIsNone(diagnose(problem(FIVE, "C"), "C"))
        self.assertIsNone(diagnose(problem(FIVE, "C"), "c"))

    def test_letter_outside_the_options_is_none(self):
        self.assertIsNone(diagnose(problem(FIVE, "C"), "F"))
        self.assertIsNone(diagnose(problem(FIVE, "C"), ""))
        self.assertIsNone(diagnose(problem(FIVE, "C"), None))
        self.assertIsNone(diagnose(problem({"A": "6", "C": "10"}, "C"), "B"))

    def test_missing_label_or_options_is_none(self):
        self.assertIsNone(diagnose(problem(FIVE, ""), "A"))
        self.assertIsNone(diagnose(problem({}, "C"), "A"))
        self.assertIsNone(diagnose({"id": "x"}, "A"))
        self.assertIsNone(diagnose(None, "A"))

    def test_non_numeric_options_are_none(self):
        pictures = {"A": "", "B": "", "C": "", "D": "", "E": ""}
        self.assertIsNone(diagnose(problem(pictures, "C"), "A"))
        words = {"A": "Anna", "B": "Bernat", "C": "Carla", "D": "David", "E": "Eva"}
        self.assertIsNone(diagnose(problem(words, "C"), "A"))
        orders = {"A": "N,M,P,Q", "B": "M,N,Q,P", "C": "Q,N,M,P", "D": "N,Q,M,P", "E": "P,Q,M,N"}
        self.assertIsNone(diagnose(problem(orders, "C"), "A"))
        sets = {"A": "{2,3,5,7}", "B": "{1,3,6,19}", "C": "{3,5,7,9}", "D": "4", "E": "8"}
        self.assertIsNone(diagnose(problem(sets, "A"), "B"))
        self.assertIsNone(diagnose(problem(sets, "A"), "D"), "the correct option itself is a set")

    def test_ocr_noise_in_the_compared_option_is_none(self):
        noisy = {"A": "49", "B": "60", "C": "63", "D": "70", "E": "77 2"}
        self.assertIsNone(diagnose(problem(noisy, "D"), "E"))
        self.assertIsNotNone(diagnose(problem(noisy, "D"), "B"), "the other distractors still work")

    def test_equal_values_under_different_letters_is_none(self):
        self.assertIsNone(diagnose(problem({"A": "4", "B": "4.0", "C": "5", "D": "6", "E": "7"}, "A"), "B"))


class OptionValueTest(unittest.TestCase):
    def test_single_numbers(self):
        self.assertEqual(option_value("18"), 18)
        self.assertEqual(option_value("18 cm"), 18)
        self.assertEqual(option_value("17,5cm"), 17.5)
        self.assertEqual(option_value("2.5"), 2.5)
        self.assertEqual(option_value("3/4"), 0.75)
        self.assertEqual(option_value("−3"), -3)
        self.assertEqual(option_value("-3"), -3)
        self.assertEqual(option_value("80 cm²"), 80)
        self.assertEqual(option_value("1820cm3"), 1820)
        self.assertEqual(option_value("25%"), 25)
        self.assertEqual(option_value("60°"), 60)

    def test_not_a_single_number(self):
        for text in ("77 2", "{2,3,5,7}", "3 : 4", "1 1/2", "m+n", "r²", "TT", "", None, "19cm 28cm"):
            self.assertIsNone(option_value(text), text)


class StatementNumbersTest(unittest.TestCase):
    def test_leading_index_is_not_a_number_of_the_statement(self):
        self.assertEqual(statement_numbers("13. For 3 days the cat caught 2 mice."), [3, 2])

    def test_decimals_fractions_and_duplicates(self):
        self.assertEqual(statement_numbers("Pay 2,5 euros for 1/2 kg, then 2,5 more."), [2.5, 0.5])

    def test_empty(self):
        self.assertEqual(statement_numbers(""), [])
        self.assertEqual(statement_numbers(None), [])


class EachSignatureTest(unittest.TestCase):
    def check(self, prob, letter, key):
        d = diagnose(prob, letter)
        self.assertIsNotNone(d, key)
        self.assertEqual(d["signature"], key, d)
        return d

    def test_double_and_half(self):
        p = problem({"A": "3", "B": "6", "C": "12", "D": "24", "E": "30"}, "C")
        self.check(p, "D", "double")
        self.check(p, "B", "half")

    def test_double_with_units_and_fractions(self):
        self.check(problem({"A": "18 cm", "B": "36 cm", "C": "40 cm", "D": "50 cm", "E": "72 cm"}, "A"), "B", "double")
        self.check(problem({"A": "1/4", "B": "3/4", "C": "1,5", "D": "2", "E": "3"}, "B"), "C", "double")
        self.check(problem({"A": "0,25", "B": "3/4", "C": "1,5", "D": "2", "E": "3"}, "C"), "B", "half")

    def test_off_by_one(self):
        p = problem({"A": "8", "B": "9", "C": "10", "D": "11", "E": "20"}, "C")
        self.check(p, "D", "plus_one")
        self.check(p, "B", "minus_one")

    def test_one_and_two_is_off_by_one_not_a_doubling(self):
        p = problem({"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}, "A")
        self.check(p, "B", "plus_one")
        p = problem({"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}, "B")
        self.check(p, "A", "minus_one")

    def test_power_of_ten(self):
        p = problem({"A": "0,36", "B": "3,6", "C": "36", "D": "360", "E": "3600"}, "C")
        self.assertEqual(self.check(p, "D", "times_10")["evidence"]["factor"], 10)
        self.assertEqual(self.check(p, "E", "times_10")["evidence"]["factor"], 100)
        self.assertEqual(self.check(p, "B", "div_10")["evidence"]["factor"], 10)
        self.assertEqual(self.check(p, "A", "div_10")["evidence"]["factor"], 100)

    def test_digits_swapped(self):
        p = problem({"A": "12", "B": "21", "C": "27", "D": "72", "E": "102"}, "C")
        self.check(p, "D", "digits_swapped")
        p = problem({"A": "123", "B": "132", "C": "213", "D": "312", "E": "321"}, "A")
        self.check(p, "E", "digits_swapped")

    def test_sign(self):
        p = problem({"A": "-3", "B": "−1", "C": "0", "D": "1", "E": "3"}, "E")
        self.check(p, "A", "sign")
        p = problem({"A": "-3", "B": "−1", "C": "0", "D": "1", "E": "3"}, "B")
        self.check(p, "D", "sign")

    def test_sum_vs_product(self):
        text = "A room has 6 rows of 7 chairs. How many chairs are there?"
        p = problem({"A": "13", "B": "36", "C": "42", "D": "49", "E": "67"}, "C", text)
        d = self.check(p, "A", "sum_vs_product")
        self.assertEqual((d["evidence"]["a"], d["evidence"]["b"]), ("6", "7"))
        text = "Marta has 6 marbles and gets 7 more. How many marbles does she have?"
        p = problem({"A": "13", "B": "36", "C": "42", "D": "49", "E": "67"}, "A", text)
        self.check(p, "C", "product_vs_sum")

    def test_missing_add_and_subtract(self):
        text = "Anna has 3 bags with 4 apples in each bag. She eats 2 apples. How many are left?"
        p = problem({"A": "8", "B": "9", "C": "10", "D": "12", "E": "14"}, "C", text)
        self.assertEqual(self.check(p, "A", "missing_add")["evidence"]["x"], "2")        # 8 = 10 - 2
        self.assertEqual(self.check(p, "E", "missing_subtract")["evidence"]["x"], "4")   # 14 = 10 + 4
        self.assertEqual(self.check(p, "D", "missing_subtract")["evidence"]["x"], "2")   # 12 = 10 + 2 (forgot to eat)

    def test_missing_direction_and_fallbacks(self):
        text = "There are 20 children; 8 are boys. How many girls are there?"
        p = problem({"A": "4", "B": "6", "C": "12", "D": "20", "E": "28"}, "C", text)
        self.assertEqual(diagnose(p, "A")["signature"], "missing_add")        # 4 = 12 - 8
        self.assertEqual(diagnose(p, "A")["evidence"]["x"], "8")
        d = diagnose(p, "D")                                                  # 20 = 12 + 8, and 20 is in the text
        self.assertEqual(d["signature"], "missing_subtract")
        self.assertEqual(d["evidence"]["candidates"], ["missing_subtract", "statement_number"])
        self.assertEqual(diagnose(p, "B")["signature"], "half")               # 6 = 12 / 2
        self.assertEqual(diagnose(p, "E")["signature"], "none")               # 28: 16 away, not in the text

    def test_statement_number(self):
        text = "A square has a perimeter of 36 cm. What is its area?"
        p = problem({"A": "36 cm²", "B": "72 cm²", "C": "81 cm²", "D": "144 cm²", "E": "324 cm²"}, "C", text)
        self.check(p, "A", "statement_number")

    def test_none_when_nothing_fits(self):
        p = problem({"A": "7", "B": "11", "C": "13", "D": "17", "E": "19"}, "C", "Primes.")
        d = self.check(p, "E", "none")
        self.assertEqual(d["evidence"]["candidates"], [])
        self.assertTrue(d["text_ca"] and d["text_en"])


class TiesTest(unittest.TestCase):
    """Two signatures fit: the more specific one wins (the order in copilot/signatures.py)."""

    def test_sum_vs_product_beats_off_by_one(self):
        text = "There are 2 shelves with 3 books each. How many books?"
        p = problem({"A": "4", "B": "5", "C": "6", "D": "7", "E": "8"}, "C", text)
        d = diagnose(p, "B")                            # 5 = 2 + 3 and also 6 - 1
        self.assertEqual(d["signature"], "sum_vs_product")
        self.assertEqual(d["evidence"]["candidates"], ["sum_vs_product", "minus_one"])

    def test_digits_swapped_beats_statement_difference(self):
        text = "Add 9 to the number."
        p = problem({"A": "3", "B": "12", "C": "21", "D": "30", "E": "40"}, "B", text)
        d = diagnose(p, "C")                            # 21 = swap(12) and also 12 + 9
        self.assertEqual(d["signature"], "digits_swapped")
        self.assertIn("missing_subtract", d["evidence"]["candidates"])

    def test_power_of_ten_beats_double_and_statement(self):
        text = "Each of 90 boxes..."
        p = problem({"A": "5", "B": "10", "C": "50", "D": "100", "E": "200"}, "B", text)
        d = diagnose(p, "D")                            # 100 = 10 x 10 and also 10 + 90
        self.assertEqual(d["signature"], "times_10")
        self.assertEqual(d["evidence"]["candidates"], ["times_10", "missing_subtract"])

    def test_double_beats_statement_difference(self):
        text = "8 friends share 4 cakes..."
        p = problem({"A": "2", "B": "4", "C": "8", "D": "12", "E": "16"}, "B", text)
        d = diagnose(p, "C")                            # 8 = 2 x 4, also 4 + 4, and 8 is in the text
        self.assertEqual(d["signature"], "double")
        self.assertEqual(d["evidence"]["candidates"], ["double", "missing_subtract", "statement_number"])

    def test_off_by_one_beats_statement_number(self):
        text = "Pages 4 to 9 of the book."
        p = problem({"A": "4", "B": "5", "C": "6", "D": "7", "E": "9"}, "C", text)
        d = diagnose(p, "B")                            # 5 = 6 - 1; 5 is not in the text
        self.assertEqual(d["signature"], "minus_one")
        d = diagnose(p, "D")                            # 7 = 6 + 1
        self.assertEqual(d["signature"], "plus_one")
        d = diagnose(p, "E")                            # 9: a number of the statement, 3 away from 6 (3 not in text)
        self.assertEqual(d["signature"], "statement_number")


class NeverLeaksTest(unittest.TestCase):
    """No text ever carries the correct value or letter: copilot.leak_filter is the judge."""

    def test_texts_pass_the_leak_filter_on_the_sample_problems(self):
        with open(os.path.join(ROOT, "data", "sample_problems.jsonl"), encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        checked = 0
        for r in rows:
            for letter in "ABCDE":
                d = diagnose(r, letter)
                if d is None:
                    continue
                checked += 1
                self.assertFalse(leaks(d["text_ca"], r["label"], r["options"]), (r["id"], letter, d["text_ca"]))
                self.assertFalse(leaks(d["text_en"], r["label"], r["options"]), (r["id"], letter, d["text_en"]))
                self.assertIn(d["signature"], SIGNATURE_KEYS)
        self.assertGreater(checked, 10)

    def test_a_leaking_text_is_dropped_and_the_next_signature_is_tried(self):
        # Correct value 2: the Catalan "dues vegades" of `double` names it, so `double` is dropped.
        p = problem({"A": "1", "B": "2", "C": "4", "D": "5", "E": "6"}, "B", "Two friends...")
        d = diagnose(p, "C")
        self.assertNotEqual(d["signature"], "double")
        self.assertIn("double", d["evidence"]["dropped_by_leak_filter"])
        self.assertFalse(leaks(d["text_ca"], "B", p["options"]))

    def test_statement_number_equal_to_the_answer_is_dropped(self):
        # The difference 5 is the correct value itself: "el 5 de l'enunciat" would leak it.
        text = "5 children..."
        p = problem({"A": "0", "B": "5", "C": "7", "D": "8", "E": "9"}, "B", text)
        d = diagnose(p, "A")
        self.assertIn("missing_add", d["evidence"]["dropped_by_leak_filter"])
        self.assertFalse(leaks(d["text_ca"], "B", p["options"]))

    def test_evidence_shape(self):
        d = diagnose(problem(FIVE, "C"), "E")
        for key in ("chosen_letter", "chosen_value", "correct_value", "difference", "ratio",
                    "statement_numbers", "candidates", "dropped_by_leak_filter"):
            self.assertIn(key, d["evidence"])
        self.assertEqual(d["evidence"]["chosen_value"], "20")
        self.assertEqual(d["evidence"]["ratio"], "2")
        self.assertEqual(set(d), {"signature", "text_ca", "text_en", "evidence"})


if __name__ == "__main__":
    unittest.main()
