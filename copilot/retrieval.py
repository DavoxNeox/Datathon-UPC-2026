"""Neighbour problems by embedding similarity, filtered by level and topic.

Owner: B (branch `data`). Phase 0 stub by A: serves data/sample_problems.jsonl.
See INTERFACES.md for the contract.
"""
import json
import os

from .config import ROOT

_SAMPLE = os.path.join(ROOT, "data", "sample_problems.jsonl")


def _sample_problems():
    with open(_SAMPLE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def neighbors(problem_id, level_delta=0, same_topic=True, lang="cat", k=1):
    """Up to k Problem dicts in `lang`, most similar first, never the problem itself.

    Stub: returns the sample problems in `lang` (any language if none match),
    ignoring similarity, level and topic.
    """
    pool = [p for p in _sample_problems() if p["id"] != problem_id]
    same_lang = [p for p in pool if p.get("language") == lang]
    return (same_lang or pool)[:k]
