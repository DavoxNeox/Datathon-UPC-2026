"""Contract tests for INTERFACES.md: shapes every module must keep, stub or real."""
import unittest

from copilot import hints, retrieval, solvers, topics, trainer
from copilot.hal import led

LETTERS = set("ABCDE")


class TopicsTest(unittest.TestCase):
    def test_eight_topics_in_led_order(self):
        self.assertEqual(len(topics.TOPICS), 8)
        for t in topics.TOPICS:
            self.assertEqual(set(t), {"key", "name_ca", "name_en", "visual"})

    def test_get_topic_returns_known_key(self):
        self.assertIn(topics.get_topic("sample-1"), topics.TOPIC_KEYS)
        self.assertIn(topics.get_topic("unknown-id"), topics.TOPIC_KEYS)
        self.assertIsInstance(topics.is_visual("areas"), bool)


class RetrievalTest(unittest.TestCase):
    def test_neighbors_never_returns_itself(self):
        hits = retrieval.neighbors("sample-4", level_delta=-1, same_topic=True, lang="cat", k=3)
        self.assertLessEqual(len(hits), 3)
        for p in hits:
            self.assertNotEqual(p["id"], "sample-4")
            self.assertIn("text", p)
            self.assertIn("level", p)


class TrainerTest(unittest.TestCase):
    def test_next_problem_is_a_problem(self):
        p = trainer.next_problem("student-test")
        for key in ("id", "text", "options", "level", "language"):
            self.assertIn(key, p)

    def test_record_answer_shape(self):
        r = trainer.record_answer("student-test", "sample-4", "C", 0)
        self.assertEqual(set(r), {"correct", "label", "topic", "mastery_before", "mastery_after", "review"})
        self.assertTrue(r["correct"])

    def test_mastery_map_has_all_topics(self):
        m = trainer.mastery_map("student-test")
        self.assertEqual(set(m), set(topics.TOPIC_KEYS))
        for v in m.values():
            self.assertIn(v, range(6))


class SolversTest(unittest.TestCase):
    def test_solve_shape_or_none(self):
        self.assertIsNone(solvers.solve({"id": "sample-2", "text": "x", "options": {}}))
        r = solvers.solve({"id": "sample-1", "text": "x", "options": {}})
        self.assertTrue({"answer", "value", "family", "trace"} <= set(r))
        self.assertTrue(set(r) <= {"answer", "value", "family", "trace", "timings"})
        self.assertIn(r["answer"], LETTERS)
        self.assertGreaterEqual(len(r["trace"]), 2)
        for step in r["trace"]:
            self.assertIn("text_ca", step)
            self.assertIn("text_en", step)


class HintsTest(unittest.TestCase):
    def test_every_rung_has_bilingual_text(self):
        hints.prefetch("sample-4", "cat")
        for rung in (1, 2, 3, 4):
            h = hints.get_hint("sample-4", rung, "cat")
            self.assertEqual(h["rung"], rung)
            self.assertIn(h["kind"], {"neighbour", "strategy", "trace", "llm", "solution"})
            self.assertIn("text_ca", h)
            self.assertIn("text_en", h)
            self.assertIn("estimated_board_seconds", h)
        self.assertNotIn("label", hints.get_hint("sample-4", 1, "cat")["problem"] or {})


class LedTest(unittest.TestCase):
    def test_frames_are_8x13(self):
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            led.show_result(True)
            led.show_mastery(trainer.mastery_map("student-test"))
            led.show_path([[1, 1, 1], [1, 2, 3], [1, 3, 6]])
        frame = led.last_frame()
        self.assertEqual(len(frame), 8)
        self.assertTrue(all(len(row) == 13 for row in frame))
        self.assertEqual(frame[0][:3], [7, 7, 7])


if __name__ == "__main__":
    unittest.main()
