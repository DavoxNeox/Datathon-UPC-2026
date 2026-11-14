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

    def neighbour(self, pid, level, topic, label="B"):
        return {"id": pid, "language": "cat", "level": level, "topic": topic, "text": "x", "options": {"B": "2"}, "label": label}

    def test_rung1_neighbour_without_label(self):
        easier = self.neighbour("n-1", 0, "arithmetic")
        with mock.patch.object(hints.retrieval, "neighbors", return_value=[easier]) as nb:
            h = hints.get_hint("sample-4", 1, "cat")  # sample-4 is level 1, arithmetic
        nb.assert_called_once_with("sample-4", level_delta=-1, same_topic=True, lang="cat", k=5)
        self.assertEqual(h["kind"], "neighbour")
        self.assertEqual(h["problem"]["id"], "n-1")
        self.assertNotIn("label", h["problem"])
        self.assertTrue(h["easier"])
        self.assertIn("més fàcil (nivell 0)", h["text_ca"])
        self.assertEqual(h["estimated_board_seconds"], 0.0)

    def test_rung1_level_0_uses_a_same_level_neighbour_and_says_so(self):
        same = self.neighbour("n-0", 0, "arithmetic")
        with mock.patch.object(hints.retrieval, "neighbors", return_value=[same]):
            h = hints.get_hint("sample-1", 1, "cat")  # sample-1 is level 0
        self.assertEqual(h["problem"]["id"], "n-0")
        self.assertFalse(h["easier"])
        self.assertIn("del mateix nivell", h["text_ca"])
        self.assertIn("same level", h["text_en"])
        self.assertNotIn("més fàcil", h["text_ca"])

    def test_rung1_never_goes_up_a_level_or_changes_topic(self):
        harder = self.neighbour("n-up", 1, "arithmetic")
        other = self.neighbour("n-areas", 0, "areas")
        ok = self.neighbour("n-ok", 0, "arithmetic")
        with mock.patch.object(hints.retrieval, "neighbors", return_value=[harder, other, ok]):
            h = hints.get_hint("sample-1", 1, "cat")
        self.assertEqual(h["problem"]["id"], "n-ok")
        with mock.patch.object(hints.retrieval, "neighbors", return_value=[harder, other]):
            h = hints.get_hint("sample-1", 1, "cat")
        self.assertIsNone(h["problem"])
        self.assertIn("Prova-ho amb una estratègia", h["text_ca"])

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


