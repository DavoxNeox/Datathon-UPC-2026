"""Empirical difficulty per class, from the answers stored on the board.

M3Kang's `level` (0..7) is the Kangaroo age band the problem was set for. How hard a
problem really is for ONE class comes out of that class's own answers, which the trainer
keeps in the `answers` table of its SQLite file. This module reads that table (read-only,
nothing leaves the device) and turns it into three things:

- `estimate(db_path)`: per problem id, how often it was answered correctly, with a
  Bayesian shrinkage towards the prior of its level, so a problem seen twice is not called
  "impossible" after two misses;
- `adjusted_level(problem, estimates)`: the M3Kang level moved up or down by what the
  class observed, for the trainer's adaptive rule (see "Empirical difficulty" in
  INTERFACES.md and `DIFFICULTY_ADJUST` in config.env);
- `report(db_path)`: the teacher's view, JSON-serialisable, labels in Catalan and English.

The estimator
-------------
For a problem answered n times with k correct answers, at M3Kang level L:

    p_shrunk = (k + a * prior_L) / (n + a)                         a = PRIOR_WEIGHT

`a` is the weight of the prior in answers: with a = 3 the first three answers count as
much as the prior does. `prior_L` is the class's mean rate of correct answers on level L,
itself shrunk towards 0.5 with the same weight so a level with one answer is not fixed at
0% or 100%:

    prior_L = (K_L + a * 0.5) / (N_L + a)        K_L, N_L: correct and total answers at L

With no answer at level L the prior is 0.5. In `estimate`'s output, `p_correct` and
`p_without_hints` are the RAW rates (k/n and correct-at-rung-0/n) for the teacher, and
`shrunk` is p_shrunk, the figure the adjustment uses.

The adjustment
--------------
The adjusted level is the M3Kang level plus a shift in levels proportional to how far the
problem's shrunk rate sits from the rate of its level-mates:

    shift = (prior_L - p_shrunk) / POINTS_PER_LEVEL        clipped to [-MAX_SHIFT, MAX_SHIFT]
    adjusted = clamp(L + shift, 0, 7)

POINTS_PER_LEVEL = 0.25: a problem solved 25 points less often than the other problems of
its level counts as one level harder. MAX_SHIFT = 2 levels. A problem with fewer than
MIN_N (3) answers keeps its M3Kang level exactly: nothing is inferred from one or two
answers. All constants are module attributes and keyword arguments, so a class with a
long history can be measured with a bigger MIN_N.

What is measured and what is not
--------------------------------
The estimator and the adjustment were validated ONLY on a SIMULATED class
(laptop/measure_difficulty.py, docs/difficulty.md): synthetic students whose success
depends on a planted per-problem difficulty. With real students nothing is measured yet.
The recommended use is the teacher's `report()`, which shows what this class finds hard
and easy; the trainer hook behind `DIFFICULTY_ADJUST` did not help a simulated student and
stays off by default.

Standard library only (sqlite3), no model call: a full estimate over a few thousand
answers is milliseconds of Python on the board.
"""
import json
import os
import sqlite3

PRIOR_WEIGHT = 3          # a: the prior counts as this many answers
MIN_N = 3                 # answers a problem needs before its level is adjusted
POINTS_PER_LEVEL = 0.25   # rate points below the level's rate that make one level harder
MAX_SHIFT = 2.0           # levels
TOP = 10                  # problems listed in each report table
DEFAULT_PRIOR = 0.5

LABELS = {
    "hardest": {"ca": "Problemes més difícils observats", "en": "Hardest problems observed"},
    "easiest": {"ca": "Problemes més fàcils observats", "en": "Easiest problems observed"},
    "by_level": {"ca": "Taxa d'encert per nivell", "en": "Rate of correct answers per level"},
    "id": {"ca": "Problema", "en": "Problem"},
    "level": {"ca": "Nivell M3Kang", "en": "M3Kang level"},
    "n": {"ca": "Respostes", "en": "Answers"},
    "correct": {"ca": "Encerts", "en": "Correct"},
    "p_correct": {"ca": "Taxa d'encert", "en": "Rate of correct answers"},
    "p_without_hints": {"ca": "Encert sense pistes", "en": "Correct without hints"},
    "shrunk": {"ca": "Taxa estimada (contreta cap al nivell)", "en": "Estimated rate (shrunk to the level)"},
    "prior": {"ca": "Taxa del nivell a la classe", "en": "Level's rate in this class"},
    "adjusted_level": {"ca": "Nivell ajustat a la classe", "en": "Level adjusted to this class"},
    "answers": {"ca": "Respostes a la classe", "en": "Answers in this class"},
    "problems_seen": {"ca": "Problemes resposts", "en": "Problems answered"},
    "problems_rated": {"ca": "Problemes amb prou respostes", "en": "Problems with enough answers"},
    "note": {"ca": "Dificultat observada en aquesta classe a partir de les seves respostes. El mètode s'ha "
                   "validat només amb una classe simulada, no amb alumnes reals.",
             "en": "Difficulty observed in this class from its own answers. The method was validated only "
                   "on a simulated class, not with real students."},
}


def _db_path(db_path):
    if db_path:
        return db_path
    from . import trainer
    return trainer.db_path()


