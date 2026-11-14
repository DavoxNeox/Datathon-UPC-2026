"""Measure the empirical-difficulty module on a simulated class over the real problem bank.

    python3 laptop/measure_difficulty.py                      # writes docs/difficulty.md
    python3 laptop/measure_difficulty.py --neighbors index    # no embedding server needed

Three experiments, all with copilot/simulate.py's trainer loop on data/train.jsonl +
data/val.jsonl (1747 ids), fixed seeds, 60 steps per student:

1. LABEL CLASS: ten of simulate's own students (threshold 0..7, random20, improving). For
   them the true difficulty IS the M3Kang level, so this measures the estimator's noise:
   how many problems get an adjusted level different from their band, and the correlation
   between the band and the observed rate of correct answers.
2. HIDDEN CLASS: ten threshold students whose success depends on a HIDDEN difficulty,
   the band plus a per-problem offset in {-2, -1, 0, +1, +2} drawn from the id (40% of the
   problems are off their band). A wrong student guesses a letter (20% right), like a real
   multiple-choice answer. This is the case the module exists for: does the class's history
   recover the offsets? Reported: problems whose adjusted level moves, the error of the band
   and of the adjusted level against the hidden difficulty, and the share of shifts that
   point the right way.
3. PROBES: on a copy of the hidden class's database, three new hidden-difficulty students
   (threshold 1, 3, 5) run 60 steps with DIFFICULTY_ADJUST off and on. Fewer wrong answers
   and fewer steps to settle with the flag on means the adjustment helps a student whose
   class already answered.

The hidden offsets are an assumption, not M3Kang data: they show what the module does when
the band is wrong for a class. The real figure comes from a real class on the board. Ids
only in the output, never problem text.
"""
import argparse
import math
import os
import shutil
import statistics
import sys
import tempfile
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot import difficulty, simulate, trainer  # noqa: E402

LABEL_STUDENTS = "threshold0,threshold1,threshold2,threshold3,threshold4,threshold5,threshold6,threshold7,random20-1,improving"
HIDDEN_THRESHOLDS = (0, 1, 2, 3, 4, 5, 6, 7, 2, 5)
PROBE_THRESHOLDS = (1, 3, 5)
OFFSET_CUTS = ((10, -2), (30, -1), (70, 0), (90, 1), (100, 2))
NOTES_MARKER = "## Reading the figures"


def hidden_offset(problem_id):
    """Per-problem offset from the id: 10% -2, 20% -1, 40% 0, 20% +1, 10% +2."""
    h = zlib.crc32(problem_id.encode("utf-8")) % 100
    for cut, offset in OFFSET_CUTS:
        if h < cut:
            return offset
    return 0


def hidden_level(problem):
    return max(0, min(7, int(problem["level"]) + hidden_offset(problem["id"])))


class HiddenStudent(simulate.Student):
    """Correct when the HIDDEN level is at most the threshold; otherwise a random letter."""

    def __init__(self, name, threshold, seed=0):
        super().__init__(name, "threshold", threshold, seed=seed)

    def answer(self, problem):
        self.answered += 1
        if hidden_level(problem) <= self.param:
            return problem.get("label", "A"), 0
        return self.rng.choice("ABCDE"), 0


def pearson(xs, ys):
    if len(xs) < 2:
        return float("nan")
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))


def fmt(x, digits=2):
    if isinstance(x, float):
        return "nan" if math.isnan(x) else f"{x:.{digits}f}"
    return str(x)


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(fmt(v) for v in r) + " |")
    return "\n".join(out)


def configure(db_path, neighbors_fn):
    trainer.configure(db_path=db_path, neighbors_fn=neighbors_fn)


def run_class(students, steps):
    logs = {}
    for s in students:
        log, _calls = simulate.run_student(s, steps)
        logs[s.name] = log
    return logs


