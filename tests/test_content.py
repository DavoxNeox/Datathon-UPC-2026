"""Content tests: data_curated/strategies.json and data_curated/demo_set.json.

Both files are read by the hint ladder and shown to the student, so they must be valid JSON,
bilingual, short where the UI needs them short, never give the answer of the problem they
belong to, and never copy M3Kang statements (the dataset is research-only; the repository
holds ids and our own words). The answer and anticopy checks need data/val.jsonl and
data/train.jsonl (symlinks to ~/m3kang-data); they are skipped when the data is not linked.
"""
import json
import os
import re
import unicodedata
import unittest

from copilot.leak_filter import leak_reason
from copilot.topics import TOPIC_KEYS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRATEGIES = os.path.join(ROOT, "data_curated", "strategies.json")
DEMO_SET = os.path.join(ROOT, "data_curated", "demo_set.json")
DATA_FILES = [os.path.join(ROOT, "data", name) for name in ("val.jsonl", "train.jsonl")]

MAX_STRATEGY_WORDS_CA = 15   # the card must be read in a glance on the student page
MAX_STRATEGY_WORDS_EN = 18   # English needs a few more function words
COPY_WINDOW = 12             # this many consecutive words equal to a statement = a copy
LETTERS = "ABCDE"
MANIPULATIVES = {"rotate", "paths", "dice"}
# "48cm", "27 cm²", "80 cm2", "4cm²2" -> "48", "27", "80", "4": the OCR glues a unit (and stray digits) to the value
_UNIT = re.compile(r"\s*(?:cm|dm|mm|km|m|kg|g|l|ml)[23²³]?\d?\s*$", re.I)


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _problems():
    """{id: {language: row}} from the linked data, {} when none is linked."""
    found = {}
    for path in DATA_FILES:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    found.setdefault(row["id"], {})[row["language"]] = row
    return found


