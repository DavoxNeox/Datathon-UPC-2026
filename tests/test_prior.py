"""The learned option prior (copilot/prior.py): the rules on made-up options, and the committed table."""
import json
import os
import unittest
from fractions import Fraction
from unittest import mock

from copilot import prior

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUMERIC = {"A": "20", "B": "8", "C": "13", "D": "11", "E": "12"}
ASCENDING = {"A": "12", "B": "15", "C": "18", "D": "20", "E": "24"}
NOISY = {"A": "1 10", "B": "11", "C": "12", "D": "13", "E": "15 2 3"}
WORDS = {"A": "a square", "B": "a circle", "C": "a cube", "D": "a line", "E": "none of these"}
TABLE = {"stratifications": [
    {"dims": ["level", "picture", "kind"], "strata": {"level=2|picture=text|kind=numeric": {"chosen": "max"}}},
    {"dims": ["kind"], "strata": {"kind=words": {"chosen": "none_option"}, "kind=noisy_numeric": {"chosen": "middle"}}},
]}


class LenientNumbersTest(unittest.TestCase):
    def test_stray_digit_and_trailing_junk(self):
        for text, value in [("1 10", 10), ("4 40cm", 40), ("6 600 g", 600), ("9 90cm", 90), ("88 616", 88), ("15 2 3", 15),
                            ("300 g 400g 100g 2", 300), ("5 12345", 5), ("42 4m", 42), ("12 m 1m", 12), ("1/2", Fraction(1, 2)),
                            ("2,5", Fraction(5, 2)), ("-3", -3), ("20 = 28", 20)]:
            self.assertEqual(prior.lenient_number(text), Fraction(value), text)

    def test_abstains_on_letters_dates_and_symbols(self):
        for text in ["1S0S", "7: 9", "3∈", "15/4/2015", "GDA", "", None, "E1 4"]:
            self.assertIsNone(prior.lenient_number(text), repr(text))

    def test_lenient_options_need_five_distinct_values(self):
        self.assertEqual(prior.lenient_options(NOISY)["A"], Fraction(10))
        self.assertIsNone(prior.lenient_options({"A": "1 10", "B": "10", "C": "12", "D": "13", "E": "15"}))
        self.assertIsNone(prior.lenient_options({"A": "1", "B": "2", "C": "3", "D": "4"}))
        self.assertIsNone(prior.lenient_options({}))


class FeaturesTest(unittest.TestCase):
    def test_kind_and_order(self):
        f = prior.features({"level": 3, "text_only": True, "language": "eng", "options": ASCENDING})
        self.assertEqual((f["kind"], f["order"], f["picture"], f["level"], f["language"]), ("numeric", "ascending", "text", 3, "eng"))
        self.assertEqual(prior.features({"level": 3, "text_only": False, "options": NUMERIC})["order"], "unsorted")
        self.assertEqual(prior.features({"level": 0, "text_only": False, "options": NOISY})["kind"], "noisy_numeric")
        self.assertEqual(prior.features({"level": 0, "text_only": False, "options": WORDS})["kind"], "words")
        self.assertEqual(prior.features({"level": 0, "text_only": False, "options": {}})["kind"], "no_options")
        self.assertEqual(prior.features({"options": {}})["kind"], "no_options")

    def test_patterns(self):
        f = prior.features({"level": 5, "text_only": True, "options": {"A": "1/2", "B": "1/3", "C": "2/3", "D": "3/4", "E": "1/5"}})
        self.assertTrue(f["fraction"])
        f = prior.features({"level": 5, "text_only": True, "options": {"A": "π", "B": "2π", "C": "√2", "D": "3", "E": "4"}})
        self.assertEqual((f["kind"], f["pi_root"]), ("words", True))
        f = prior.features({"level": 5, "text_only": True, "options": WORDS})
        self.assertTrue(f["none_text"])
        self.assertEqual(prior.none_letters(WORDS), ["E"])
        self.assertEqual(prior.none_letters({"A": "Cap", "B": "3", "C": "4", "D": "5", "E": "6"}), ["A"])
        self.assertEqual(prior.features({"level": 1, "text_only": True, "options": {"A": "3", "B": "3", "C": "4", "D": "5", "E": "6"}})["distinct"], 4)

    def test_stratum_keys(self):
        f = prior.features({"level": 3, "text_only": True, "language": "eng", "options": ASCENDING})
        self.assertEqual(prior.stratum_key(f), "level=3|picture=text|kind=numeric")
        self.assertEqual(prior.stratum_key(f, ("kind", "order")), "kind=numeric|order=ascending")
        self.assertIsNone(prior.stratum_key(prior.features({"options": ASCENDING})))  # no level, no text_only
        self.assertIsNone(prior.stratum_key(prior.features({"level": 3, "options": ASCENDING}), ("picture",)))


