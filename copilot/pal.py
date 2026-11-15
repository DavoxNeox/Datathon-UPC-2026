"""Program-aided reasoning (PAL): the 0.8B writes a few lines of Python, the board runs them (flag PAL, off by default).

Hypothesis (docs/reason-experiments.md, Experiment 8): the model gets arithmetic wrong in prose but
writes a short calculation acceptably; if Python does the arithmetic and the result has to equal one
of the five options, the letter is right more often than with the brief text reasoning of think.py.

One request: a stable block (instruction and two invented worked examples, earlier messages so the
server's checkpoint at the start of the last user message keeps them cached between problems) and
the problem with its five options as the last user message. Temperature 0, SEED, max_tokens from the
board clock inside PAL_BUDGET_SECONDS (minus the 2 s the program may take). The code block is checked
(ast) and run with exec in a thread: no import but math, no attribute starting with "_" or naming a
frame (gi_frame, f_back, ...), no dunder name, no try/with/class/global; only a short list of pure
builtins and the math module; a 2 s wall-clock deadline and a cap on executed lines (a tracer), on
range() lengths, on the integers **, * and << may build, on sequences built by * and +, on
math.factorial/comb/perm/prod, and on any container a variable holds. The threat is a 0.8B writing a
runaway program, not an attacker; a single long C call is the one thing the tracer cannot interrupt,
which is why the operators that can start one are size-checked. Whatever goes wrong (no code, syntax error, rejected node,
exception, time-out, no `answer`, no unique matching option) abstains and the caller falls through
to its usual order (think, then the middle value).

Matching: the value of `answer` against every option that is one clean number (a short unit allowed,
copilot/ladder rule; "3/4" and "25%" included, a percentage also matches its fraction 0.25). Equal
within 1e-6 (relative above 1): that option, if it is the only one. No exact hit: the nearest option
when it is within 1% and is the only option within 1%. Otherwise None.

Cache: with --parallel 1 and --cache-ram 0 the server keeps only the last prompt, so the stable block
is cached only when the previous chat request was this stage's. copilot/client.py records the leading
messages of the last completed chat request per server (one process runs the whole exam); the block is
counted as read again unless they are this stage's, so a solver extraction or a think request in
between (on this problem or the one before) is paid for in the budget.
"""
import ast
import itertools
import math
import re
import sys
import threading
import time
import types
from fractions import Fraction

from . import board_clock
from . import client
from .client import post
from .config import CONFIG
from .llm import URL, format_problem
from .solvers.common import parse_number

LETTERS = "ABCDE"
BUDGET = float(CONFIG.get("PAL_BUDGET_SECONDS", "45") or 45)
MAX_TOKENS = int(CONFIG.get("PAL_MAX_TOKENS", "200") or 200)
MIN_TOKENS = int(CONFIG.get("PAL_MIN_TOKENS", "60") or 60)
EXEC_SECONDS = 2.0          # wall-clock deadline of the program; also kept out of the token budget
MAX_LINES = 1_000_000       # executed line events
MAX_RANGE = 1_000_000       # longest range()
MAX_INT_BITS = 100_000      # largest integer a power, product or shift may produce (7**2026 is 5 700 bits)
MAX_SEQ = 1_000_000         # longest str/list/tuple built by * or +
MAX_CONTAINER = 2_000_000   # longest container a variable may hold (checked on every executed line)
MAX_FACTORIAL = 10_000      # largest n for math.factorial, comb and perm
TEMPLATE_TOKENS = 12        # <|im_start|>user ... <|im_end|><|im_start|>assistant and the closed think block
# Measurement only (Experiment 8, variant B): read the statement from another field of the row, e.g. the
# English twin of a Catalan problem. "text" (default) is what the exam run uses.
TEXT_FIELD = CONFIG.get("PAL_TEXT_FIELD", "text") or "text"
# PAL_TEXT_ONLY=1: only problems without a figure (balances, charts, nets need the picture; they go to think).
TEXT_ONLY = CONFIG.get("PAL_TEXT_ONLY", "1") != "0"
MAX_COMBOS = 2_000_000      # most tuples itertools.permutations/combinations/product may yield

