"""Adaptive trainer: next problem, answer bookkeeping and mastery per topic.

Owner: C (branch `trainer`). See INTERFACES.md for the contract.

No language model runs here. The trainer uses `retrieval.neighbors` (embeddings),
one SQLite file and rules, so a step costs about one embedding plus Python.

State
-----
One SQLite file, `STUDENTS_DB` in config.env or the environment (default
`data/students.db`, git-ignored). `student_id` is a pseudonym chosen by the student or
the teacher; nothing else about the student is stored (they are minors).

    students(student_id, created_at, base_level, diagnostic_done)
    answers(id, student_id, problem_id, topic, level, letter, label, correct,
            hint_rung, review, created_at)
    topic_state(student_id, topic, mastery, level, updated_at)
    pending(student_id, problem_id, topic, level, label, review, problem_json, issued_at)

Problem level vs. student mastery
---------------------------------
A PROBLEM has a level 0..7 (M3Kang `level`, 0 = grade 5). A STUDENT has, per topic, a
mastery 0..5 (INTERFACES.md). Mastery is derived from the last `WINDOW` answers on the
topic; a "counting" correct answer is one given with hint rung 0, 1 or 2 (after rung 3 or
4 the solution was in sight, so it never raises mastery):

    0  no answers on the topic
    1  answers, but no counting correct answer
    2  at least one counting correct answer ("correct with hints")
    3  2+ counting correct answers on distinct problems, at least one at rung 0, and the
       counting correct answers are at least half of the window ("sometimes without hints")
    4  the last 3 answers are correct at rung 0, on distinct problems ("consistently")
    5  mastery 4 and one of those answers is on a problem one level above the student's
       base level ("correct without hints one level above")

So a topic only rises past 2 with two independent correct answers, at least one without
hints. A failed REVIEW problem lowers the mastery by one step as well (floor 1).

The TARGET LEVEL of a topic, used for review problems and whenever there is no chain of
neighbours to follow, is an explicit function of the student's base level (set by the
diagnostic) and the topic's mastery:

    target = clamp(base_level + MASTERY_OFFSET[mastery], 0, 7)
    MASTERY_OFFSET = {0: 0, 1: -2, 2: -1, 3: 0, 4: +1, 5: +2}

Each topic also keeps a PRACTICE LEVEL: the level of the last problem answered on the
topic, plus one after a correct answer, minus one after a wrong one. Review problems are
drawn at the practice level when the topic has one, else at the target level.

Choosing the next problem
-------------------------
1. Diagnostic for a new student: 3 to 5 problems of increasing level (DIAGNOSTIC_LEVELS),
   on rotating topics. It stops after the first wrong answer once 3 are done. The base
   level is the highest level answered correctly (0 when none).
2. Review, about one problem in five (REVIEW_RATE): the worked topic whose last answer is
   the oldest, other than the current one, at its practice level. The student is not told;
   the `record_answer` result carries `review: True`. The main path then resumes from
   the last non-review problem: a review is a detour, not a change of course.
3. Otherwise the adaptive rule from the last answered problem: correct -> an embedding
   neighbour one level up, any topic; wrong -> a neighbour on the same topic one level down.
4. A problem the student has already seen is never served again while candidates remain.
   Neighbours are asked with k=NEIGHBOUR_K and filtered; when all are seen, the problem
   bank is searched at the wanted level (nearest level with candidates).

Every random choice uses `random.Random` seeded from SEED, the student id and the number
of answers so far, so a student's path is reproducible.

Problem bank: `TRAINER_BANK` (comma-separated jsonl paths; default data/train.jsonl and
data/val.jsonl, falling back to data/sample_problems.jsonl). Only the Catalan and English
rows are kept in memory. Problems are served in Catalan when the bank has that version.
The returned dict is the full Problem (label included): the web app strips the label.
"""
import json
import os
import random
import sqlite3
import time
import zlib

from .config import CONFIG, ROOT
from .retrieval import neighbors as _retrieval_neighbors
from .topics import TOPIC_KEYS, TOPICS, get_topic

SEED = int(CONFIG.get("SEED", 42))
LEVELS = range(8)
MASTERY_OFFSET = {0: 0, 1: -2, 2: -1, 3: 0, 4: 1, 5: 2}
WINDOW = 6                 # answers per topic that mastery is derived from
STREAK = 3                 # rung-0 correct answers in a row for mastery 4
COUNTING_RUNGS = (0, 1, 2)  # a correct answer after rung 3 or 4 never raises mastery
DIAGNOSTIC_LEVELS = (0, 2, 4, 6, 7)
DIAGNOSTIC_MIN = 3
REVIEW_RATE = 0.2
NEIGHBOUR_K = 8
STUDENT_LANGS = ("cat", "eng")   # shown in Catalan; English is the fallback

