"""The hint ladder: four rungs, from an easier neighbour to the solution.

Owner: D (branch `hints-app`). Contract in INTERFACES.md.

    prefetch(problem_id, lang)          # when the problem is shown: warm the LLM prompt cache in a thread
    get_hint(problem_id, rung, lang)    # rung 1..4, see below

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

from . import retrieval, solvers, topics
from .board_clock import estimate
from .client import post
from .config import CONFIG, ROOT
from .leak_filter import leak_reason

STRATEGIES_FILE = os.path.join(ROOT, "data_curated", "strategies.json")
QUALITY_FILE = os.path.join(ROOT, "data_curated", "hint_quality.json")
IMAGES_DIR = os.path.join(ROOT, "data", "images")
# Where problems are looked up by id: the shared splits when linked, else the samples
PROBLEM_FILES = [os.path.join(ROOT, "data", name) for name in
                 ("val.jsonl", "train.jsonl", "sample_problems.jsonl")]
STUDENT_LANGS = ("cat", "eng")

QUALITY_MIN = float(CONFIG.get("HINT_QUALITY_MIN", 70))
MAX_TOKENS = int(CONFIG.get("HINT_MAX_TOKENS", 40))
LLM_URL = f"http://127.0.0.1:{CONFIG['LLM_PORT']}/v1/chat/completions"
LLM_TIMEOUT = float(CONFIG.get("TIME_LIMIT_SECONDS", 60))
# "two": one short call per language (English first, then Catalan). "one": both in one JSON answer.
LLM_MODE = CONFIG.get("HINT_LLM_MODE", "two")

# Stable system prompt: llama-server caches the start of the prompt, so keep it identical.
SYSTEM = ("You are a maths tutor for school students aged 10 to 18. You help with ONE short sentence "
          "that points to the first step, without giving the answer.")
LANG_NAME = {"cat": "Catalan", "eng": "English", "spa": "Spanish"}

_lock = threading.Lock()
_problems = {}          # (id, language) -> Problem
_loaded = False
_state = {}             # problem_id -> {"strategy": int, "trace_step": int, "solved": ..., "llm": {...}}
_strategies = None
_quality = None


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


def reset(problem_id):
    """Forget the ladder position of a problem (a new attempt starts at the bottom)."""
    with _lock:
        _state.pop(problem_id, None)


def _st(problem_id):
    with _lock:
        return _state.setdefault(problem_id, {"strategy": 0, "trace_step": 0, "solved": "?", "llm": {}})


def _topic_of(problem):
    return problem.get("topic") or topics.get_topic(problem["id"])


# ---------------------------------------------------------------- strategies and quality

def strategies(topic):
    global _strategies
    if _strategies is None:
        with open(STRATEGIES_FILE, encoding="utf-8") as f:
            _strategies = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    return _strategies.get(topic) or _strategies.get("arithmetic") or []


def quality(topic):
    """Judged quality (0..100) of LLM hints for a topic, or None when not judged yet."""
    global _quality
    if _quality is None:
        _quality = {}
        if os.path.exists(QUALITY_FILE):
            with open(QUALITY_FILE, encoding="utf-8") as f:
                _quality = json.load(f).get("topics", {})
    row = _quality.get(topic)
    return None if not row or not row.get("n") else float(row.get("percent", 0))


def llm_allowed(topic):
    q = quality(topic)
    return q is not None and q >= QUALITY_MIN


# ---------------------------------------------------------------- rungs

def _image_path(problem_id, lang):
    for candidate in (lang, "eng", "cat"):
        path = os.path.join(IMAGES_DIR, f"{problem_id}_{candidate}.png")
        if os.path.exists(path):
            return os.path.relpath(path, ROOT)
    return None


def _rung1(problem, lang):
    hits = retrieval.neighbors(problem["id"], level_delta=-1, same_topic=True, lang=lang, k=1)
    shown = None
    if hits:
        shown = {k: v for k, v in hits[0].items() if k != "label"}
        if topics.is_visual(_topic_of(problem)):
            shown["image"] = _image_path(shown["id"], shown.get("language", lang))
    level = shown.get("level") if shown else None
    return {"kind": "neighbour", "problem": shown,
            "text_ca": "Mira aquest problema semblant, més fàcil" + (f" (nivell {level})" if level is not None else "") +
                       ". Com el resoldries? La mateixa idea serveix per al teu.",
            "text_en": "Look at this similar, easier problem" + (f" (level {level})" if level is not None else "") +
                       ". How would you solve it? The same idea works for yours."}


def _rung2(problem, state):
    cards = strategies(_topic_of(problem))
    if not cards:
        return {"kind": "strategy", "manipulative": None,
                "text_ca": "Escriu les dades del problema i què et demanen.",
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
    if llm_allowed(_topic_of(problem)):
        result = llm_hint(problem, lang)
        if result.get("ok"):
            return {"kind": "llm", "text_ca": result["text_ca"], "text_en": result["text_en"],
                    "estimated_board_seconds": result["estimated_board_seconds"]}
        fallback = _rung2(problem, state)
        fallback["estimated_board_seconds"] = result.get("estimated_board_seconds", 0.0)
        return fallback
    return _rung2(problem, state)


def _rung4(problem, state):
    solved = _solved(problem, state)
    label = problem.get("label", "?")
    value = (problem.get("options") or {}).get(label) or (solved or {}).get("value") or ""
    head_ca = f"Solució: opció {label}" + (f" ({value})" if value else "") + "."
    head_en = f"Solution: option {label}" + (f" ({value})" if value else "") + "."
    trace = (solved or {}).get("trace") or []
    text_ca = head_ca + "".join(" " + s["text_ca"] for s in trace)
    text_en = head_en + "".join(" " + s["text_en"] for s in trace)
    return {"kind": "solution", "label": label, "value": value,
            "trace": [{"text_ca": s["text_ca"], "text_en": s["text_en"]} for s in trace],
            "text_ca": text_ca, "text_en": text_en}


def get_hint(problem_id, rung, lang="cat"):
    """Hint result for one rung (1..4), see INTERFACES.md. Never raises for a known problem."""
    rung = max(1, min(4, int(rung)))
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
    text = (f"The correct answer is {answer}. Write ONE short sentence in {LANG_NAME.get(lang, 'Catalan')} "
            f"that helps the student find it, without revealing the answer, the letter or the value.")
    if strict:
        text += (f" Do NOT write '{value}', the letter {label}, or the words 'answer' or 'solution'. "
                 "Point only to the first step of the reasoning.")
    return text


def _messages(problem, lang=None, strict=False):
    content = _problem_block(problem)
    if lang:
        content += "\n\n" + _request(problem, lang, strict)
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]


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
    """Read the problem into the prompt cache now (max_tokens 1), so the hint request reads only
    its last lines. Returns the server timings, or {} when the server is unreachable."""
    problem = problem_for(problem_id, lang)
    if problem is None:
        return {}
    try:
        _text, timings = _call(_messages(problem), max_tokens=1, timeout=LLM_TIMEOUT)
        return timings
    except (OSError, ValueError, KeyError):
        return {}


def prefetch(problem_id, lang="cat"):
    """Warm the LLM prompt cache for this problem in a background thread, and start the ladder over."""
    reset(problem_id)
    if not llm_allowed(_topic_of(problem_for(problem_id, lang) or {"id": problem_id})):
        return None  # no LLM for this topic, nothing to warm
    threading.Thread(target=warm, args=(problem_id, lang), daemon=True).start()
    return None


_ONE_CALL_GRAMMAR = ('root ::= "{\\"en\\": \\"" str "\\", \\"ca\\": \\"" str "\\"}"\n'
                     'str ::= [^"\\\\\\n{}]+')


def llm_hint(problem, lang="cat", mode=None, strict_first=False):
    """One-sentence hint in Catalan and English, filtered by leak_filter and retried once.

    Returns {"ok", "text_ca", "text_en", "estimated_board_seconds", "prompt_n", "predicted_n",
             "attempts", "rejected": [reasons]}.
    `mode` is "two" (one call per language) or "one" (one JSON call); default HINT_LLM_MODE.
    """
    mode = mode or LLM_MODE
    label, options = problem.get("label"), problem.get("options") or {}
    out = {"ok": False, "text_ca": "", "text_en": "", "estimated_board_seconds": 0.0,
           "prompt_n": 0, "predicted_n": 0, "attempts": 0, "rejected": [], "mode": mode}

    def record(timings):
        out["prompt_n"] += int(timings.get("prompt_n", 0) or 0)
        out["predicted_n"] += int(timings.get("predicted_n", 0) or 0)
        out["estimated_board_seconds"] += estimate(timings)

    for attempt, strict in enumerate((strict_first, True)):
        out["attempts"] = attempt + 1
        try:
            if mode == "one":
                raw, timings = _call(_messages(problem, "cat", strict), 2 * MAX_TOKENS + 12, grammar=_ONE_CALL_GRAMMAR)
                record(timings)
                try:
                    both = json.loads(raw)
                except ValueError:
                    out["rejected"].append("format")
                    continue
                text_en, text_ca = _one_sentence(both.get("en", "")), _one_sentence(both.get("ca", ""))
            else:
                raw_en, t1 = _call(_messages(problem, "eng", strict), MAX_TOKENS)
                record(t1)
                raw_ca, t2 = _call(_messages(problem, "cat", strict), MAX_TOKENS)
                record(t2)
                text_en, text_ca = _one_sentence(raw_en), _one_sentence(raw_ca)
        except (OSError, ValueError, KeyError) as error:
            out["rejected"].append(f"error:{error}")
            return out
        reason = leak_reason(text_ca, label, options) or leak_reason(text_en, label, options)
        if reason:
            out["rejected"].append(reason)
            continue
        out.update(ok=True, text_ca=text_ca, text_en=text_en)
        return out
    return out
