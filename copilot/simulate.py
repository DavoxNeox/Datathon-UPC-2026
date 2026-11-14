"""Synthetic students against the adaptive trainer: does the path settle at the right level?

    python3 -m copilot.simulate                       # synthetic bank, every student type
    python3 -m copilot.simulate --bank data --steps 40  # real retrieval and data/train.jsonl
    python3 -m copilot.simulate --bank stub            # the Phase 0 stubs and sample problems

Standard library only, so it also runs on the board. Three banks:

- `synthetic`: 8 topics x 8 levels x PER_CELL made-up problems and a neighbour function
  that respects level and topic (what B's retrieval promises), so the trainer's rules can
  be checked before the real data exists. The numbers say nothing about M3Kang itself.
- `stub`: the Phase 0 retrieval stub over data/sample_problems.jsonl (5 problems).
- `data`: `copilot.retrieval` as it is, over data/train.jsonl. Each step then costs one
  real embedding; these are the numbers to report.

Student models (answer(problem) -> (letter, hint_rung)):

- threshold N: correct on levels <= N, wrong above, never a hint
- random20: a letter at random (20% correct), never a hint
- always: always correct, never a hint
- improving: threshold that rises one level every IMPROVE_EVERY problems
- hints_only: always correct, but always after hint rung 2 (must cap at mastery 2)

Metrics per student: the band of levels where the path settles, how many problems it took,
how often the next problem stays on the topic after a wrong answer, how many topics rose to
mastery 3+ (false rises for random20), reviews served, repeated problems, and the time per
step on the laptop with the board estimate (one embedding per neighbour call).
"""
import argparse
import os
import random
import statistics
import tempfile
import time
from collections import Counter

from . import board_clock, trainer
from .topics import TOPIC_KEYS

PER_CELL = 6           # synthetic problems per (topic, level)
IMPROVE_EVERY = 8
TAIL = 10              # last problems that define the settled band


# ----------------------------------------------------------------------------- synthetic bank

def synthetic_problems(per_cell=PER_CELL):
    """8 topics x 8 levels x per_cell Problem dicts with a `topic` field, in Catalan."""
    problems = []
    for topic in TOPIC_KEYS:
        for level in range(8):
            for i in range(per_cell):
                pid = f"syn-{topic}-{level}-{i}"
                label = "ABCDE"[(level + i) % 5]
                problems.append({"id": pid, "language": "cat", "level": level, "year": 2000 + level,
                                 "text_only": True, "topic": topic,
                                 "text": f"Problema sintètic {topic} nivell {level} número {i}.",
                                 "options": {k: str(n) for k, n in zip("ABCDE", range(1, 6))},
                                 "label": label})
    return problems


def _parse(pid):
    _, topic, level, _ = pid.split("-")
    return topic, int(level)


def make_synthetic_neighbors(problems):
    """A neighbour function with retrieval's contract over the synthetic bank.

    Most similar first is faked with a shuffle seeded by the query id, so the order is
    stable. Without `same_topic` the same topic still comes first, as embeddings tend to.
    """
    by_cell = {}
    for p in problems:
        by_cell.setdefault((p["topic"], p["level"]), []).append(p)

    def neighbors(problem_id, level_delta=0, same_topic=True, lang="cat", k=1):
        topic, level = _parse(problem_id)
        wanted = max(0, min(7, level + level_delta))
        rng = random.Random(f"{problem_id}:{level_delta}:{same_topic}")
        for distance in range(8):
            hits = []
            for lvl in sorted({max(0, wanted - distance), min(7, wanted + distance)}):
                same = [p for p in by_cell.get((topic, lvl), []) if p["id"] != problem_id]
                rng.shuffle(same)
                hits.extend(same)
                if not same_topic:
                    others = [p for t in TOPIC_KEYS if t != topic for p in by_cell.get((t, lvl), [])]
                    rng.shuffle(others)
                    hits.extend(others)
            if hits:
                return [dict(p) for p in hits[:k]]
        return []

    return neighbors


# ----------------------------------------------------------------------------- students

def _wrong_letter(label, rng):
    return rng.choice([c for c in "ABCDE" if c != label])


