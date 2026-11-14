"""The student's copilot session behind the web page: problems, answers, the hint ladder, the LED.

Owner: D (branch `hints-app`). Pure app logic: every handler takes path parameters and returns
a JSON-able dict, whatever serves it (copilot/hal/web.py). Nothing here calls the LLM inside a
handler: the hint ladder runs in a thread and the page polls /api/state.

    routes()   -> [(method, path, handler), ...] for hal.web.serve
    start()    -> draw the resting LED frame
"""
import base64
import importlib
import json
import os
import threading
import time

from . import hints, topics, trainer
from .board_clock import estimate_tokens
from .config import CONFIG, ROOT
from .hal import led

RESULT_SECONDS = 3.0        # the tick or cross stays this long, then the mastery map comes back
LANGS = ("cat", "eng")
TOPIC_NAMES = {t["key"]: t for t in topics.TOPICS}
# Rung 0 counters survive a restart of the app here (data/ is git-ignored, no problem text inside)
RUNG0_FILE = os.path.join(ROOT, "data", "rung0.json")


def _empty_counts():
    return {"uses": 0, "problems": 0, "with": {"answers": 0, "correct": 0}, "without": {"answers": 0, "correct": 0}}


HINT_MAX_USES = int(CONFIG.get("HINT_MAX_USES", 3))  # hint-button uses per problem; rung 0 and the solution do not count
# The last allowed press gives a short lesson (hints.get_lesson) instead of another hint
HINT_LESSON_ON_LAST = str(CONFIG.get("HINT_LESSON_ON_LAST", "1")).strip().lower() in ("1", "true", "yes", "on")
LESSON_RUNG = 3  # what the lesson counts as for mastery (record_answer)


class Rung0Stats:
    """How often the problem was read in the other language (rung 0), per student and in this
    session, and whether the answer that followed was right. Pseudonyms and counts only."""

    def __init__(self, path=None):
        self.path = path
        self.session = _empty_counts()
        self.students = {}
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self.students = {k: v for k, v in json.load(f).get("students", {}).items()}
            except (OSError, ValueError):
                self.students = {}

    def _row(self, student):
        return self.students.setdefault(student, _empty_counts())

    def use(self, student, first_on_this_problem):
        for row in (self._row(student), self.session):
            row["uses"] += 1
            if first_on_this_problem:
                row["problems"] += 1
        self._save()

    def answer(self, student, used_rung0, correct):
        key = "with" if used_rung0 else "without"
        for row in (self._row(student), self.session):
            row[key]["answers"] += 1
            row[key]["correct"] += int(bool(correct))
        self._save()

    def forget(self, student):
        self.students.pop(student, None)
        self._save()

    def report(self):
        """For the teacher page: who uses rung 0 and the accuracy after it against without it."""
        out = {"students_using": sum(1 for r in self.students.values() if r["uses"]),
               "students_total": len(self.students), "uses": 0,
               "with": {"answers": 0, "correct": 0}, "without": {"answers": 0, "correct": 0},
               "by_student": self.students}
        for row in self.students.values():
            out["uses"] += row["uses"]
            for key in ("with", "without"):
                out[key]["answers"] += row[key]["answers"]
                out[key]["correct"] += row[key]["correct"]
        return out

    def _save(self):
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"students": self.students}, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.path)
        except OSError:
            pass  # counters are a convenience, never a reason to fail the page



def _diagnose(problem, letter):
    """The error signature of a wrong answer, or None: module absent, no signature, or low confidence."""
    try:
        signatures = importlib.import_module("copilot.signatures")  # optional module; importlib honours sys.modules
    except ImportError:
        return None
    try:
        result = signatures.diagnose(problem, letter)
    except Exception:  # a diagnosis must never break the correction
        return None
    if not result or result.get("confidence", "high") == "low":
        return None
    return result