class RulesTest(unittest.TestCase):
    def test_rank_rules_on_strict_and_noisy_numbers(self):
        p = {"options": NUMERIC}
        self.assertEqual([prior.apply_rule(r, p) for r in ("min", "second_smallest", "middle", "second_largest", "max")],
                         ["B", "D", "E", "C", "A"])
        self.assertEqual(prior.apply_rule("middle", {"options": NOISY}), "C")
        self.assertIsNone(prior.apply_rule("middle", {"options": WORDS}))
        self.assertIsNone(prior.apply_rule("max", {"options": {}}))

    def test_letter_and_none_rules(self):
        self.assertEqual(prior.apply_rule("D", {"options": {}}), "D")
        self.assertEqual(prior.apply_rule("none_option", {"options": WORDS}), "E")
        self.assertIsNone(prior.apply_rule("none_option", {"options": NUMERIC}))
        self.assertIsNone(prior.apply_rule("none_option", {"options": {"A": "none", "B": "impossible", "C": "1", "D": "2", "E": "3"}}))
        self.assertIsNone(prior.apply_rule("unknown_rule", {"options": NUMERIC}))

    def test_default_letter_is_the_current_policy(self):
        self.assertEqual(prior.default_letter({"options": NUMERIC}), "E")
        self.assertEqual(prior.default_letter({"options": NOISY}, fallback="D"), "D")
        self.assertEqual(prior.default_letter({"options": WORDS}, fallback="B"), "B")


class ChooseTest(unittest.TestCase):
    def test_finest_stratification_first_then_fall_through(self):
        numeric_level2 = {"level": 2, "text_only": True, "options": NUMERIC}
        self.assertEqual(prior.choose(numeric_level2, TABLE), "A")  # max, from level/picture/kind
        self.assertIsNone(prior.choose({"level": 3, "text_only": True, "options": NUMERIC}, TABLE))  # no rule: the pipeline continues
        self.assertEqual(prior.choose({"level": 3, "text_only": True, "options": WORDS}, TABLE), "E")  # kind=words -> none_option
        self.assertIsNone(prior.choose({"level": 3, "text_only": True, "options": {**WORDS, "E": "a point"}}, TABLE))  # rule abstains
        self.assertEqual(prior.choose({"level": 7, "text_only": False, "options": NOISY}, TABLE), "C")
        self.assertIsNone(prior.choose({"options": NUMERIC}, TABLE))  # no level: the fine stratum is unknown, kind still is
        with mock.patch.object(prior, "PRIOR", None):
            self.assertIsNone(prior.choose(numeric_level2, None))  # None = the module's table, here none loaded
        self.assertIsNone(prior.choose(numeric_level2, {"stratifications": []}))


class CommittedTableTest(unittest.TestCase):
    def test_json_loads_holds_counts_only_and_matches_the_doc(self):
        table = prior.load()
        self.assertIsNotNone(table, "data_curated/option_prior.json is missing or malformed")
        self.assertEqual(table["learned_on"]["languages"], ["eng"])
        self.assertEqual(table["min_gain"], prior.MIN_GAIN)
        self.assertEqual(table["stratifications"][0]["dims"], ["level", "picture", "kind"])
        for stratification in table["stratifications"]:
            for key, row in stratification["strata"].items():
                self.assertEqual(set(row["letters"]), set("ABCDE"), key)
                self.assertEqual(sum(row["letters"].values()), row["n"], key)
                self.assertTrue(row["chosen"] is None or row["chosen"] in table["rules"], key)
                self.assertEqual(row["gain"], row["best_hits"] - row["default_hits"], key)
                if row["chosen"]:
                    self.assertGreaterEqual(row["gain"], table["min_gain"], key)
        # no problem text: every string in the file is a key, a rule or a short label
        with open(os.path.join(ROOT, prior.DEFAULT_PATH), encoding="utf-8") as f:
            data = json.load(f)

        def strings(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    yield k
                    yield from strings(v)
            elif isinstance(x, list):
                for v in x:
                    yield from strings(v)
            elif isinstance(x, str):
                yield x
        long_strings = [s for s in strings(data) if len(s) > 60 and not s.startswith("Learned option prior")]
        self.assertEqual(long_strings, [])
        # the numbers the documentation quotes
        self.assertEqual((table["train"]["default_hits"], table["validation"]["default_hits"]), (405, 77))

    def test_missing_file_gives_none(self):
        self.assertIsNone(prior.load(os.path.join(ROOT, "data_curated", "does_not_exist.json")))

    def test_pipeline_flag_off_by_default_and_the_hook_answers_when_on(self):
        from copilot import pipeline
        self.assertFalse(pipeline.USE_OPTION_PRIOR)
        problem = {"id": "x", "level": 2, "text_only": True, "text": "How many?", "options": NUMERIC}
        no_think = mock.patch.object(pipeline, "THINK_LEVELS", set())   # the brief-reasoning stage runs first on main
        no_pal = mock.patch.object(pipeline, "USE_PAL", False)
        no_pal.start(); self.addCleanup(no_pal.stop)
        with no_think, mock.patch.object(pipeline, "USE_OPTION_PRIOR", True), mock.patch.object(pipeline, "USE_SOLVERS", False), \
             mock.patch.object(prior, "PRIOR", TABLE):
            result = pipeline.solve(problem)
        self.assertEqual((result["answer"], result["rule"], result["status"], result["board_seconds"]), ("A", "option_prior", "ok", 0.0))
        with no_think, mock.patch.object(pipeline, "USE_OPTION_PRIOR", True), mock.patch.object(pipeline, "USE_SOLVERS", False), \
             mock.patch.object(prior, "PRIOR", TABLE):
            result = pipeline.solve({**problem, "level": 3})
        self.assertEqual((result["answer"], result["rule"]), ("E", "middle_value"))  # no rule: the middle value answers
        with no_think, mock.patch.object(pipeline, "USE_OPTION_PRIOR", False), mock.patch.object(pipeline, "USE_SOLVERS", False), \
             mock.patch.object(prior, "PRIOR", TABLE):
            result = pipeline.solve(problem)
        self.assertEqual((result["answer"], result["rule"]), ("E", "middle_value"))


if __name__ == "__main__":
    unittest.main()