class Rung0Test(unittest.TestCase):
    """Rung 0: the problem in the other language, found by id, never with its label."""

    def setUp(self):
        hints.register_problem({"id": "bi-1", "language": "cat", "level": 1, "text": "Quants cromos li queden?",
                                "options": {"A": "6", "B": "8", "C": "9"}, "label": "C"})
        hints.register_problem({"id": "bi-1", "language": "eng", "level": 1, "text": "How many cards are left?",
                                "options": {"A": "6", "B": "8", "C": "9"}, "label": "C"})

    def test_catalan_reader_gets_the_english_version_by_id(self):
        h = hints.translation("bi-1", "cat")
        self.assertEqual(h["kind"], "translation")
        self.assertEqual(h["rung"], 0)
        self.assertTrue(h["available"])
        self.assertEqual(h["language"], "eng")
        self.assertEqual(h["text"], "How many cards are left?")
        self.assertEqual(h["options"], {"A": "6", "B": "8", "C": "9"})
        self.assertIn("en anglès", h["text_ca"])
        self.assertIn("in English", h["text_en"])

    def test_english_reader_gets_the_catalan_version(self):
        h = hints.translation("bi-1", "eng")
        self.assertEqual(h["language"], "cat")
        self.assertEqual(h["text"], "Quants cromos li queden?")
        self.assertIn("in Catalan", h["text_en"])

    def test_translation_never_carries_the_label(self):
        for lang in ("cat", "eng"):
            h = hints.translation("bi-1", lang)
            self.assertNotIn("label", h)
            self.assertNotIn("label", str(h).lower())
            self.assertNotIn("answer", str(h).lower())
            self.assertEqual(set(h), {"rung", "kind", "language", "estimated_board_seconds", "text_ca", "text_en",
                                      "available", "text", "options"})

    def test_rung_0_costs_no_model_time(self):
        self.assertEqual(hints.translation("bi-1", "cat")["estimated_board_seconds"], 0.0)

    def test_missing_other_language_is_not_available_and_never_raises(self):
        h = hints.translation("sample-4", "cat")  # sample-4 exists in Catalan only
        self.assertFalse(h["available"])
        self.assertEqual(h["text"], "")
        self.assertEqual(h["options"], {})
        self.assertFalse(hints.translation("no-such-problem", "cat")["available"])

    def test_get_hint_rung_0_is_the_translation_and_rungs_stay_clamped_at_0(self):
        self.assertEqual(hints.get_hint("bi-1", 0, "cat"), hints.translation("bi-1", "cat"))
        self.assertEqual(hints.get_hint("bi-1", -3, "cat")["rung"], 0)
        self.assertEqual(hints.get_hint("sample-4", 1, "cat")["rung"], 1)

    def test_problem_in_is_strict_about_the_language(self):
        self.assertIsNone(hints.problem_in("sample-4", "eng"))
        self.assertEqual(hints.problem_in("sample-4", "cat")["id"], "sample-4")
        self.assertEqual(hints.other_language("cat"), "eng")
        self.assertEqual(hints.other_language("eng"), "cat")


class DisplayValueTest(unittest.TestCase):
    """The solution shows the option value cleaned of OCR residue, or no value at all."""

    def test_units_and_superscripts(self):
        cases = {"4cm²2": "4 cm²", "27cm2": "27 cm²", "80 cm2": "80 cm²", "165 cm²": "165 cm²", "48cm": "48 cm",
                 "24 cm": "24 cm", "3m3": "3 m³", "10%": "10%", "1/2": "1/2", "0,5": "0,5", "18": "18",
                 "x = 4": "x = 4", "2 + 3": "2 + 3", "15:30": "15:30", "hexagon": "hexagon", " 12 ": "12",
                 "{2,3,5,7}": "{2,3,5,7}", "(3, 4)": "(3, 4)", "56km/h": "56 km/h", "9km.": "9 km"}
        for raw, want in cases.items():
            self.assertEqual(hints.display_value(raw), want, raw)

    def test_illegible_values_are_dropped(self):
        for raw in ("2 11 cm2", "1 10", "12 m 1m", "", None, "   ", "x" * 31):
            self.assertEqual(hints.display_value(raw), "", repr(raw))

    def test_solution_text_uses_the_cleaned_value_or_none(self):
        base = {"id": "fake-sol", "language": "cat", "level": 3, "text": "t", "label": "E"}
        with mock.patch.object(hints, "problem_for", return_value=dict(base, options={"E": "4cm²2"})):
            hints.reset("fake-sol")
            h = hints.get_hint("fake-sol", 4, "cat")
        self.assertTrue(h["text_ca"].startswith("Solució: opció E (4 cm²)."), h["text_ca"])
        self.assertTrue(h["text_en"].startswith("Solution: option E (4 cm²)."))
        self.assertEqual((h["value"], h["value_shown"]), ("4cm²2", "4 cm²"))
        with mock.patch.object(hints, "problem_for", return_value=dict(base, options={"E": "2 11 cm2"})):
            hints.reset("fake-sol")
            h = hints.get_hint("fake-sol", 4, "cat")
        self.assertTrue(h["text_ca"].startswith("Solució: opció E."), h["text_ca"])
        self.assertEqual(h["value_shown"], "")


