"""Neighbour problems by embedding similarity, filtered by level and topic.

Owner: B (branch `data`). See INTERFACES.md for the contract.

How a search works (Phase 3 bis):

1. The query vector is the ENGLISH version of `problem_id` (bge-small is an English
   model). If the id is in the index (a training problem) its stored vector is reused:
   no embedding call, so the search costs no model time on the board. Otherwise (a
   validation problem) the English text is read from data/*.jsonl and embedded once.
2. Candidates are the English rows of the index whose level is problem.level +
   level_delta (or the nearest level that has candidates), with the same topic when
   same_topic, never the same id. Filtering comes before the dot products, so the
   Python loop is short.
3. The best k ids are returned as the rows in `lang` (Catalan by default), most
   similar first, with the topic key added.

Without an index (a fresh checkout), neighbors() serves data/sample_problems.jsonl,
as the Phase 0 stub did, so the contract tests run anywhere.
"""
import json
import os

from .config import ROOT
from .embed import embed
from .llm import format_problem
from .topics import get_topic

INDEX_DB = os.environ.get("INDEX_DB", os.path.join(ROOT, "data", "index.db"))
TEXT_FILES = [os.path.join(ROOT, "data", "val.jsonl"), os.path.join(ROOT, "data", "train.jsonl")]
_SAMPLE = os.path.join(ROOT, "data", "sample_problems.jsonl")
LEVELS = range(8)

_INDEX = None       # Catalog, loaded once
_TEXTS = None       # {id: English problem dict} for ids outside the index, loaded once
_QUERY_CACHE = {}   # {id: vector} for embedded validation problems


def _sample_problems():
    with open(_SAMPLE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class Catalog:
    """The retrieval index arranged for neighbour search: English rows with vectors, every row by key."""

    def __init__(self, db_path=INDEX_DB):
        from .rag import Index
        self.by_key = {}       # "id|lang" -> problem dict
        self.english = []      # (id, level, topic, vector) for the English rows
        for key, problem, vec in Index(db_path).rows:
            self.by_key[key] = problem
            if problem.get("language") == "eng":
                self.english.append((problem["id"], int(problem.get("level", 0)), get_topic(problem["id"]), vec))
        self.vectors = {pid: vec for pid, _l, _t, vec in self.english}

    def row(self, problem_id, lang):
        """The problem in `lang`, else its English row, else None."""
        return self.by_key.get(f"{problem_id}|{lang}") or self.by_key.get(f"{problem_id}|eng")

    def candidates(self, exclude_id, level, topic):
        return [(pid, vec) for pid, lvl, top, vec in self.english
                if pid != exclude_id and lvl == level and (topic is None or top == topic)]

    def search(self, query_vec, exclude_id, target_level, topic, k, prefer_lower=True):
        """Top-k (score, id) at the target level, or the nearest level with candidates."""
        for level in _level_order(target_level, prefer_lower):
            pool = self.candidates(exclude_id, level, topic)
            if pool:
                break
        else:
            return []
        scored = [(sum(a * b for a, b in zip(query_vec, vec)), pid) for pid, vec in pool]
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return scored[:k]


def _level_order(target, prefer_lower):
    """target first, then the nearest levels: ties go to the lower level when prefer_lower."""
    target = max(min(int(target), max(LEVELS)), min(LEVELS))
    others = sorted((lvl for lvl in LEVELS if lvl != target),
                    key=lambda lvl: (abs(lvl - target), lvl if prefer_lower else -lvl))
    return [target] + others


def _catalog():
    global _INDEX
    if _INDEX is None and os.path.exists(INDEX_DB):
        _INDEX = Catalog(INDEX_DB)
    return _INDEX


def _english_text(problem_id):
    """The English problem dict for an id that is not in the index (a validation problem)."""
    global _TEXTS
    if _TEXTS is None:
        _TEXTS = {}
        for path in TEXT_FILES:
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if '"eng"' not in line:
                        continue
                    row = json.loads(line)
                    if row.get("language") == "eng":
                        _TEXTS.setdefault(row["id"], row)
    return _TEXTS.get(problem_id)


def query_vector(problem_id, catalog):
    """(vector, level, embeddings_used) for the English version of problem_id, or None."""
    vec = catalog.vectors.get(problem_id)
    if vec is not None:
        row = catalog.row(problem_id, "eng")
        return vec, int(row.get("level", 0)), 0
    if problem_id in _QUERY_CACHE:
        return _QUERY_CACHE[problem_id]
    row = _english_text(problem_id)
    if row is None:
        return None
    vec = embed([format_problem(row)])[0]  # a document vector, like the stored ones
    _QUERY_CACHE[problem_id] = (vec, int(row.get("level", 0)), 1)
    return _QUERY_CACHE[problem_id]


def neighbors(problem_id, level_delta=0, same_topic=True, lang="cat", k=1):
    """Up to k Problem dicts in `lang`, most similar first, never the problem itself.

    Level: problem.level + level_delta, or the nearest level with candidates (ties go
    down when level_delta < 0, up otherwise). Topic: the same as problem_id's when
    same_topic. The search runs on the English text; results are returned in `lang`.
    """
    k = max(0, int(k))
    catalog = _catalog()
    found = query_vector(problem_id, catalog) if catalog is not None else None
    if found is None:
        return _fallback(problem_id, lang, k)
    vec, level, _embeds = found
    topic = get_topic(problem_id) if same_topic else None
    hits = catalog.search(vec, problem_id, level + int(level_delta), topic, k, prefer_lower=level_delta <= 0)
    results = []
    for score, pid in hits:
        row = catalog.row(pid, lang)
        if row is None:
            continue
        out = dict(row)
        out["topic"] = get_topic(pid)
        out["similarity"] = round(score, 4)
        results.append(out)
    return results


def neighbors_for_vector(vector, exclude_id, level, topic, lang="cat", k=1, prefer_lower=True):
    """Same search from a ready vector: used by the laptop analyses (Catalan vs English queries)."""
    catalog = _catalog()
    if catalog is None:
        return []
    hits = catalog.search(vector, exclude_id, level, topic, k, prefer_lower)
    return [dict(catalog.row(pid, lang), topic=get_topic(pid), similarity=round(score, 4))
            for score, pid in hits if catalog.row(pid, lang)]


def _fallback(problem_id, lang, k):
    """No index, or an id whose text is unknown: the sample problems, as the Phase 0 stub."""
    pool = [p for p in _sample_problems() if p["id"] != problem_id]
    same_lang = [p for p in pool if p.get("language") == lang]
    return (same_lang or pool)[:k]
