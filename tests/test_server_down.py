"""With the model server off (RUNTIME=sim, a closed port), every stage follows the normal order and says so.

The checks run in a subprocess so that copilot.config reads LLM_PORT from the environment at import.
Port 9 (discard) is closed on a development machine: every request fails at once with a URLError.
"""
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBLEMS = {
    # K2: no text. The think stage must not send a request on the options alone; the middle value answers.
    "empty_text": {"id": "k2", "text": "", "level": 3, "text_only": True,
                   "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}},
    "null_text": {"id": "k2b", "text": None, "level": 3, "text_only": True,
                  "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"}},
    # K4: a family solver classifies it; the server is down; the normal order (middle value) must answer.
    "consecutive": {"id": "k4", "text": "The sum of five consecutive whole numbers is 105. What is the largest?",
                    "level": 4, "text_only": True, "options": {"A": "19", "B": "21", "C": "23", "D": "25", "E": "27"}},
    # the ages family's hint alone costs about 44 estimated seconds: SOLVER_BUDGET_SECONDS skips it before any request
    "ages": {"id": "k4c", "text": "The ages of a family of five add up to 80 years. What was the sum 7 years ago?",
             "level": 4, "text_only": True, "options": {"A": "45", "B": "52", "C": "60", "D": "66", "E": "73"}},
    # K3: the solver is skipped by the budget and the fallback letter keeps the status that says so.
    "long_ages": {"id": "k3", "text": ("The ages of the five people in a family add up to 80 years. " * 55).strip(),
                  "level": 4, "text_only": True, "options": {"A": "cat", "B": "dog", "C": "cow", "D": "hen", "E": "pig"}},
    # a think problem with the server down: the working never arrives, the middle value answers
    "think": {"id": "k4b", "text": "Anna has 3 bags with 4 apples each and eats 2. How many are left?",
              "level": 3, "text_only": True, "options": {"A": "8", "B": "9", "C": "10", "D": "12", "E": "14"}},
}
SCRIPT = """
import json, sys
from copilot import pipeline
problems = json.loads(sys.stdin.read())
out = {}
for key, problem in problems.items():
    r = pipeline.solve(problem)
    out[key] = {"answer": r["answer"], "status": r["status"], "rule": r["rule"], "seconds": r["seconds"],
                "think": r["extra"].get("think")}
print(json.dumps(out))
"""


class ServerDownTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env = {**os.environ, "RUNTIME": "sim", "LLM_PORT": "9", "LLM_HOST": "127.0.0.1", "SOLVERS": "1",
               "THINK_LEVELS": "all", "THINK_TEXT_ONLY": "0", "LETTER_MODEL": "0", "MIDDLE_VALUE": "1"}
        proc = subprocess.run([sys.executable, "-c", SCRIPT], input=json.dumps(PROBLEMS), cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=120)
        assert proc.returncode == 0, proc.stderr[-2000:]
        cls.results = json.loads(proc.stdout)

    def test_every_problem_gets_a_letter_quickly(self):
        for key, r in self.results.items():
            self.assertIn(r["answer"], list("ABCDE"), key)
            self.assertLess(r["seconds"], 5.0, key)

    def test_k2_no_request_without_a_text(self):
        for key in ("empty_text", "null_text"):
            r = self.results[key]
            self.assertIsNone(r["think"], key)  # the stage never ran: no request on nothing
            self.assertEqual((r["answer"], r["rule"], r["status"]), ("C", "middle_value", "ok"), key)

    def test_k4_server_down_on_a_solver_problem_follows_the_normal_order(self):
        r = self.results["consecutive"]
        self.assertEqual((r["answer"], r["rule"]), ("C", "middle_value"))  # 23 is the middle value, not D
        self.assertTrue(r["status"].startswith("ok (solver skipped: error"), r["status"])
        r = self.results["ages"]
        self.assertEqual((r["answer"], r["rule"], r["status"]), ("C", "middle_value", "ok (solver skipped: budget)"))
        r = self.results["think"]
        self.assertEqual((r["answer"], r["rule"], r["status"]), ("C", "middle_value", "ok"))
        self.assertTrue(r["think"]["skipped"].startswith("error"), r["think"])

    def test_k3_the_skip_note_survives_the_fallback_letter(self):
        r = self.results["long_ages"]
        self.assertEqual((r["answer"], r["rule"]), ("D", ""))  # words as options: the fallback letter
        self.assertEqual(r["status"], "ok (solver skipped: budget)")


if __name__ == "__main__":
    unittest.main()