SYSTEM = ("Solve the multiple-choice math problem with a short Python program: one ```python block of 3 to 8 "
          "lines that computes the answer and ends with answer = ... . No print, no explanation.")
# Invented for this module (not from any problem bank), both explicit brute force: most practice problems are
# enumerations over a small space, which a loop solves exactly. Kept short: the whole block is read again
# (about 15 s on the board) whenever the cache is cold.
EXAMPLES = [
    ("How many numbers from 1 to 50 are divisible by 3 or by 7?\nA) 20\nB) 21\nC) 22\nD) 23\nE) 24",
     "```python\ncount = 0\nfor n in range(1, 51):\n    if n % 3 == 0 or n % 7 == 0:\n        count += 1\n"
     "answer = count\n```"),
    ("Two whole numbers add up to 20 and their product is 96. What is the larger one?\nA) 10\nB) 12\nC) 14\nD) 16\nE) 18",
     "```python\nfor a in range(1, 20):\n    b = 20 - a\n    if a * b == 96 and a > b:\n        answer = a\n```"),
]
INSTRUCTION = "\n\nWrite the Python program."

_STATE = {"prefix_tokens": None}


def stable_messages():
    messages = [{"role": "system", "content": SYSTEM}]
    for question, code in EXAMPLES:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": code})
    return messages


def problem_text(problem):
    text = problem.get(TEXT_FIELD) if TEXT_FIELD != "text" else None
    if not (isinstance(text, str) and text.strip()):
        return problem
    return dict(problem, text=text)


def build_messages(problem):
    return stable_messages() + [{"role": "user", "content": format_problem(problem_text(problem)) + INSTRUCTION}]


# ---------------------------------------------------------------- the options

_CLEAN = re.compile(r"^\s*-?\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?\s*(?:%|€|\$|°|[A-Za-z]{1,7}(?:[²³2]|/[A-Za-z]{1,3})?)?\s*$")


def option_values(options):
    """{letter: [float, ...]} for every option that is one clean number; a percentage also stands for its fraction."""
    values = {}
    for letter in LETTERS:
        text = str((options or {}).get(letter, "")).replace("−", "-")
        if not _CLEAN.match(text):
            continue
        value = parse_number(text)
        if value is None:
            continue
        values[letter] = [float(value)] + ([float(value) / 100] if "%" in text else [])
    return values


def applies(problem, text_only=None):
    """Text, five options, at least three of them plain numbers (a program can only land on a number) and,
    with PAL_TEXT_ONLY=1, no figure."""
    options = problem.get("options") or {}
    if (TEXT_ONLY if text_only is None else text_only) and not problem.get("text_only", False):
        return False
    return bool((problem.get("text") or "").strip()) and len(options) == 5 and len(option_values(options)) >= 3


# A program that builds the list of solutions instead of counting them: its length is the answer only when the
# question asks how many (English, Catalan); anything else that is a collection abstains.
_HOW_MANY = re.compile(r"\bhow\s+many\b|\bquant(?:s|es)\b", re.I)


def collection_answer(answer, text):
    """(value, note): a list/set/tuple/dict becomes its length for a "how many" question, else None."""
    if not isinstance(answer, (list, tuple, set, frozenset, dict)):
        return answer, ""
    if _HOW_MANY.search(text or ""):
        return len(answer), "len"
    return None, "collection"


def _as_number(answer):
    if isinstance(answer, bool) or answer is None:
        return None
    if isinstance(answer, (int, float)):
        try:
            value = float(answer)
        except OverflowError:  # an int beyond 1e308 is no option's value
            return None
    elif isinstance(answer, str):
        number = parse_number(answer)
        value = None if number is None else float(number)
    else:
        try:  # Fraction, Decimal and the like
            value = float(answer)
        except (TypeError, ValueError, OverflowError):
            return None
    return value if value is not None and math.isfinite(value) else None


