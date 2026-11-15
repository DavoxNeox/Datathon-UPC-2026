"""Program-aided reasoning (copilot/pal.py): the sandbox, the matching, the budget and the pipeline hook."""
import math
import time
import unittest
import urllib.error
from fractions import Fraction
from unittest import mock

from copilot import client, pal, pipeline

OPTIONS = {"A": "8", "B": "9", "C": "10", "D": "12", "E": "14"}
PROBLEM = {"id": "p1", "text": "Anna has 3 bags with 4 apples each and eats 2. How many are left?",
           "options": OPTIONS, "level": 0, "text_only": True, "language": "eng"}


class SandboxTest(unittest.TestCase):
    def run_ok(self, code):
        answer, status, _ = pal.run_program(code)
        self.assertEqual(status, "ok", code)
        return answer

    def test_plain_programs_run(self):
        self.assertEqual(self.run_ok("bags = 3\nanswer = bags * 4 - 2"), 10)
        self.assertEqual(self.run_ok("c = 0\nfor n in range(10, 100):\n    if n // 10 + n % 10 == 5:\n        c += 1\nanswer = c"), 5)
        self.assertEqual(self.run_ok("def f(x):\n    return x * x\nanswer = sum(f(i) for i in range(1, 4))"), 14)
        self.assertEqual(self.run_ok("import math\nanswer = math.sqrt(16) + math.gcd(4, 6)"), 6.0)
        self.assertEqual(self.run_ok("from math import comb as c\nanswer = c(5, 2)"), 10)
        self.assertEqual(self.run_ok("answer = 7 ** 2026 % 10"), 9)
        self.assertEqual(self.run_ok("t = 0\nfor _ in range(3):\n    t += 2\nanswer = t"), 6)
        self.assertEqual(self.run_ok("d = [0] * 3\nd[1] += 5\nanswer = d[1]"), 5)

    def test_malicious_code_is_rejected(self):
        for code in ["import os\nanswer = 1", "from os import system\nanswer = 1", "import math, os\nanswer = 1",
                     "from math import *\nanswer = 1", "answer = ().__class__.__bases__",
                     "answer = __import__('os')", "answer = (x for x in [1]).gi_frame.f_back",
                     "def f():\n    pass\nanswer = f.__globals__", "try:\n    x = 1\nexcept:\n    pass\nanswer = 1",
                     "with x:\n    pass", "class A:\n    pass", "global q\nanswer = 1"]:
            answer, status, _ = pal.run_program(code)
            self.assertIsNone(answer, code)
            self.assertTrue(status.startswith("rejected"), (code, status))

    def test_missing_builtins_raise_inside_and_are_caught(self):
        for code in ["open('/etc/passwd')\nanswer = 1", "eval('1')\nanswer = 1", "exec('x=1')\nanswer = 1",
                     "answer = getattr(1, 'real')", "answer = type(1)", "answer = globals()", "answer = vars()"]:
            answer, status, _ = pal.run_program(code)
            self.assertIsNone(answer, code)
            self.assertEqual(status, "error: NameError", code)

    def test_exceptions_are_captured(self):
        self.assertEqual(pal.run_program("answer = 1 / 0")[1], "error: ZeroDivisionError")
        self.assertEqual(pal.run_program("def f(n):\n    return f(n + 1)\nanswer = f(0)")[1], "error: RecursionError")
        self.assertEqual(pal.run_program("answer = [1][5]")[1], "error: IndexError")
        self.assertEqual(pal.run_program("answer = (")[1], "syntax")
        self.assertEqual(pal.run_program("x = 3")[1], "no_answer")

    def test_infinite_loops_are_cut(self):
        start = time.perf_counter()
        self.assertIn(pal.run_program("while True:\n    pass")[1], ("lines", "timeout"))
        self.assertIn(pal.run_program("s = 0\nfor i in range(10**6):\n    for j in range(10**6):\n        s += 1\nanswer = s")[1],
                      ("lines", "timeout"))
        self.assertIn(pal.run_program("answer = sum(i * j for i in range(10**6) for j in range(10**6))")[1], ("lines", "timeout"))
        self.assertEqual(pal.run_program("while True:\n    pass", seconds=0.2, max_lines=10**9)[1], "timeout")
        self.assertLess(time.perf_counter() - start, 4 * (pal.EXEC_SECONDS + 0.5))

    def test_size_caps(self):
        for code in ["answer = 10 ** 10 ** 8", "answer = math.factorial(10 ** 8)", "answer = 'a' * 10 ** 9",
                     "answer = list(range(10 ** 9))", "answer = 1 << 10 ** 9", "answer = math.prod(range(1, 10 ** 6))"]:
            self.assertEqual(pal.run_program(code)[1], "error: ValueError", code)
        self.assertEqual(pal.run_program("x = [1]\nfor i in range(40):\n    x.extend(x)\nanswer = len(x)")[1], "memory")
        self.assertEqual(pal.run_program("x = 2\nfor i in range(40):\n    x = x * x\nanswer = x")[1], "error: ValueError")


