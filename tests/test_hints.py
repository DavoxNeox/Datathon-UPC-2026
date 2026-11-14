"""copilot/hints.py: the hint ladder without a language model (rungs 1, 2, 4, 3a and 3c)."""
import contextlib
import io
import unittest

from copilot import board_clock
from unittest import mock

from copilot import hints

OPTIONS = {"A": "8", "B": "9", "C": "10", "D": "12", "E": "14"}


class LadderTest(unittest.TestCase):
    def setUp(self):
        hints.reset("sample-1")
        hints.reset("sample-4")
        hints.reset("sample-3")

    def test_rung1_neighbour_without_label(self):
        h = hints.get_hint("sample-4", 1, "cat")
        self.assertEqual(h["kind"], "neighbour")
        self.assertIsNotNone(h["problem"])
        self.assertNotIn("label", h["problem"])
        self.assertEqual(h["estimated_board_seconds"], 0.0)

    def test_rung1_visual_topic_has_image_key(self):
        h = hints.get_hint("sample-3", 1, "eng")  # sample-3 is "areas", a visual topic
        self.assertIn("image", h["problem"])

    def test_rung2_cycles_strategies_of_the_topic(self):
        a = hints.get_hint("sample-4", 2, "cat")
        b = hints.get_hint("sample-4", 2, "cat")
        self.assertEqual(a["kind"], "strategy")
        self.assertIn("manipulative", a)
        self.assertNotEqual(a["text_ca"], b["text_ca"])
        self.assertIn(a["text_ca"], [c["text_ca"] for c in hints.strategies("arithmetic")])

    def test_every_topic_has_strategies_in_both_languages(self):
        from copilot.topics import TOPIC_KEYS
        for key in TOPIC_KEYS:
            cards = hints.strategies(key)
            self.assertGreaterEqual(len(cards), 3, key)
            for card in cards:
                self.assertTrue(card["text_ca"] and card["text_en"], key)
                self.assertIn(card.get("manipulative"), (None, "rotate", "paths", "dice"))

    def test_rung3_walks_the_trace_but_never_its_last_step(self):
        first = hints.get_hint("sample-1", 3, "cat")
        second = hints.get_hint("sample-1", 3, "cat")
        third = hints.get_hint("sample-1", 3, "cat")
        self.assertEqual(first["kind"], "trace")
        self.assertEqual(second["kind"], "trace")
        self.assertTrue(first["text_ca"].startswith("Pas 1 de 2"))
        self.assertTrue(second["text_en"].startswith("Step 2 of 2"))
        self.assertNotIn("10", first["text_ca"] + second["text_ca"] + first["text_en"] + second["text_en"])
        self.assertEqual(third["kind"], "strategy")  # trace exhausted, topic not validated: 3c

    def test_rung3_without_trace_and_without_validated_topic_is_a_strategy(self):
        h = hints.get_hint("sample-4", 3, "cat")
        self.assertEqual(h["kind"], "strategy")
        self.assertEqual(h["rung"], 3)

    def test_rung3_uses_the_llm_only_for_validated_topics(self):
        fake = {"ok": True, "text_ca": "Resta les que dóna.", "text_en": "Subtract the ones given.",
                "estimated_board_seconds": 12.5}
        with mock.patch.object(hints, "llm_allowed", return_value=True), \
                mock.patch.object(hints, "llm_hint", return_value=fake) as llm:
            h = hints.get_hint("sample-4", 3, "cat")
        self.assertEqual(h["kind"], "llm")
        self.assertEqual(h["estimated_board_seconds"], 12.5)
        llm.assert_called_once()

    def test_rung3_falls_back_to_a_strategy_when_the_llm_hint_leaks(self):
        fake = {"ok": False, "text_ca": "", "text_en": "", "estimated_board_seconds": 20.0,
                "rejected": ["value:9", "value:9"]}
        with mock.patch.object(hints, "llm_allowed", return_value=True), \
                mock.patch.object(hints, "llm_hint", return_value=fake):
            h = hints.get_hint("sample-4", 3, "cat")
        self.assertEqual(h["kind"], "strategy")
        self.assertEqual(h["estimated_board_seconds"], 20.0)

    def test_rung4_solution_has_letter_value_and_trace(self):
        h = hints.get_hint("sample-1", 4, "cat")
        self.assertEqual(h["kind"], "solution")
        self.assertEqual(h["label"], "C")
        self.assertEqual(h["value"], "10")
        self.assertEqual(len(h["trace"]), 3)
        self.assertIn("opció C (10)", h["text_ca"])
        self.assertIn("option C (10)", h["text_en"])

    def test_unknown_problem_never_raises(self):
        for rung in (1, 2, 3, 4):
            h = hints.get_hint("no-such-problem", rung, "cat")
            self.assertIn("text_ca", h)

    def test_prefetch_resets_the_ladder_and_skips_unvalidated_topics(self):
        hints.get_hint("sample-1", 3, "cat")
        with mock.patch.object(hints.threading, "Thread") as thread:
            hints.prefetch("sample-1", "cat")
            thread.assert_not_called()  # arithmetic is not validated: no LLM, nothing to warm
        self.assertTrue(hints.get_hint("sample-1", 3, "cat")["text_ca"].startswith("Pas 1"))

    def test_prefetch_warms_in_a_thread_for_validated_topics(self):
        with mock.patch.object(hints, "llm_allowed", return_value=True), \
                mock.patch.object(hints.threading, "Thread") as thread:
            hints.prefetch("sample-4", "cat")
            thread.assert_called_once()