def match_answer(answer, options):
    """(letter or None, how): how is "exact", "near" (within 1%), or why nothing matched."""
    value = _as_number(answer)
    if value is None:
        return None, "not_a_number"
    values = option_values(options)
    if not values:
        return None, "no_numeric_option"
    exact = [l for l, vs in values.items() if any(abs(value - v) <= 1e-6 * max(1.0, abs(v)) for v in vs)]
    if len(exact) == 1:
        return exact[0], "exact"
    if len(exact) > 1:
        return None, "several_exact"
    near = [l for l, vs in values.items() if any(v != 0 and abs(value - v) / abs(v) < 0.01 for v in vs)]
    if len(near) == 1:
        return near[0], "near"
    return None, "no_match" if not near else "several_near"


# ---------------------------------------------------------------- running the program

class Rejected(Exception):
    """The program uses something the sandbox does not allow."""


class _Stop(BaseException):
    """Raised from the tracer: the program ran out of time, lines or memory. BaseException, and try is banned."""


_BANNED = (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.ClassDef, ast.AsyncFunctionDef,
           ast.Await, ast.AsyncFor, ast.AsyncWith, ast.With, ast.Try, getattr(ast, "TryStar", ast.Try))
# Frame, code and traceback attributes reach the interpreter's globals without any underscore (gen.gi_frame.f_back).
_BANNED_ATTR_PREFIXES = ("_", "gi_", "cr_", "ag_", "f_", "tb_", "co_")
_CONTAINERS = (str, bytes, list, tuple, dict, set, frozenset)


def _bits(value):
    """Size in bits of an int, or of the larger term of a Fraction; 0 for anything else."""
    if isinstance(value, int):
        return abs(value).bit_length()
    if isinstance(value, Fraction):
        return max(abs(value.numerator).bit_length(), value.denominator.bit_length())
    return 0


def _too_big_int(value):
    # plain ints only: the tracer also sees half-built Fractions inside fractions.py, which have no numerator yet
    return type(value) is int and value.bit_length() > MAX_INT_BITS


def _pow(a, b, mod=None):
    if mod is not None:
        return pow(a, b, mod)
    if isinstance(b, int) and abs(b) > 1 and _bits(a) > 1 and abs(b) * _bits(a) > MAX_INT_BITS:
        raise ValueError("power too large")
    return a ** b


def _mul(a, b):
    for seq, n in ((a, b), (b, a)):
        if isinstance(seq, _CONTAINERS) and isinstance(n, int) and len(seq) * n > MAX_SEQ:
            raise ValueError("sequence too long")
    if _bits(a) + _bits(b) > MAX_INT_BITS:
        raise ValueError("product too large")
    return a * b


def _add(a, b):
    if isinstance(a, _CONTAINERS) and isinstance(b, _CONTAINERS) and len(a) + len(b) > MAX_SEQ:
        raise ValueError("sequence too long")
    return a + b


def _lshift(a, b):
    if isinstance(b, int) and isinstance(a, int) and a.bit_length() + b > MAX_INT_BITS:
        raise ValueError("shift too large")
    return a << b


def _range(*args):
    r = range(*args)
    if len(r) > MAX_RANGE:
        raise ValueError("range too long")
    return r


def _small(n, name):
    if isinstance(n, int) and n > MAX_FACTORIAL:
        raise ValueError(name + " too large")


def _factorial(n):
    _small(n, "factorial")
    return math.factorial(n)


def _comb(n, k):
    _small(n, "comb")
    return math.comb(n, k)


def _perm(n, k=None):
    _small(n, "perm")
    return math.perm(n, k)


def _prod(iterable, start=1):
    total = start
    for item in iterable:
        total = _mul(total, item)
    return total


# The math module as the program sees it: the same functions, the ones that can run for minutes in C size-checked.
SAFE_MATH = types.SimpleNamespace(**{name: getattr(math, name) for name in dir(math) if not name.startswith("_")})
SAFE_MATH.factorial, SAFE_MATH.comb, SAFE_MATH.perm, SAFE_MATH.prod = _factorial, _comb, _perm, _prod



def _pool(iterable):
    pool = tuple(iterable)
    if len(pool) > MAX_RANGE:
        raise ValueError("iterable too long")
    return pool


def _check_combos(count):
    if count > MAX_COMBOS:
        raise ValueError("too many combinations")


def _permutations(iterable, r=None):
    pool = _pool(iterable)
    r = len(pool) if r is None else r
    _check_combos(math.perm(len(pool), r) if 0 <= r <= len(pool) else 0)
    return itertools.permutations(pool, r)


