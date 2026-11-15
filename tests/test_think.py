"""Brief reasoning by the model (copilot/think.py): budget, parsing, and how the pipeline falls back."""
import unittest
import urllib.error
from unittest import mock

from copilot import board_clock, pipeline, think

OPTIONS = {"A": "8", "B": "9", "C": "10", "D": "12", "E": "14"}
PROBLEM = {"id": "t1", "text": "Anna has 3 bags with 4 apples each and eats 2. How many are left?",
           "options": OPTIONS, "level": 0, "text_only": True, "language": "eng"}


def fake_server(content, finish="stop", prompt_n=120):
    def post(url, payload, timeout):
        if url.endswith("/tokenize"):
            return {"tokens": list(range(100))}
        post.calls.append(payload)
        return {"choices": [{"message": {"content": content}, "finish_reason": finish}],
                "timings": {"prompt_n": prompt_n, "predicted_n": min(payload["max_tokens"], 60)}}
    post.calls = []
    return post


class ParseTest(unittest.TestCase):
    def test_answer_line_wins_and_is_the_last_one(self):
        self.assertEqual(think.parse_letter("Maybe A.\nAnswer: B\nAnswer: C", OPTIONS), ("C", "answer_line"))
        self.assertEqual(think.parse_letter("The correct answer is **(D)** 12.", OPTIONS)[0], "D")
        self.assertEqual(think.parse_letter("so the answer is E) 14", OPTIONS)[0], "E")

    def test_bold_paren_and_value_fallbacks(self):
        self.assertEqual(think.parse_letter("Thus **D) 12 apples**.", OPTIONS), ("D", "bold"))
        self.assertEqual(think.parse_letter("12 - 2 = 10.\nThat is option C) 10.", OPTIONS), ("C", "paren"))
        self.assertEqual(think.parse_letter("Total = 12 - 2 = 10 apples.", OPTIONS), ("C", "value"))
        self.assertEqual(think.parse_letter("Total = 12 - 2 = 10 apples.", {"A": "cat", "B": "dog", "C": "10", "D": "x", "E": "y"}), (None, ""))
        self.assertEqual(think.parse_letter("Options: A) 8 and B) 9 both appear, so 100.", OPTIONS), (None, ""))  # two letters, no value
        self.assertEqual(think.parse_letter("", OPTIONS), (None, ""))

    def test_a_cut_off_working_only_counts_an_explicit_answer_line(self):
        self.assertEqual(think.parse_letter("If a = 6 then b = 4.\nIf a = 7", OPTIONS, finished=False), (None, ""))
        self.assertEqual(think.parse_letter("Comparing to the options: A) 16", OPTIONS, finished=False), (None, ""))
        self.assertEqual(think.parse_letter("Answer: B\nChecking once more: 3 x", OPTIONS, finished=False), ("B", "answer_line"))


class BudgetTest(unittest.TestCase):
    def test_prompt_plus_output_never_passes_the_budget(self):
        for prompt in (50, 130, 200, 300, 450):
            for cold in (False, True):
                n = think.output_budget(prompt, 50.0, cold=cold)
                read = prompt + think.TEMPLATE_TOKENS + (think.SYSTEM_TOKENS if cold else 0)
                self.assertLessEqual(board_clock.estimate_tokens(read, n), 50.0, (prompt, cold))
                self.assertLessEqual(n, think.MAX_TOKENS)
        self.assertEqual(think.output_budget(130, 50.0), think.MAX_TOKENS)  # a normal problem keeps the full cap
        self.assertEqual(think.output_budget(600, 50.0), 0)

    def test_too_little_output_left_means_no_request(self):
        post = fake_server("Answer: C")
        with mock.patch.object(think, "post", post):
            letter, info, timings = think.think_letter(PROBLEM, budget=20.0)
        self.assertEqual((letter, info["skipped"], timings), (None, "budget", {}))
        self.assertEqual(post.calls, [])

    def test_a_request_inside_the_budget_is_capped_and_parsed(self):
        post = fake_server("3 x 4 = 12, minus 2 is 10.\nAnswer: C")
        with mock.patch.object(think, "post", post):
            letter, info, timings = think.think_letter(PROBLEM, budget=50.0)
        self.assertEqual(letter, "C")
        self.assertEqual(info["how"], "answer_line")
        self.assertEqual(post.calls[0]["max_tokens"], think.MAX_TOKENS)
        self.assertEqual(post.calls[0]["temperature"], 0)
        self.assertEqual(timings["prompt_n"], 120)

    def test_tokenize_failure_guesses_high_instead_of_failing(self):
        def post(url, payload, timeout):
            raise urllib.error.URLError("down")
        with mock.patch.object(think, "post", post):
            self.assertGreater(think.count_prompt_tokens("x" * 300), 100)


