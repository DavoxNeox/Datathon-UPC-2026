"""Topics of M3Kang problems: eight keys, one per LED matrix row.

Owner: B (branch `data`). See INTERFACES.md for the contract.

The topic of every problem is precomputed on the laptop by laptop/build_topics.py
(keyword rules on the English text, plus embedding clusters in Phase 3b) and stored in
data_curated/topics.json as {id: topic_key}: ids only, never problem text, so the file
is committed and the board needs no text to answer get_topic(problem_id).
"""
import json
import os

from .config import ROOT

TOPICS_FILE = os.path.join(ROOT, "data_curated", "topics.json")

# LED row order. `visual` is measured by build_topics.py (share of problems that need the
# figure) and overridden from topics.json at import time when the file has it.
TOPICS = [
    {"key": "arithmetic", "name_ca": "Aritmètica i problemes", "name_en": "Arithmetic and word problems", "visual": False},
    {"key": "logic", "name_ca": "Lògica", "name_en": "Logic", "visual": False},
    {"key": "digits", "name_ca": "Xifres i nombres", "name_en": "Digits and numbers", "visual": False},
    {"key": "counting", "name_ca": "Comptatge i camins", "name_en": "Counting and paths", "visual": False},
    {"key": "areas", "name_ca": "Àrees i fraccions", "name_en": "Areas and fractions", "visual": True},
    {"key": "angles", "name_ca": "Angles", "name_en": "Angles", "visual": True},
    {"key": "spatial", "name_ca": "Raonament espacial", "name_en": "Spatial reasoning", "visual": True},
    {"key": "boards", "name_ca": "Taulers i patrons", "name_en": "Boards and patterns", "visual": True},
]
TOPIC_KEYS = [t["key"] for t in TOPICS]
_BY_KEY = {t["key"]: t for t in TOPICS}
DEFAULT_TOPIC = "arithmetic"

# The made-up problems in data/sample_problems.jsonl, used by the smoke tests
_SAMPLE_TOPICS = {"sample-1": "arithmetic", "sample-2": "arithmetic", "sample-3": "areas",
                  "sample-4": "arithmetic", "sample-5": "digits"}

_TABLE = None  # {id: topic}, loaded once


def _load(path=TOPICS_FILE):
    """Read topics.json once. Missing or broken file: an empty table, never an exception."""
    global _TABLE
    if _TABLE is None:
        table = {}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            table = {k: v for k, v in data.get("topics", {}).items() if v in _BY_KEY}
            for key, flag in data.get("visual", {}).items():
                if key in _BY_KEY:
                    _BY_KEY[key]["visual"] = bool(flag)
        except (OSError, ValueError):
            pass
        _TABLE = table
    return _TABLE


def get_topic(problem_id):
    """Topic key of a problem. "arithmetic" when unknown."""
    table = _load()
    return table.get(problem_id) or _SAMPLE_TOPICS.get(problem_id, DEFAULT_TOPIC)


def is_visual(topic):
    """True when most problems of the topic need the figure (measured in Phase 3)."""
    _load()
    return bool(_BY_KEY.get(topic, _BY_KEY[DEFAULT_TOPIC])["visual"])


def topic_name(topic, lang="cat"):
    """Student-facing name of a topic key, in Catalan (default) or English."""
    row = _BY_KEY.get(topic, _BY_KEY[DEFAULT_TOPIC])
    return row["name_en"] if lang == "eng" else row["name_ca"]


def counts():
    """{topic: number of problems} in the table, for reports and tests."""
    result = {key: 0 for key in TOPIC_KEYS}
    for topic in _load().values():
        result[topic] += 1
    return result