def _combinations(iterable, r):
    pool = _pool(iterable)
    _check_combos(math.comb(len(pool), r) if 0 <= r <= len(pool) else 0)
    return itertools.combinations(pool, r)


def _combinations_with_replacement(iterable, r):
    pool = _pool(iterable)
    _check_combos(math.comb(len(pool) + r - 1, r) if pool and r >= 0 else 0)
    return itertools.combinations_with_replacement(pool, r)


def _product(*iterables, repeat=1):
    pools = [_pool(it) for it in iterables] * repeat
    count = 1
    for pool in pools:
        count *= len(pool)
        _check_combos(count)
    return itertools.product(*pools)


# itertools without its infinite iterators (count, cycle, repeat: list() of one never returns, in C), and with the
# combinatorial ones size-checked before they start.
SAFE_ITERTOOLS = types.SimpleNamespace(
    permutations=_permutations, combinations=_combinations, product=_product,
    combinations_with_replacement=_combinations_with_replacement,
    accumulate=itertools.accumulate, chain=itertools.chain, islice=itertools.islice, pairwise=itertools.pairwise,
    groupby=itertools.groupby, zip_longest=itertools.zip_longest, compress=itertools.compress,
    takewhile=itertools.takewhile, dropwhile=itertools.dropwhile, starmap=itertools.starmap)
SAFE_FRACTIONS = types.SimpleNamespace(Fraction=Fraction)
MODULES = {"math": SAFE_MATH, "itertools": SAFE_ITERTOOLS, "fractions": SAFE_FRACTIONS}

_SAFE_BINOPS = {ast.Pow: "_pow_", ast.Mult: "_mul_", ast.LShift: "_lshift_", ast.Add: "_add_"}


class _Guard(ast.NodeTransformer):
    """Rejects the banned nodes and names, and routes **, *, << and + through the size-checked helpers.

    Imports of math, itertools and fractions are the only ones allowed (the model writes them out of habit), and
    they bind the restricted versions already in the namespace: `import itertools as it` becomes
    it = itertools, `from math import sqrt` becomes sqrt = math.sqrt."""

    def visit_Import(self, node):
        if not all(alias.name in MODULES for alias in node.names):
            raise Rejected("Import")
        return [ast.copy_location(ast.Assign([ast.Name(a.asname or a.name, ast.Store())], ast.Name(a.name, ast.Load())), node)
                for a in node.names]

    def visit_ImportFrom(self, node):
        if node.module not in MODULES or node.level or any(
                a.name == "*" or a.name.startswith("_") or not hasattr(MODULES[node.module], a.name) for a in node.names):
            raise Rejected("ImportFrom")
        return [ast.copy_location(ast.Assign([ast.Name(a.asname or a.name, ast.Store())],
                                             ast.Attribute(ast.Name(node.module, ast.Load()), a.name, ast.Load())), node)
                for a in node.names]

    def generic_visit(self, node):
        if isinstance(node, _BANNED):
            raise Rejected(type(node).__name__)
        if isinstance(node, ast.Attribute) and node.attr.startswith(_BANNED_ATTR_PREFIXES):
            raise Rejected("attribute " + node.attr)
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise Rejected("name " + node.id)
        if isinstance(node, ast.arg) and node.arg.startswith("__"):
            raise Rejected("argument " + node.arg)
        return super().generic_visit(node)

    def visit_BinOp(self, node):
        node = self.generic_visit(node)
        helper = _SAFE_BINOPS.get(type(node.op))
        if helper is None:
            return node
        return ast.copy_location(ast.Call(ast.Name(helper, ast.Load()), [node.left, node.right], []), node)

    def visit_AugAssign(self, node):
        node = self.generic_visit(node)
        helper = _SAFE_BINOPS.get(type(node.op))
        if helper is None:
            return node
        if not isinstance(node.target, ast.Name):
            if isinstance(node.op, ast.Add):
                return node  # count[i] += 1: everywhere in counting programs; ints cannot blow up by addition
            raise Rejected("augmented assignment on " + type(node.target).__name__)
        call = ast.Call(ast.Name(helper, ast.Load()), [ast.Name(node.target.id, ast.Load()), node.value], [])
        return ast.copy_location(ast.Assign([node.target], call), node)