DEFAULT_DB = os.path.join(ROOT, "data", "students.db")
DEFAULT_BANK = (os.path.join(ROOT, "data", "train.jsonl"), os.path.join(ROOT, "data", "val.jsonl"))
SAMPLE_BANK = os.path.join(ROOT, "data", "sample_problems.jsonl")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    base_level INTEGER NOT NULL DEFAULT 0,
    diagnostic_done INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    level INTEGER NOT NULL,
    letter TEXT NOT NULL,
    label TEXT NOT NULL,
    correct INTEGER NOT NULL,
    hint_rung INTEGER NOT NULL,
    review INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS answers_student ON answers(student_id, id);
CREATE TABLE IF NOT EXISTS topic_state (
    student_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    mastery INTEGER NOT NULL DEFAULT 0,
    level INTEGER,
    updated_at REAL NOT NULL,
    PRIMARY KEY (student_id, topic)
);
CREATE TABLE IF NOT EXISTS pending (
    student_id TEXT PRIMARY KEY,
    problem_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    level INTEGER NOT NULL,
    label TEXT NOT NULL,
    review INTEGER NOT NULL DEFAULT 0,
    problem_json TEXT NOT NULL,
    issued_at REAL NOT NULL
);
"""

# Module state: the database path, the problem bank and the neighbour function.
# `configure` swaps them (tests use a temporary file and the simulator a synthetic bank).
_settings = {"db_path": None, "bank_paths": None, "neighbors": None, "extra_problems": None}
_bank = None
stats = {"neighbor_calls": 0}   # the simulator reads it: one call is about one embedding


def configure(db_path=None, bank_paths=None, neighbors_fn=None, problems=None):
    """Point the trainer at another database, problem bank or neighbour function.

    `problems` is a list of Problem dicts used as the bank instead of files (simulator).
    Call with no arguments to go back to the defaults.
    """
    global _bank
    _settings["db_path"] = db_path
    _settings["bank_paths"] = bank_paths
    _settings["neighbors"] = neighbors_fn
    _settings["extra_problems"] = problems
    _bank = None
    stats["neighbor_calls"] = 0


def db_path():
    return _settings["db_path"] or os.environ.get("STUDENTS_DB") or CONFIG.get("STUDENTS_DB") or DEFAULT_DB


def _connect():
    path = db_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def _rng(student_id, step):
    """Deterministic randomness: the same student at the same step draws the same numbers."""
    return random.Random(zlib.crc32(f"{SEED}:{student_id}:{step}".encode("utf-8")))


def _clamp_level(level):
    return max(0, min(7, int(level)))


def _topic_of(problem):
    topic = problem.get("topic") or get_topic(problem["id"])
    return topic if topic in TOPIC_KEYS else "arithmetic"


# ----------------------------------------------------------------------------- bank

class _Bank:
    """Problems by id, with the Catalan version preferred, and by (topic, level)."""

    def __init__(self, problems, gradable_only=()):
        """`gradable_only` problems can be graded but are never served (the smoke-test samples)."""
        self.by_id = {}        # id -> {lang: problem}
        for p in gradable_only:
            self.by_id.setdefault(p["id"], {})[p.get("language", "eng")] = p
        served = set()
        for p in problems:
            self.by_id.setdefault(p["id"], {})[p.get("language", "eng")] = p
            served.add(p["id"])
        self.ids = sorted(served)
        self.meta = {}         # id -> (topic, level)
        self.by_topic_level = {}
        for pid in self.ids:
            p = self.get(pid)
            topic, level = _topic_of(p), _clamp_level(p.get("level", 0))
            self.meta[pid] = (topic, level)
            self.by_topic_level.setdefault((topic, level), []).append(pid)

    def get(self, problem_id):
        versions = self.by_id.get(problem_id)
        if not versions:
            return None
        for lang in STUDENT_LANGS:
            if lang in versions:
                return dict(versions[lang])
        return dict(next(iter(versions.values())))

    def candidates(self, level, topic=None, exclude=()):
        """Unseen ids at the nearest level to `level` that has any; same topic when given."""
        exclude = set(exclude)
        for distance in range(8):
            for lvl in sorted({_clamp_level(level - distance), _clamp_level(level + distance)}):
                keys = [(topic, lvl)] if topic else [(t, lvl) for t in TOPIC_KEYS]
                found = [pid for key in keys for pid in self.by_topic_level.get(key, []) if pid not in exclude]
                if found:
                    return sorted(found)
        return []


def _bank_paths():
    if _settings["bank_paths"] is not None:
        return list(_settings["bank_paths"])
    raw = os.environ.get("TRAINER_BANK") or CONFIG.get("TRAINER_BANK")
    if raw:
        return [os.path.join(ROOT, p.strip()) for p in raw.split(",") if p.strip()]
    paths = [p for p in DEFAULT_BANK if os.path.exists(p)]
    return paths or [SAMPLE_BANK]


def _read_bank(paths):
    """Only the Catalan and English rows: M3Kang has 100+ languages per id."""
    wanted = tuple(f'"language": "{lang}"' for lang in STUDENT_LANGS)
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip() or not any(w in line for w in wanted):
                    continue
                p = json.loads(line)
                if p.get("language") in STUDENT_LANGS:
                    yield p


def bank():
    global _bank
    if _bank is None:
        problems = _settings["extra_problems"]
        paths = _bank_paths()
        if problems is None:
            problems = list(_read_bank(paths))
        # The smoke-test samples stay gradable (tests, predict.py checks) but are only
        # served when they are the bank itself
        samples = [] if SAMPLE_BANK in paths else list(_read_bank([SAMPLE_BANK]))
        _bank = _Bank(problems, gradable_only=samples)
    return _bank


def _neighbors(problem_id, level_delta, same_topic, k=NEIGHBOUR_K):
    stats["neighbor_calls"] += 1
    fn = _settings["neighbors"] or _retrieval_neighbors
    return fn(problem_id, level_delta=level_delta, same_topic=same_topic, lang="cat", k=k)


# ----------------------------------------------------------------------------- mastery

def derive_mastery(history, base_level):
    """Mastery 0..5 from the answers on one topic (oldest first, dicts with
    `correct`, `hint_rung`, `level`, `problem_id`). Only the last WINDOW answers count."""
    recent = list(history)[-WINDOW:]
    if not recent:
        return 0
    counting = [a for a in recent if a["correct"] and a["hint_rung"] in COUNTING_RUNGS]
    clean = [a for a in counting if a["hint_rung"] == 0]
    if not counting:
        return 1
    distinct = {a["problem_id"] for a in counting}
    if len(distinct) < 2 or not clean or 2 * len(counting) < len(recent):
        return 2
    tail = recent[-STREAK:]
    streak = (len(tail) == STREAK and all(a["correct"] and a["hint_rung"] == 0 for a in tail)
              and len({a["problem_id"] for a in tail}) >= 2)
    if not streak:
        return 3
    if any(a["level"] >= base_level + 1 for a in tail):
        return 5
    return 4


def target_level(base_level, mastery):
    """Explicit mapping from a topic's mastery to the level of its next problems."""
    return _clamp_level(base_level + MASTERY_OFFSET[int(mastery)])


