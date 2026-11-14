"""Adaptive trainer: next problem, answer bookkeeping and mastery per topic.

Owner: C (branch `trainer`). Phase 0 stub by A: no SQLite, fixed answers.
See INTERFACES.md for the contract.
"""
from .retrieval import _sample_problems
from .topics import TOPIC_KEYS, get_topic

_STUB_MASTERY = {key: 0 for key in TOPIC_KEYS}
_STUB_MASTERY["arithmetic"] = 2


def next_problem(student_id):
    """A Problem dict in Catalan. Stub: always sample-4."""
    for p in _sample_problems():
        if p["id"] == "sample-4":
            return dict(p)
    return _sample_problems()[0]


def record_answer(student_id, problem_id, letter, hint_rung_used):
    """Check the answer and update mastery. Stub: checks against the sample labels only."""
    labels = {p["id"]: p["label"] for p in _sample_problems()}
    label = labels.get(problem_id, "?")
    topic = get_topic(problem_id)
    before = _STUB_MASTERY[topic]
    return {"correct": letter == label, "label": label, "topic": topic,
            "mastery_before": before, "mastery_after": before, "review": False}


def mastery_map(student_id):
    """{topic_key: 0..5} with all eight keys. Stub: fixed values."""
    return dict(_STUB_MASTERY)
