"""Empirical difficulty per class (copilot/difficulty.py) on a temporary trainer database."""
import json
import os
import tempfile
import unittest

from copilot import difficulty, trainer
from copilot.simulate import make_synthetic_neighbors, synthetic_problems


class DifficultyDbTest(unittest.TestCase):
    """Answers written through trainer.record_answer, read back by difficulty.estimate."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "students.db")
        self.problems = synthetic_problems()
        self.by_id = {p["id"]: p for p in self.problems}
        trainer.configure(db_path=self.db, problems=self.problems,
                          neighbors_fn=make_synthetic_neighbors(self.problems))
        self.adjust = trainer.DIFFICULTY_ADJUST
        trainer.DIFFICULTY_ADJUST = False

    def tearDown(self):
        trainer.DIFFICULTY_ADJUST = self.adjust
        trainer.configure()
        self.tmp.cleanup()

    def answer(self, student, problem_id, correct, rung=0):
        label = self.by_id[problem_id]["label"]
        letter = label if correct else ("A" if label != "A" else "B")
        return trainer.record_answer(student, problem_id, letter, rung)

    def test_no_database_means_no_estimates(self):
        self.assertEqual(difficulty.estimate(self.db), {})
        self.assertEqual(difficulty.estimate(os.path.join(self.tmp.name, "missing.db")), {})
        self.assertEqual(difficulty.report(self.db)["answers"], 0)

    def test_shrinkage_formula_and_raw_rates(self):
        # Level 3: four misses on one problem, four hits on another, one hinted hit on a third
        for s in "abcd":
            self.answer(s, "syn-logic-3-0", correct=False)
            self.answer(s, "syn-logic-3-1", correct=True)
        self.answer("a", "syn-logic-3-2", correct=True, rung=2)
        est = difficulty.estimate(self.db)
        a = difficulty.PRIOR_WEIGHT
        prior = (5 + a * 0.5) / (9 + a)              # the level's rate, shrunk towards 0.5
        hard = est["syn-logic-3-0"]
        self.assertEqual(hard["n"], 4)
        self.assertEqual(hard["p_correct"], 0.0)
        self.assertAlmostEqual(hard["prior"], prior)
        self.assertAlmostEqual(hard["shrunk"], (0 + a * prior) / (4 + a))
        self.assertGreater(hard["shrunk"], 0.0)       # never "impossible" after a few misses
        easy = est["syn-logic-3-1"]
        self.assertAlmostEqual(easy["shrunk"], (4 + a * prior) / (4 + a))
        self.assertLess(easy["shrunk"], 1.0)
        hinted = est["syn-logic-3-2"]
        self.assertEqual(hinted["p_correct"], 1.0)
        self.assertEqual(hinted["p_without_hints"], 0.0)   # correct, but after a hint

    def test_prior_is_half_when_the_level_has_no_other_data(self):
        self.answer("a", "syn-areas-6-0", correct=False)
        est = difficulty.estimate(self.db)
        a = difficulty.PRIOR_WEIGHT
        # The only answer at level 6 is this one: prior_6 = (0 + a/2) / (1 + a)
        self.assertAlmostEqual(est["syn-areas-6-0"]["prior"], (a * 0.5) / (1 + a))
        self.assertEqual(difficulty.level_priors([]), {})
        self.assertEqual(difficulty.adjusted_level({"id": "x", "level": 2}, {"x": {"n": 9, "shrunk": 0.1, "prior": 0.5}}), 3.6)

    def test_adjusted_level_moves_hard_up_and_easy_down(self):
        for s in "abcd":
            self.answer(s, "syn-logic-3-0", correct=False)
            self.answer(s, "syn-logic-3-1", correct=True)
        est = difficulty.estimate(self.db)
        hard = difficulty.adjusted_level(self.by_id["syn-logic-3-0"], est)
        easy = difficulty.adjusted_level(self.by_id["syn-logic-3-1"], est)
        self.assertGreater(hard, 3.0)
        self.assertLess(easy, 3.0)
        self.assertLessEqual(hard - 3.0, difficulty.MAX_SHIFT)
        self.assertLessEqual(3.0 - easy, difficulty.MAX_SHIFT)
        # The documented mapping, by hand
        e = est["syn-logic-3-0"]
        self.assertAlmostEqual(hard, 3.0 + min(difficulty.MAX_SHIFT, (e["prior"] - e["shrunk"]) / difficulty.POINTS_PER_LEVEL))

    def test_fewer_than_min_n_answers_keep_the_m3kang_level(self):
        for s in "ab":
            self.answer(s, "syn-digits-4-0", correct=False)
        for s in "abcdefgh":
            self.answer(s, "syn-digits-4-1", correct=True)   # makes the level look easy
        est = difficulty.estimate(self.db)
        self.assertEqual(est["syn-digits-4-0"]["n"], 2)
        self.assertEqual(difficulty.adjusted_level(self.by_id["syn-digits-4-0"], est), 4.0)
        self.assertLess(difficulty.adjusted_level(self.by_id["syn-digits-4-1"], est), 4.0)
        # With a stricter minimum the easy one is not adjusted either
        self.assertEqual(difficulty.adjusted_level(self.by_id["syn-digits-4-1"], est, min_n=20), 4.0)

    def test_problem_without_data_keeps_its_level_as_a_float(self):
        self.answer("a", "syn-logic-3-0", correct=False)
        est = difficulty.estimate(self.db)
        self.assertEqual(difficulty.adjusted_level(self.by_id["syn-spatial-5-3"], est), 5.0)
        self.assertEqual(difficulty.adjusted_level({"id": "unknown", "level": 9}, est), 7.0)
        self.assertEqual(difficulty.adjusted_level({"id": "unknown"}, {}), 0.0)

    def test_shift_is_clipped_and_the_result_stays_in_range(self):
        # A level-0 problem nobody gets right while the level is otherwise easy
        for s in "abcdefghij":
            self.answer(s, "syn-counting-0-0", correct=False)
            self.answer(s, "syn-counting-0-1", correct=True)
            self.answer(s, "syn-counting-0-2", correct=True)
        est = difficulty.estimate(self.db)
        self.assertEqual(difficulty.adjusted_level(self.by_id["syn-counting-0-0"], est), 0.0 + difficulty.MAX_SHIFT)
        self.assertGreaterEqual(difficulty.adjusted_level(self.by_id["syn-counting-0-1"], est), 0.0)

    def test_report_is_serialisable_bilingual_and_ids_only(self):
        for i in range(12):
            for s in "abc":
                self.answer(s, f"syn-arithmetic-2-{i % 6}", correct=(i % 3 == 0))
        for s in "abc":
            self.answer(s, "syn-angles-7-0", correct=False)
        self.answer("a", "syn-boards-1-0", correct=True)     # n=1: never listed
        rep = difficulty.report(self.db)
        text = json.dumps(rep, ensure_ascii=False)
        back = json.loads(text)
        self.assertEqual(back["answers"], 40)
        self.assertEqual(back["problems_seen"], 8)
        self.assertEqual(back["problems_rated"], 7)
        self.assertLessEqual(len(back["hardest"]), difficulty.TOP)
        self.assertLessEqual(len(back["easiest"]), difficulty.TOP)
        listed = {r["id"] for r in back["hardest"]} | {r["id"] for r in back["easiest"]}
        self.assertNotIn("syn-boards-1-0", listed)
        shrunk = [r["shrunk"] for r in back["hardest"]]
        self.assertEqual(shrunk, sorted(shrunk))
        self.assertEqual(back["hardest"][0]["p_correct"], 0.0)
        self.assertIn("syn-angles-7-0", {r["id"] for r in back["hardest"]})
        self.assertEqual(back["easiest"][0]["shrunk"], max(r["shrunk"] for r in back["easiest"]))
        for row in back["hardest"] + back["easiest"]:
            self.assertEqual(set(row), {"id", "level", "n", "p_correct", "p_without_hints", "shrunk", "prior", "adjusted_level"})
            self.assertNotIn("text", row)
        levels = {r["level"] for r in back["by_level"]}
        self.assertEqual(levels, {1, 2, 7})
        for key, label in back["labels"].items():
            self.assertEqual(set(label), {"ca", "en"}, key)
            self.assertTrue(label["ca"] and label["en"], key)
        for key in ("hardest", "easiest", "by_level", "n", "p_correct", "p_without_hints", "shrunk", "adjusted_level"):
            self.assertIn(key, back["labels"])

    def test_estimate_does_not_create_or_write_the_database(self):
        before = os.path.exists(self.db)
        difficulty.estimate(self.db)
        difficulty.report(self.db)
        self.assertEqual(os.path.exists(self.db), before)
        self.answer("a", "syn-logic-3-0", correct=False)
        stamp = os.path.getmtime(self.db)
        difficulty.report(self.db)
        self.assertEqual(os.path.getmtime(self.db), stamp)


class TrainerHookTest(unittest.TestCase):
    """DIFFICULTY_ADJUST=1: the adaptive rule reads the class's empirical level; off by default."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "students.db")
        self.problems = synthetic_problems()
        self.by_id = {p["id"]: p for p in self.problems}
        trainer.configure(db_path=self.db, problems=self.problems,
                          neighbors_fn=make_synthetic_neighbors(self.problems))
        self.adjust, self.review = trainer.DIFFICULTY_ADJUST, trainer.REVIEW_RATE
        trainer.REVIEW_RATE = 0.0

    def tearDown(self):
        trainer.DIFFICULTY_ADJUST, trainer.REVIEW_RATE = self.adjust, self.review
        trainer.configure()
        self.tmp.cleanup()

    def make_class(self):
        """Ten students miss syn-logic-3-0 while level 3 is otherwise answered well."""
        for s in "abcdefghij":
            trainer.record_answer(s, "syn-logic-3-0", "Z", 0)
            trainer.record_answer(s, "syn-logic-3-1", self.by_id["syn-logic-3-1"]["label"], 0)
            trainer.record_answer(s, "syn-logic-3-2", self.by_id["syn-logic-3-2"]["label"], 0)

    def test_flag_is_off_by_default_in_config(self):
        from copilot.config import CONFIG
        self.assertEqual(os.environ.get("DIFFICULTY_ADJUST", CONFIG.get("DIFFICULTY_ADJUST", "0")), "0")

    def test_level_of_is_the_m3kang_level_when_off(self):
        self.make_class()
        trainer.DIFFICULTY_ADJUST = False
        self.assertEqual(trainer._level_of("syn-logic-3-0", 3), 3)

    def test_level_of_is_adjusted_when_on(self):
        self.make_class()
        trainer.DIFFICULTY_ADJUST = True
        est = difficulty.estimate(self.db)
        self.assertEqual(trainer._level_of("syn-logic-3-0", 3), difficulty.adjusted_level(self.by_id["syn-logic-3-0"], est))
        self.assertGreater(trainer._level_of("syn-logic-3-0", 3), 3)
        self.assertEqual(trainer._level_of("syn-logic-3-5", 3), 3)   # no data: unchanged

    def test_wrong_answer_on_a_hard_problem_steps_down_from_its_empirical_level(self):
        self.make_class()
        trainer.DIFFICULTY_ADJUST = True
        est = difficulty.estimate(self.db)
        hard = difficulty.adjusted_level(self.by_id["syn-logic-3-0"], est)   # about 4.4
        # A new student answers it wrong on the main path: the next problem is one level
        # below the EMPIRICAL level (4 -> 3), not below the M3Kang level (3 -> 2)
        trainer.start_student("new", level=3)
        for _ in range(3):                      # diagnostic: 3 misses, base level 2
            p = trainer.next_problem("new")
            trainer.record_answer("new", p["id"], "Z", 0)
        db = trainer._connect()
        db.execute("INSERT INTO answers (student_id, problem_id, topic, level, letter, label, correct, hint_rung, review, created_at) "
                   "VALUES ('new', 'syn-logic-3-0', 'logic', 3, 'Z', 'A', 0, 0, 0, 1.0)")
        db.commit()
        db.close()
        nxt = trainer.next_problem("new")
        self.assertEqual(nxt["topic"], "logic")
        self.assertEqual(nxt["level"], max(0, min(7, round(hard) - 1)))
        trainer.DIFFICULTY_ADJUST = False
        trainer.start_student("plain", level=3)
        for _ in range(3):
            p = trainer.next_problem("plain")
            trainer.record_answer("plain", p["id"], "Z", 0)
        db = trainer._connect()
        db.execute("INSERT INTO answers (student_id, problem_id, topic, level, letter, label, correct, hint_rung, review, created_at) "
                   "VALUES ('plain', 'syn-logic-3-0', 'logic', 3, 'Z', 'A', 0, 0, 0, 1.0)")
        db.commit()
        db.close()
        self.assertEqual(trainer.next_problem("plain")["level"], 2)


if __name__ == "__main__":
    unittest.main()