def _topic_history(db, student_id, topic):
    rows = db.execute("SELECT problem_id, level, correct, hint_rung FROM answers "
                      "WHERE student_id=? AND topic=? ORDER BY id", (student_id, topic)).fetchall()
    return [dict(r) for r in rows]


def _student(db, student_id):
    row = db.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()
    if row is None:
        db.execute("INSERT INTO students (student_id, created_at) VALUES (?, ?)", (student_id, time.time()))
        db.commit()
        row = db.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()
    return dict(row)


def _seen_ids(db, student_id):
    seen = {r[0] for r in db.execute("SELECT problem_id FROM answers WHERE student_id=?", (student_id,))}
    seen |= {r[0] for r in db.execute("SELECT problem_id FROM pending WHERE student_id=?", (student_id,))}
    return seen


def _topic_states(db, student_id):
    rows = db.execute("SELECT topic, mastery, level, updated_at FROM topic_state WHERE student_id=?",
                      (student_id,)).fetchall()
    return {r["topic"]: dict(r) for r in rows}


# ----------------------------------------------------------------------------- choosing

def _pick(rng, ids):
    return ids[rng.randrange(len(ids))] if ids else None


def _problem_dict(problem_id, fallback=None):
    """The Catalan version from the bank, else the dict the neighbour function gave."""
    return bank().get(problem_id) or (dict(fallback) if fallback else None)


def _choose_diagnostic(db, student, rng, seen, n_answers):
    """Problem n of the diagnostic: level DIAGNOSTIC_LEVELS[n] on a rotating topic."""
    level = DIAGNOSTIC_LEVELS[min(n_answers, len(DIAGNOSTIC_LEVELS) - 1)]
    order = list(TOPIC_KEYS)
    _rng(student["student_id"], "diagnostic-topics").shuffle(order)
    topic = order[n_answers % len(order)]
    ids = bank().candidates(level, topic, exclude=seen) or bank().candidates(level, None, exclude=seen)
    pid = _pick(rng, ids)
    return pid, False