class Session:
    """One student at the page. The app serves one student at a time (one board, one page)."""

    def __init__(self, stats_path=None):
        self.lock = threading.Lock()
        self.student = "demo"
        self.started = False         # the start screen is shown until the student presses "Comença"
        self.level = None            # the level chosen on the start screen, None = let the trainer decide
        self.lang = "cat"
        self.problem = None          # the Problem dict as served (with its label, never sent)
        self.rung = 0                # highest rung used on this problem
        self.hints = []              # hint results shown, in order
        self.hint_uses = 0           # times the hint button was accepted on this problem (max HINT_MAX_USES)
        self.answer = None           # {"letter", "correct", ...} after answering
        self.busy = False
        self.message = {"ca": "", "en": ""}
        self.timeline = []           # the last actions: {"action", "laptop_s", "board_s"}
        self.mastery = {}
        self.students = set()
        self._timer = None
        self.translation_shown = False   # rung 0: the other language is on the page
        self.rung0_uses = 0              # how many times rung 0 was opened on this problem
        self.rung0 = Rung0Stats(stats_path)

    # ------------------------------------------------------------ helpers

    def _record(self, action, started, board_s=0.0):
        self.timeline.append({"action": action, "laptop_s": round(time.perf_counter() - started, 3),
                              "board_s": round(board_s, 2)})
        del self.timeline[:-12]

    def _public_problem(self):
        p = self.problem
        if not p:
            return None
        shown = {k: v for k, v in p.items() if k != "label"}
        shown["has_image"] = hints._image_path(p["id"], p.get("language", "cat")) is not None
        topic = p.get("topic") or topics.get_topic(p["id"])
        shown["topic"] = topic
        shown["topic_name_ca"] = TOPIC_NAMES.get(topic, {}).get("name_ca", topic)
        shown["topic_name_en"] = TOPIC_NAMES.get(topic, {}).get("name_en", topic)
        # the same problem in the other language, when the data has it
        other = hints.problem_for(p["id"], "eng" if p.get("language") == "cat" else "cat")
        if other and other.get("language") != p.get("language"):
            shown["text_" + other["language"]] = other["text"]
            shown["options_" + other["language"]] = {k: v for k, v in (other.get("options") or {}).items()}
        return shown

    def _shown_language(self):
        """The language the statement is shown in: the page language when the data has that
        version, else the language the problem came in."""
        p = self.problem
        if not p:
            return self.lang
        return self.lang if hints.problem_in(p["id"], self.lang) else p.get("language", "cat")

    def _translation(self):
        """Rung 0 result for the current problem, or None when no other version exists."""
        if not self.problem:
            return None
        result = hints.translation(self.problem["id"], self._shown_language())
        return result if result.get("available") else None

    def _show_mastery(self):
        self.mastery = trainer.mastery_map(self.student)
        led.show_mastery(self.mastery)

    def _load_next(self):
        started = time.perf_counter()
        self.problem = trainer.next_problem(self.student)
        hints.register_problem(self.problem)
        self.rung, self.hints, self.answer = 0, [], None
        self.hint_uses = 0
        self.translation_shown, self.rung0_uses = False, 0
        self.message = {"ca": "Tria una resposta o demana una pista.", "en": "Choose an answer, or ask for a hint."}
        hints.prefetch(self.problem["id"], self.lang)
        self._show_mastery()
        self._record("next", started)

    # ------------------------------------------------------------ handlers

    def state(self):
        with self.lock:
            translation = self._translation()
            return {
                "student": self.student, "started": self.started, "level": self.level,
                "lang": self.lang, "problem": self._public_problem(),
                "shown_language": self._shown_language(),
                "translation_available": translation is not None,
                "other_language": translation["language"] if translation else None,
                "translation": translation if self.translation_shown else None,
                "rung0": {"uses": self.rung0_uses, "session": self.rung0.session},
                "rung": self.rung, "hints": self.hints, "answer": self.answer, "busy": self.busy,
                "hints_left": max(0, HINT_MAX_USES - self.hint_uses), "hints_max": HINT_MAX_USES,
                "message": self.message, "timeline": self.timeline, "mastery": self.mastery,
                "led": led.last_frame(), "llm_allowed": bool(self.problem) and
                hints.llm_allowed(self.problem.get("topic") or topics.get_topic(self.problem["id"]), self.lang),
            }

    def set_student(self, student):
        return self.start(student, "auto")

    def start(self, student, level="auto"):
        """The start screen's button: pseudonym, optional level 0..7 ("auto" = the trainer decides).

        Calls trainer.start_student(student_id, level) when the trainer has it (it returns the
        mastery map); otherwise the current flow, which starts with the trainer's diagnostic.
        """
        student = student.strip()[:32] or "demo"
        chosen = int(level) if str(level).isdigit() and 0 <= int(level) <= 7 else None
        started = time.perf_counter()
        with self.lock:
            self.student, self.level = student, chosen
            self.students.add(student)
            start_student = getattr(trainer, "start_student", None)
            if callable(start_student):
                try:
                    start_student(student, chosen) if chosen is not None else start_student(student)
                    self.rung0.forget(student)  # the trainer forgot this pseudonym: so do the rung 0 counters
                except Exception as error:  # an older trainer: keep going with its own flow
                    self.message = {"ca": "", "en": ""}
                    self.timeline.append({"action": f"start_student failed: {type(error).__name__}", "laptop_s": 0, "board_s": 0})
            self.started = True
            self._load_next()
            self._record("start", started)
        return self.state()

    def reset(self):
        """"Reinicia l'alumne": forget this student's history (trainer.reset_student when it exists)
        and go back to the start screen."""
        with self.lock:
            if self.busy:
                return {"error": "busy"}
            reset_student = getattr(trainer, "reset_student", None)
            done = False
            if callable(reset_student):
                try:
                    reset_student(self.student)
                    done = True
                except Exception as error:
                    self.timeline.append({"action": f"reset_student failed: {type(error).__name__}", "laptop_s": 0, "board_s": 0})
            if self._timer:
                self._timer.cancel()
            if done:
                self.rung0.forget(self.student)
            self.problem, self.rung, self.hints, self.answer = None, 0, [], None
            self.hint_uses = 0
            self.translation_shown, self.rung0_uses = False, 0
            self.started, self.level = False, None
            self.message = {"ca": "", "en": ""}
            self.mastery = trainer.mastery_map(self.student) if done else {}
            led.show_mastery(self.mastery)
        state = self.state()
        state["reset_supported"] = done
        return state

    def set_lang(self, lang):
        with self.lock:
            self.lang = lang if lang in LANGS else "cat"
        return self.state()

    def next(self):
        with self.lock:
            if self.busy:
                return {"error": "busy"}
            self._load_next()
        return self.state()

    def answer_letter(self, letter):
        letter = letter.upper()
        with self.lock:
            if letter not in "ABCDE" or len(letter) != 1 or not self.problem:
                return {"error": "choose A to E"}
            if self.answer or self.busy:
                return {"error": "already answered" if self.answer else "busy"}
            started = time.perf_counter()
            # rung 0 never touches self.rung: reading the other language is not a hint for mastery
            result = trainer.record_answer(self.student, self.problem["id"], letter, self.rung)
            self.answer = {"letter": letter, **result}
            self.rung0.answer(self.student, self.rung0_uses > 0, result["correct"])
            self.mastery = trainer.mastery_map(self.student)
            led.show_result(result["correct"])
            if result["correct"]:
                self.message = {"ca": "Molt bé, correcte!", "en": "Correct!"}
            else:
                self.message = {"ca": f"No és aquesta. La resposta correcta era la {result['label']}.",
                                "en": f"Not quite. The correct answer was {result['label']}."}
                # Error signature (copilot/signatures.py, when present): an explanation of the
                # slip, shown ONLY now that the problem is closed and the answer is on screen.
                # Never before answering: most signatures pin the correct option.
                diagnosis = _diagnose(self.problem, letter)
                if diagnosis:
                    self.answer["signature"] = diagnosis.get("signature")
                    self.message = {"ca": self.message["ca"] + " " + diagnosis.get("text_ca", ""),
                                    "en": self.message["en"] + " " + diagnosis.get("text_en", "")}
            self._record("answer", started)
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(RESULT_SECONDS, self._after_result)
            self._timer.daemon = True
            self._timer.start()
        return self.state()

    def _after_result(self):
        with self.lock:
            self._show_mastery()

    def translate(self, action="show"):
        """Rung 0: show (or hide) the same problem in the other language next to the statement.

        Each show is counted (per session and per student) and gets a timeline row, costs no
        model time and leaves `rung` alone, so `record_answer` still receives 0 when the student
        used nothing else.
        """
        started = time.perf_counter()
        with self.lock:
            if not self.problem:
                return {"error": "no problem"}
            if action == "hide":
                self.translation_shown = False
            else:
                if self._translation() is None:
                    return {"error": "no other language for this problem"}
                self.rung0.use(self.student, first_on_this_problem=self.rung0_uses == 0)
                self.rung0_uses += 1
                self.translation_shown = True
                self._record("rung0:translation", started)
        return self.state()

    def hint(self):
        """Climb one rung (1, 2, then 3 again and again) in a thread; the page polls /api/state."""
        with self.lock:
            if not self.problem or self.busy:
                return {"error": "busy" if self.busy else "no problem"}
            if self.answer:
                return {"error": "already answered"}
            if self.hint_uses >= HINT_MAX_USES:
                # The ladder is capped: three hints per problem, then the student answers or asks
                # for the solution on purpose. Rung 0 (the other language) does not count.
                self.message = {"ca": f"Ja has fet servir les {HINT_MAX_USES} pistes d'aquest problema. Prova-ho o demana la solució.",
                                "en": f"You have used the {HINT_MAX_USES} hints for this problem. Give it a try, or ask for the solution."}
                return {"error": "no hints left", "hints_left": 0}
            self.hint_uses += 1
            self.busy = True
            if HINT_LESSON_ON_LAST and self.hint_uses == HINT_MAX_USES:
                # the fourth hint: a short lesson on this kind of problem, not another step
                self.message = {"ca": "Preparant una petita lliçó…", "en": "Preparing a short lesson…"}
                threading.Thread(target=self._compute_hint, args=("lesson",), daemon=True).start()
                return {"ok": True, "busy": True, "rung": "lesson"}
            rung = min(3, self.rung + 1)
            self.message = {"ca": "Preparant una pista…", "en": "Thinking of a hint…"}
        threading.Thread(target=self._compute_hint, args=(rung,), daemon=True).start()
        return {"ok": True, "busy": True, "rung": rung}

    def solution(self):
        """Rung 4, only when the student asks for it on purpose."""
        with self.lock:
            if not self.problem or self.busy:
                return {"error": "busy" if self.busy else "no problem"}
            self.busy = True
        threading.Thread(target=self._compute_hint, args=(4,), daemon=True).start()
        return {"ok": True, "busy": True, "rung": 4}

    def _compute_lesson(self):
        """The last allowed press: hints.get_lesson, or a strategy card when there is no lesson.
        Either way it counts as rung 3 for mastery."""
        started = time.perf_counter()
        problem_id = self.problem["id"]
        try:
            result = hints.get_lesson(problem_id, self.lang)
            if result is None:
                result = hints.get_hint(problem_id, 2, self.lang)  # a strategy card
                result["rung"] = "lesson"
                result["fallback"] = "no lesson"
        except Exception as error:
            result = {"rung": "lesson", "kind": "strategy", "estimated_board_seconds": 0.0,
                      "text_ca": "Ara no puc preparar la lliçó. Torna-ho a provar.", "text_en": "I could not prepare the lesson.",
                      "error": f"{type(error).__name__}: {error}"}
        self._finish_hint(result, LESSON_RUNG, started, "lesson", problem_id)

    def _compute_hint(self, rung):
        """Runs in a thread: one rung of the ladder, or the lesson when rung == "lesson"."""
        if rung == "lesson":
            return self._compute_lesson()
        started = time.perf_counter()
        problem_id = self.problem["id"]
        try:
            result = hints.get_hint(problem_id, rung, self.lang)
        except Exception as error:  # never leave the page waiting
            result = {"rung": rung, "kind": "strategy", "estimated_board_seconds": 0.0,
                      "text_ca": "Ara no puc preparar cap pista. Torna-ho a provar.", "text_en": "I could not prepare the hint.",
                      "error": f"{type(error).__name__}: {error}"}
        self._finish_hint(result, rung, started, f"hint{rung}", problem_id)

    def _finish_hint(self, result, rung, started, label, problem_id):
        """Store a hint computed in a thread, unless the problem changed meanwhile."""
        laptop_s = time.perf_counter() - started
        if result.get("kind") == "neighbour" and result.get("problem"):
            image = result["problem"].get("image")
            if image:
                result["problem"]["image_b64"] = _read_image(image)
        result["laptop_seconds"] = round(laptop_s, 3)
        with self.lock:
            if self.problem and self.problem["id"] == problem_id:
                self.hints.append(result)
                self.rung = max(self.rung, rung)
                if not self.answer:  # after answering, the verdict stays (the solution does not erase it)
                    self.message = {"ca": "", "en": ""}
            self.busy = False
            self._record(f"{label}:{result.get('kind')}", started, result.get("estimated_board_seconds", 0.0))

    def image(self):
        """The current problem's picture as base64 PNG, or {} when there is none."""
        with self.lock:
            if not self.problem:
                return {}
            path = hints._image_path(self.problem["id"], self.problem.get("language", "cat"))
        return {"image_b64": _read_image(path)} if path else {}

    def led_path(self, grid):
        """Manipulative (b): the page sends the path-count grid as rows of ints, '1,1,1;1,2,3'."""
        rows = [[int(v or 0) for v in row.split(",")] for row in grid.split(";") if row]
        started = time.perf_counter()
        led.show_path(rows)
        with self.lock:
            self._record("led_path", started)
        return {"ok": True, "led": led.last_frame()}

    def led_frame(self):
        return {"led": led.last_frame()}

    def teacher(self):
        """Mastery by topic and student, and hits by level when the trainer reports them."""
        report = getattr(trainer, "teacher_report", None)
        students = sorted(self.students | {self.student})
        out = {"topics": topics.TOPICS, "students": {}, "by_level": None, "source": "mastery_map",
               "rung0": self.rung0.report()}
        if callable(report):
            try:
                data = report()
                if isinstance(data, dict):
                    return _normalise_report(data, out)
            except Exception as error:
                out["error"] = f"teacher_report: {type(error).__name__}: {error}"
        for s in students:
            out["students"][s] = trainer.mastery_map(s)
        return out

    def estimate(self, prompt_tokens, output_tokens):
        """Board seconds for a request of this size (the page shows it next to measured times)."""
        return {"board_seconds": round(estimate_tokens(int(prompt_tokens), int(output_tokens)), 2)}