def _words(text):
    """Lowercase words without accents or punctuation, for the anticopy comparison."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.findall(r"[a-z0-9]+", text)


def _copies(text, statement, window=COPY_WINDOW):
    """True when `window` consecutive words of text appear, in order, in statement."""
    words, source = _words(text), _words(statement)
    if len(words) < window or len(source) < window:
        return False
    grams = {tuple(source[i:i + window]) for i in range(len(source) - window + 1)}
    return any(tuple(words[i:i + window]) in grams for i in range(len(words) - window + 1))


def _clean_options(options):
    return {k: _UNIT.sub("", str(v)) for k, v in (options or {}).items()}


def _demo_texts(item, include_last_step=False):
    """(field, text) pairs of a demo problem that must not give its answer away."""
    out = []
    for key in ("figure_ca", "figure_en", "common_mistake_ca", "common_mistake_en", "why_in_demo"):
        if item.get(key):
            out.append((key, item[key]))
    steps = item.get("steps") or []
    for n, step in enumerate(steps if include_last_step else steps[:-1]):
        out.append((f"step {n + 1} ca", step.get("text_ca", "")))
        out.append((f"step {n + 1} en", step.get("text_en", "")))
    return out


class StrategiesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = _load_json(STRATEGIES)
        cls.cards = {k: v for k, v in cls.data.items() if not k.startswith("_")}

    def test_every_topic_has_bilingual_cards(self):
        self.assertEqual(set(self.cards), set(TOPIC_KEYS))
        for topic, cards in self.cards.items():
            self.assertGreaterEqual(len(cards), 3, topic)
            for card in cards:
                self.assertTrue(card.get("text_ca", "").strip(), (topic, card))
                self.assertTrue(card.get("text_en", "").strip(), (topic, card))
                self.assertNotEqual(card["text_ca"], card["text_en"], (topic, card))
                if "manipulative" in card:
                    self.assertIn(card["manipulative"], MANIPULATIVES, (topic, card))

    def test_cards_are_one_short_sentence(self):
        for topic, cards in self.cards.items():
            for card in cards:
                ca, en = card["text_ca"], card["text_en"]
                self.assertLessEqual(len(ca.split()), MAX_STRATEGY_WORDS_CA, (topic, ca))
                self.assertLessEqual(len(en.split()), MAX_STRATEGY_WORDS_EN, (topic, en))
                for text in (ca, en):
                    # one sentence: no full stop followed by a new sentence
                    self.assertFalse(re.search(r"[.!?]\s+[A-ZÀ-Ú]", text), (topic, text))

    def test_cards_never_announce_an_option(self):
        for topic, cards in self.cards.items():
            for card in cards:
                for text in (card["text_ca"], card["text_en"]):
                    self.assertIsNone(re.search(r"\b(opci[oó]|option)\s*[A-E]\b", text), (topic, text))
                    self.assertIsNone(re.search(r"(resposta|answer) (és|is)\b", text, re.I), (topic, text))


class DemoSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(DEMO_SET):
            raise unittest.SkipTest("data_curated/demo_set.json not written yet")
        cls.data = _load_json(DEMO_SET)
        cls.problems = cls.data.get("problems", [])
        cls.known = _problems()

    def test_shape_is_bilingual_and_marked(self):
        self.assertTrue(self.problems)
        ids = [p["id"] for p in self.problems]
        self.assertEqual(len(ids), len(set(ids)), "duplicate ids")
        for item in self.problems:
            tag = item["id"]
            self.assertRegex(tag, r"^lvl-\d_\d{4}_\d+$")
            self.assertIn(item.get("topic"), TOPIC_KEYS, tag)
            self.assertIn(item.get("status"), ("draft", "reviewed"), tag)
            for key in ("figure_ca", "figure_en", "common_mistake_ca", "common_mistake_en"):
                self.assertTrue(item.get(key, "").strip(), (tag, key))
            steps = item.get("steps") or []
            self.assertTrue(3 <= len(steps) <= 5, (tag, len(steps)))
            for step in steps:
                self.assertTrue(step.get("text_ca", "").strip(), tag)
                self.assertTrue(step.get("text_en", "").strip(), tag)
        for key in ("demo_core", "demo_reserve"):
            for pid in self.data.get(key, []):
                self.assertIn(pid, ids, f"{key}: {pid} is not described")

    def test_no_text_gives_the_answer_before_the_last_step(self):
        if not self.known:
            self.skipTest("data/val.jsonl and data/train.jsonl not linked")
        for item in self.problems:
            rows = self.known.get(item["id"])
            self.assertIsNotNone(rows, f"{item['id']} not in the data")
            row = rows.get("eng") or next(iter(rows.values()))
            label = row["label"]
            options = _clean_options(row.get("options") or rows.get("cat", {}).get("options"))
            for field, text in _demo_texts(item):
                self.assertIsNone(leak_reason(text, label, options), (item["id"], field, text))
            last = item["steps"][-1]
            self.assertRegex(last["text_ca"] + " " + last["text_en"], rf"(?i)\b(opció|option)\s*{label}\b",
                             f"{item['id']}: the last step should name option {label}")

    def test_option_values_stay_out_of_the_texts(self):
        """Licence rule: no distractor value anywhere; the correct value only in the last step."""
        if not self.known:
            self.skipTest("data/val.jsonl and data/train.jsonl not linked")
        for item in self.problems:
            rows = self.known.get(item["id"], {})
            row = rows.get("eng") or next(iter(rows.values()))
            options = _clean_options(row.get("options") or rows.get("cat", {}).get("options"))
            label = row["label"]
            values = {letter: re.sub(r"\s+", "", v) for letter, v in options.items() if re.fullmatch(r"[\d\s./,]+", v or "")}
            texts = _demo_texts(item, include_last_step=True)
            last_fields = {f"step {len(item['steps'])} ca", f"step {len(item['steps'])} en"}
            for field, text in texts:
                for letter, value in values.items():
                    if letter == label and field in last_fields:
                        continue
                    pattern = r"(?<![\d.,/])" + re.escape(value) + r"(?![\d.,/]|\s*[×x·])"
                    self.assertIsNone(re.search(pattern, text), (item["id"], field, f"option {letter} = {value}", text))

    def test_no_field_copies_the_statement(self):
        if not self.known:
            self.skipTest("data/val.jsonl and data/train.jsonl not linked")
        for item in self.problems:
            for row in self.known.get(item["id"], {}).values():
                for field, text in _demo_texts(item, include_last_step=True):
                    self.assertFalse(_copies(text, row["text"]), (item["id"], field, row["language"]))

    def test_strategies_do_not_copy_statements_either(self):
        # cheap sanity check over the whole dataset: a strategy is generic, it can never match a statement
        if not self.known:
            self.skipTest("data/val.jsonl and data/train.jsonl not linked")
        cards = [c for k, v in _load_json(STRATEGIES).items() if not k.startswith("_") for c in v]
        texts = [c["text_ca"] for c in cards] + [c["text_en"] for c in cards]
        for rows in self.known.values():
            for row in rows.values():
                for text in texts:
                    self.assertFalse(_copies(text, row["text"]), (row["id"], text))


if __name__ == "__main__":
    unittest.main()
