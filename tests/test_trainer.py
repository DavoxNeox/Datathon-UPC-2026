"""The adaptive trainer's rules, on a temporary SQLite file and a synthetic problem bank."""
import os
import tempfile
import unittest

from copilot import trainer
from copilot.simulate import make_synthetic_neighbors, synthetic_problems
from copilot.topics import TOPIC_KEYS


def hit(problem_id="p1", level=2, rung=0, correct=True):
    return {"problem_id": problem_id, "level": level, "hint_rung": rung, "correct": correct}


class DeriveMasteryTest(unittest.TestCase):
    """Mastery 0..5 from the history on one topic (INTERFACES.md table)."""

    def test_no_data_is_zero(self):
        self.assertEqual(trainer.derive_mastery([], base_level=2), 0)

    def test_always_fails_is_one(self):
        self.assertEqual(trainer.derive_mastery([hit("a", correct=False), hit("b", correct=False)], 2), 1)

    def test_one_correct_is_two_not_three(self):
        self.assertEqual(trainer.derive_mastery([hit("a", rung=0)], 2), 2)
        self.assertEqual(trainer.derive_mastery([hit("a", rung=2)], 2), 2)

    def test_two_hits_need_one_without_hints(self):
        with_hints = [hit("a", rung=1), hit("b", rung=2)]
        self.assertEqual(trainer.derive_mastery(with_hints, 2), 2)
        one_clean = [hit("a", rung=1), hit("b", rung=0)]
        self.assertEqual(trainer.derive_mastery(one_clean, 2), 3)

    def test_two_hits_must_be_independent_problems(self):
        self.assertEqual(trainer.derive_mastery([hit("a", rung=0), hit("a", rung=0)], 2), 2)

    def test_correct_after_solution_never_counts(self):
        self.assertEqual(trainer.derive_mastery([hit("a", rung=4), hit("b", rung=3)], 2), 1)
        self.assertEqual(trainer.derive_mastery([hit("a", rung=0), hit("b", rung=3)], 2), 2)

    def test_three_clean_in_a_row_is_four(self):
        history = [hit("a", 2), hit("b", 2), hit("c", 2)]
        self.assertEqual(trainer.derive_mastery(history, base_level=2), 4)

    def test_one_level_above_base_is_five(self):
        history = [hit("a", 2), hit("b", 3), hit("c", 2)]
        self.assertEqual(trainer.derive_mastery(history, base_level=2), 5)
        self.assertEqual(trainer.derive_mastery(history, base_level=3), 4)

    def test_half_the_window_must_be_correct_for_three(self):
        history = [hit("a", correct=False), hit("b", correct=False), hit("c", correct=False),
                   hit("d", correct=False), hit("e"), hit("f")]
        self.assertEqual(trainer.derive_mastery(history, 2), 2)

    def test_target_level_mapping_is_explicit(self):
        self.assertEqual([trainer.target_level(3, m) for m in range(6)], [3, 1, 2, 3, 4, 5])
        self.assertEqual(trainer.target_level(0, 1), 0)
        self.assertEqual(trainer.target_level(7, 5), 7)


