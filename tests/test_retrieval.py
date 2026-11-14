"""copilot/retrieval.py: level order, fallback without an index, and real searches when data/index.db exists."""
import os
import unittest

from copilot import retrieval, topics

HAS_INDEX = os.path.exists(retrieval.INDEX_DB)
HAS_VAL = os.path.exists(retrieval.TEXT_FILES[0])


class LevelOrderTest(unittest.TestCase):
    def test_target_first_then_nearest_ties_down(self):
        self.assertEqual(retrieval._level_order(3, prefer_lower=True), [3, 2, 4, 1, 5, 0, 6, 7])
        self.assertEqual(retrieval._level_order(3, prefer_lower=False), [3, 4, 2, 5, 1, 6, 0, 7])

    def test_target_is_clipped_to_0_7(self):
        self.assertEqual(retrieval._level_order(-2, True)[0], 0)
        self.assertEqual(retrieval._level_order(9, False)[0], 7)


class FallbackTest(unittest.TestCase):
    def test_unknown_id_serves_sample_problems_in_lang(self):
        hits = retrieval.neighbors("sample-4", level_delta=-1, lang="cat", k=3)
        self.assertTrue(hits)
        for p in hits:
            self.assertNotEqual(p["id"], "sample-4")
            self.assertEqual(p["language"], "cat")

    def test_k_zero_returns_nothing(self):
        self.assertEqual(retrieval.neighbors("sample-4", k=0), [])


@unittest.skipUnless(HAS_INDEX, "data/index.db not built")
class IndexSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = retrieval._catalog()
        cls.train_id = cls.catalog.english[0][0]

    def test_train_id_needs_no_embedding(self):
        vec, level, embeds = retrieval.query_vector(self.train_id, self.catalog)
        self.assertEqual(embeds, 0)
        self.assertEqual(len(vec), 384)

    def test_neighbors_are_in_lang_same_topic_one_level_down_and_never_itself(self):
        pid = next(i for i, lvl, _t, _v in self.catalog.english if lvl >= 2)
        level = next(lvl for i, lvl, _t, _v in self.catalog.english if i == pid)
        hits = retrieval.neighbors(pid, level_delta=-1, same_topic=True, lang="cat", k=3)
        self.assertTrue(hits)
        self.assertLessEqual(len(hits), 3)
        topic = topics.get_topic(pid)
        for p in hits:
            self.assertNotEqual(p["id"], pid)
            self.assertEqual(p["language"], "cat")
            self.assertEqual(p["level"], level - 1)
            self.assertEqual(p["topic"], topic)
            self.assertIn("text", p)
        sims = [p["similarity"] for p in hits]
        self.assertEqual(sims, sorted(sims, reverse=True))

    def test_level_below_zero_falls_to_nearest_level_with_candidates(self):
        pid = next(i for i, lvl, _t, _v in self.catalog.english if lvl == 0)
        hits = retrieval.neighbors(pid, level_delta=-1, same_topic=False, lang="eng", k=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["level"], 0)

    def test_any_topic_scores_at_least_as_high(self):
        pid = self.train_id
        same = retrieval.neighbors(pid, 0, True, "eng", 1)
        free = retrieval.neighbors(pid, 0, False, "eng", 1)
        self.assertGreaterEqual(free[0]["similarity"], same[0]["similarity"])

    @unittest.skipUnless(HAS_VAL, "data/val.jsonl missing")
    def test_val_id_is_embedded_once_and_cached(self):
        import json
        with open(retrieval.TEXT_FILES[0], encoding="utf-8") as f:
            row = next(json.loads(l) for l in f if '"eng"' in l)
        retrieval._QUERY_CACHE.pop(row["id"], None)
        hits = retrieval.neighbors(row["id"], 0, True, "cat", 2)
        self.assertTrue(hits)
        self.assertIn(row["id"], retrieval._QUERY_CACHE)
        self.assertEqual(retrieval._QUERY_CACHE[row["id"]][2], 1)
        for p in hits:
            self.assertNotEqual(p["id"], row["id"])


if __name__ == "__main__":
    unittest.main()