class ModulesAndOutputsTest(unittest.TestCase):
    def test_itertools_and_fractions_are_there_and_bounded(self):
        self.assertEqual(pal.run_program("import itertools\nanswer = len(list(itertools.permutations(range(5))))")[0], 120)
        self.assertEqual(pal.run_program("import itertools as it\nanswer = sum(1 for t in it.product(range(3), repeat=3) if sum(t) == 3)")[0], 7)
        self.assertEqual(pal.run_program("from fractions import Fraction\nanswer = Fraction(1, 3) + Fraction(1, 6)")[0], Fraction(1, 2))
        self.assertEqual(pal.run_program("from itertools import permutations\nanswer = len(list(permutations(range(12))))")[1], "error: ValueError")
        self.assertEqual(pal.run_program("import itertools\nanswer = list(itertools.count())")[1], "error: AttributeError")  # no infinite iterators
        self.assertEqual(pal.run_program("from itertools import cycle\nanswer = 1")[1], "rejected: ImportFrom")
        self.assertEqual(pal.run_program("from fractions import Fraction\nanswer = Fraction(1, 3) ** 10 ** 7")[1], "error: ValueError")
        self.assertEqual(pal.run_program("import fractions, os\nanswer = 1")[1], "rejected: Import")

    def test_last_print_stands_in_for_answer(self):
        self.assertEqual(pal.run_program("print(41)\nprint(42)"), (42, "ok_print", mock.ANY))
        self.assertEqual(pal.run_program("print(41)\nanswer = 7")[:2], (7, "ok"))

    def test_a_collection_counts_only_for_how_many(self):
        self.assertEqual(pal.collection_answer([1, 2, 3], "Ann has cards. How many ways are there?"), (3, "len"))
        self.assertEqual(pal.collection_answer({4, 5}, "Quants nombres hi ha?"), (2, "len"))
        self.assertEqual(pal.collection_answer([1, 2], "What is the smallest number?"), (None, "collection"))
        self.assertEqual(pal.collection_answer(5, "What is it?"), (5, ""))


