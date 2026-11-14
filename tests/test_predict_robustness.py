"""predict.py writes exactly one row per input line, whatever the line contains.

The organisers' format promises only "id" and "text". A row with options as a list or
a string, a row without an id, a line that is a JSON array, or a line that is not JSON
at all must not end the run: the exam is scored on the rows that exist.
"""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREDICT = os.path.join(ROOT, "predict.py")

# Made-up rows, no M3Kang text. Each tuple: a label and the raw line to write.
ROWS = [
    ("plain", json.dumps({"id": "r1", "text": "Made-up question.", "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}})),
    ("options as list", json.dumps({"id": "r2", "text": "Made-up question.", "options": ["1", "2", "3", "4", "5"]})),
    ("options as string", json.dumps({"id": "r3", "text": "Made-up question.", "options": "A) 1 B) 2 C) 3 D) 4 E) 5"})),
    ("options as ints", json.dumps({"id": "r4", "text": "Made-up question.", "options": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}})),
    ("nested options", json.dumps({"id": "r5", "text": "Made-up question.", "options": {"A": {"text": "1"}, "B": [2]}})),
    ("no id", json.dumps({"text": "Made-up question without an id."})),
    ("null text", json.dumps({"id": "r7", "text": None})),
    ("missing text", json.dumps({"id": "r8"})),
    ("empty object", "{}"),
    ("json array", json.dumps(["r10", "Made-up question."])),
    ("json number", "42"),
    ("not json", "this line is not json at all"),
    ("lowercase keys", json.dumps({"id": "r13", "text": "Made-up question.", "options": {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"}})),
    ("numeric id", json.dumps({"id": 14, "text": "Made-up question.", "language": "cat"})),
    ("ages words, long", json.dumps({"id": "r15", "text": "How old is Ann if her mother is twice her age? " * 40,
                                     "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}})),
]


class PredictRobustness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.inp = os.path.join(cls.tmp, "exam.jsonl")
        cls.out = os.path.join(cls.tmp, "predictions.csv")
        with open(cls.inp, "w") as f:
            for _, line in ROWS:
                f.write(line + "\n")
            f.write("\n")  # a blank line gets no row
        env = dict(os.environ, RUNTIME="sim", LETTER_MODEL="0", SOLVERS="0", PYTHONPATH=ROOT)
        cls.proc = subprocess.run([sys.executable, PREDICT, "--input", cls.inp, "--output", cls.out],
                                  capture_output=True, text=True, env=env, cwd=ROOT, timeout=300)
        with open(cls.out, newline="") as f:
            cls.rows = list(csv.DictReader(f))

    def test_the_run_finishes(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-2000:])

    def test_one_row_per_line(self):
        self.assertEqual(len(self.rows), len(ROWS), self.proc.stderr[-2000:])

    def test_every_row_has_a_letter(self):
        for row in self.rows:
            self.assertIn(row["answer"], list("ABCDE"), row)

    def test_ids_are_kept_or_made(self):
        ids = [row["id"] for row in self.rows]
        self.assertEqual(ids[0], "r1")
        self.assertEqual(ids[13], "14")
        for label, row in zip((label for label, _ in ROWS), self.rows):
            if label in ("no id", "empty object", "json array", "json number", "not json"):
                self.assertTrue(row["id"].startswith("line-"), (label, row))

    def test_bad_lines_are_marked(self):
        by_label = dict(zip((label for label, _ in ROWS), self.rows))
        self.assertTrue(by_label["not json"]["status"].startswith("error:json"))
        self.assertEqual(by_label["json array"]["status"], "error:not-an-object")
        self.assertEqual(by_label["json number"]["status"], "error:not-an-object")

    def test_language_column(self):
        by_label = dict(zip((label for label, _ in ROWS), self.rows))
        self.assertEqual(by_label["numeric id"]["language"], "cat")
        self.assertEqual(by_label["not json"]["language"], "")


if __name__ == "__main__":
    unittest.main()