def _noop(*args, **kwargs):
    return None


SAFE_BUILTINS = {
    # the list asked for ...
    "abs": abs, "min": min, "max": max, "sum": sum, "range": _range, "len": len, "round": round, "int": int,
    "float": float, "sorted": sorted, "enumerate": enumerate, "zip": zip, "divmod": divmod, "pow": _pow,
    # ... and pure helpers the model reaches for in digit and counting problems (no I/O, no introspection)
    "str": str, "list": list, "set": set, "tuple": tuple, "dict": dict, "bool": bool, "any": any, "all": all,
    "reversed": reversed, "map": map, "filter": filter, "print": _noop,  # replaced per run: the last print is kept
    "True": True, "False": False, "None": None,
}


def compile_program(code):
    """Parse, check and rewrite the program; raises Rejected or SyntaxError."""
    tree = _Guard().visit(ast.parse(code, mode="exec"))
    ast.fix_missing_locations(tree)
    return compile(tree, "<pal>", "exec")


def _oversized(frame):
    for value in list(frame.f_locals.values()):
        if isinstance(value, _CONTAINERS) and len(value) > MAX_CONTAINER:
            return True
        if _too_big_int(value):
            return True
    return False


def run_program(code, seconds=EXEC_SECONDS, max_lines=MAX_LINES):
    """(answer or None, status, seconds). status: ok, ok_print (the last value printed), no_answer, syntax, rejected: X, error: X, timeout, lines, memory."""
    start = time.perf_counter()
    try:
        compiled = compile_program(code)
    except SyntaxError:
        return None, "syntax", 0.0
    except Rejected as error:
        return None, f"rejected: {error}", 0.0
    except (ValueError, RecursionError, MemoryError) as error:  # e.g. null bytes, a too deep tree
        return None, f"rejected: {type(error).__name__}", 0.0
    printed = []

    def record(*args, **kwargs):  # a program that prints its result instead of assigning answer
        if len(args) == 1:
            printed[:] = [args[0]]

    namespace = {"__builtins__": dict(SAFE_BUILTINS, print=record), **MODULES,
                 "_pow_": _pow, "_mul_": _mul, "_lshift_": _lshift, "_add_": _add}
    outcome = {"status": "timeout"}
    deadline = start + seconds
    counter = [0]

    def tracer(frame, event, arg):
        counter[0] += 1
        if counter[0] > max_lines:
            outcome["status"] = "lines"
            raise _Stop()
        if time.perf_counter() > deadline:
            outcome["status"] = "timeout"
            raise _Stop()
        if _oversized(frame):  # l.extend(l) in a loop doubles a list in C between two lines
            outcome["status"] = "memory"
            raise _Stop()
        return tracer

    def target():
        sys.settrace(tracer)
        try:
            exec(compiled, namespace)
            outcome["status"] = "ok"
        except _Stop:
            pass
        except BaseException as error:  # anything the program raises, MemoryError and RecursionError included
            outcome["status"] = f"error: {type(error).__name__}"
        finally:
            sys.settrace(None)

    worker = threading.Thread(target=target, name="pal-exec", daemon=True)
    worker.start()
    worker.join(seconds + 0.5)  # backstop: one long C call is not traced
    elapsed = round(time.perf_counter() - start, 4)
    if worker.is_alive():
        return None, "timeout", elapsed
    if outcome["status"] != "ok":
        return None, outcome["status"], elapsed
    if "answer" not in namespace:
        if printed:
            return printed[0], "ok_print", elapsed
        return None, "no_answer", elapsed
    return namespace["answer"], "ok", elapsed


_FENCE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.S | re.I)
_OPEN_FENCE = re.compile(r"```(?:python|py)?[ \t]*\n", re.I)


def extract_code(content, finished=True):
    """The program in the reply: the first closed ```python block; with no fence, the whole reply when it
    assigns answer. A block cut by max_tokens (no closing fence, finished=False) is not run."""
    text = content or ""
    match = _FENCE.search(text)
    if match:
        return match.group(1)
    if _OPEN_FENCE.search(text):
        return None if not finished else _OPEN_FENCE.split(text, 1)[1]
    return text if finished and re.search(r"^\s*answer\s*=", text, re.M) else None


