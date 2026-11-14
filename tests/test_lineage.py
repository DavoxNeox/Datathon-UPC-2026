"""copilot/lineage.py on a small synthetic index: order by level, never itself, never the label, the LED frame."""
import json
import math
import os
import sqlite3
import tempfile
import unittest
from array import array
from unittest import mock

from copilot import lineage, retrieval

DIMS = 384

# Synthetic problems: id -> (level, year, topic, direction). Problems that share a direction
# are "the same idea"; a small per-problem wobble makes the similarities distinct.
SYNTH = {
    "syn-0": (0, 2010, "areas", 0),
    "syn-1": (1, 2012, "areas", 0),
    "syn-2": (2, 2014, "areas", 0),
    "syn-3": (3, 2016, "areas", 0),
    "syn-5": (5, 2018, "areas", 0),
    "syn-7": (7, 2020, "areas", 0),
    "syn-7b": (7, 2021, "areas", 1),        # same topic, another idea: far away
    "syn-4-digits": (4, 2015, "digits", 0),  # same idea, other topic: never a link
    "syn-3-far": (3, 2008, "areas", 2),      # same topic and level as syn-3 but another idea
}
TOPIC_OF = {pid: row[2] for pid, row in SYNTH.items()}
QUERY = "syn-3"


def _vector(direction, wobble):
    """A unit vector near axis `direction`, tilted by `wobble` towards axis 100 + direction."""
    vec = [0.0] * DIMS
    vec[direction] = math.cos(wobble)
    vec[100 + direction] = math.sin(wobble)
    return vec


def _build_index(path):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE problems (key TEXT PRIMARY KEY, problem TEXT NOT NULL, vec BLOB NOT NULL)")
    for i, (pid, (level, year, _topic, direction)) in enumerate(sorted(SYNTH.items())):
        vec = _vector(direction, 0.05 * i)
        for lang in ("eng", "cat"):
            problem = {"id": pid, "language": lang, "level": level, "year": year, "text_only": True,
                       "text": f"{lang} text of {pid}", "options": {"A": "1", "B": "2"}, "label": "B"}
            db.execute("INSERT INTO problems VALUES (?, ?, ?)",
                       (f"{pid}|{lang}", json.dumps(problem), array("f", vec).tobytes()))
    db.commit()
    db.close()


def _fake_topic(problem_id):
    return TOPIC_OF.get(problem_id, "arithmetic")


class LineageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = os.path.join(cls.tmp.name, "index.db")
        _build_index(db)
        with mock.patch.object(retrieval, "get_topic", _fake_topic):
            cls.catalog = retrieval.Catalog(db)
        cls.patch = mock.patch.object(lineage, "get_topic", _fake_topic)
        cls.patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tmp.cleanup()

    def chain(self, **kw):
        kw.setdefault("lang", "cat")
        kw.setdefault("min_similarity", 0.6)
        return lineage.lineage(QUERY, catalog=self.catalog, **kw)

    def test_one_link_per_other_level_sorted_easiest_first(self):
        chain = self.chain(max_links=8)
        self.assertEqual([link["level"] for link in chain], [0, 1, 2, 5, 7])
        self.assertEqual(len({link["level"] for link in chain}), len(chain))

    def test_never_itself_nor_its_own_level_nor_another_topic(self):
        ids = {link["id"] for link in self.chain(max_links=8)}
        self.assertNotIn(QUERY, ids)
        self.assertNotIn("syn-3-far", ids)       # same level as the query
        self.assertNotIn("syn-4-digits", ids)    # same idea, other topic
        self.assertNotIn("syn-7b", ids)          # same topic, another idea (below the threshold)
        self.assertIn("syn-7", ids)

    def test_links_carry_the_contract_fields_and_never_the_label(self):
        for link in self.chain(max_links=8):
            for key in ("id", "level", "year", "topic", "similarity", "text"):
                self.assertIn(key, link)
            self.assertNotIn("label", link)
            self.assertEqual(link["topic"], "areas")
            self.assertEqual(link["language"], "cat")
            self.assertTrue(link["text"].startswith("cat text of"))
            self.assertGreaterEqual(link["similarity"], 0.6)
            self.assertLessEqual(link["similarity"], 1.0)

    def test_language_falls_back_to_english(self):
        chain = self.chain(max_links=2, lang="eng")
        self.assertTrue(all(link["language"] == "eng" for link in chain))

    def test_threshold_cuts_the_chain(self):
        full = self.chain(max_links=8, min_similarity=0.0)
        strict = self.chain(max_links=8, min_similarity=0.99)
        self.assertEqual([link["level"] for link in full], [0, 1, 2, 5, 7])  # one per level: syn-7b loses to syn-7
        self.assertEqual(full[-1]["id"], "syn-7")
        self.assertLess(len(strict), len(full))
        self.assertTrue(all(link["similarity"] >= 0.99 for link in strict))
        self.assertEqual(self.chain(max_links=8, min_similarity=1.01), [])

    def test_max_links_keeps_the_most_similar_then_sorts_by_level(self):
        chain = self.chain(max_links=2)
        self.assertEqual(len(chain), 2)
        self.assertEqual([link["level"] for link in chain], sorted(link["level"] for link in chain))
        best = sorted((link["similarity"] for link in self.chain(max_links=8)), reverse=True)[:2]
        self.assertEqual(sorted((link["similarity"] for link in chain), reverse=True), best)
        self.assertEqual(self.chain(max_links=0), [])

    def test_unknown_id_or_no_index_gives_an_empty_chain(self):
        self.assertEqual(lineage.lineage("nobody", catalog=self.catalog), [])
        with mock.patch.object(retrieval, "_catalog", lambda: None):
            self.assertEqual(lineage.lineage("syn-3"), [])

    def test_embeddings_needed(self):
        self.assertEqual(lineage.embeddings_needed(QUERY, catalog=self.catalog), 0)
        self.assertEqual(lineage.embeddings_needed("lvl-9_2099_1", catalog=self.catalog), 1)


class LedFrameTest(unittest.TestCase):
    CHAIN = [{"level": 1, "similarity": 0.84}, {"level": 3, "similarity": 0.62}, {"level": 7, "similarity": 1.0}]

    def test_frame_is_8_by_13_with_brightness_0_to_7(self):
        frame = lineage.led_frame(self.CHAIN, 4)
        self.assertEqual(len(frame), 8)
        self.assertTrue(all(len(row) == 13 for row in frame))
        self.assertTrue(all(0 <= v <= 7 for row in frame for v in row))

    def test_current_level_is_the_brightest_full_row(self):
        frame = lineage.led_frame(self.CHAIN, 4)
        self.assertEqual(frame[4], [lineage.CURRENT_BRIGHTNESS] * 13)
        others = [v for r, row in enumerate(frame) if r != 4 for v in row]
        self.assertLess(max(others), lineage.CURRENT_BRIGHTNESS)

    def test_links_light_a_bar_that_grows_with_similarity_and_other_rows_stay_dark(self):
        frame = lineage.led_frame(self.CHAIN, 4)
        lit = {r: sum(1 for v in row if v) for r, row in enumerate(frame)}
        self.assertEqual(lit[7], 13)
        self.assertGreater(lit[1], lit[3])
        self.assertGreaterEqual(lit[3], 1)
        for r in (0, 2, 5, 6):
            self.assertEqual(lit[r], 0)
        self.assertTrue(all(v == lineage.LINK_BRIGHTNESS for v in frame[1][:lit[1]]))

    def test_empty_chain_and_odd_input(self):
        frame = lineage.led_frame([], 2)
        self.assertEqual(sum(v for row in frame for v in row), 13 * lineage.CURRENT_BRIGHTNESS)
        frame = lineage.led_frame([{"level": 9, "similarity": 0.9}, {"level": 0, "similarity": -3}], -1)
        self.assertEqual(len(frame), 8)
        self.assertEqual(sum(1 for v in frame[0] if v), 1)
        self.assertEqual(sum(v for row in frame[1:] for v in row), 0)


if __name__ == "__main__":
    unittest.main()