class AppliesTest(unittest.TestCase):
    def test_levels_options_and_figure(self):
        levels = think.levels_from_config("0,1, 2")
        self.assertTrue(think.applies(PROBLEM, levels))
        self.assertFalse(think.applies({**PROBLEM, "level": 5}, levels))
        self.assertFalse(think.applies({**PROBLEM, "options": {}}, levels))
        self.assertFalse(think.applies({**PROBLEM, "options": dict(list(OPTIONS.items())[:4])}, levels))
        self.assertFalse(think.applies({**PROBLEM, "text_only": False}, levels))
        self.assertTrue(think.applies({**PROBLEM, "text_only": False}, levels, text_only_only=False))
        self.assertFalse(think.applies({**PROBLEM, "level": "two"}, levels))
        self.assertFalse(think.applies(PROBLEM, set()))
        self.assertEqual(think.levels_from_config(""), set())
        self.assertEqual(think.levels_from_config("all"), set(range(8)))

    def test_every_flag_is_in_config_env_so_the_environment_can_override_it(self):
        # copilot.config applies environment overrides only to keys present in config.env
        from copilot.config import CONFIG
        for key in ("THINK_LEVELS", "THINK_TEXT_ONLY", "THINK_NUMERIC", "THINK_STYLE", "THINK_BUDGET_SECONDS",
                    "THINK_MAX_TOKENS", "THINK_MIN_TOKENS"):
            self.assertIn(key, CONFIG, key)
        self.assertEqual(think.BUDGET, 45.0)
        self.assertIn(think.STYLE, think.INSTRUCTIONS)

    def test_the_exam_setting_is_every_level_with_figures(self):
        # Team decision of 15 Nov 2026 after the organisers' practice set (config.env, the EXAM SETTING note):
        # the stage runs on every level, figures included; THINK_LEVELS= (empty) restores the shipped policy.
        from copilot.config import CONFIG
        self.assertEqual(think.levels_from_config(CONFIG.get("THINK_LEVELS", "")), set(range(8)))
        self.assertEqual(str(CONFIG.get("THINK_TEXT_ONLY", "1")), "0")


class PipelineTest(unittest.TestCase):
    def solve(self, post, **flags):
        patches = [mock.patch.object(pipeline, "USE_SOLVERS", False), mock.patch.object(pipeline, "USE_LETTER_MODEL", False),
                   mock.patch.object(pipeline, "USE_PAL", False),   # the program stage (exam setting) is tested in test_pal
                   mock.patch.object(pipeline, "THINK_LEVELS", set(range(8))), mock.patch.object(think, "post", post)]
        patches += [mock.patch.object(pipeline, key, value) for key, value in flags.items()]
        for patch in patches:
            patch.start()
        try:
            return pipeline.solve(PROBLEM)
        finally:
            for patch in patches:
                patch.stop()

    def test_a_parsed_letter_answers_with_rule_think_and_the_clock_counts_it(self):
        post = fake_server("12 - 2 = 10.\nAnswer: B")
        result = self.solve(post)
        self.assertEqual((result["answer"], result["rule"], result["status"]), ("B", "think", "ok"))
        # the pipeline's budget is THINK_BUDGET_SECONDS (45): a 100-token prompt leaves 195 output tokens, not the 200 cap
        self.assertEqual(post.calls[0]["max_tokens"], think.output_budget(100, think.BUDGET))
        self.assertLess(post.calls[0]["max_tokens"], think.MAX_TOKENS)
        self.assertLessEqual(board_clock.estimate_tokens(100 + think.TEMPLATE_TOKENS, post.calls[0]["max_tokens"]), think.BUDGET)
        self.assertEqual(result["prompt_tokens"], 120)
        self.assertGreater(result["board_seconds"], 10)
        self.assertEqual(result["extra"]["think"]["how"], "answer_line")

    def test_unreadable_working_falls_back_to_the_middle_value(self):
        result = self.solve(fake_server("Let me think about the bags", finish="length"))
        self.assertEqual((result["answer"], result["rule"], result["status"]), ("C", "middle_value", "ok"))
        self.assertEqual(result["extra"]["think"]["finish"], "length")

    def test_server_down_or_timeout_still_answers_with_status_ok(self):
        def down(url, payload, timeout):
            if url.endswith("/tokenize"):
                return {"tokens": [1] * 100}
            raise urllib.error.URLError("no server")
        result = self.solve(down)
        self.assertEqual((result["answer"], result["rule"], result["status"]), ("C", "middle_value", "ok"))
        self.assertTrue(result["extra"]["think"]["skipped"].startswith("error"))

        def slow(url, payload, timeout):
            if url.endswith("/tokenize"):
                return {"tokens": [1] * 100}
            raise TimeoutError()
        result = self.solve(slow)
        self.assertEqual((result["answer"], result["rule"]), ("C", "middle_value"))

    def test_levels_off_never_calls_the_model(self):
        post = fake_server("Answer: A")
        result = self.solve(post, THINK_LEVELS=set())
        self.assertEqual((result["answer"], result["rule"]), ("C", "middle_value"))
        self.assertEqual(post.calls, [])
        self.assertNotIn("think", result["extra"])

    def test_a_figure_problem_is_skipped_unless_allowed(self):
        post = fake_server("Answer: A")
        with mock.patch.dict(PROBLEM, {"text_only": False}):
            self.assertEqual(self.solve(post, THINK_TEXT_ONLY=True)["rule"], "middle_value")
            self.assertEqual(self.solve(post, THINK_TEXT_ONLY=False)["rule"], "think")


if __name__ == "__main__":
    unittest.main()
