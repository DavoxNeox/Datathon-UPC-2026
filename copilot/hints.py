"""The hint ladder: four rungs, from an easier neighbour to the solution.

Owner: D (branch `hints-app`). Contract in INTERFACES.md.

    prefetch(problem_id, lang)          # when the problem is shown: warm the LLM prompt cache in a thread
    get_hint(problem_id, rung, lang)    # rung 0..4, see below
    translation(problem_id, lang)       # rung 0 on its own: the problem in the other language

Rung 0  the same problem in the other language (M3Kang aligns Catalan and English by id), text
        and options, never the label. It separates "I don't understand the statement" from
        "I can't solve it", so it is NOT a hint for mastery: the app keeps hint_rung_used at 0.
Rung 1  an easier solved neighbour (retrieval.neighbors), with its image when the topic is visual
Rung 2  a strategy card of the topic (data_curated/strategies.json), maybe with a manipulative
Rung 3  (a) the next step of the solver trace, never the last one;
        (b) else a one-sentence LLM hint, only for topics whose judged quality reaches
            HINT_QUALITY_MIN (data_curated/hint_quality.json), checked by copilot/leak_filter.py
            and retried once with a stricter prompt;
        (c) else another strategy card
Rung 4  the solution: letter, value and the full trace, only when the student asks for it

The LLM never reasons here: it writes one sentence, given the problem AND the correct answer.
The student decides when to climb. Rungs 1, 2 and 4 use no model and cost well under a second.
"""
import json
import os
import re
import threading
import unicodedata

from . import retrieval, solvers, topics
from .board_clock import estimate
from .client import post
from .config import CONFIG, ROOT
from .leak_filter import leak_reason

STRATEGIES_FILE = os.path.join(ROOT, "data_curated", "strategies.json")
# Problems the team explains by hand for the demo: steps[] per id, the last step is the solution
DEMO_SET_FILE = os.path.join(ROOT, "data_curated", "demo_set.json")
# The fourth hint: a short lesson per solver family or topic, and the id -> family table
LESSONS_FILE = os.path.join(ROOT, "data_curated", "lessons.json")
FAMILIES_FILE = os.path.join(ROOT, "data_curated", "families.json")
QUALITY_FILE = os.path.join(ROOT, "data_curated", "hint_quality.json")
IMAGES_DIR = os.path.join(ROOT, "data", "images")
# Where problems are looked up by id: the shared splits when linked, else the samples
PROBLEM_FILES = [os.path.join(ROOT, "data", name) for name in
                 ("val.jsonl", "train.jsonl", "sample_problems.jsonl")]
STUDENT_LANGS = ("cat", "eng")

QUALITY_MIN = float(CONFIG.get("HINT_QUALITY_MIN", 70))
MAX_TOKENS = int(CONFIG.get("HINT_MAX_TOKENS", 40))
# A leaking hint is retried once only if the first attempt cost less than this (board seconds):
# a cold retry on a long problem would push rung 3 past the 60 s limit (measured max 92.5 s on val)
RETRY_BUDGET = float(CONFIG.get("HINT_RETRY_BUDGET", 30))
LLM_URL = f"http://{CONFIG['LLM_HOST']}:{CONFIG['LLM_PORT']}/v1/chat/completions"
LLM_TIMEOUT = float(CONFIG.get("TIME_LIMIT_SECONDS", 60))
# What prefetch() does in its thread: "full" writes the hint ahead, "warm" only reads the prompt, "off" nothing
PREFETCH = CONFIG.get("HINT_PREFETCH", "full")
# HINT_LLM_LANG=en: the model writes its hint in English only (its Catalan is poor) and the page shows
# that English sentence even in Catalan; the quality gate then uses percent_en. Empty: the page language.
LLM_LANG = (CONFIG.get("HINT_LLM_LANG", "") or "").strip().lower()


def _llm_lang(lang):
    """The language the LLM hint is written in and gated by."""
    return "eng" if LLM_LANG in ("en", "eng") else lang


def _llm_langs(lang):
    """The calls llm_hint makes: Catalan then English, or English only with HINT_LLM_LANG=en."""
    return ("eng",) if _llm_lang(lang) == "eng" and lang != "eng" and LLM_LANG else ("cat", "eng")

# Stable system prompt: llama-server caches the start of the prompt, so keep it identical.
SYSTEM = ("You are a maths tutor. You never give answers. You help with ONE short question that makes "
          "the student think about the first step of the problem.")
