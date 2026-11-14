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
# A leaking hint is retried once only if the first attempt cost less than this (board seconds):
# a cold retry on a long problem would push rung 3 past the 60 s limit (measured max 92.5 s on val)
RETRY_BUDGET = float(CONFIG.get("HINT_RETRY_BUDGET", 30))
LLM_URL = f"http://{CONFIG['LLM_HOST']}:{CONFIG['LLM_PORT']}/v1/chat/completions"
LLM_TIMEOUT = float(CONFIG.get("TIME_LIMIT_SECONDS", 60))
# What prefetch() does in its thread: "full" writes the hint ahead, "warm" only reads the prompt, "off" nothing
PREFETCH = CONFIG.get("HINT_PREFETCH", "full")

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
    if llm_allowed(_topic_of(problem), lang):
        result = _prefetched(state) or llm_hint(problem, lang)
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
        _text, timings = _call(_messages(problem, "cat"), max_tokens=1, timeout=LLM_TIMEOUT)
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
    if PREFETCH == "off" or problem is None or not llm_allowed(_topic_of(problem), lang):
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
    out = {"ok": False, "text_ca": "", "text_en": "", "estimated_board_seconds": 0.0,
           "prompt_n": 0, "predicted_n": 0, "attempts": 0, "rejected": []}

    def record(timings):
        out["prompt_n"] += int(timings.get("prompt_n", 0) or 0)
        out["predicted_n"] += int(timings.get("predicted_n", 0) or 0)
        out["estimated_board_seconds"] += estimate(timings)

    for attempt, strict in enumerate((strict_first, True)):
        out["attempts"] = attempt + 1
        try:
            raw_ca, t1 = _call(_messages(problem, "cat", strict), MAX_TOKENS, grammar=HINT_GRAMMAR)
            record(t1)
            raw_en, t2 = _call(_messages(problem, "eng", strict), MAX_TOKENS, grammar=HINT_GRAMMAR)
            record(t2)
        except (OSError, ValueError, KeyError) as error:
            out["rejected"].append(f"error:{error}")
            return out
        text_ca, text_en = _one_sentence(raw_ca), _one_sentence(raw_en)
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