class TrainerDbTest(unittest.TestCase):
    """End to end on a temporary database and the synthetic bank (8 topics x 8 levels)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "students.db")
        self.problems = synthetic_problems()
        trainer.configure(db_path=self.db, problems=self.problems,
                          neighbors_fn=make_synthetic_neighbors(self.problems))
        self.review_rate = trainer.REVIEW_RATE
        trainer.REVIEW_RATE = 0.0   # the review tests set it themselves

    def tearDown(self):
        trainer.REVIEW_RATE = self.review_rate
        trainer.configure()
        self.tmp.cleanup()

    def play(self, student, steps, answer):
        """answer(problem) -> (letter, rung). Returns the list of (problem, result)."""
        log = []
        for _ in range(steps):
            p = trainer.next_problem(student)
            letter, rung = answer(p)
            log.append((p, trainer.record_answer(student, p["id"], letter, rung)))
        return log

    @staticmethod
    def threshold(n):
        return lambda p: ((p["label"] if p["level"] <= n else "ABCDE"[("ABCDE".index(p["label"]) + 1) % 5]), 0)

    def test_db_file_is_created_at_the_configured_path(self):
        trainer.next_problem("s")
        self.assertTrue(os.path.exists(self.db))
        self.assertFalse(os.path.exists(trainer.DEFAULT_DB) and self.db == trainer.DEFAULT_DB)

    def test_same_problem_until_answered(self):
        a = trainer.next_problem("s")
        b = trainer.next_problem("s")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(a["language"], "cat")

    def test_diagnostic_is_three_to_five_increasing_levels(self):
        log = self.play("s", 5, self.threshold(3))
        levels = [p["level"] for p, _ in log]
        # 0 ok, 2 ok, 4 wrong: three answers, done; base level 2
        self.assertEqual(levels[:3], [0, 2, 4])
        report = trainer.teacher_report("s")["students"][0]
        self.assertTrue(report["diagnostic_done"])
        self.assertEqual(report["base_level"], 2)
        log = self.play("perfect", 6, lambda p: (p["label"], 0))
        self.assertEqual([p["level"] for p, _ in log][:5], [0, 2, 4, 6, 7])
        self.assertEqual(trainer.teacher_report("perfect")["students"][0]["base_level"], 7)

    def test_correct_goes_one_level_up_and_wrong_stays_on_topic_one_level_down(self):
        log = self.play("s", 20, self.threshold(3))
        for (p, r), (q, _) in list(zip(log, log[1:]))[3:]:   # after the diagnostic
            if r["correct"]:
                self.assertEqual(q["level"], min(7, p["level"] + 1))
            else:
                self.assertEqual(q["level"], max(0, p["level"] - 1))
                self.assertEqual(q["topic"], r["topic"])

    def test_path_settles_around_the_students_level(self):
        log = self.play("s", 30, self.threshold(4))
        self.assertTrue(all(p["level"] in (4, 5) for p, _ in log[-10:]), [p["level"] for p, _ in log])

    def test_mastery_rises_only_with_two_independent_hits(self):
        log = self.play("s", 12, lambda p: (p["label"], 2))   # always right, always with hints
        self.assertLessEqual(max(trainer.mastery_map("s").values()), 2)
        self.assertTrue(all(r["mastery_after"] <= 2 for _, r in log))
        log = self.play("clean", 12, lambda p: (p["label"], 0))
        self.assertGreaterEqual(max(trainer.mastery_map("clean").values()), 3)
        for _, r in log:
            if r["mastery_before"] == 0:
                self.assertLessEqual(r["mastery_after"], 2, "a single answer is never mastery 3")

    def test_answer_after_rung_three_or_four_never_raises(self):
        for rung in (3, 4):
            student = f"s{rung}"
            log = self.play(student, 10, lambda p: (p["label"], rung))
            for _, r in log:
                self.assertLessEqual(r["mastery_after"], max(r["mastery_before"], 1))
            self.assertLessEqual(max(trainer.mastery_map(student).values()), 1)

    def test_mastery_map_has_all_topics_in_range(self):
        self.play("s", 8, self.threshold(2))
        m = trainer.mastery_map("s")
        self.assertEqual(set(m), set(TOPIC_KEYS))
        self.assertTrue(all(v in range(6) for v in m.values()))
        self.assertEqual(trainer.mastery_map("nobody"), {k: 0 for k in TOPIC_KEYS})

    def test_review_is_flagged_and_a_failed_review_lowers_mastery(self):
        self.play("s", 5, lambda p: (p["label"], 0))   # diagnostic: 0, 2, 4, 6, 7 right -> five topics worked
        trainer.REVIEW_RATE = 1.0
        p = trainer.next_problem("s")
        worked = {t for t, v in trainer.mastery_map("s").items() if v}
        self.assertIn(p["topic"], worked)
        before = trainer.mastery_map("s")[p["topic"]]
        r = trainer.record_answer("s", p["id"], "ABCDE"[("ABCDE".index(p["label"]) + 1) % 5], 0)
        self.assertTrue(r["review"])
        self.assertFalse(r["correct"])
        self.assertEqual(r["mastery_after"], max(1, before - 1))

    def test_review_rate_is_about_one_in_five(self):
        trainer.REVIEW_RATE = self.review_rate
        log = self.play("s", 105, lambda p: (p["label"], 0))
        reviews = sum(r["review"] for _, r in log[5:])
        self.assertTrue(10 <= reviews <= 30, reviews)

    def test_review_resumes_the_main_path(self):
        trainer.REVIEW_RATE = self.review_rate
        log = self.play("s", 60, self.threshold(3))
        main = [(p, r) for p, r in log if not r["review"]]
        for (p, r), (q, _) in list(zip(main, main[1:]))[3:]:
            self.assertEqual(q["level"], min(7, p["level"] + 1) if r["correct"] else max(0, p["level"] - 1))

    def test_never_repeats_while_candidates_remain(self):
        trainer.REVIEW_RATE = self.review_rate
        log = self.play("s", 80, self.threshold(3))
        ids = [p["id"] for p, _ in log]
        self.assertEqual(len(ids), len(set(ids)))

    def test_repeats_only_when_the_bank_is_exhausted(self):
        small = [p for p in self.problems if p["topic"] == "logic" and p["level"] <= 1]   # 12 problems
        trainer.configure(db_path=self.db, problems=small, neighbors_fn=make_synthetic_neighbors(small))
        log = self.play("s", 15, lambda p: (p["label"], 0))
        ids = [p["id"] for p, _ in log]
        self.assertEqual(len(set(ids[:12])), 12)
        self.assertEqual(len(ids), 15)

    def test_deterministic_for_the_same_student_id(self):
        trainer.REVIEW_RATE = self.review_rate
        first = [p["id"] for p, _ in self.play("s", 30, self.threshold(3))]
        other = os.path.join(self.tmp.name, "again.db")
        trainer.configure(db_path=other, problems=self.problems, neighbors_fn=make_synthetic_neighbors(self.problems))
        second = [p["id"] for p, _ in self.play("s", 30, self.threshold(3))]
        self.assertEqual(first, second)
        third = [p["id"] for p, _ in self.play("t", 30, self.threshold(3))]
        self.assertNotEqual(first, third)

    def test_record_answer_grades_from_the_bank_without_next_problem(self):
        r = trainer.record_answer("s", "syn-areas-3-0", "d", 0)   # label "ABCDE"[(3 + 0) % 5] = D
        self.assertTrue(r["correct"])
        self.assertEqual(r["label"], "D")
        self.assertEqual(r["topic"], "areas")
        r = trainer.record_answer("s", "not-a-problem", "A", 0)
        self.assertFalse(r["correct"])

    def test_teacher_report(self):
        self.play("ana", 10, self.threshold(2))
        self.play("bo", 6, self.threshold(5))
        report = trainer.teacher_report()
        self.assertEqual([s["student_id"] for s in report["students"]], ["ana", "bo"])
        ana = trainer.teacher_report("ana")["students"][0]
        self.assertEqual(ana["answers"], 10)
        self.assertEqual(set(ana["mastery"]), set(TOPIC_KEYS))
        self.assertEqual(sum(v["answers"] for v in ana["by_level"].values()), 10)
        self.assertEqual(sum(v["answers"] for v in ana["by_topic"].values()), 10)
        self.assertEqual(len(report["topics"]), 8)

    def test_start_student_level_sets_the_diagnostic_and_the_base_level(self):
        self.assertEqual(trainer.start_student("s", level=4), {k: 0 for k in TOPIC_KEYS})
        self.assertEqual(trainer.next_problem("s")["level"], 4)
        self.assertEqual(trainer.teacher_report("s")["students"][0]["base_level"], 4)
        log = self.play("s", 3, self.threshold(5))        # 4 ok, 6 wrong, 7 wrong: diagnostic done
        self.assertEqual([p["level"] for p, _ in log], [4, 6, 7])
        report = trainer.teacher_report("s")["students"][0]
        self.assertTrue(report["diagnostic_done"])
        self.assertEqual(report["base_level"], 4)
        self.assertEqual(report["start_level"], 4)
        self.assertEqual(trainer.diagnostic_levels(5), (5, 7, 7, 7, 7))
        self.assertEqual(trainer.diagnostic_levels(None), trainer.DIAGNOSTIC_LEVELS)

    def test_start_student_without_level_behaves_as_before(self):
        trainer.start_student("s")
        log = self.play("s", 3, self.threshold(7))
        self.assertEqual([p["level"] for p, _ in log], [0, 2, 4])
        self.assertIsNone(trainer.teacher_report("s")["students"][0]["start_level"])

    def test_start_level_failing_everything_drops_one_level(self):
        trainer.start_student("s", level=3)
        self.play("s", 3, self.threshold(-1))
        self.assertEqual(trainer.teacher_report("s")["students"][0]["base_level"], 2)
        trainer.start_student("zero", level=0)
        self.play("zero", 3, self.threshold(-1))
        self.assertEqual(trainer.teacher_report("zero")["students"][0]["base_level"], 0)

    def test_reset_student_forgets_everything_and_allows_seen_problems_again(self):
        first = [p["id"] for p, _ in self.play("s", 8, self.threshold(3))]
        self.assertNotEqual(trainer.mastery_map("s"), {k: 0 for k in TOPIC_KEYS})
        trainer.reset_student("s")
        self.assertEqual(trainer.mastery_map("s"), {k: 0 for k in TOPIC_KEYS})
        self.assertEqual(trainer.teacher_report("s")["students"], [])
        again = [p["id"] for p, _ in self.play("s", 8, self.threshold(3))]
        self.assertEqual(first, again)
        trainer.reset_student("never-seen")   # must not raise

    def test_start_student_restarts_an_existing_student(self):
        self.play("s", 6, self.threshold(3))
        pending = trainer.next_problem("s")
        trainer.start_student("s", level=2)
        self.assertEqual(trainer.teacher_report("s")["students"][0]["answers"], 0)
        self.assertNotEqual(trainer.next_problem("s")["id"], pending["id"])
        self.assertEqual(trainer.next_problem("s")["level"], 2)

    def test_start_student_is_deterministic(self):
        trainer.REVIEW_RATE = self.review_rate
        trainer.start_student("s", level=3)
        first = [p["id"] for p, _ in self.play("s", 25, self.threshold(4))]
        trainer.start_student("s", level=3)
        self.assertEqual([p["id"] for p, _ in self.play("s", 25, self.threshold(4))], first)

    def test_old_database_without_start_level_is_migrated(self):
        import sqlite3
        old = os.path.join(self.tmp.name, "old.db")
        db = sqlite3.connect(old)
        db.execute("CREATE TABLE students (student_id TEXT PRIMARY KEY, created_at REAL NOT NULL, "
                   "base_level INTEGER NOT NULL DEFAULT 0, diagnostic_done INTEGER NOT NULL DEFAULT 0)")
        db.execute("INSERT INTO students VALUES ('old', 0, 3, 1)")
        db.commit()
        db.close()
        trainer.configure(db_path=old, problems=self.problems, neighbors_fn=make_synthetic_neighbors(self.problems))
        self.assertEqual(trainer.teacher_report("old")["students"][0]["start_level"], None)
        self.assertEqual(trainer.start_student("old", level=1), {k: 0 for k in TOPIC_KEYS})

    def test_no_personal_data_columns(self):
        import sqlite3
        trainer.next_problem("s")
        db = sqlite3.connect(self.db)
        columns = {row[1] for table in ("students", "answers", "topic_state", "pending")
                   for row in db.execute(f"PRAGMA table_info({table})")}
        db.close()
        for forbidden in ("name", "email", "birth", "school", "class"):
            self.assertFalse(any(forbidden in c for c in columns), columns)


if __name__ == "__main__":
    unittest.main()
