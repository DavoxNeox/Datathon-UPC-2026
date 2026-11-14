"""copilot/topics.py: the id -> topic table and the visual flags."""
import json
import os
import unittest

from copilot import topics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_JSON = os.path.join(ROOT, "data_curated", "topics.json")


class TopicsTableTest(unittest.TestCase):
    def test_table_is_committed_and_holds_only_ids_and_keys(self):
        self.assertTrue(os.path.exists(TOPICS_JSON), "data_curated/topics.json missing: run laptop/build_topics.py")
        with open(TOPICS_JSON, encoding="utf-8") as f:
            data = json.load(f)
        table = data["topics"]
        self.assertGreater(len(table), 1000, "every M3Kang id should have a topic")
        for pid, key in table.items():
            self.assertRegex(pid, r"^lvl-\d_\d{4}_\d+$", "keys are M3Kang ids, never text")
            self.assertIn(key, topics.TOPIC_KEYS)
        self.assertEqual(set(data["visual"]), set(topics.TOPIC_KEYS))

    def test_every_topic_is_used(self):
        for key, n in topics.counts().items():
            self.assertGreater(n, 0, f"topic {key} has no problems")

    def test_get_topic_reads_the_table_and_falls_back(self):
        with open(TOPICS_JSON, encoding="utf-8") as f:
            table = json.load(f)["topics"]
        pid, key = next(iter(table.items()))
        self.assertEqual(topics.get_topic(pid), key)
        self.assertEqual(topics.get_topic("no-such-problem"), "arithmetic")
        self.assertEqual(topics.get_topic("sample-3"), "areas")

    def test_visual_flags_match_the_table(self):
        with open(TOPICS_JSON, encoding="utf-8") as f:
            flags = json.load(f)["visual"]
        for key in topics.TOPIC_KEYS:
            self.assertEqual(topics.is_visual(key), flags[key])
        self.assertTrue(topics.is_visual("spatial"))
        self.assertFalse(topics.is_visual("arithmetic"))
        self.assertIsInstance(topics.is_visual("unknown-topic"), bool)

    def test_names_are_bilingual(self):
        self.assertEqual(topics.topic_name("angles", "cat"), "Angles")
        self.assertEqual(topics.topic_name("boards", "eng"), "Boards and patterns")


if __name__ == "__main__":
    unittest.main()