# ---------------------------------------------------------------- the request

def _tokenize_url(url):
    import urllib.parse
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, "/tokenize", "", ""))


def count_tokens(text, url=URL, timeout=5):
    try:
        return len(post(_tokenize_url(url), {"content": text}, timeout=timeout)["tokens"])
    except Exception:  # a failed count must not cost the answer: guess high
        return int(len(text) / (board_clock.CHARS_PER_TOKEN * 0.8)) + 1


def prefix_tokens(url=URL):
    """Tokens of the stable block (system and examples, with their template tokens), counted once."""
    if _STATE["prefix_tokens"] is None:
        stable = stable_messages()
        _STATE["prefix_tokens"] = sum(count_tokens(m["content"], url) for m in stable) + 5 * len(stable)
    return _STATE["prefix_tokens"]


def output_budget(prompt_tokens, budget, max_tokens=MAX_TOKENS):
    seconds_left = budget - EXEC_SECONDS - board_clock.estimate_tokens(prompt_tokens)
    if seconds_left <= 0:
        return 0
    return max(0, min(max_tokens, math.floor(seconds_left * board_clock.GEN_TPS)))


def prefix_cached(url=URL):
    """True when the last chat request this process sent to that server carried this stage's stable block."""
    import urllib.parse
    return client.LAST_CHAT.get(urllib.parse.urlsplit(url).netloc) == stable_messages()


def pal_letter(problem, timeout=60, url=URL, budget=None, cold=False, max_tokens=MAX_TOKENS, min_tokens=MIN_TOKENS):
    """(letter or None, info, timings). info keeps the program, its answer and why it abstained, for the CSV."""
    messages = build_messages(problem)
    cold = cold or not prefix_cached(url)
    prompt_tokens = count_tokens(messages[-1]["content"], url) + TEMPLATE_TOKENS + (prefix_tokens(url) if cold else 0)
    n_predict = max_tokens if budget is None else output_budget(prompt_tokens, budget, max_tokens)
    info = {"skipped": "", "cold": cold, "prompt_guess": prompt_tokens, "n_predict": n_predict, "finish": "",
            "code": "", "run": "", "answer": None, "how": "", "exec_s": 0.0}
    if n_predict < min_tokens:
        info["skipped"] = "budget"
        return None, info, {}
    response = post(url, {"messages": messages, "max_tokens": n_predict, "temperature": 0,
                          "seed": int(CONFIG["SEED"]), "cache_prompt": True}, timeout=timeout)
    choice = response["choices"][0]
    content = choice["message"].get("content") or ""
    info["finish"] = choice.get("finish_reason", "")
    code = extract_code(content, finished=info["finish"] == "stop")
    if code is None:
        info.update(run="no_code", code=content[:600])
        return None, info, response.get("timings", {})
    info["code"] = code[:600]
    answer, status, seconds = run_program(code)
    info.update(run=status, exec_s=seconds, answer=answer if isinstance(answer, (int, float, str)) else repr(answer)[:60])
    if not status.startswith("ok"):
        return None, info, response.get("timings", {})
    answer, note = collection_answer(answer, problem_text(problem).get("text", ""))
    if answer is None:
        info["how"] = note
        return None, info, response.get("timings", {})
    letter, how = match_answer(answer, problem.get("options"))
    info["how"] = how if not note else f"{note}_{how}"
    return letter, info, response.get("timings", {})


def stage(problem, timeout, url, budget, cold):
    """pal_letter for the pipeline: a server error or a time-out abstains."""
    import socket
    import urllib.error
    try:
        letter, info, timings = pal_letter(problem, timeout=timeout, url=url, budget=budget, cold=cold)
    except (socket.timeout, TimeoutError, urllib.error.URLError) as error:
        letter, info, timings = None, {"skipped": f"error: {getattr(error, 'reason', error)}"}, {}
    except Exception as error:  # a bug here (an odd reply, an odd value) must abstain, never cost the answer
        letter, info, timings = None, {"skipped": f"bug: {type(error).__name__}: {error}"[:200]}, {}
    return letter, info, timings
