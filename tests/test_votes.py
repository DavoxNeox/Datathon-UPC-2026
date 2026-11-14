import unittest
from unittest import mock

from copilot import votes

PROBLEM = {"id": "x", "text": "How many apples?", "options": {"A": "10", "B": "12", "C": "13", "D": "14", "E": "15"}}


def fake_post_factory(answers):
    """answers: letter the fake model writes on each successive request."""
    calls = []

    def fake_post(url, payload, timeout):
        calls.append(payload)
        return {"choices": [{"message": {"content": answers[len(calls) - 1]}}], "timings": {"prompt_n": 44, "predicted_n": 1}}
    return fake_post, calls


class VotesTest(unittest.TestCase):
    def test_value_grammar_lists_the_distinct_option_strings_escaped(self):
        self.assertEqual(votes.value_grammar({"A": "10", "B": "12", "C": "12", "D": '1"', "E": "15"}),
                         'root ::= "10" | "12" | "1\\"" | "15"')

    def test_value_letter_maps_the_value_back(self):
        fake, calls = fake_post_factory(["13"])
        with mock.patch.object(votes, "post", fake):
            letter, value, timings = votes.value_letter(PROBLEM)
        self.assertEqual((letter, value, timings["prompt_n"]), ("C", "13", 44))
        self.assertIn('"13"', calls[0]["grammar"])
        self.assertEqual(calls[0]["temperature"], 0)

    def test_value_letter_abstains_without_options_or_on_a_shared_value(self):
        self.assertEqual(votes.value_letter({"text": "x", "options": {}}), (None, "", {}))
        fake, _ = fake_post_factory(["12"])
        with mock.patch.object(votes, "post", fake):
            letter, _, _ = votes.value_letter({"text": "x", "options": {"A": "12", "B": "12", "C": "1", "D": "2", "E": "3"}})
        self.assertIsNone(letter)

    def test_shifted_messages_relabel_the_options_and_keep_the_text_in_its_own_message(self):
        messages = votes.shifted_messages(PROBLEM, "BCDEA")
        self.assertEqual(messages[1]["content"], "How many apples?")
        self.assertEqual(messages[-1]["content"], "A) 12\nB) 13\nC) 14\nD) 15\nE) 10\nAnswer:")

    def test_vote_counts_the_original_option_and_needs_a_strict_majority(self):
        # A purely positional model always says "A": every option gets one vote, so a tie and None
        fake, _ = fake_post_factory(["A"] * 5)
        with mock.patch.object(votes, "post", fake):
            letter, tally, spent = votes.vote_letter(PROBLEM)
        self.assertIsNone(letter)
        self.assertEqual(tally, {"A": 1, "B": 1, "C": 1, "D": 1, "E": 1})
        self.assertEqual(len(spent), 5)
        # A model that always picks the option "13" wherever it is: shown letters C, B, A, E, D
        fake, _ = fake_post_factory(["C", "B", "A", "E", "D"])
        with mock.patch.object(votes, "post", fake):
            letter, tally, _ = votes.vote_letter(PROBLEM)
        self.assertEqual((letter, tally["C"]), ("C", 5))
        # Two votes are not enough with min_votes=3
        fake, _ = fake_post_factory(["C", "B", "B", "B", "B"])  # 13 twice (C, B), then 14, 15, 10
        with mock.patch.object(votes, "post", fake):
            letter, tally, _ = votes.vote_letter(PROBLEM)
        self.assertEqual(tally["C"], 2)
        self.assertIsNone(letter)

    def test_pipeline_flags_are_off_by_default(self):
        from copilot import pipeline
        self.assertEqual((pipeline.VOTE_SHIFTS, pipeline.USE_VALUE_MODEL), (0, False))


if __name__ == "__main__":
    unittest.main()