class MatchTest(unittest.TestCase):
    def test_exact_integer_float_and_fraction(self):
        self.assertEqual(pal.match_answer(10, OPTIONS), ("C", "exact"))
        self.assertEqual(pal.match_answer(10.0000000001, OPTIONS), ("C", "exact"))
        self.assertEqual(pal.match_answer(Fraction(24, 2), OPTIONS), ("D", "exact"))
        self.assertEqual(pal.match_answer("12", OPTIONS), ("D", "exact"))
        fractions = {"A": "1/10", "B": "3/20", "C": "1/5", "D": "1/4", "E": "1/2"}
        self.assertEqual(pal.match_answer(0.25, fractions), ("D", "exact"))
        self.assertEqual(pal.match_answer(3 / 20, fractions), ("B", "exact"))

    def test_units_and_percentages(self):
        self.assertEqual(pal.match_answer(105, {"A": "75°", "B": "100°", "C": "105°", "D": "115 °", "E": "120°"}), ("C", "exact"))
        self.assertEqual(pal.match_answer(12, {"A": "9 km", "B": "11 km", "C": "12km", "D": "13km", "E": "14km"}), ("C", "exact"))
        percent = {"A": "10%", "B": "20%", "C": "25%", "D": "30%", "E": "50%"}
        self.assertEqual(pal.match_answer(25, percent), ("C", "exact"))
        self.assertEqual(pal.match_answer(0.25, percent), ("C", "exact"))

    def test_nearest_only_within_one_percent_and_unique(self):
        self.assertEqual(pal.match_answer(10.05, OPTIONS), ("C", "near"))
        self.assertEqual(pal.match_answer(10.5, OPTIONS), (None, "no_match"))
        close = {"A": "100", "B": "100.5", "C": "300", "D": "400", "E": "500"}
        self.assertEqual(pal.match_answer(100.2, close), (None, "several_near"))
        self.assertEqual(pal.match_answer(0.001, {"A": "0", "B": "1", "C": "2", "D": "3", "E": "4"}), (None, "no_match"))

    def test_abstentions(self):
        self.assertEqual(pal.match_answer(None, OPTIONS)[0], None)
        self.assertEqual(pal.match_answer(True, OPTIONS)[0], None)
        self.assertEqual(pal.match_answer([10], OPTIONS)[0], None)
        self.assertEqual(pal.match_answer(float("nan"), OPTIONS)[0], None)
        self.assertEqual(pal.match_answer(float("inf"), OPTIONS)[0], None)
        self.assertEqual(pal.match_answer(10 ** 400, OPTIONS), (None, "not_a_number"))  # too large for a float
        self.assertEqual(pal.match_answer(5, {"A": "5", "B": "5", "C": "6", "D": "7", "E": "8"}), (None, "several_exact"))
        words = {"A": "red", "B": "blue", "C": "2√3", "D": "1 10", "E": "green"}
        self.assertEqual(pal.match_answer(2, words), (None, "no_numeric_option"))  # "2√3" is not the number 2

    def test_applies_needs_text_and_three_numeric_options(self):
        self.assertTrue(pal.applies(PROBLEM))
        self.assertFalse(pal.applies(dict(PROBLEM, text_only=False), text_only=True))  # a figure goes to think
        self.assertTrue(pal.applies(dict(PROBLEM, text_only=False), text_only=False))
        self.assertFalse(pal.applies(dict(PROBLEM, text="")))
        self.assertFalse(pal.applies(dict(PROBLEM, options={"A": "red", "B": "blue", "C": "1", "D": "2", "E": "x"})))
        self.assertFalse(pal.applies(dict(PROBLEM, options={"A": "1", "B": "2", "C": "3"})))


class ExtractTest(unittest.TestCase):
    def test_fenced_block_and_cut_block(self):
        self.assertEqual(pal.extract_code("Here:\n```python\nanswer = 1\n```\nDone."), "answer = 1\n")
        self.assertEqual(pal.extract_code("```\nanswer = 2\n```"), "answer = 2\n")
        self.assertIsNone(pal.extract_code("```python\nx = 1\nfor i in", finished=False))
        self.assertEqual(pal.extract_code("answer = 3"), "answer = 3")
        self.assertIsNone(pal.extract_code("The answer is C."))


def fake_server(content, finish="stop", prompt_n=90):
    def post(url, payload, timeout):
        if url.endswith("/tokenize"):
            return {"tokens": list(range(50))}
        post.calls.append(payload)
        client.remember(url, payload)
        return {"choices": [{"message": {"content": content}, "finish_reason": finish}],
                "timings": {"prompt_n": prompt_n, "predicted_n": 30}}
    post.calls = []
    return post


