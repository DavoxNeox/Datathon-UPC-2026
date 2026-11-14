"""The hint ladder: four rungs, from an easier neighbour to the solution.

Owner: D (branch `hints-app`). Phase 0 stub by A: fixed texts, no LLM.
See INTERFACES.md for the contract.
"""
from .retrieval import neighbors


def prefetch(problem_id, lang="cat"):
    """Warm the LLM prompt cache for this problem. Stub: does nothing."""
    return None


def get_hint(problem_id, rung, lang="cat"):
    """Hint result for one rung (1..4). Stub: fixed strings."""
    rung = max(1, min(4, int(rung)))
    base = {"rung": rung, "estimated_board_seconds": 0.0}
    if rung == 1:
        hits = neighbors(problem_id, level_delta=-1, same_topic=True, lang=lang, k=1)
        shown = {k: v for k, v in hits[0].items() if k != "label"} if hits else None
        return {**base, "kind": "neighbour", "problem": shown,
                "text_ca": "Mira aquest problema semblant, més fàcil.",
                "text_en": "Look at this similar, easier problem."}
    if rung == 2:
        return {**base, "kind": "strategy", "manipulative": None,
                "text_ca": "Escriu les dades del problema i què et demanen.",
                "text_en": "Write down the data and what the problem asks."}
    if rung == 3:
        return {**base, "kind": "trace",
                "text_ca": "Primer compta el total abans de treure res.",
                "text_en": "First count the total before taking anything away."}
    return {**base, "kind": "solution",
            "text_ca": "Solució: opció C (10).", "text_en": "Solution: option C (10)."}
