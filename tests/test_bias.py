import json
import math
import os
import tempfile
import unittest

from copilot import bias

LP = {"A": -1.824, "B": -3.594, "C": -4.365, "D": -4.038, "E": -2.957}  # measured on sample-2 (truth B)


class NormalizeTest(unittest.TestCase):
    def test_probabilities_sum_to_one_and_keep_order(self):
        normed = bias.normalize(LP)
        self.assertAlmostEqual(sum(math.exp(v) for v in normed.values()), 1.0, places=9)
        self.assertEqual(max(normed, key=normed.get), "A")


class PriorTest(unittest.TestCase):
    def test_uniform_runs_give_uniform_prior(self):
        runs = [{l: -1.0 for l in "ABCDE"}] * 3
        prior = bias.prior_from_runs(runs)
        for l in "ABCDE":
            self.assertAlmostEqual(prior[l], math.log(0.2), places=9)

    def test_biased_runs_show_the_favourite_letter(self):
        prior = bias.prior_from_runs([LP, LP])
        self.assertEqual(max(prior, key=prior.get), "A")


class ChooseTest(unittest.TestCase):
    def test_alpha_zero_is_the_raw_model(self):
        prior = bias.prior_from_runs([LP])
        self.assertEqual(bias.choose(LP, prior, alpha=0.0)[0], "A")

    def test_removing_the_prior_flips_a_biased_answer(self):
        # The model prefers A on every problem; a problem where it leans less on A than usual gets corrected
        prior = bias.prior_from_runs([{"A": -0.5, "B": -3, "C": -3, "D": -3, "E": -3}] * 4)
        problem = {"A": -1.2, "B": -1.3, "C": -3, "D": -3, "E": -3}
        self.assertEqual(bias.choose(problem, prior, alpha=1.0)[0], "B")
        self.assertEqual(bias.choose(problem, prior, alpha=0.0)[0], "A")

    def test_small_margin_falls_back_to_the_common_letter(self):
        prior = {l: math.log(0.2) for l in "ABCDE"}
        tie = {"A": -1.0, "B": -1.0, "C": -5.0, "D": -5.0, "E": -5.0}
        letter, margin = bias.choose(tie, prior, alpha=1.0, min_margin=0.1, fallback="D")
        self.assertEqual(letter, "D")
        self.assertAlmostEqual(margin, 0.0, places=9)
        letter, _ = bias.choose(tie, prior, alpha=1.0, min_margin=0.0, fallback="D")
        self.assertEqual(letter, "A", "exact ties break alphabetically, deterministically")


class LoadTest(unittest.TestCase):
    def test_missing_file_means_no_calibration(self):
        self.assertIsNone(bias.load(os.path.join(tempfile.gettempdir(), "no-such-prior.json")))

    def test_file_is_loaded_with_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "prior.json")
            with open(path, "w") as f:
                json.dump({"prior": {l: math.log(0.2) for l in "ABCDE"}}, f)
            data = bias.load(path)
            self.assertEqual(data["alpha"], 1.0)
            self.assertEqual(data["min_margin"], 0.0)
            self.assertIn(data["fallback"], "ABCDE")

    def test_incomplete_prior_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "prior.json")
            with open(path, "w") as f:
                json.dump({"prior": {"A": 0.0}}, f)
            self.assertIsNone(bias.load(path))


if __name__ == "__main__":
    unittest.main()