class StageTest(unittest.TestCase):
    def setUp(self):
        pal._STATE.update(prefix_tokens=None)
        client.LAST_CHAT.clear()

    def test_letter_from_a_program_and_the_stable_block_first(self):
        server = fake_server("```python\nanswer = 3 * 4 - 2\n```")
        with mock.patch.object(pal, "post", server):
            letter, info, timings = pal.pal_letter(PROBLEM, budget=45)
        self.assertEqual((letter, info["how"], info["answer"]), ("C", "exact", 10))
        messages = server.calls[0]["messages"]
        self.assertEqual(messages[:-1], pal.stable_messages())  # stable text in earlier messages: cached between problems
        self.assertIn(PROBLEM["text"], messages[-1]["content"])
        self.assertEqual(server.calls[0]["temperature"], 0)
        self.assertTrue(info["cold"])
        with mock.patch.object(pal, "post", server):
            _, info, _ = pal.pal_letter(PROBLEM, budget=45)
        self.assertFalse(info["cold"])  # the previous request was this stage's

    def test_budget_counts_the_block_when_cold_and_skips_when_nothing_fits(self):
        server = fake_server("```python\nanswer = 10\n```")
        with mock.patch.object(pal, "post", server):
            _, cold, _ = pal.pal_letter(PROBLEM, budget=45)
            _, warm, _ = pal.pal_letter(PROBLEM, budget=45)
            letter, skipped, timings = pal.pal_letter(PROBLEM, budget=10)
        self.assertGreater(warm["n_predict"], cold["n_predict"])
        self.assertEqual((letter, skipped["skipped"], timings), (None, "budget", {}))
        self.assertEqual(len(server.calls), 2)

    def test_another_chat_request_in_between_makes_it_cold(self):
        server = fake_server("```python\nanswer = 10\n```")
        with mock.patch.object(pal, "post", server):
            pal.pal_letter(PROBLEM, budget=45)
            self.assertTrue(pal.prefix_cached(pal.URL))
            client.remember(pal.URL, {"messages": [{"role": "system", "content": "think"}, {"role": "user", "content": "x"}]})
            _, info, _ = pal.pal_letter(PROBLEM, budget=45)
        self.assertTrue(info["cold"])
        client.remember(pal.URL, {"messages": pal.build_messages(PROBLEM)}, done=False)  # sent, never answered
        self.assertFalse(pal.prefix_cached(pal.URL))
        client.remember(pal.URL.replace("/v1/chat/completions", "/tokenize"), {"content": "x"})  # no generation
        client.remember(pal.URL, {"messages": pal.build_messages(PROBLEM)})
        client.remember(pal.URL.replace("/v1/chat/completions", "/tokenize"), {"content": "x"})
        self.assertTrue(pal.prefix_cached(pal.URL))

    def test_a_bug_inside_the_stage_abstains(self):
        with mock.patch.object(pal, "pal_letter", side_effect=OverflowError("boom")):
            letter, info, _ = pal.stage(PROBLEM, timeout=5, url=pal.URL, budget=45, cold=False)
        self.assertIsNone(letter)
        self.assertTrue(info["skipped"].startswith("bug: OverflowError"))

    def test_server_error_abstains(self):
        def down(url, payload, timeout):
            raise urllib.error.URLError("connection refused")
        with mock.patch.object(pal, "post", down):
            letter, info, timings = pal.stage(PROBLEM, timeout=5, url=pal.URL, budget=45, cold=False)
        self.assertIsNone(letter)
        self.assertTrue(info["skipped"].startswith("error"))


class PipelineHookTest(unittest.TestCase):
    def setUp(self):
        pal._STATE.update(prefix_tokens=None)
        client.LAST_CHAT.clear()

    def solve(self, content, **flags):
        server = fake_server(content, prompt_n=200)
        patches = [mock.patch.object(pipeline, "USE_PAL", True), mock.patch.object(pipeline, "USE_SOLVERS", False),
                   mock.patch.object(pipeline, "THINK_LEVELS", {0}), mock.patch.object(pal, "post", server)]
        think_calls = []

        def fake_think(problem, timeout, url, budget, cold):
            think_calls.append(budget)
            return None, {"skipped": "budget"}, {}
        patches.append(mock.patch.object(pipeline.think, "think_letter", fake_think))
        for p in patches:
            p.start()
        try:
            result = pipeline.solve(dict(PROBLEM))
        finally:
            for p in patches:
                p.stop()
        return result, think_calls

    def test_pal_answers_with_rule_pal(self):
        result, think_calls = self.solve("```python\nanswer = 12\n```")
        self.assertEqual((result["answer"], result["rule"]), ("D", "pal"))
        self.assertEqual(think_calls, [])

    def test_abstention_falls_to_think_with_what_is_left(self):
        result, think_calls = self.solve("```python\nanswer = 1 / 0\n```")
        self.assertEqual(result["extra"]["pal"]["run"], "error: ZeroDivisionError")
        self.assertEqual(len(think_calls), 1)
        spent = 200 / pal.board_clock.PREFILL_TPS + 30 / pal.board_clock.GEN_TPS
        self.assertAlmostEqual(think_calls[0], pipeline.think.BUDGET - spent, places=2)
        self.assertEqual(result["rule"], "middle_value")


if __name__ == "__main__":
    unittest.main()


CAT = {"id": "c1", "text": "La Marta té 3 bosses amb 4 pomes cadascuna i se'n menja 2. Quantes en queden?",
       "options": OPTIONS, "level": 0, "text_only": True, "language": "cat"}
ENGLISH = "Marta has 3 bags with 4 apples each and eats 2. How many are left?"