class LlmHintTest(unittest.TestCase):
    """llm_hint with a fake server: the leak filter and the retry, no network."""

    def problem(self):
        return {"id": "fake-1", "language": "eng", "level": 0, "text": "3 bags of 4 apples, 2 eaten. Left?",
                "options": OPTIONS, "label": "C"}

    def test_two_calls_catalan_then_english_accept_a_clean_hint(self):
        answers = iter([("Compta totes les pomes primer.", {"prompt_n": 50, "predicted_n": 8}),
                        ("Count all the apples first.", {"prompt_n": 30, "predicted_n": 7})])
        with mock.patch.object(hints, "_call", side_effect=lambda *a, **k: next(answers)):
            r = hints.llm_hint(self.problem(), "cat")
        self.assertEqual(r["text_ca"], "Compta totes les pomes primer.")
        self.assertTrue(r["ok"])
        self.assertEqual(r["attempts"], 1)
        self.assertEqual(r["prompt_n"], 80)
        self.assertEqual(r["predicted_n"], 15)
        self.assertAlmostEqual(r["estimated_board_seconds"], 80 / board_clock.PREFILL_TPS + 15 / board_clock.GEN_TPS, places=3)

    def test_leaking_hint_is_retried_once_with_a_strict_prompt(self):
        calls = []

        def fake(messages, max_tokens, grammar=None, timeout=0):
            calls.append(messages[-1]["content"])
            if len(calls) <= 2:
                return "You have 10 apples left.", {"prompt_n": 10, "predicted_n": 6}
            return "Subtract what she ate.", {"prompt_n": 10, "predicted_n": 6}

        with mock.patch.object(hints, "_call", side_effect=fake):
            r = hints.llm_hint(self.problem(), "cat")
        self.assertTrue(r["ok"])
        self.assertEqual(r["attempts"], 2)
        self.assertEqual(r["rejected"], ["value:10"])
        self.assertIn("gave the answer away", calls[2])

    def test_no_retry_when_the_first_attempt_was_already_expensive(self):
        heavy = ("The answer is C.", {"prompt_n": 400, "predicted_n": 40})  # ~43 s on the board
        with mock.patch.object(hints, "_call", return_value=heavy) as call:
            r = hints.llm_hint(self.problem(), "cat")
        self.assertFalse(r["ok"])
        self.assertEqual(call.call_count, 2)  # one attempt, two languages, no retry
        self.assertIn("no-retry:over-budget", r["rejected"])

    def test_two_leaks_give_up(self):
        with mock.patch.object(hints, "_call", return_value=("The answer is C.", {"prompt_n": 1, "predicted_n": 5})):
            r = hints.llm_hint(self.problem(), "cat")
        self.assertFalse(r["ok"])
        self.assertEqual(r["attempts"], 2)
        self.assertEqual(len(r["rejected"]), 2)

    def test_prompt_puts_the_problem_before_the_last_user_message(self):
        msgs = hints._messages(self.problem(), "cat")
        self.assertEqual([m["role"] for m in msgs], ["system", "user", "assistant", "user"])
        self.assertIn("3 bags", msgs[1]["content"])
        self.assertIn("C (10)", msgs[3]["content"])
        self.assertIn("Catalan", msgs[3]["content"])
        # the warm-up prompt is exactly the Catalan hint prompt
        self.assertEqual(hints._messages(self.problem(), "cat"), msgs)

    def test_grammar_allows_no_digit_of_any_alphabet(self):
        import re
        allowed = re.search(r"\[(.+)\]\+", hints.HINT_GRAMMAR).group(1)
        for ch in "0123456789٣٦³⁶½ƒ？":
            self.assertNotIn(ch, allowed)
        for ch in "àèéíïòóúüç·?":
            self.assertIn(ch, allowed)

    def test_full_prefetch_result_is_used_by_rung_3(self):
        hints.reset("sample-4")
        fake = {"ok": True, "text_ca": "Quants en tenia al principi?", "text_en": "How many at first?",
                "estimated_board_seconds": 9.0}
        with mock.patch.object(hints, "llm_allowed", return_value=True), \
                mock.patch.object(hints, "llm_hint", return_value=fake) as llm, \
                mock.patch.object(hints, "PREFETCH", "full"):
            hints.prefetch("sample-4", "cat")
            h = hints.get_hint("sample-4", 3, "cat")
        self.assertEqual(h["kind"], "llm")
        self.assertEqual(h["text_ca"], "Quants en tenia al principi?")
        llm.assert_called_once()  # written ahead by prefetch, not again by get_hint

    def test_server_down_is_not_ok_and_does_not_raise(self):
        with mock.patch.object(hints, "_call", side_effect=OSError("down")):
            r = hints.llm_hint(self.problem(), "cat")
        self.assertFalse(r["ok"])
        self.assertTrue(r["rejected"][0].startswith("error:"))

    def test_hint_llm_lang_en_makes_one_english_call_and_shows_it_in_catalan_too(self):
        calls = []

        def fake(messages, max_tokens, grammar=None, timeout=0):
            calls.append(messages[-1]["content"])
            return "What is the total first?", {"prompt_n": 10, "predicted_n": 6}

        with mock.patch.object(hints, "LLM_LANG", "en"), mock.patch.object(hints, "_call", side_effect=fake):
            r = hints.llm_hint(self.problem(), "cat")
        self.assertTrue(r["ok"])
        self.assertEqual(len(calls), 1)
        self.assertIn("English", calls[0])
        self.assertEqual(r["lang"], "eng")
        self.assertEqual(r["text_ca"], r["text_en"])
        # the gate then reads the English quality
        with mock.patch.object(hints, "LLM_LANG", "en"):
            self.assertEqual(hints._llm_lang("cat"), "eng")
        with mock.patch.object(hints, "LLM_LANG", ""):
            self.assertEqual(hints._llm_lang("cat"), "cat")

    def test_only_the_first_sentence_is_kept(self):
        self.assertEqual(hints._one_sentence('"Count first. Then subtract."'), "Count first.")
        self.assertEqual(hints._one_sentence("Compta\nprimer"), "Compta primer")


if __name__ == "__main__":
    unittest.main()