class DemoSetTest(unittest.TestCase):
    """Hand-written steps from data_curated/demo_set.json come first on rung 3, never the last one."""

    STEPS = [{"text_ca": "Pensa en el pitjor cas.", "text_en": "Think of the worst case."},
             {"text_ca": "Compta les que no valen.", "text_en": "Count the ones that do not count."},
             {"text_ca": "Suma'n una més.", "text_en": "Add one more."},
             {"text_ca": "Són 9 cromos: opció C.", "text_en": "That is 9 cards: option C."}]

    def use_file(self, content):
        import json, os, tempfile
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        if content is not None:
            self.tmp.write(content if isinstance(content, str) else json.dumps(content))
        self.tmp.close()
        self.addCleanup(lambda: os.path.exists(self.tmp.name) and os.unlink(self.tmp.name))
        patch = mock.patch.object(hints, "DEMO_SET_FILE", self.tmp.name)
        patch.start()
        self.addCleanup(patch.stop)
        hints._demo_set = None
        self.addCleanup(setattr, hints, "_demo_set", None)
        hints.reset("sample-4")

    def test_steps_in_order_never_the_last_then_strategy(self):
        self.use_file({"problems": [{"id": "sample-4", "steps": self.STEPS}]})
        got = [hints.get_hint("sample-4", 3, "cat") for _ in range(5)]
        self.assertEqual([h["kind"] for h in got[:3]], ["demo_steps"] * 3)
        self.assertEqual(got[0]["text_ca"], "Pas 1 de 3: Pensa en el pitjor cas.")
        self.assertEqual(got[1]["text_en"], "Step 2 of 3: Count the ones that do not count.")
        self.assertEqual(got[2]["text_ca"], "Pas 3 de 3: Suma'n una més.")
        self.assertEqual((got[0]["step"], got[0]["steps_total"]), (1, 3))
        for h in got:
            self.assertNotIn("9 cromos", h["text_ca"] + h["text_en"])
        # steps exhausted: sample-4 has no solver trace and its topic is not validated -> a strategy card
        self.assertEqual(got[3]["kind"], "strategy")
        self.assertEqual(got[4]["kind"], "strategy")

    def test_rung4_shows_the_last_step_with_letter_and_value(self):
        self.use_file({"problems": [{"id": "sample-4", "steps": self.STEPS}]})
        h = hints.get_hint("sample-4", 4, "cat")
        self.assertEqual(h["kind"], "solution")
        self.assertEqual(h["source"], "demo_set")
        self.assertEqual((h["label"], h["value"]), ("C", "9"))
        self.assertEqual(len(h["trace"]), 4)
        self.assertTrue(h["text_ca"].startswith("Solució: opció C (9)."))
        self.assertIn("Són 9 cromos: opció C.", h["text_ca"])

    def test_prefetch_restarts_the_steps(self):
        self.use_file({"problems": [{"id": "sample-4", "steps": self.STEPS}]})
        hints.get_hint("sample-4", 3, "cat")
        hints.prefetch("sample-4", "cat")
        self.assertEqual(hints.get_hint("sample-4", 3, "cat")["step"], 1)

    def test_missing_empty_or_broken_file_means_no_demo_steps(self):
        import os
        for content in (None, "", "{not json", {"problems": []}, {"problems": [{"id": "sample-4", "steps": []}]}):
            self.use_file(content)
            if content is None:
                os.unlink(self.tmp.name)
            self.assertIsNone(hints.demo_steps("sample-4"))
            self.assertEqual(hints.get_hint("sample-4", 3, "cat")["kind"], "strategy")

    def test_one_step_only_is_the_solution_and_never_a_hint(self):
        self.use_file({"problems": [{"id": "sample-4", "steps": self.STEPS[-1:]}]})
        self.assertEqual(hints.get_hint("sample-4", 3, "cat")["kind"], "strategy")
        self.assertIn("Són 9 cromos", hints.get_hint("sample-4", 4, "cat")["text_ca"])

    def test_other_problems_are_not_affected(self):
        self.use_file({"problems": [{"id": "sample-4", "steps": self.STEPS}]})
        hints.reset("sample-1")
        self.assertEqual(hints.get_hint("sample-1", 3, "cat")["kind"], "trace")


