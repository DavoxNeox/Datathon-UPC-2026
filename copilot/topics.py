"""Topics of M3Kang problems: eight keys, one per LED matrix row.

Owner: B (branch `data`). Phase 0 stub by A: keyword-free, returns fixed values.
See INTERFACES.md for the contract.
"""

# LED row order. `visual` is provisional until B measures it (Phase 3).
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

# Stub data: the made-up problems in data/sample_problems.jsonl
_STUB_TOPICS = {"sample-1": "arithmetic", "sample-2": "arithmetic", "sample-3": "areas",
                "sample-4": "arithmetic", "sample-5": "digits"}


def get_topic(problem_id):
    """Topic key of a problem. "arithmetic" when unknown."""
    return _STUB_TOPICS.get(problem_id, "arithmetic")


def is_visual(topic):
    return _BY_KEY.get(topic, _BY_KEY["arithmetic"])["visual"]