def _choose_review(db, student, rng, seen, last):
    """The worked topic with the oldest last answer, excluding the current one."""
    states = _topic_states(db, student["student_id"])
    worked = [s for t, s in states.items() if t != last["topic"]]
    if not worked:
        return None
    oldest = min(worked, key=lambda s: (s["updated_at"], s["topic"]))
    level = oldest["level"] if oldest["level"] is not None else target_level(student["base_level"], oldest["mastery"])
    ids = bank().candidates(level, oldest["topic"], exclude=seen)
    return _pick(rng, ids)


def _choose_adaptive(student, rng, seen, last):
    """Correct -> neighbour one level up (any topic); wrong -> same topic, one level down."""
    delta = 1 if last["correct"] else -1
    same_topic = not last["correct"]
    hits = _neighbors(last["problem_id"], level_delta=delta, same_topic=same_topic)
    for p in hits:
        if p["id"] not in seen and p["id"] != last["problem_id"]:
            return p["id"], p
    level = _clamp_level(last["level"] + delta)
    ids = bank().candidates(level, last["topic"] if same_topic else None, exclude=seen)
    if not ids:
        ids = bank().candidates(level, None, exclude=seen)
    return _pick(rng, ids), None


def _least_recent(db, student_id):
    """Everything is seen: repeat the problem answered longest ago."""
    row = db.execute("SELECT problem_id FROM answers WHERE student_id=? ORDER BY id LIMIT 1",
                     (student_id,)).fetchone()
    return row[0] if row else None


def _diagnostic_finished(rows):
    """3 to 5 answers; stop at the first wrong answer once 3 are done."""
    if len(rows) >= len(DIAGNOSTIC_LEVELS):
        return True
    return len(rows) >= DIAGNOSTIC_MIN and not all(r["correct"] for r in rows)


def next_problem(student_id):
    """A Problem dict in Catalan (English when there is no Catalan version).

    Asking twice without answering returns the same problem.
    """
    db = _connect()
    try:
        student = _student(db, student_id)
        pending = db.execute("SELECT problem_json FROM pending WHERE student_id=?", (student_id,)).fetchone()
        if pending:
            return json.loads(pending[0])
        n_answers = db.execute("SELECT COUNT(*) FROM answers WHERE student_id=?", (student_id,)).fetchone()[0]
        rng = _rng(student_id, n_answers)
        seen = _seen_ids(db, student_id)
        # The chain follows the last problem of the main path: a review is a detour
        last_row = db.execute("SELECT problem_id, topic, level, correct FROM answers "
                              "WHERE student_id=? AND review=0 ORDER BY id DESC LIMIT 1", (student_id,)).fetchone()
        last = dict(last_row) if last_row else None
        given = None
        review = False
        if not student["diagnostic_done"] or last is None:
            pid, _ = _choose_diagnostic(db, student, rng, seen, n_answers)
        else:
            pid = None
            if rng.random() < REVIEW_RATE:
                pid = _choose_review(db, student, rng, seen, last)
                review = pid is not None
            if pid is None:
                pid, given = _choose_adaptive(student, rng, seen, last)
        if pid is None:
            pid = _least_recent(db, student_id) or (bank().ids[0] if bank().ids else None)
        if pid is None:
            raise RuntimeError("the problem bank is empty: check TRAINER_BANK")
        problem = _problem_dict(pid, given)
        topic, level = _topic_of(problem), _clamp_level(problem.get("level", 0))
        db.execute("INSERT OR REPLACE INTO pending VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (student_id, pid, topic, level, str(problem.get("label", "?")), int(review),
                    json.dumps(problem, ensure_ascii=False), time.time()))
        db.commit()
        return problem
    finally:
        db.close()