class LessonTest(unittest.TestCase):
    """get_lesson: the fourth hint, by solver family, else by topic, always through the leak filter."""

    LESSONS = {"lessons": [
        {"key": "arithmetic", "family": "sharing", "title_ca": "Repartir", "title_en": "Sharing",
         "text_ca": "Quan es reparteix, pensa primer en el total i després en les parts.",
         "text_en": "When sharing, think of the total first and then of the parts.", "strategy_ref": 1},
        {"key": "arithmetic", "title_ca": "Problemes de paraules", "title_en": "Word problems",
         "text_ca": "Tradueix cada frase a una operació abans de calcular res.",
         "text_en": "Turn each sentence into an operation before computing anything."},
        {"key": "areas", "title_ca": "Àrees", "title_en": "Areas", "text_ca": "Talla la figura.", "text_en": "Cut the figure."},
    ]}

    def use_lessons(self, content, families=None):
        import json, os, tempfile
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        if content is not None:
            tmp.write(content if isinstance(content, str) else json.dumps(content))
        tmp.close()
        if content is None:
            os.unlink(tmp.name)
        self.addCleanup(lambda: os.path.exists(tmp.name) and os.unlink(tmp.name))
        for name, value in (("LESSONS_FILE", tmp.name), ("_lessons", None), ("_families", families or {})):
            patch = mock.patch.object(hints, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def test_lesson_of_the_family_comes_first(self):
        self.use_lessons(self.LESSONS, {"sample-4": "sharing"})
        lesson = hints.get_lesson("sample-4", "cat")
        self.assertEqual(lesson["kind"], "lesson")
        self.assertEqual(lesson["rung"], "lesson")
        self.assertEqual(lesson["family"], "sharing")
        self.assertEqual(lesson["title_ca"], "Repartir")
        self.assertEqual(lesson["strategy_ref"], 1)
        self.assertEqual(lesson["estimated_board_seconds"], 0.0)

    def test_lesson_of_the_topic_when_the_problem_has_no_family(self):
        self.use_lessons(self.LESSONS, {})
        lesson = hints.get_lesson("sample-4", "cat")   # arithmetic
        self.assertIsNone(lesson["family"])
        self.assertEqual(lesson["title_en"], "Word problems")
        self.assertEqual(hints.get_lesson("sample-3", "eng")["key"], "areas")

    def test_no_lesson_for_an_unknown_topic_or_missing_file(self):
        self.use_lessons({"lessons": [{"key": "boards", "text_ca": "x", "text_en": "x"}]})
        self.assertIsNone(hints.get_lesson("sample-4", "cat"))
        self.use_lessons(None)
        self.assertIsNone(hints.get_lesson("sample-4", "cat"))
        self.use_lessons("{broken")
        self.assertIsNone(hints.get_lesson("sample-4", "cat"))

    def test_a_leaking_lesson_is_skipped_for_the_next_candidate_or_none(self):
        leaking = dict(self.LESSONS["lessons"][0], text_ca="En Pau es queda amb 9 cromos.", text_en="Pau keeps 9 cards.")
        self.use_lessons({"lessons": [leaking, self.LESSONS["lessons"][1]]}, {"sample-4": "sharing"})
        lesson = hints.get_lesson("sample-4", "cat")   # sample-4: C = 9
        self.assertEqual(lesson["title_en"], "Word problems")
        self.use_lessons({"lessons": [leaking]}, {"sample-4": "sharing"})
        self.assertIsNone(hints.get_lesson("sample-4", "cat"))

    def test_families_file_is_read_once_and_tolerated(self):
        with mock.patch.object(hints, "FAMILIES_FILE", "/nonexistent/families.json"), mock.patch.object(hints, "_families", None):
            self.assertIsNone(hints.family_of("sample-4"))


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