LANG_NAME = {"cat": "Catalan", "eng": "English", "spa": "Spanish"}

_lock = threading.Lock()
_problems = {}          # (id, language) -> Problem
_loaded = False
_state = {}             # problem_id -> {"strategy": int, "trace_step": int, "solved": ..., "llm": {...}}
_strategies = None
_quality = None
_demo_set = None        # {id: [steps]} from DEMO_SET_FILE, loaded once
_lessons = None         # [lesson dicts] from LESSONS_FILE, loaded once
_families = None        # {id: family key} from FAMILIES_FILE, loaded once


# ---------------------------------------------------------------- problems by id

def register_problem(problem):
    """Make a problem known to the ladder (the app calls it with what trainer.next_problem returned)."""
    with _lock:
        _problems[(problem["id"], problem.get("language", "cat"))] = problem


def _load_problems():
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        for path in PROBLEM_FILES:
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    p = json.loads(line)
                    if p.get("language") in STUDENT_LANGS or path.endswith("sample_problems.jsonl"):
                        _problems.setdefault((p["id"], p.get("language", "cat")), p)
        _loaded = True


def problem_for(problem_id, lang="cat"):
    """The problem in `lang`, else in English, else in any language we have. None if unknown."""
    _load_problems()
    for candidate in (lang, "eng", "cat"):
        p = _problems.get((problem_id, candidate))
        if p:
            return p
    for (pid, _l), p in _problems.items():
        if pid == problem_id:
            return p
    return None


def problem_in(problem_id, lang):
    """The problem exactly in `lang`, or None (no fallback to another language)."""
    _load_problems()
    return _problems.get((problem_id, lang))


def other_language(lang):
    """The other student language: Catalan for English and English for anything else."""
    return "cat" if lang == "eng" else "eng"


def translation(problem_id, lang="cat"):
    """Rung 0: the problem of this id in the other language, text and options, never the label.

    `lang` is the language the student is reading now. Returns a Hint result of kind
    "translation" with `available` False (and no text) when the data has no such version.
    Costs no model time: a dictionary lookup.
    """
    other = other_language(lang)
    problem = problem_in(problem_id, other)
    base = {"rung": 0, "kind": "translation", "language": other, "estimated_board_seconds": 0.0,
            "text_ca": "El mateix problema, en anglès." if other == "eng" else "El mateix problema, en català.",
            "text_en": "The same problem, in English." if other == "eng" else "The same problem, in Catalan."}
    if problem is None:
        return {**base, "available": False, "text": "", "options": {}}
    options = {k: str(v) for k, v in (problem.get("options") or {}).items() if k in "ABCDE"}
    return {**base, "available": True, "text": problem.get("text", ""), "options": options}


def reset(problem_id):
    """Forget the ladder position of a problem (a new attempt starts at the bottom)."""
    with _lock:
        _state.pop(problem_id, None)


def _st(problem_id):
    with _lock:
        return _state.setdefault(problem_id, {"strategy": 0, "trace_step": 0, "demo_step": 0, "solved": "?", "llm": {}})


def _topic_of(problem):
    return problem.get("topic") or topics.get_topic(problem["id"])


# ---------------------------------------------------------------- strategies and quality

def strategies(topic):
    global _strategies
    if _strategies is None:
        with open(STRATEGIES_FILE, encoding="utf-8") as f:
            _strategies = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    return _strategies.get(topic) or _strategies.get("arithmetic") or []