def estimate_summary(db_path, lines):
    """Common figures for a class: coverage, moved problems, correlations."""
    est = difficulty.estimate(db_path)
    bank = trainer.bank()
    rated = {pid: e for pid, e in est.items() if e["n"] >= difficulty.MIN_N}
    moved = {}
    for pid, e in rated.items():
        adj = difficulty.adjusted_level({"id": pid, "level": e["level"]}, est)
        if adj != float(e["level"]):
            moved[pid] = adj
    big = sum(1 for pid, adj in moved.items() if abs(adj - rated[pid]["level"]) >= 1.0)
    rounded = sum(1 for pid, adj in moved.items() if round(adj) != rated[pid]["level"])
    answers = sum(e["n"] for e in est.values())
    n_dist = {}
    for e in est.values():
        n_dist[e["n"]] = n_dist.get(e["n"], 0) + 1
    lines.append(f"- Answers: {answers}; problems answered: {len(est)} of {len(bank.ids)} in the bank; "
                 f"with at least {difficulty.MIN_N} answers (rated): {len(rated)}.")
    lines.append("- Answers per problem: " + ", ".join(f"n={n}: {c}" for n, c in sorted(n_dist.items())) + ".")
    lines.append(f"- Rated problems whose adjusted level differs from the band: {len(moved)} of {len(rated)}; "
                 f"{rounded} change band once rounded, as the trainer's rule does ({big} move by one level or more).")
    levels = [e["level"] for e in est.values()]
    rates = [e["p_correct"] for e in est.values()]
    lines.append(f"- Correlation between the M3Kang band and the observed rate of correct answers, over the "
                 f"{len(est)} answered problems: Pearson {fmt(pearson(levels, rates))}, Spearman {fmt(spearman(levels, rates))} "
                 f"(negative = harder bands are answered less often).")
    rep = difficulty.report(db_path)
    lines.append("")
    lines.append("Rate per level (`by_level` of the report; `prior` is the shrunk rate the estimator uses):")
    lines.append("")
    lines.append(table(["level", "n", "correct", "p_correct", "prior"],
                       [(r["level"], r["n"], r["correct"], r["p_correct"], r["prior"]) for r in rep["by_level"]]))
    return est, rated, moved, rep


def report_tables(rep, lines):
    cols = ["id", "level", "n", "p_correct", "p_without_hints", "shrunk", "adjusted_level"]
    for key in ("hardest", "easiest"):
        lines.append("")
        lines.append(f"{rep['labels'][key]['en']} / {rep['labels'][key]['ca']} (`{key}`):")
        lines.append("")
        lines.append(table(cols, [tuple(r[c] for c in cols) for r in rep[key]]))


def hidden_accuracy(est, rated, lines):
    """Band vs adjusted level against the hidden difficulty, on the rated problems."""
    bank = trainer.bank()
    err_band, err_adj, right, wrong, flat = [], [], 0, 0, 0
    for pid, e in rated.items():
        p = bank.get(pid)
        true = hidden_level(p)
        adj = difficulty.adjusted_level(p, est)
        err_band.append(abs(e["level"] - true))
        err_adj.append(abs(adj - true))
        offset = true - e["level"]
        shift = adj - e["level"]
        if offset == 0 or abs(shift) < 0.5:
            flat += 1
        elif (shift > 0) == (offset > 0):
            right += 1
        else:
            wrong += 1
    off_band = sum(1 for x in err_band if x > 0)
    lines.append(f"- Rated problems off their band in the hidden model: {off_band} of {len(rated)}.")
    lines.append(f"- Mean absolute error against the hidden difficulty, over the {len(rated)} rated problems: "
                 f"band {fmt(statistics.fmean(err_band)) if err_band else 'nan'} levels, "
                 f"adjusted level {fmt(statistics.fmean(err_adj)) if err_adj else 'nan'} levels.")
    lines.append(f"- Shifts of half a level or more on problems that are off their band: {right} point the right way, "
                 f"{wrong} the wrong way; {flat} rated problems are on their band or barely moved.")


