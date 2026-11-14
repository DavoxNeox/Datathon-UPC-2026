"""Two more ways to ask the small model about the options, both behind flags (off by default).

value_letter: ask for the VALUE of the correct option, with a grammar that allows only the
five option strings, and map it back to its letter. The model never writes a letter, so
its letter bias cannot act; the cost is the same prompt plus the value's few tokens.

vote_letter: ask for a letter once per cyclic shift of the options (A B C D E, B C D E A,
...), each option in each position exactly once, and count the votes per option. A model
that only follows position gives every option one vote (a tie, so the caller falls back);
any real preference breaks the tie. The problem text goes in its own earlier message and
the options in the last one, because llama-server restores this hybrid model's cache only
at the start of the last user message (docs/results-A.md): the text is read once, every
further shift re-reads the options only (about 45 tokens).
"""
from collections import Counter

from .client import post
from .config import CONFIG
from .llm import SYSTEM, URL, format_problem

LETTERS = "ABCDE"
VALUE_SYSTEM = ("You solve multiple-choice math competition problems for school students. "
                "Read the problem and the options, then reply with the value of the correct option, exactly as written.")
SHIFTS = ["ABCDE", "BCDEA", "CDEAB", "DEABC", "EABCD"]


def _gbnf_string(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def value_grammar(options):
    """root ::= "12" | "15" | ... : one alternative per distinct option string."""
    values = []
    for letter in LETTERS:
        if letter in options and str(options[letter]).strip() not in values:
            values.append(str(options[letter]).strip())
    return "root ::= " + " | ".join(_gbnf_string(v) for v in values)


def value_letter(problem, timeout=60, url=URL):
    """(letter or None, value, timings). None when the options are missing or several share the value."""
    options = problem.get("options") or {}
    if len(options) < 2:
        return None, "", {}
    response = post(url, {
        "messages": [{"role": "system", "content": VALUE_SYSTEM},
                     {"role": "user", "content": format_problem(problem) + "\nThe correct value is:"}],
        "grammar": value_grammar(options),
        "max_tokens": 16,
        "temperature": 0,
        "seed": int(CONFIG["SEED"]),
        "cache_prompt": True,
    }, timeout=timeout)
    value = response["choices"][0]["message"]["content"].strip()
    hits = [l for l in LETTERS if l in options and str(options[l]).strip() == value]
    return (hits[0] if len(hits) == 1 else None), value, response.get("timings", {})


def shifted_messages(problem, shift):
    """The problem text in its own message; the options, relabelled in this order, in the last one."""
    options = problem["options"]
    lines = [f"{letter}) {options[original]}" for letter, original in zip(LETTERS, shift) if original in options]
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": problem["text"].strip()},
            {"role": "assistant", "content": "I have read the problem. Give me the options."},
            {"role": "user", "content": "\n".join(lines) + "\nAnswer:"}]


def vote_letter(problem, shifts=SHIFTS, timeout=60, url=URL, min_votes=3):
    """(letter or None, {original option: votes}, [timings per request]).

    The letter is the option with the most votes when it has at least min_votes and no
    other option ties with it; else None, and the caller falls back.
    """
    options = problem.get("options") or {}
    if len(options) != 5:
        return None, {}, []
    votes = Counter()
    spent = []
    for shift in shifts:
        response = post(url, {
            "messages": shifted_messages(problem, shift),
            "grammar": "root ::= [A-E]",
            "max_tokens": 1,
            "temperature": 0,
            "seed": int(CONFIG["SEED"]),
            "cache_prompt": True,
        }, timeout=timeout)
        shown = response["choices"][0]["message"]["content"].strip()
        votes[shift[LETTERS.index(shown)]] += 1
        spent.append(response.get("timings", {}))
    ranked = votes.most_common()
    if ranked and ranked[0][1] >= min_votes and (len(ranked) == 1 or ranked[1][1] < ranked[0][1]):
        return ranked[0][0], dict(votes), spent
    return None, dict(votes), spent