class Student:
    def __init__(self, name, kind, param=None, seed=0):
        self.name, self.kind, self.param = name, kind, param
        self.rng = random.Random(f"{name}:{seed}")
        self.answered = 0

    def expected_band(self):
        if self.kind == "threshold":
            return (self.param, min(7, self.param + 1))
        if self.kind == "always":
            return (7, 7)
        return None

    def answer(self, problem):
        label = problem.get("label", "A")
        level = problem.get("level", 0)
        self.answered += 1
        if self.kind == "threshold":
            return (label if level <= self.param else _wrong_letter(label, self.rng)), 0
        if self.kind == "random20":
            return self.rng.choice("ABCDE"), 0
        if self.kind == "always":
            return label, 0
        if self.kind == "hints_only":
            return label, 2
        if self.kind == "improving":
            threshold = min(7, 1 + (self.answered - 1) // IMPROVE_EVERY)
            return (label if level <= threshold else _wrong_letter(label, self.rng)), 0
        raise ValueError(self.kind)


def parse_students(spec):
    students = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if item.startswith("threshold"):
            students.append(Student(item, "threshold", int(item[len("threshold"):])))
        elif item.startswith("random20"):
            suffix = item[len("random20"):] or "0"
            students.append(Student(item, "random20", seed=int(suffix.lstrip("-") or 0)))
        elif item in ("always", "hints_only", "improving"):
            students.append(Student(item, item))
        else:
            raise SystemExit(f"unknown student type: {item}")
    return students


# ----------------------------------------------------------------------------- one run

def run_student(student, steps):
    """Drive one student through `steps` problems; return the per-step log and timings."""
    log = []
    seen = set()
    neighbor_calls_before = trainer.stats["neighbor_calls"]
    for _ in range(steps):
        t0 = time.perf_counter()
        problem = trainer.next_problem(student.name)
        letter, rung = student.answer(problem)
        result = trainer.record_answer(student.name, problem["id"], letter, rung)
        seconds = time.perf_counter() - t0
        log.append({"id": problem["id"], "level": problem["level"], "topic": result["topic"],
                    "correct": result["correct"], "review": result["review"],
                    "mastery_before": result["mastery_before"], "mastery_after": result["mastery_after"],
                    "repeat": problem["id"] in seen, "seconds": seconds})
        seen.add(problem["id"])
    calls = trainer.stats["neighbor_calls"] - neighbor_calls_before
    return log, calls


def metrics(student, log, calls):
    """The table row for one student."""
    path = [x for x in log if not x["review"]]
    levels = [x["level"] for x in path]
    tail = levels[-TAIL:]
    band = (min(tail), max(tail)) if tail else (None, None)
    settled = tail and band[1] - band[0] <= 1
    steps_to_settle = None
    if settled:
        steps_to_settle = len(levels)
        for i in range(len(levels)):
            if all(band[0] <= lvl <= band[1] for lvl in levels[i:]):
                steps_to_settle = i
                break
    expected = student.expected_band()
    converged = "n/a"
    if expected is not None and settled:
        converged = "yes" if (band[0] >= expected[0] - 0 and band[1] <= expected[1]) else "no"
    elif expected is not None:
        converged = "no"

    # After a wrong answer, is the next (non-review) problem on the same topic?
    # (a review is a detour: the path resumes from the last non-review problem)
    same, pairs, same_any, pairs_any = 0, 0, 0, 0
    for a, b in zip(path, path[1:]):
        if a["correct"]:
            continue
        pairs += 1
        same += a["topic"] == b["topic"]
    for a, b in zip(log, log[1:]):
        if a["correct"] or a["review"]:
            continue
        pairs_any += 1
        same_any += a["topic"] == b["topic"]

    rises = sum(1 for x in log if x["mastery_after"] >= 3 > x["mastery_before"])
    final = trainer.mastery_map(student.name)
    high = sum(1 for v in final.values() if v >= 3)
    seconds = [x["seconds"] for x in log]
    python_ms = 1000 * statistics.mean(seconds)
    per_step_calls = calls / len(log)
    board = board_clock.estimate_tokens(0, 0, embeddings=per_step_calls, python_seconds=statistics.mean(seconds))
    return {
        "student": student.name,
        "steps": len(log),
        "accuracy": f"{100 * sum(x['correct'] for x in log) / len(log):.0f}%",
        "band": f"{band[0]}-{band[1]}" if settled else (f"{band[0]}-{band[1]} (unsettled)" if tail else "-"),
        "expected": f"{expected[0]}-{expected[1]}" if expected else "-",
        "converged": converged,
        "steps_to_settle": steps_to_settle if steps_to_settle is not None else "-",
        "same_topic_after_fail": f"{100 * same / pairs:.0f}% ({same}/{pairs})" if pairs else "-",
        "same_topic_incl_reviews": f"{100 * same_any / pairs_any:.0f}% ({same_any}/{pairs_any})" if pairs_any else "-",
        "topics_mastery_3plus": high,
        "rises_to_3plus": rises,
        "max_mastery": max(final.values()),
        "reviews": sum(x["review"] for x in log),
        "repeats": sum(x["repeat"] for x in log),
        "laptop_ms": f"{python_ms:.1f}",
        "embeddings_per_step": f"{per_step_calls:.2f}",
        "board_s_est": f"{board:.2f}",
    }


COLUMNS = [("student", "student"), ("steps", "n"), ("accuracy", "acc"), ("band", "settled levels"),
           ("expected", "expected"), ("converged", "converged"), ("steps_to_settle", "steps to settle"),
           ("same_topic_after_fail", "same topic after fail"), ("same_topic_incl_reviews", "next shown incl. reviews"),
           ("topics_mastery_3plus", "topics >=3"), ("rises_to_3plus", "rises to >=3"), ("max_mastery", "max mastery"),
           ("reviews", "reviews"), ("repeats", "repeats"), ("laptop_ms", "laptop ms/step"),
           ("embeddings_per_step", "emb/step"), ("board_s_est", "board s/step (est.)")]


def markdown_table(rows):
    head = [title for _, title in COLUMNS]
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(r[key]) for key, _ in COLUMNS) + " |")
    return "\n".join(lines)