def demo_steps(problem_id):
    """The hand-written steps of a demo problem (data_curated/demo_set.json), or None.

    Each step has text_ca and text_en; the LAST one states the solution and only rung 4 shows it.
    A missing, empty or broken file means no demo problems, never an error.
    """
    global _demo_set
    if _demo_set is None:
        table = {}
        try:
            with open(DEMO_SET_FILE, encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("problems", []) if isinstance(data, dict) else []:
                steps = [st for st in entry.get("steps", []) if isinstance(st, dict) and (st.get("text_ca") or st.get("text_en"))]
                if entry.get("id") and steps:
                    table[entry["id"]] = steps
        except (OSError, ValueError):
            pass
        _demo_set = table
    return _demo_set.get(problem_id)


def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def family_of(problem_id):
    """The solver family of a problem from data_curated/families.json, or None."""
    global _families
    if _families is None:
        data = _load_json(FAMILIES_FILE, {})
        table = data.get("families", data) if isinstance(data, dict) else {}
        _families = {k: v for k, v in table.items() if isinstance(v, str)} if isinstance(table, dict) else {}
    return _families.get(problem_id)


def _lesson_list():
    global _lessons
    if _lessons is None:
        data = _load_json(LESSONS_FILE, {})
        rows = data.get("lessons", []) if isinstance(data, dict) else data
        _lessons = [r for r in (rows or []) if isinstance(r, dict) and (r.get("text_ca") or r.get("text_en"))]
    return _lessons


def get_lesson(problem_id, lang="cat"):
    """The fourth hint: a short lesson on how to think about this kind of problem, no formula and
    no solving. From data_curated/lessons.json: the lesson of the problem's solver family when
    there is one, else the lesson of its topic. Every text goes through the leak filter against
    this problem. None when the file is missing or nothing fits (the page then shows a strategy).
    """
    lessons = _lesson_list()
    if not lessons:
        return None
    problem = problem_for(problem_id, lang) or {"id": problem_id}
    topic = _topic_of(problem)
    family = family_of(problem_id)
    by_family = [r for r in lessons if family and r.get("family") == family]
    by_topic = [r for r in lessons if r.get("key") == topic and not r.get("family")]
    any_topic = [r for r in lessons if r.get("key") == topic and r not in by_topic]
    label, options = problem.get("label"), problem.get("options") or {}
    for row in by_family + by_topic + any_topic:
        texts = [row.get("title_ca", ""), row.get("title_en", ""), row.get("text_ca", ""), row.get("text_en", "")]
        if label and any(leak_reason(t, label, options) for t in texts if t):
            continue
        return {"kind": "lesson", "rung": "lesson", "key": row.get("key", topic), "family": row.get("family"),
                "title_ca": row.get("title_ca") or row.get("title_en") or "",
                "title_en": row.get("title_en") or row.get("title_ca") or "",
                "text_ca": row.get("text_ca") or row.get("text_en") or "",
                "text_en": row.get("text_en") or row.get("text_ca") or "",
                "strategy_ref": row.get("strategy_ref"), "estimated_board_seconds": 0.0}
    return None


def quality(topic, lang="cat"):
    """Judged quality (0..100) of the LLM hints of a topic in `lang`, or None when not judged yet.

    data_curated/hint_quality.json keeps `percent` for the Catalan hint (what the student sees
    by default) and `percent_en` for the English one, from laptop/judge_hints.py.
    """
    global _quality
    if _quality is None:
        _quality = {}
        if os.path.exists(QUALITY_FILE):
            with open(QUALITY_FILE, encoding="utf-8") as f:
                _quality = json.load(f).get("topics", {})
    row = _quality.get(topic)
    if not row or not row.get("n"):
        return None
    key = "percent_en" if lang == "eng" else "percent"
    return float(row.get(key, row.get("percent", 0)))


def llm_allowed(topic, lang="cat"):
    q = quality(topic, lang)
    return q is not None and q >= QUALITY_MIN


# ---------------------------------------------------------------- rungs

def _image_path(problem_id, lang):
    for candidate in (lang, "eng", "cat"):
        path = os.path.join(IMAGES_DIR, f"{problem_id}_{candidate}.png")
        if os.path.exists(path):
            return os.path.relpath(path, ROOT)
    return None


def _rung1(problem, lang):
    """An easier neighbour of the same topic. Never a harder one and never another topic: at level 0,
    or when nothing easier exists, a neighbour of the same level, said so."""
    level = int(problem.get("level", 0) or 0)
    topic = _topic_of(problem)
    hits = retrieval.neighbors(problem["id"], level_delta=-1, same_topic=True, lang=lang, k=5)
    fitting = [h for h in hits if int(h.get("level", level) or 0) <= level and h.get("topic", topic) == topic]
    if not fitting:
        return {"kind": "neighbour", "problem": None,
                "text_ca": "No tinc cap problema semblant més fàcil. Prova-ho amb una estratègia.",
                "text_en": "I have no similar, easier problem. Try a strategy."}
    shown = {k: v for k, v in fitting[0].items() if k != "label"}
    if topics.is_visual(topic):
        shown["image"] = _image_path(shown["id"], shown.get("language", lang))
    easier = int(shown.get("level", level) or 0) < level
    if easier:
        text_ca = f"Un problema semblant i més fàcil (nivell {shown['level']}). Com el resoldries?"
        text_en = f"A similar, easier problem (level {shown['level']}). How would you solve it?"
    else:
        text_ca = "Un problema semblant, del mateix nivell. Com el resoldries?"
        text_en = "A similar problem of the same level. How would you solve it?"
    return {"kind": "neighbour", "problem": shown, "easier": easier, "text_ca": text_ca, "text_en": text_en}


def _rung2(problem, state):
    cards = strategies(_topic_of(problem))
    if not cards:
        return {"kind": "strategy", "manipulative": None,
                "text_ca": "Escriu les dades del problema i encercla què et demanen.",
                "text_en": "Write down the data and what the problem asks."}
    with _lock:
        i = state["strategy"] % len(cards)
        state["strategy"] += 1
    card = cards[i]
    return {"kind": "strategy", "manipulative": card.get("manipulative"),
            "text_ca": card["text_ca"], "text_en": card["text_en"]}


def _solved(problem, state):
    if state["solved"] == "?":
        try:
            state["solved"] = solvers.solve(problem)
        except Exception:  # a solver bug must never break the ladder
            state["solved"] = None
    return state["solved"]


def _step_text(step, i, n, lang_key):
    text = step.get(lang_key) or step.get("text_en") or ""
    head = f"Pas {i} de {n}: " if lang_key == "text_ca" else f"Step {i} of {n}: "
    return head + text


def _rung3(problem, state, lang):
    # (0) the team's hand-written steps for the demo problems, one per request, never the last
    steps = demo_steps(problem["id"])
    if steps and len(steps) >= 2 and state["demo_step"] < len(steps) - 1:
        i = state["demo_step"]
        state["demo_step"] = i + 1
        shown = len(steps) - 1
        return {"kind": "demo_steps", "step": i + 1, "steps_total": shown,
                "text_ca": _step_text(steps[i], i + 1, shown, "text_ca"),
                "text_en": _step_text(steps[i], i + 1, shown, "text_en")}
    solved = _solved(problem, state)
    label, options = problem.get("label"), problem.get("options") or {}
    if solved and len(solved.get("trace") or []) >= 2:
        trace = solved["trace"]
        shown = len(trace) - 1  # the last step states the answer and is never a hint
        if state["trace_step"] < shown:
            i = state["trace_step"]
            step = trace[i]
            text_ca = _step_text(step, i + 1, shown, "text_ca")
            text_en = _step_text(step, i + 1, shown, "text_en")
            # An intermediate value equal to the answer would give it away: check anyway
            if leak_reason(text_ca, label, options) is None and leak_reason(text_en, label, options) is None:
                state["trace_step"] = i + 1
                return {"kind": "trace", "text_ca": text_ca, "text_en": text_en}
            state["trace_step"] = shown  # skip the rest of the trace
    if llm_allowed(_topic_of(problem), _llm_lang(lang)):
        result = _prefetched(state) or llm_hint(problem, lang)
        if result.get("ok"):
            return {"kind": "llm", "text_ca": result["text_ca"], "text_en": result["text_en"],
                    "llm_lang": result.get("lang", "cat"),
                    "estimated_board_seconds": result["estimated_board_seconds"]}
        fallback = _rung2(problem, state)
        fallback["estimated_board_seconds"] = result.get("estimated_board_seconds", 0.0)
        return fallback
    return _rung2(problem, state)


_UNIT_SQ = re.compile(r"(?<=\d)\s*(cm|dm|mm|km|m)\s*(?:²|2)\s*\d?(?![A-Za-z0-9])", re.IGNORECASE)
_UNIT_CU = re.compile(r"(?<=\d)\s*(cm|dm|mm|km|m)\s*(?:³|3)\s*\d?(?![A-Za-z0-9])", re.IGNORECASE)
_OPERATOR = re.compile(r"[/:+\-×x·*=]")


def display_value(raw):
    """An option value as the student should read it, or "" when the OCR left it illegible.

    "4cm²2" -> "4 cm²", "27cm2" -> "27 cm²", "48cm" -> "48 cm", "10%" -> "10%", "1/2" -> "1/2";
    "2 11 cm2", "12 m 1m" or "1 10" (two numbers with nothing between them) -> "".
    """
    text = unicodedata.normalize("NFC", str(raw or "")).strip()
    text = re.sub(r"\s+", " ", text)
    text = _UNIT_SQ.sub(lambda m: f" {m.group(1).lower()}²", text)
    text = _UNIT_CU.sub(lambda m: f" {m.group(1).lower()}³", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)        # "48cm" -> "48 cm"
    text = re.sub(r"\s+", " ", text).strip(" .;,")
    if not text or len(text) > 30:
        return ""
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    if len(numbers) >= 2 and not _OPERATOR.search(text):
        return ""   # OCR noise: two numbers side by side ("2 11 cm²", "1 10", "12 m 1 m")
    return text


def _rung4(problem, state):
    solved = _solved(problem, state)
    label = problem.get("label", "?")
    value = (problem.get("options") or {}).get(label) or (solved or {}).get("value") or ""
    shown = display_value(value)
    head_ca = f"Solució: opció {label}" + (f" ({shown})" if shown else "") + "."
    head_en = f"Solution: option {label}" + (f" ({shown})" if shown else "") + "."
    steps = demo_steps(problem["id"])
    source = "demo_set" if steps else ("solver" if solved else None)
    trace = steps or (solved or {}).get("trace") or []
    text_ca = head_ca + "".join(" " + (s.get("text_ca") or s.get("text_en") or "") for s in trace)
    text_en = head_en + "".join(" " + (s.get("text_en") or s.get("text_ca") or "") for s in trace)
    return {"kind": "solution", "label": label, "value": value, "value_shown": shown, "source": source,
            "trace": [{"text_ca": s.get("text_ca") or s.get("text_en") or "",
                       "text_en": s.get("text_en") or s.get("text_ca") or ""} for s in trace],
            "text_ca": text_ca, "text_en": text_en}


def get_hint(problem_id, rung, lang="cat"):
    """Hint result for one rung (0..4), see INTERFACES.md. Never raises for a known problem."""
    rung = max(0, min(4, int(rung)))
    if rung == 0:
        return translation(problem_id, lang)
    problem = problem_for(problem_id, lang)
    base = {"rung": rung, "estimated_board_seconds": 0.0}
    if problem is None:
        return {**base, "kind": "strategy", "manipulative": None,
                "text_ca": "No conec aquest problema. Escriu les dades i què et demanen.",
                "text_en": "I don't know this problem. Write down the data and what it asks."}
    state = _st(problem_id)
    if rung == 1:
        return {**base, **_rung1(problem, lang)}
    if rung == 2:
        return {**base, **_rung2(problem, state)}
    if rung == 3:
        return {**base, **_rung3(problem, state, lang)}
    return {**base, **_rung4(problem, state)}


# ---------------------------------------------------------------- the LLM hint (rung 3b)
#
# Qwen3.5 is a hybrid (recurrent) model, so llama-server can restore its prompt cache only at
# checkpoints: the start of the LAST user message and the end of the prompt (--ctx-checkpoints 2).
# The problem therefore goes in its own user message, with a fixed "OK." in between, and the hint
# request is the last message: a second request about the same problem reads only its own tokens.
# Measured on the samples (laptop, n=10): plain "write a hint" prompts leaked the value 5/10 times;
# asking for ONE QUESTION with a grammar that allows no digits leaked 0/10 and wrote fewer tokens.

# A character whitelist: letters (Catalan accents included), spaces and punctuation. No digits of
# any alphabet, so the hint cannot spell the value with 36, ٣٦, ³⁶ or ½.
HINT_GRAMMAR = ("root ::= [a-zA-ZàèéíïòóúüçÀÈÉÍÏÒÓÚÜÇñÑ·'’ ,;:.?!()-]+")
ACK = "OK."


def _problem_block(problem):
    """The stable part of the prompt: the problem in English when we have it, and its options."""
    english = problem_for(problem["id"], "eng") or problem
    lines = ["Problem:", english["text"].strip()]
    options = english.get("options") or problem.get("options") or {}
    for letter in "ABCDE":
        if letter in options:
            lines.append(f"{letter}) {options[letter]}")
    return "\n".join(lines)


def _request(problem, lang, strict=False):
    label = problem.get("label", "")
    value = (problem.get("options") or {}).get(label, "")
    answer = f"{label} ({value})" if value else label
    name = LANG_NAME.get(lang, "Catalan")
    if strict:
        return (f"The correct answer is {answer}. Your previous question gave the answer away. Ask a different "
                f"short question in {name} about the very first step only, with no numbers and no option letters.")
    return (f"The correct answer is {answer}. Ask the student ONE short question in {name} about the first step. "
            f"Do not mention the answer, the letter or any number.")


def _messages(problem, lang=None, strict=False):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": _problem_block(problem)}]
    if lang:
        messages += [{"role": "assistant", "content": ACK}, {"role": "user", "content": _request(problem, lang, strict)}]
    return messages


def _one_sentence(text):
    text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip().strip('"“”«»')
    m = re.match(r"^(.+?[.!?])(\s|$)", text)
    return (m.group(1) if m else text).strip()


def _call(messages, max_tokens, grammar=None, timeout=LLM_TIMEOUT):
    payload = {"messages": messages, "max_tokens": max_tokens, "temperature": 0,
               "seed": int(CONFIG["SEED"]), "cache_prompt": True}
    if grammar:
        payload["grammar"] = grammar
    response = post(LLM_URL, payload, timeout=timeout)
    return response["choices"][0]["message"]["content"], response.get("timings", {})


def warm(problem_id, lang="cat"):
    """Read the exact Catalan hint prompt into the server's cache now (max_tokens 1), so the hint
    request later reads only a few tokens. Returns the server timings, {} if unreachable."""
    problem = problem_for(problem_id, lang)
    if problem is None:
        return {}
    try:
        _text, timings = _call(_messages(problem, _llm_langs(lang)[0]), max_tokens=1, timeout=LLM_TIMEOUT)
        return timings
    except (OSError, ValueError, KeyError):
        return {}


def _prefetch_full(problem_id, lang):
    problem = problem_for(problem_id, lang)
    if problem is None:
        return
    result = llm_hint(problem, lang)
    with _lock:
        if problem_id in _state:
            _state[problem_id]["llm"]["result"] = result


def prefetch(problem_id, lang="cat"):
    """Start the ladder over and, for topics that may use the LLM, work ahead in a background thread:
    HINT_PREFETCH=warm reads the prompt into the cache; full (default) also writes the hint."""
    reset(problem_id)
    problem = problem_for(problem_id, lang)
    if PREFETCH == "off" or problem is None or not llm_allowed(_topic_of(problem), _llm_lang(lang)):
        return None
    target = _prefetch_full if PREFETCH == "full" else warm
    thread = threading.Thread(target=target, args=(problem_id, lang), daemon=True)
    _st(problem_id)["llm"]["thread"] = thread
    thread.start()
    return None


def _prefetched(state, timeout=LLM_TIMEOUT):
    """The hint a full prefetch produced, waiting for its thread if it is still running."""
    thread = state["llm"].get("thread")
    if thread is not None:
        thread.join(timeout)
    return state["llm"].pop("result", None)


def llm_hint(problem, lang="cat", strict_first=False):
    """One-sentence hint in English and Catalan, filtered by leak_filter and retried once.

    Two short calls (English first, then Catalan): the second reads only its request thanks to
    the message split above. Returns {"ok", "text_ca", "text_en", "estimated_board_seconds",
    "prompt_n", "predicted_n", "attempts", "rejected": [reasons]}.
    """
    label, options = problem.get("label"), problem.get("options") or {}
    langs = _llm_langs(lang)
    out = {"ok": False, "text_ca": "", "text_en": "", "estimated_board_seconds": 0.0,
           "prompt_n": 0, "predicted_n": 0, "attempts": 0, "rejected": [], "lang": "eng" if langs == ("eng",) else "cat"}

    def record(timings):
        out["prompt_n"] += int(timings.get("prompt_n", 0) or 0)
        out["predicted_n"] += int(timings.get("predicted_n", 0) or 0)
        out["estimated_board_seconds"] += estimate(timings)

    for attempt, strict in enumerate((strict_first, True)):
        out["attempts"] = attempt + 1
        try:
            texts = {}
            for call_lang in langs:
                raw, timings = _call(_messages(problem, call_lang, strict), MAX_TOKENS, grammar=HINT_GRAMMAR)
                record(timings)
                texts[call_lang] = _one_sentence(raw)
        except (OSError, ValueError, KeyError) as error:
            out["rejected"].append(f"error:{error}")
            return out
        text_en = texts.get("eng", "")
        text_ca = texts.get("cat", text_en)  # English only: the Catalan page shows the English sentence
        reason = leak_reason(text_ca, label, options) or leak_reason(text_en, label, options)
        if reason:
            out["rejected"].append(reason)
            if out["estimated_board_seconds"] > RETRY_BUDGET:
                out["rejected"].append("no-retry:over-budget")
                return out
            continue
        out.update(ok=True, text_ca=text_ca, text_en=text_en)
        return out
    return out
