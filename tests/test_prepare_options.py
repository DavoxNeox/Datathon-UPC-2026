"""The option parser of laptop/prepare_m3kang.py on made-up OCR boxes (no M3Kang data).

A box is [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], text, score. The helpers below lay texts
on one or two rows so reading_order sees them as the OCR would.
"""
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("prepare_m3kang", os.path.join(ROOT, "laptop", "prepare_m3kang.py"))
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


def row(texts, y=100, x0=10, step=60, h=14):
    boxes = []
    for i, text in enumerate(texts):
        x = x0 + i * step
        boxes.append([[[x, y], [x + 40, y], [x + 40, y + h], [x, y + h]], text, 0.9])
    return boxes


class Markers(unittest.TestCase):
    def test_plain_and_parenthesised(self):
        self.assertEqual(prep.is_marker("A) 12", "A", strict=True), "12")
        self.assertEqual(prep.is_marker("(A) 12", "A", strict=True), "12")
        self.assertEqual(prep.is_marker("a) 12", "A", strict=True), "12")
        self.assertEqual(prep.is_marker("A: 12", "A", strict=True), "12")

    def test_lower_case_needs_the_parenthesis(self):
        self.assertIsNone(prep.is_marker("a 12", "A", strict=False))
        self.assertIsNone(prep.is_marker("ada", "A", strict=False))

    def test_lax_only_without_strict(self):
        self.assertIsNone(prep.is_marker("E16", "E", strict=True))
        self.assertEqual(prep.is_marker("E16", "E", strict=False), "16")
        self.assertEqual(prep.is_marker("C", "C", strict=False), "")


class ParseOptions(unittest.TestCase):
    def test_five_markers_one_row(self):
        boxes = row(["Question text here"], y=20) + row(["A) 1", "B) 2", "C) 3", "D) 4", "E) 5"])
        self.assertEqual(prep.parse_options(boxes), {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"})

    def test_parenthesised_and_lower_case_markers(self):
        boxes = row(["(A) 10", "(B) 11", "(C) 12", "(D) 13", "(E) 14"])
        self.assertEqual(prep.parse_options(boxes)["E"], "14")
        boxes = row(["a) 10", "b) 11", "c) 12", "d) 13", "e) 14"])
        self.assertEqual(prep.parse_options(boxes)["A"], "10")

    def test_value_in_its_own_box(self):
        boxes = row(["A)", "7", "B)", "8", "C)", "9", "D)", "10", "E)", "11"], step=30)
        self.assertEqual(prep.parse_options(boxes), {"A": "7", "B": "8", "C": "9", "D": "10", "E": "11"})

    def test_missing_a_marker_is_inferred_from_the_box_before_b(self):
        boxes = row(["Some statement"], y=20) + row(["12", "B) 15", "C) 18", "D) 20", "E) 24"])
        self.assertEqual(prep.parse_options(boxes), {"A": "12", "B": "15", "C": "18", "D": "20", "E": "24"})

    def test_missing_a_is_not_a_word(self):
        boxes = row(["therefore", "B) 15", "C) 18", "D) 20", "E) 24"])
        self.assertEqual(prep.parse_options(boxes), {})

    def test_lost_e_marker_taken_from_the_second_box_after_d(self):
        boxes = row(["A) 1", "B) 2", "C) 3", "D) 4", "5"])
        self.assertEqual(prep.parse_options(boxes), {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"})

    def test_lost_middle_marker(self):
        boxes = row(["A) 1", "B) 2", "3", "D) 4", "E) 5"])
        self.assertEqual(prep.parse_options(boxes), {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"})

    def test_four_markers_and_nothing_else_is_not_enough(self):
        boxes = row(["A) 1", "B) 2", "C) 3", "D) 4"])
        self.assertEqual(prep.parse_options(boxes), {})

    def test_pictures_as_options_give_nothing(self):
        boxes = row(["A)", "B)", "C)", "D)", "E)"])
        self.assertEqual(prep.parse_options(boxes), {})

    def test_last_sequence_wins(self):
        boxes = row(["A) old", "B) old", "C) old", "D) old", "E) old"], y=20) + row(["A) 1", "B) 2", "C) 3", "D) 4", "E) 5"])
        self.assertEqual(prep.parse_options(boxes)["A"], "1")


class Vote(unittest.TestCase):
    def test_language_neutral(self):
        self.assertTrue(prep.language_neutral({"A": "12", "B": "3/4", "C": "5 cm", "D": "7 cm²", "E": "100%"}))
        self.assertFalse(prep.language_neutral({"A": "Monday", "B": "2", "C": "3", "D": "4", "E": "5"}))
        self.assertFalse(prep.language_neutral({"A": "dilluns", "B": "2", "C": "3", "D": "4", "E": "5"}))

    def test_missing_language_takes_the_other(self):
        five = {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}
        rows = [{"id": "p1", "language": "eng", "options": dict(five)}, {"id": "p1", "language": "cat", "options": {}}]
        self.assertEqual(prep.vote_options(rows), 1)
        self.assertEqual(rows[1]["options"], five)
        self.assertEqual(rows[1]["options_source"], "vote")

    def test_words_are_not_copied(self):
        rows = [{"id": "p1", "language": "eng", "options": {"A": "Monday", "B": "2", "C": "3", "D": "4", "E": "5"}},
                {"id": "p1", "language": "cat", "options": {}}]
        self.assertEqual(prep.vote_options(rows), 0)
        self.assertEqual(rows[1]["options"], {})

    def test_majority_corrects_a_noisy_reading(self):
        good = {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}
        noisy = {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5 =一"}
        rows = [{"id": "p1", "language": "eng", "options": dict(good)}, {"id": "p1", "language": "esp", "options": dict(good)},
                {"id": "p1", "language": "cat", "options": dict(noisy)}]
        self.assertEqual(prep.vote_options(rows), 1)
        self.assertEqual(rows[2]["options"], good)

    def test_no_full_reading_changes_nothing(self):
        rows = [{"id": "p1", "language": "eng", "options": {}}, {"id": "p1", "language": "cat", "options": {}}]
        self.assertEqual(prep.vote_options(rows), 0)


if __name__ == "__main__":
    unittest.main()