def two_step_server(translation, program, finish="stop"):
    """First chat request: the translation; second: the program. Both see the same stable block."""
    def post(url, payload, timeout):
        if url.endswith("/tokenize"):
            return {"tokens": list(range(30))}
        post.calls.append(payload)
        client.remember(url, payload)
        last = payload["messages"][-1]["content"]
        content = translation if last.startswith(pal.TRANSLATE_HEADER) else program
        return {"choices": [{"message": {"content": content}, "finish_reason": finish}],
                "timings": {"prompt_n": 40, "predicted_n": 25}}
    post.calls = []
    return post


class TranslateTest(unittest.TestCase):
    def setUp(self):
        pal._STATE.update(prefix_tokens=None)
        client.LAST_CHAT.clear()
        client.remember(pal.URL, {"messages": pal.stable_messages(True) + [{"role": "user", "content": "x"}]})  # warm

    def patch(self, server):
        return [mock.patch.object(pal, "post", server), mock.patch.object(pal, "TRANSLATE", True)]

    def run_stage(self, problem, server, budget=50):
        patches = self.patch(server)
        for p in patches:
            p.start()
        try:
            return pal.stage(problem, timeout=30, url=pal.URL, budget=budget, cold=False)
        finally:
            for p in patches:
                p.stop()

    def test_looks_english(self):
        self.assertTrue(pal.looks_english(ENGLISH))
        self.assertFalse(pal.looks_english(CAT["text"]))
        self.assertFalse(pal.looks_english("Un reloj muestra las horas. ¿Cuántas veces al día muestra el número?"))

    def test_numbers_kept(self):
        self.assertTrue(pal.numbers_kept(CAT["text"], ENGLISH))
        self.assertFalse(pal.numbers_kept(CAT["text"], "Marta has bags with 4 apples and eats 2."))
        self.assertTrue(pal.numbers_kept("Fa 2,5 km i 1.000 passes", "It is 2.5 km and 1,000 steps"))
        self.assertFalse(pal.numbers_kept("3 i 3", "3 and three"))

    def test_catalan_is_translated_then_solved_on_the_shared_block(self):
        server = two_step_server("Translation: " + ENGLISH, "```python\nanswer = 3 * 4 - 2\n```")
        letter, info, timings = self.run_stage(CAT, server)
        self.assertEqual(letter, "C")
        self.assertEqual(len(server.calls), 2)
        first, second = server.calls
        self.assertTrue(first["messages"][-1]["content"].startswith(pal.TRANSLATE_HEADER))
        self.assertEqual(first["messages"][:-1], second["messages"][:-1])  # same cached prefix for both requests
        self.assertIn(ENGLISH, second["messages"][-1]["content"])             # the program is written from the English
        self.assertTrue(info["translate"]["numbers_kept"])
        self.assertFalse(info["cold"])
        self.assertEqual(timings, {"prompt_n": 80, "predicted_n": 50})
        self.assertLessEqual(first["max_tokens"], math.ceil(1.4 * 30))

    def test_english_problem_is_not_translated(self):
        server = two_step_server("unused", "```python\nanswer = 10\n```")
        letter, info, _ = self.run_stage(PROBLEM, server)
        self.assertEqual((letter, len(server.calls)), ("C", 1))
        self.assertNotIn("translate", info)
        self.assertFalse(server.calls[0]["messages"][-1]["content"].startswith(pal.TRANSLATE_HEADER))

    def test_lost_number_cut_output_or_no_budget_abstain_before_the_program(self):
        for translation, finish, budget, why in [("Marta has bags with 4 apples and eats 2.", "stop", 50, "numbers"),
                                                 (ENGLISH, "length", 50, "cut"), (ENGLISH, "stop", 8, "budget"),
                                                 (CAT["text"], "stop", 50, "not_english")]:
            server = two_step_server(translation, "```python\nanswer = 10\n```", finish=finish)
            letter, info, _ = self.run_stage(CAT, server, budget=budget)
            self.assertIsNone(letter, why)
            self.assertEqual(info["skipped"], "translate: " + why)
            self.assertLessEqual(len(server.calls), 1)

    def test_budget_for_and_languages(self):
        with mock.patch.object(pal, "TRANSLATE", True):
            self.assertEqual(pal.budget_for(CAT), pal.TRANSLATE_BUDGET)
            self.assertEqual(pal.budget_for(PROBLEM), pal.BUDGET)
        with mock.patch.object(pal, "TRANSLATE", False):
            self.assertEqual(pal.budget_for(CAT), pal.BUDGET)
        with mock.patch.object(pal, "LANGUAGES", {"eng"}):
            self.assertTrue(pal.applies(PROBLEM))
            self.assertFalse(pal.applies(CAT))