def probe(db_source, neighbors_fn, steps, tmpdir, lines, tag=""):
    """Each probe twice, flag off and on, from a copy of the class's database."""
    rows = []
    class_est = difficulty.estimate(db_source)
    for threshold in PROBE_THRESHOLDS:
        for flag in (False, True):
            db = os.path.join(tmpdir, f"probe{tag}-{threshold}-{int(flag)}.db")
            shutil.copy(db_source, db)
            configure(db, neighbors_fn)
            trainer.DIFFICULTY_ADJUST = flag
            student = HiddenStudent(f"probe{threshold}", threshold, seed=7)
            t0 = time.perf_counter()
            log, calls = simulate.run_student(student, steps)
            ms = 1000 * (time.perf_counter() - t0) / steps
            m = simulate.metrics(student, log, calls)
            wrong = sum(1 for x in log if not x["correct"])
            hidden_all = [hidden_level(trainer.bank().get(x["id"])) for x in log]
            hidden = hidden_all[-simulate.TAIL:]
            distance = statistics.fmean(abs(h - threshold) for h in hidden_all)
            # Steps whose problem had a class estimate that moves it half a level or more:
            # the only steps where the flag can change the next choice
            active = sum(1 for x in log if x["id"] in class_est and class_est[x["id"]]["n"] >= difficulty.MIN_N
                         and abs(difficulty.adjusted_level({"id": x["id"], "level": x["level"]}, class_est) - x["level"]) >= 0.5)
            rows.append((f"hidden threshold {threshold}", "on" if flag else "off", steps, wrong, fmt(distance),
                         active, m["band"], f"{min(hidden)}-{max(hidden)}", m["steps_to_settle"], m["repeats"], fmt(ms, 1)))
    trainer.DIFFICULTY_ADJUST = False
    lines.append(table(["probe", "DIFFICULTY_ADJUST", "n", "wrong answers", "mean hidden level - threshold",
                        "steps on a rated problem", "settled band (M3Kang)", "hidden levels, last 10",
                        "steps to settle", "repeats", "laptop ms/step"], rows))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--steps", type=int, default=60)
    p.add_argument("--neighbors", default="retrieval", choices=["retrieval", "index"],
                   help="copilot.retrieval (needs the embedding server for validation ids) or the index stop-gap")
    p.add_argument("--long-steps", type=int, default=300,
                   help="steps per student of the long-history hidden class (experiment 4); 0 skips it")
    p.add_argument("--out", default=os.path.join("docs", "difficulty.md"))
    p.add_argument("--keep-db", default="", help="folder to keep the class databases in (default: temporary)")
    args = p.parse_args()

    if not any(os.path.exists(x) for x in trainer.DEFAULT_BANK):
        raise SystemExit("no data/train.jsonl or data/val.jsonl: link ~/m3kang-data first")
    neighbors_fn = None
    if args.neighbors == "index":
        neighbors_fn = simulate.make_index_neighbors(os.path.join(trainer.ROOT, "data", "index.db"))

    tmp = tempfile.TemporaryDirectory()
    folder = args.keep_db or tmp.name
    os.makedirs(folder, exist_ok=True)
    lines = ["# Empirical difficulty per class: measurements on a SIMULATED class", "",
             "Every figure in this file comes from simulated students whose success depends on a difficulty "
             "planted by this script. Nothing is measured with real students yet; the recommended use of "
             "copilot/difficulty.py is the teacher's report(), not the choice of problems.", "",
             f"`python3 laptop/measure_difficulty.py --steps {args.steps} --neighbors {args.neighbors}` on "
             f"{time.strftime('%d %b %Y')}, laptop, bank data/train.jsonl + data/val.jsonl. "
             f"Estimator constants: a = {difficulty.PRIOR_WEIGHT}, MIN_N = {difficulty.MIN_N}, "
             f"{difficulty.POINTS_PER_LEVEL:.2f} rate points per level, max shift {difficulty.MAX_SHIFT:g} levels. "
             "See the module docstring of copilot/difficulty.py for the formula and laptop/measure_difficulty.py "
             "for the four experiments.", ""]

    # 1. Label class
    db1 = os.path.join(folder, "label-class.db")
    configure(db1, neighbors_fn)
    trainer.DIFFICULTY_ADJUST = False
    students = simulate.parse_students(LABEL_STUDENTS)
    t0 = time.perf_counter()
    run_class(students, args.steps)
    secs = time.perf_counter() - t0
    lines += ["## 1. Label class: ten of simulate's students, true difficulty = M3Kang band", "",
              f"Students: {LABEL_STUDENTS}; {args.steps} steps each, {secs:.1f} s on the laptop.", ""]
    _est1, _rated1, _moved1, rep1 = estimate_summary(db1, lines)
    report_tables(rep1, lines)

    # 2. Hidden class
    db2 = os.path.join(folder, "hidden-class.db")
    configure(db2, neighbors_fn)
    hidden = [HiddenStudent(f"hidden{i}-t{t}", t, seed=i) for i, t in enumerate(HIDDEN_THRESHOLDS)]
    t0 = time.perf_counter()
    run_class(hidden, args.steps)
    secs = time.perf_counter() - t0
    bank = trainer.bank()
    off = sum(1 for pid in bank.ids if hidden_offset(pid) != 0)
    lines += ["", "## 2. Hidden class: ten threshold students on a hidden difficulty", "",
              f"Thresholds {HIDDEN_THRESHOLDS}; hidden level = band + offset(id), offsets -2/-1/0/+1/+2 for "
              f"10/20/40/20/10% of the ids ({off} of {len(bank.ids)} bank problems are off their band); a student "
              f"above their threshold guesses a letter. {args.steps} steps each, {secs:.1f} s on the laptop.", ""]
    est2, rated2, _moved2, rep2 = estimate_summary(db2, lines)
    lines.append("")
    hidden_accuracy(est2, rated2, lines)
    report_tables(rep2, lines)

    # 3. Probes
    lines += ["", "## 3. Probes: a new student on the hidden class's history, flag off and on", "",
              f"Three hidden-difficulty students (thresholds {PROBE_THRESHOLDS}) run {args.steps} steps each on a "
              "copy of the hidden class's database, once with DIFFICULTY_ADJUST=0 and once with 1 (same seeds). "
              "The settled band is simulate's (last 10 non-review problems, M3Kang levels); the hidden column is "
              "the hidden levels of the last 10 problems served, which is what the student actually faced.", ""]
    probe(db2, neighbors_fn, args.steps, folder, lines)

    # 4. Long history
    if args.long_steps:
        db4 = os.path.join(folder, "hidden-long.db")
        configure(db4, neighbors_fn)
        hidden = [HiddenStudent(f"hidden{i}-t{t}", t, seed=i) for i, t in enumerate(HIDDEN_THRESHOLDS)]
        t0 = time.perf_counter()
        run_class(hidden, args.long_steps)
        secs = time.perf_counter() - t0
        lines += ["", f"## 4. Long history: the hidden class after {args.long_steps} steps per student", "",
                  f"Same ten students and offsets as experiment 2, {args.long_steps} steps each ({secs:.1f} s on the "
                  "laptop): what the estimate and the probes look like once the class has a term's worth of answers.", ""]
        est4, rated4, _moved4, rep4 = estimate_summary(db4, lines)
        lines.append("")
        hidden_accuracy(est4, rated4, lines)
        report_tables(rep4, lines)
        lines += ["", f"Probes ({args.steps} steps each) on this history:", ""]
        probe(db4, neighbors_fn, args.steps, folder, lines, tag="-long")

    trainer.configure()
    text = "\n".join(lines) + "\n"
    out = os.path.join(trainer.ROOT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # Hand-written notes at the end of the file (from the NOTES_MARKER line on) survive a rerun
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            old = f.read()
        if NOTES_MARKER in old:
            text += "\n" + old[old.index(NOTES_MARKER):]
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print(f"written to {args.out}")
    tmp.cleanup()


if __name__ == "__main__":
    main()