def _read_answers(db_path):
    """(problem_id, level, correct, hint_rung) rows, read-only; [] when the file does not exist."""
    path = _db_path(db_path)
    if not path or not os.path.exists(path):
        return []
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "answers" not in tables:
            return []
        return db.execute("SELECT problem_id, level, correct, hint_rung FROM answers").fetchall()
    finally:
        db.close()


def level_priors(rows, prior_weight=PRIOR_WEIGHT):
    """{level: prior_L} from the answer rows: the level's rate shrunk towards 0.5."""
    totals = {}
    for _pid, level, correct, _rung in rows:
        n, k = totals.get(level, (0, 0))
        totals[level] = (n + 1, k + int(bool(correct)))
    return {level: (k + prior_weight * DEFAULT_PRIOR) / (n + prior_weight) for level, (n, k) in totals.items()}


def estimate(db_path=None, prior_weight=PRIOR_WEIGHT):
    """{problem_id: {"n", "p_correct", "p_without_hints", "shrunk", "level", "prior"}}.

    Reads the trainer's `answers` table at `db_path` (default: the trainer's own file).
    `p_correct` and `p_without_hints` are raw rates; `shrunk` is the estimator above.
    An empty dict when there is no database or no answer.
    """
    rows = _read_answers(db_path)
    priors = level_priors(rows, prior_weight)
    counts = {}
    for pid, level, correct, rung in rows:
        c = counts.setdefault(pid, {"n": 0, "k": 0, "k0": 0, "level": level})
        c["n"] += 1
        c["k"] += int(bool(correct))
        c["k0"] += int(bool(correct) and int(rung) == 0)
    out = {}
    for pid, c in counts.items():
        prior = priors.get(c["level"], DEFAULT_PRIOR)
        out[pid] = {"n": c["n"], "p_correct": c["k"] / c["n"], "p_without_hints": c["k0"] / c["n"],
                    "shrunk": (c["k"] + prior_weight * prior) / (c["n"] + prior_weight),
                    "level": c["level"], "prior": prior}
    return out


def adjusted_level(problem, estimates, min_n=MIN_N, points_per_level=POINTS_PER_LEVEL, max_shift=MAX_SHIFT):
    """The M3Kang level shifted by the class's observations; the level itself when unknown.

    `problem` is a Problem dict (or any dict with `id` and `level`). The mapping is the one
    documented at the top of the module: shift = (prior_L - shrunk) / points_per_level,
    clipped to +-max_shift, nothing before min_n answers. Returns a float in [0, 7].
    """
    level = float(max(0, min(7, int(problem.get("level", 0)))))
    est = estimates.get(problem.get("id"))
    if not est or est["n"] < min_n:
        return level
    shift = (est["prior"] - est["shrunk"]) / points_per_level
    shift = max(-max_shift, min(max_shift, shift))
    return max(0.0, min(7.0, level + shift))


def _row(pid, est, min_n):
    return {"id": pid, "level": est["level"], "n": est["n"],
            "p_correct": round(est["p_correct"], 3), "p_without_hints": round(est["p_without_hints"], 3),
            "shrunk": round(est["shrunk"], 3), "prior": round(est["prior"], 3),
            "adjusted_level": round(adjusted_level({"id": pid, "level": est["level"]}, {pid: est}, min_n=min_n), 2)}


def report(db_path=None, min_n=MIN_N, top=TOP, prior_weight=PRIOR_WEIGHT):
    """The teacher's view of the class's empirical difficulty, ready for json.dumps.

    {"labels": {key: {"ca", "en"}}, "answers", "problems_seen", "problems_rated", "min_n",
     "prior_weight", "hardest": [row], "easiest": [row], "by_level": [{"level", "n", "correct",
     "p_correct", "prior"}]}  where row = {"id", "level", "n", "p_correct", "p_without_hints",
     "shrunk", "prior", "adjusted_level"}. Only problems with at least `min_n` answers are
     listed, hardest first by the shrunk rate (ties by raw rate, then id). `note` (ca/en) says the
     method was validated on a simulated class only. Ids only, never text.
    """
    rows = _read_answers(db_path)
    estimates = estimate(db_path, prior_weight)
    rated = {pid: e for pid, e in estimates.items() if e["n"] >= min_n}
    order = sorted(rated, key=lambda pid: (rated[pid]["shrunk"], rated[pid]["p_correct"], pid))
    hardest = [_row(pid, rated[pid], min_n) for pid in order[:top]]
    easiest = [_row(pid, rated[pid], min_n) for pid in reversed(order[-top:])] if order else []
    priors = level_priors(rows, prior_weight)
    totals = {}
    for _pid, level, correct, _rung in rows:
        n, k = totals.get(level, (0, 0))
        totals[level] = (n + 1, k + int(bool(correct)))
    by_level = [{"level": level, "n": n, "correct": k, "p_correct": round(k / n, 3), "prior": round(priors[level], 3)}
                for level, (n, k) in sorted(totals.items())]
    return {"labels": LABELS, "note": LABELS["note"], "answers": len(rows), "problems_seen": len(estimates), "problems_rated": len(rated),
            "min_n": min_n, "prior_weight": prior_weight, "hardest": hardest, "easiest": easiest, "by_level": by_level}


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Print the class's empirical difficulty report as JSON.")
    p.add_argument("--db", default=None, help="SQLite file of the trainer (default: STUDENTS_DB)")
    p.add_argument("--min-n", type=int, default=MIN_N)
    args = p.parse_args(argv)
    print(json.dumps(report(args.db, min_n=args.min_n), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
