"""The student's copilot session behind the web page: problems, answers, the hint ladder, the LED.

Owner: D (branch `hints-app`). Pure app logic: every handler takes path parameters and returns
a JSON-able dict, whatever serves it (copilot/hal/web.py). Nothing here calls the LLM inside a
handler: the hint ladder runs in a thread and the page polls /api/state.

    routes()   -> [(method, path, handler), ...] for hal.web.serve
    start()    -> draw the resting LED frame
"""
import base64
import os
import threading
import time

from . import hints, topics, trainer
from .board_clock import estimate_tokens
from .config import ROOT
from .hal import led

RESULT_SECONDS = 3.0        # the tick or cross stays this long, then the mastery map comes back
LANGS = ("cat", "eng")
TOPIC_NAMES = {t["key"]: t for t in topics.TOPICS}


class Session:
    """One student at the page. The app serves one student at a time (one board, one page)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.student = "demo"
        self.lang = "cat"
        self.problem = None          # the Problem dict as served (with its label, never sent)
        self.rung = 0                # highest rung used on this problem
        self.hints = []              # hint results shown, in order
        self.answer = None           # {"letter", "correct", ...} after answering
        self.busy = False
        self.message = {"ca": "", "en": ""}
        self.timeline = []           # the last actions: {"action", "laptop_s", "board_s"}
        self.mastery = {}
        self.students = set()
        self._timer = None

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

    def _show_mastery(self):
        self.mastery = trainer.mastery_map(self.student)
        led.show_mastery(self.mastery)

    def _load_next(self):
        started = time.perf_counter()
        self.problem = trainer.next_problem(self.student)
        hints.register_problem(self.problem)
        self.rung, self.hints, self.answer = 0, [], None
        self.message = {"ca": "Tria una resposta, o demana una pista.", "en": "Choose an answer, or ask for a hint."}
        hints.prefetch(self.problem["id"], self.lang)
        self._show_mastery()
        self._record("next", started)

    # ------------------------------------------------------------ handlers

    def state(self):
        with self.lock:
            return {
                "student": self.student, "lang": self.lang, "problem": self._public_problem(),
                "rung": self.rung, "hints": self.hints, "answer": self.answer, "busy": self.busy,
                "message": self.message, "timeline": self.timeline, "mastery": self.mastery,
                "led": led.last_frame(), "llm_allowed": bool(self.problem) and
                hints.llm_allowed(self.problem.get("topic") or topics.get_topic(self.problem["id"])),
            }

    def set_student(self, student):
        student = student.strip()[:32] or "demo"
        with self.lock:
            self.student = student
            self.students.add(student)
            self._load_next()
        return self.state()

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
            result = trainer.record_answer(self.student, self.problem["id"], letter, self.rung)
            self.answer = {"letter": letter, **result}
            led.show_result(result["correct"])
            if result["correct"]:
                self.message = {"ca": "Correcte!", "en": "Correct!"}
            else:
                self.message = {"ca": f"No és això. La resposta era {result['label']}.",
                                "en": f"Not this time. The answer was {result['label']}."}
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

    def hint(self):
        """Climb one rung (1, 2, then 3 again and again) in a thread; the page polls /api/state."""
        with self.lock:
            if not self.problem or self.busy:
                return {"error": "busy" if self.busy else "no problem"}
            if self.answer:
                return {"error": "already answered"}
            rung = min(3, self.rung + 1)
            self.busy = True
            self.message = {"ca": "Pensant una pista…", "en": "Thinking of a hint…"}
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

    def _compute_hint(self, rung):
        started = time.perf_counter()
        problem_id = self.problem["id"]
        try:
            result = hints.get_hint(problem_id, rung, self.lang)
        except Exception as error:  # never leave the page waiting
            result = {"rung": rung, "kind": "strategy", "estimated_board_seconds": 0.0,
                      "text_ca": "No he pogut preparar la pista.", "text_en": "I could not prepare the hint.",
                      "error": f"{type(error).__name__}: {error}"}
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
                self.message = {"ca": "", "en": ""}
            self.busy = False
            self._record(f"hint{rung}:{result.get('kind')}", started, result.get("estimated_board_seconds", 0.0))

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
        out = {"topics": topics.TOPICS, "students": {}, "by_level": None, "source": "mastery_map"}
        if callable(report):
            try:
                data = report()
                if isinstance(data, dict):
                    out.update(data)
                    out["source"] = "teacher_report"
                    return out
            except Exception as error:
                out["error"] = f"teacher_report: {type(error).__name__}: {error}"
        for s in students:
            out["students"][s] = trainer.mastery_map(s)
        return out

    def estimate(self, prompt_tokens, output_tokens):
        """Board seconds for a request of this size (the page shows it next to measured times)."""
        return {"board_seconds": round(estimate_tokens(int(prompt_tokens), int(output_tokens)), 2)}


def _read_image(relative_path):
    try:
        with open(os.path.join(ROOT, relative_path), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError:
        return None


SESSION = Session()


def routes(session=SESSION):
    return [
        ("GET", "/api/state", session.state),
        ("GET", "/api/student/{student}", session.set_student),
        ("GET", "/api/lang/{lang}", session.set_lang),
        ("GET", "/api/next", session.next),
        ("GET", "/api/answer/{letter}", session.answer_letter),
        ("GET", "/api/hint", session.hint),
        ("GET", "/api/solution", session.solution),
        ("GET", "/api/image", session.image),
        ("GET", "/api/led", session.led_frame),
        ("GET", "/api/led/path/{grid}", session.led_path),
        ("GET", "/api/teacher", session.teacher),
        ("GET", "/api/estimate/{prompt_tokens}/{output_tokens}", session.estimate),
    ]


def start(session=SESSION):
    """Load the first problem and draw the resting frame."""
    with session.lock:
        session.students.add(session.student)
        session._load_next()