def _normalise_report(data, out):
    """The page wants {"students": {name: {topic: 0..5}}, "by_level": {name: {level: {"correct", "total"}}}}.

    The trainer's teacher_report gives a list of students with "mastery" and "by_level"
    {level: {"answers", "correct"}}; an older shape with a dict of students is passed through.
    """
    out["source"] = "teacher_report"
    rows = data.get("students")
    if isinstance(rows, dict):
        out["students"] = rows
        out["by_level"] = data.get("by_level")
        return out
    by_level = {}
    for row in rows or []:
        name = str(row.get("student_id", "?"))
        out["students"][name] = row.get("mastery") or {}
        levels = row.get("by_level") or {}
        by_level[name] = {str(lvl): {"correct": int(v.get("correct") or 0), "total": int(v.get("answers", v.get("total", 0)) or 0)}
                          for lvl, v in levels.items()}
        out.setdefault("details", {})[name] = {k: row.get(k) for k in ("base_level", "diagnostic_done", "answers", "correct", "reviews")}
    out["by_level"] = by_level if any(by_level.values()) else None
    return out


def _read_image(relative_path):
    try:
        with open(os.path.join(ROOT, relative_path), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError:
        return None


SESSION = Session(stats_path=RUNG0_FILE)


def routes(session=SESSION):
    return [
        ("GET", "/api/state", session.state),
        ("GET", "/api/student/{student}", session.set_student),
        ("GET", "/api/start/{student}/{level}", session.start),
        ("GET", "/api/reset", session.reset),
        ("GET", "/api/lang/{lang}", session.set_lang),
        ("GET", "/api/next", session.next),
        ("GET", "/api/answer/{letter}", session.answer_letter),
        ("GET", "/api/translate/{action}", session.translate),
        ("GET", "/api/hint", session.hint),
        ("GET", "/api/solution", session.solution),
        ("GET", "/api/image", session.image),
        ("GET", "/api/led", session.led_frame),
        ("GET", "/api/led/path/{grid}", session.led_path),
        ("GET", "/api/teacher", session.teacher),
        ("GET", "/api/estimate/{prompt_tokens}/{output_tokens}", session.estimate),
    ]


def start(session=SESSION):
    """Draw the resting frame. The first problem loads when the student presses "Comença"."""
    with session.lock:
        session.students.add(session.student)
        session._show_mastery()
