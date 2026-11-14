"""The Reason policy (predict.py) stays apart from the Teach modules and always answers a letter."""
import ast
import os
import unittest
import urllib.error
from unittest import mock

from copilot import pipeline, think, votes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEACH_MODULES = ["hints.py", "webapp.py", "trainer.py", "topics.py", "retrieval.py", "leak_filter.py"]
REASON_MODULES = {"ladder", "votes", "bias", "pipeline", "think"}

PROBLEMS = [
    {"id": "p1", "text": "How many apples?", "options": {"A": "10", "B": "12", "C": "13", "D": "14", "E": "15"}},
    {"id": "p2", "text": "Which figure?", "options": {"A": "a square", "B": "a circle", "C": "a cube", "D": "a line", "E": "none"}},
    {"id": "p3", "text": "The options are in the picture.", "options": {}},
    {"id": "p4", "text": "No options key at all."},
    {"id": "p5", "text": "OCR noise", "options": {"A": "1 10", "B": "11", "C": "12", "D": "13", "E": "15"}},
    {"id": "p6", "text": "Duplicates", "options": {"A": "3", "B": "3", "C": "4", "D": "5", "E": "6"}},
    {"id": "p7", "text": "Units", "options": {"A": "48cm", "B": "40 cm", "C": "32cm", "D": "24 cm", "E": "16cm"}},
]


def imported_copilot_modules(path):
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level >= 1:
            if node.module:
                names.add(node.module.split(".")[0])
            else:
                names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("copilot."):
                    names.add(alias.name.split(".")[1])
    return names


class TeachIsolationTest(unittest.TestCase):
    def test_teach_modules_import_nothing_from_the_reason_policy(self):
        for name in TEACH_MODULES:
            path = os.path.join(ROOT, "copilot", name)
            if not os.path.exists(path):
                continue
            leaked = imported_copilot_modules(path) & REASON_MODULES
            self.assertEqual(leaked, set(), f"copilot/{name} imports {sorted(leaked)}: the hint ladder must not depend on the answer policy")


class AlwaysALetterTest(unittest.TestCase):
    def check_all(self, expect_ok=True, **flags):
        patches = [mock.patch.object(pipeline, "USE_SOLVERS", False)]
        patches += [mock.patch.object(pipeline, key, value) for key, value in flags.items()]
        for patch in patches:
            patch.start()
        try:
            for problem in PROBLEMS:
                result = pipeline.solve(problem)
                self.assertIn(result["answer"], "ABCDE", problem["id"])
                if expect_ok:
                    self.assertEqual(result["status"], "ok", problem["id"])
                yield problem, result
        finally:
            for patch in patches:
                patch.stop()

    def test_default_policy_middle_value_then_fallback(self):
        answers = {p["id"]: r for p, r in self.check_all(USE_MIDDLE_VALUE=True, USE_LETTER_MODEL=False)}
        self.assertEqual((answers["p1"]["answer"], answers["p1"]["rule"]), ("C", "middle_value"))
        self.assertEqual((answers["p7"]["answer"], answers["p7"]["rule"]), ("C", "middle_value"))
        for pid in ("p2", "p3", "p4", "p5", "p6"):
            self.assertEqual((answers[pid]["answer"], answers[pid]["rule"]), (pipeline.FALLBACK, ""), pid)

    def test_rule_off_is_the_old_policy(self):
        for problem, result in self.check_all(USE_MIDDLE_VALUE=False, USE_LETTER_MODEL=False):
            self.assertEqual(result["answer"], pipeline.FALLBACK, problem["id"])

    def test_experiments_on_but_no_server_still_answer_a_letter(self):
        # The experiments abstain on problems without five options; on the rest a server that is down
        # (urllib raises URLError) must still end in the fallback letter, as the official run requires.
        def failing_post(url, payload, timeout):
            raise urllib.error.URLError("no server")
        with mock.patch.object(votes, "post", failing_post):
            results = dict((p["id"], (p, r)) for p, r in self.check_all(expect_ok=False, VOTE_SHIFTS=5, USE_VALUE_MODEL=True,
                                          USE_MIDDLE_VALUE=True, USE_LETTER_MODEL=False))
        statuses = {pid: r["status"] for pid, (p, r) in results.items()}
        self.assertTrue(statuses["p1"].startswith("error"))
        self.assertEqual(statuses["p3"], "ok")  # no options: the experiments never ran, D at once


    def test_think_on_but_no_server_still_answers_a_letter(self):
        def failing_post(url, payload, timeout):
            raise urllib.error.URLError("no server")
        with mock.patch.object(think, "post", failing_post):
            results = {p["id"]: r for p, r in self.check_all(THINK_LEVELS=set(range(8)), THINK_TEXT_ONLY=False,
                                                              USE_MIDDLE_VALUE=True, USE_LETTER_MODEL=False)}
        self.assertEqual(results["p1"]["answer"], "C")  # the rule answers after the failed working
        self.assertEqual(results["p3"]["answer"], pipeline.FALLBACK)


class BudgetGuardTest(unittest.TestCase):
    def test_value_skips_a_problem_whose_prompt_would_pass_the_budget(self):
        long_problem = {"text": "word " * 2000, "options": PROBLEMS[0]["options"]}
        calls = []
        with mock.patch.object(votes, "post", lambda url, payload, timeout: calls.append(payload)):
            self.assertEqual(votes.value_letter(long_problem, budget=50.0), (None, "", {}))
        self.assertEqual(calls, [])

    def test_vote_stops_before_a_shift_that_would_pass_the_budget(self):
        calls = []

        def fake_post(url, payload, timeout):
            calls.append(payload)
            # every request costs 44 prompt tokens and one letter: about 4 board seconds
            return {"choices": [{"message": {"content": "A"}}], "timings": {"prompt_n": 44, "predicted_n": 1}}
        with mock.patch.object(votes, "post", fake_post):
            letter, tally, spent = votes.vote_letter(PROBLEMS[0], budget=10.0)
        self.assertIsNone(letter)  # an interrupted vote never elects
        self.assertLess(len(spent), 5)
        self.assertEqual(len(spent), len(calls))
        with mock.patch.object(votes, "post", fake_post):
            letter, tally, spent = votes.vote_letter(PROBLEMS[0], budget=50.0)
        self.assertEqual(len(spent), 5)


if __name__ == "__main__":
    unittest.main()
