import unittest

from copilot import board_clock


class EstimateTest(unittest.TestCase):
    def test_readme_hello_world(self):
        # README step 5.5: 27 prompt tokens, 10 written, took about 4 s on the board
        seconds = board_clock.estimate({"prompt_n": 27, "predicted_n": 10})
        self.assertAlmostEqual(seconds, 27 / board_clock.PREFILL_TPS + 10 / board_clock.GEN_TPS, places=6)
        self.assertTrue(3.5 < seconds < 5.0)

    def test_baseline_problem_is_about_nine_seconds(self):
        # README 11.3: an 85-token problem, one letter, about 9 s mostly prefill
        self.assertTrue(7 < board_clock.estimate_tokens(85, 1) < 10)

    def test_missing_or_null_timings_count_as_zero(self):
        self.assertEqual(board_clock.estimate({}), 0.0)
        self.assertEqual(board_clock.estimate({"prompt_n": None, "predicted_n": None}), 0.0)

    def test_clock_adds_calls_and_embeddings(self):
        clock = board_clock.Clock()
        clock.add_llm({"prompt_n": 110, "predicted_n": 1})
        clock.add_llm({"prompt_n": 20, "predicted_n": 30})
        clock.add_embeddings(2)
        expected = 130 / board_clock.PREFILL_TPS + 31 / board_clock.GEN_TPS + 2 * board_clock.EMBED_SECONDS
        self.assertAlmostEqual(clock.board_seconds(), expected, places=6)
        self.assertGreaterEqual(clock.real_seconds(), 0.0)

    def test_sim_checks_the_estimate(self):
        import os
        clock = board_clock.Clock()
        clock.add_llm({"prompt_n": 1100, "predicted_n": 0})  # 100 s on the board, instant here
        old = os.environ.get("RUNTIME")
        try:
            os.environ["RUNTIME"] = "sim"
            self.assertGreater(clock.seconds(), 60)
            os.environ["RUNTIME"] = "board"
            self.assertLess(clock.seconds(), 1)
        finally:
            if old is None:
                os.environ.pop("RUNTIME", None)
            else:
                os.environ["RUNTIME"] = old


if __name__ == "__main__":
    unittest.main()


class RuntimeTest(unittest.TestCase):
    def test_auto_detects_from_device_tree(self):
        import os, tempfile
        from copilot import board_clock as bc
        old_env, old_file = os.environ.get("RUNTIME"), bc.BOARD_MODEL_FILE
        try:
            os.environ["RUNTIME"] = "auto"
            with tempfile.NamedTemporaryFile("wb", delete=False) as f:
                f.write(b"Arduino SA,Imola\x00")
            bc.BOARD_MODEL_FILE = f.name
            self.assertEqual(bc.runtime(), "board")
            bc.BOARD_MODEL_FILE = f.name + ".missing"
            self.assertEqual(bc.runtime(), "sim")
            os.environ["RUNTIME"] = "board"
            self.assertEqual(bc.runtime(), "board")
        finally:
            bc.BOARD_MODEL_FILE = old_file
            if old_env is None:
                os.environ.pop("RUNTIME", None)
            else:
                os.environ["RUNTIME"] = old_env
