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


class PredictResumes(unittest.TestCase):
    """A partial output is continued, not overwritten; --fresh starts over."""

    def run_predict(self, inp, out, *extra):
        env = dict(os.environ, RUNTIME="sim", LETTER_MODEL="0", SOLVERS="0", PYTHONPATH=ROOT)
        return subprocess.run([sys.executable, PREDICT, "--input", inp, "--output", out, *extra],
                              capture_output=True, text=True, env=env, cwd=ROOT, timeout=300)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.inp = os.path.join(self.tmp, "exam.jsonl")
        self.out = os.path.join(self.tmp, "predictions.csv")
        with open(self.inp, "w") as f:
            for i in range(1, 6):
                f.write(json.dumps({"id": f"q{i}", "text": "Made-up question.",
                                    "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}}) + "\n")

    def read(self):
        with open(self.out, newline="") as f:
            return list(csv.DictReader(f))

    def test_resume_appends_only_the_missing_rows(self):
        with open(self.out, "w", newline="") as f:
            f.write("id,language,answer,seconds,status\nq1,,A,0.0,ok\nq2,,B,0.0,ok\n")
        proc = self.run_predict(self.inp, self.out)
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
        self.assertIn("resuming: 2 rows", proc.stderr)
        rows = self.read()
        self.assertEqual([r["id"] for r in rows], ["q1", "q2", "q3", "q4", "q5"])
        self.assertEqual(rows[0]["answer"], "A")   # the kept row is untouched
        self.assertEqual(rows[1]["answer"], "B")

    def test_fresh_starts_over(self):
        with open(self.out, "w", newline="") as f:
            f.write("id,language,answer,seconds,status\nq1,,A,0.0,ok\n")
        proc = self.run_predict(self.inp, self.out, "--fresh")
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
        rows = self.read()
        self.assertEqual(len(rows), 5)
        self.assertNotEqual(rows[0]["answer"], "A")   # q1 answered again by the policy (C, the middle value)

    def test_foreign_file_is_replaced(self):
        with open(self.out, "w") as f:
            f.write("not,a,predictions,file\n")
        proc = self.run_predict(self.inp, self.out)
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
        self.assertEqual(len(self.read()), 5)

    def test_complete_file_adds_nothing(self):
        self.run_predict(self.inp, self.out)
        before = self.read()
        proc = self.run_predict(self.inp, self.out)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self.read(), before)


class SameIdTwoLanguages(unittest.TestCase):
    """The bank holds every problem once per language with the same id: both rows are written, and a resume keeps both."""

    def test_both_languages_get_a_row(self):
        tmp = tempfile.mkdtemp()
        inp, out = os.path.join(tmp, "exam.jsonl"), os.path.join(tmp, "p.csv")
        with open(inp, "w") as f:
            for lang in ("eng", "cat"):
                f.write(json.dumps({"id": "same", "language": lang, "text": "Made-up.",
                                    "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}}) + "\n")
        env = dict(os.environ, RUNTIME="sim", LETTER_MODEL="0", SOLVERS="0", PYTHONPATH=ROOT)
        subprocess.run([sys.executable, PREDICT, "--input", inp, "--output", out], capture_output=True, text=True, env=env, cwd=ROOT, timeout=300)
        with open(out, newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([(r["id"], r["language"]) for r in rows], [("same", "eng"), ("same", "cat")])
        proc = subprocess.run([sys.executable, PREDICT, "--input", inp, "--output", out], capture_output=True, text=True, env=env, cwd=ROOT, timeout=300)
        self.assertIn("resuming: 2 rows", proc.stderr)
        with open(out, newline="") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 2)