def setup_bank(kind, db_path):
    if kind == "synthetic":
        problems = synthetic_problems()
        trainer.configure(db_path=db_path, problems=problems, neighbors_fn=make_synthetic_neighbors(problems))
    elif kind == "stub":
        trainer.configure(db_path=db_path, bank_paths=[trainer.SAMPLE_BANK])
    elif kind == "data":
        trainer.configure(db_path=db_path)
        if not any(os.path.exists(p) for p in trainer.DEFAULT_BANK):
            raise SystemExit("no data/train.jsonl or data/val.jsonl: link ~/m3kang-data first")
    else:
        raise SystemExit(f"unknown bank: {kind}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bank", default="synthetic", choices=["synthetic", "stub", "data"])
    p.add_argument("--steps", type=int, default=40)
    p.add_argument("--students", default="threshold2,threshold5,random20-1,random20-2,random20-3,always,improving,hints_only")
    p.add_argument("--db", default="", help="SQLite file (default: a fresh temporary file)")
    p.add_argument("--path", action="store_true", help="print every step of every student")
    args = p.parse_args()

    tmp = None
    db_path = args.db
    if not db_path:
        tmp = tempfile.TemporaryDirectory()
        db_path = os.path.join(tmp.name, "students.db")
    setup_bank(args.bank, db_path)
    students = parse_students(args.students)

    rows = []
    for student in students:
        log, calls = run_student(student, args.steps)
        rows.append(metrics(student, log, calls))
        if args.path:
            print(f"\n{student.name}:")
            for n, x in enumerate(log, 1):
                print(f"  {n:3} {x['id']:28} L{x['level']} {x['topic']:10} "
                      f"{'ok ' if x['correct'] else 'KO '} m{x['mastery_before']}->{x['mastery_after']}"
                      f"{' review' if x['review'] else ''}{' REPEAT' if x['repeat'] else ''}")
    print(f"\nBank: {args.bank}, {args.steps} problems per student, trainer db {db_path}")
    print(markdown_table(rows))
    print("\nboard s/step = embeddings x BOARD_EMBED_SECONDS + Python time as measured on the laptop "
          "(the board's Python is slower; not yet measured).")
    if args.bank != "data":
        print("These numbers test the trainer's rules, not M3Kang: rerun with --bank data for the real figures.")
    trainer.configure()
    if tmp:
        tmp.cleanup()


if __name__ == "__main__":
    main()