def record_answer(student_id, problem_id, letter, hint_rung_used):
    """Grade the answer, store it and update the topic's mastery and practice level.

    Returns {"correct", "label", "topic", "mastery_before", "mastery_after", "review"}.
    """
    db = _connect()
    try:
        student = _student(db, student_id)
        pending = db.execute("SELECT * FROM pending WHERE student_id=? AND problem_id=?",
                             (student_id, problem_id)).fetchone()
        if pending:
            topic, level, label, review = pending["topic"], pending["level"], pending["label"], bool(pending["review"])
        else:
            p = bank().get(problem_id)
            topic = _topic_of(p) if p else get_topic(problem_id)
            level = _clamp_level(p.get("level", student["base_level"])) if p else student["base_level"]
            label = str(p.get("label", "?")) if p else "?"
            review = False
        rung = max(0, min(4, int(hint_rung_used)))
        correct = str(letter).strip().upper() == label
        now = time.time()
        db.execute("INSERT INTO answers (student_id, problem_id, topic, level, letter, label, correct, "
                   "hint_rung, review, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (student_id, problem_id, topic, level, str(letter).strip().upper()[:1], label,
                    int(correct), rung, int(review), now))
        db.execute("DELETE FROM pending WHERE student_id=?", (student_id,))

        states = _topic_states(db, student_id)
        before = states.get(topic, {}).get("mastery", 0)
        if not student["diagnostic_done"]:
            rows = db.execute("SELECT correct, level FROM answers WHERE student_id=? ORDER BY id",
                              (student_id,)).fetchall()
            if _diagnostic_finished(rows):
                base = max([r["level"] for r in rows if r["correct"]], default=0)
                db.execute("UPDATE students SET base_level=?, diagnostic_done=1 WHERE student_id=?",
                           (base, student_id))
                student["base_level"] = base
        after = derive_mastery(_topic_history(db, student_id, topic), student["base_level"])
        if correct and rung not in COUNTING_RUNGS:
            after = min(after, before) if before else after
        if review and not correct and before > 1:
            after = min(after, before - 1)
        practice = _clamp_level(level + (1 if correct else -1))
        db.execute("INSERT OR REPLACE INTO topic_state VALUES (?, ?, ?, ?, ?)",
                   (student_id, topic, after, practice, now))
        db.commit()
        return {"correct": correct, "label": label, "topic": topic,
                "mastery_before": before, "mastery_after": after, "review": review}
    finally:
        db.close()


def mastery_map(student_id):
    """{topic_key: 0..5} with all eight keys."""
    db = _connect()
    try:
        states = _topic_states(db, student_id)
    finally:
        db.close()
    return {key: states.get(key, {}).get("mastery", 0) for key in TOPIC_KEYS}


# ----------------------------------------------------------------------------- teacher

def teacher_report(student_id=None):
    """Mastery per topic and student, and answers per level, straight from SQLite.

    {"topics": [{"key", "name_ca", "name_en"}], "mastery_scale": {...},
     "students": [{"student_id", "base_level", "diagnostic_done", "answers", "correct",
                   "mastery": {topic: 0..5}, "by_topic": {topic: {...}}, "by_level": {level: {...}}}]}
    """
    db = _connect()
    try:
        if student_id is None:
            ids = [r[0] for r in db.execute("SELECT student_id FROM students ORDER BY student_id")]
        else:
            ids = [student_id]
        students = []
        for sid in ids:
            row = db.execute("SELECT * FROM students WHERE student_id=?", (sid,)).fetchone()
            if row is None:
                continue
            states = _topic_states(db, sid)
            by_topic, by_level = {}, {}
            for key in TOPIC_KEYS:
                s = states.get(key, {})
                hits = db.execute("SELECT COUNT(*), COALESCE(SUM(correct), 0), "
                                  "COALESCE(SUM(correct AND hint_rung = 0), 0) FROM answers "
                                  "WHERE student_id=? AND topic=?", (sid, key)).fetchone()
                mastery = s.get("mastery", 0)
                by_topic[key] = {"mastery": mastery, "level": s.get("level"),
                                 "target_level": target_level(row["base_level"], mastery),
                                 "answers": hits[0], "correct": hits[1], "correct_no_hints": hits[2]}
            for lvl, n, ok in db.execute("SELECT level, COUNT(*), SUM(correct) FROM answers "
                                         "WHERE student_id=? GROUP BY level ORDER BY level", (sid,)):
                by_level[lvl] = {"answers": n, "correct": ok}
            total = db.execute("SELECT COUNT(*), COALESCE(SUM(correct), 0), COALESCE(SUM(review), 0) "
                               "FROM answers WHERE student_id=?", (sid,)).fetchone()
            students.append({"student_id": sid, "base_level": row["base_level"],
                             "diagnostic_done": bool(row["diagnostic_done"]),
                             "answers": total[0], "correct": total[1], "reviews": total[2],
                             "mastery": {key: by_topic[key]["mastery"] for key in TOPIC_KEYS},
                             "by_topic": by_topic, "by_level": by_level})
    finally:
        db.close()
    return {"topics": [{k: t[k] for k in ("key", "name_ca", "name_en")} for t in TOPICS],
            "mastery_scale": {0: "no data", 1: "always fails", 2: "correct with hints",
                              3: "sometimes correct without hints", 4: "consistently correct without hints",
                              5: "correct without hints one level above"},
            "students": students}
