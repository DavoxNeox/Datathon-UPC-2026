"""The lineage of a problem: the same mathematical idea across the Kangaroo levels.

M3Kang covers 18 years and 8 levels, and one idea comes back at level 1 one year, at
level 4 another and at level 7 a third. For a given problem this module builds its
chain by levels: at every level other than the problem's own, the most similar
training problem of the same topic (by the embedding index), kept when its cosine
similarity reaches `min_similarity`, ordered from the easiest to the hardest level.

Cost on the board: a training id reuses its stored vector (no model call); a
validation id is embedded once by retrieval.query_vector (one embedding, cached), so a
chain never costs more than one embedding. The Python part is one dot product per
same-topic English row of the index.

Nothing here reasons: the chain is a lookup. It is an exploration ("look how this idea
grows"), not a hint: the rungs are further unsolved problems, shown without their answers.
Reuses copilot.retrieval (its Catalog and query_vector) without changing it.
"""
from . import retrieval
from .topics import get_topic

ROWS, COLS = 8, 13          # the LED matrix: one row per level 0..7
LEVELS = range(ROWS)
LINK_BRIGHTNESS = 3         # a rung of the chain
CURRENT_BRIGHTNESS = 7      # the level the student is on
BAR_FLOOR = 0.5             # similarity shown as 0 LEDs; 1.0 is the full row of 13
# Hand judgement of 74 links on validation (docs/lineage.md): below 0.70 almost no link is the
# same idea, from 0.75 two out of three are. bge's cosine scale is compressed: a random
# same-topic problem already scores 0.65.
DEFAULT_MIN_SIMILARITY = 0.75

# Fields of a stored problem that a link carries to the student. Never the label.
_LINK_FIELDS = ("id", "level", "year", "language", "text", "options", "text_only")


def _best_per_level(query_vec, catalog, exclude_id, topic):
    """{level: (score, id)}: the most similar same-topic English row at every level."""
    best = {}
    for pid, level, row_topic, vec in catalog.english:
        if pid == exclude_id or row_topic != topic:
            continue
        score = sum(a * b for a, b in zip(query_vec, vec))
        current = best.get(level)
        if current is None or (score, pid) > current:
            best[level] = (score, pid)
    return best


def _link(catalog, pid, lang, score, topic):
    row = catalog.row(pid, lang) or {}
    link = {key: row[key] for key in _LINK_FIELDS if key in row}
    link["id"] = pid
    link["level"] = int(row.get("level", 0))
    link["topic"] = topic
    link["similarity"] = round(score, 4)
    return link


def lineage(problem_id, lang="cat", min_similarity=DEFAULT_MIN_SIMILARITY, max_links=5, catalog=None):
    """The chain of `problem_id` by levels: list of link dicts, easiest level first.

    Each link: id, level, year, topic, similarity, text (in `lang`, else English),
    plus language, options and text_only when the index has them. Never the label,
    never the problem itself (in any language). One link at most per level; when more
    than `max_links` levels pass the threshold, the most similar ones stay.
    Without an index, or for an id whose text is unknown, the chain is empty.
    """
    catalog = catalog if catalog is not None else retrieval._catalog()
    if catalog is None or max_links <= 0:
        return []
    found = retrieval.query_vector(problem_id, catalog)
    if found is None:
        return []
    vec, own_level, _embeds = found
    topic = get_topic(problem_id)
    best = _best_per_level(vec, catalog, problem_id, topic)
    links = [(score, pid, level) for level, (score, pid) in best.items()
             if level != own_level and score >= min_similarity]
    links.sort(key=lambda t: (-t[0], t[1]))
    links = links[:int(max_links)]
    links.sort(key=lambda t: t[2])
    return [_link(catalog, pid, lang, score, topic) for score, pid, _level in links]


def embeddings_needed(problem_id, catalog=None):
    """0 when the id is in the index (stored vector), else 1: the board cost of a chain."""
    catalog = catalog if catalog is not None else retrieval._catalog()
    if catalog is None:
        return 0
    return 0 if problem_id in catalog.vectors else 1


def led_frame(chain, current_level, floor=BAR_FLOOR):
    """An 8x13 frame (brightness 0..7) for hal.led: one row per level 0..7.

    A link lights a bar from the left at LINK_BRIGHTNESS whose length is its similarity
    (at least 1 LED; `floor` = 0 LEDs, 1.0 = the full row, so bge's compressed scores
    spread over the 13 columns); the current level is a full row at CURRENT_BRIGHTNESS.
    Levels without a link stay dark. The caller draws it (hal.led), this only returns it.
    """
    frame = [[0] * COLS for _ in range(ROWS)]
    for link in chain:
        level = int(link.get("level", -1))
        if level not in LEVELS:
            continue
        sim = max(0.0, min(1.0, (float(link.get("similarity", 0.0)) - floor) / (1.0 - floor)))
        lit = max(1, round(COLS * sim))
        frame[level] = [LINK_BRIGHTNESS if c < lit else 0 for c in range(COLS)]
    if current_level in LEVELS:
        frame[int(current_level)] = [CURRENT_BRIGHTNESS] * COLS
    return frame
