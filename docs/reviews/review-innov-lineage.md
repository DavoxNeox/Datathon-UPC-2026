# Review of `team/innov-lineage-82f1a4` (c79f716, 14 Nov 2026)

Scope: `copilot/lineage.py`, `laptop/measure_lineage.py`, `tests/test_lineage.py`, `docs/lineage.md`,
INTERFACES section. Web and LED call not implemented (proposal only). Nothing changed by me.

**Executed**: the branch's tests (OK); `laptop/measure_lineage.py` on the shared index (every number
of the coverage, floor, cost and training-sample tables regenerated); the three demo chains at 0.75
in Catalan with their LED frames; a second call for the cache. **Only read**: the 15 hand-judged
chains (I did not re-judge the 74 links).

## Executive summary

1. The brief promised the chain of the same idea across levels from the embedding index with a
   measured coverage and a judged threshold. Delivered: the module is a lookup over
   `retrieval.Catalog` (no LLM, one embedding at most, 14 ms of Python), never returns the label or
   the problem itself (tested and checked), and every figure in `docs/lineage.md` regenerates
   exactly (random floor 0.653, 181/281 = 64.4% with 3+ links at 0.75, mean 3.65, 72/100 on training
   ids, 0.13 s board estimate).
2. The honest part is also the weak part: by the authors' own judgement a link is the same idea
   45% of the time at the contract default (0.6) and 68% at 0.75, on 74 links and one judge, and
   0.75 was chosen on those same 74 links. The module still ships 0.6 as the default.
3. The three demo chains (`lvl-0_2016_8`, `lvl-4_2015_30`, `lvl-2_2016_22`) reproduce link for
   link and are convincing; they are validation ids, so the first call embeds once (0.13 s).

## Findings

**L1 (IMPORTANT). The default threshold shows a staircase that is wrong more often than right.**
`copilot/lineage.py:lineage(..., min_similarity=0.6)` and INTERFACES keep 0.6 as the signature
default while `RECOMMENDED_MIN_SIMILARITY = 0.75` sits next to it. A caller who takes the default
gets 45% precision (docs/lineage.md, 74 links). *Fix:* make 0.75 the default and keep 0.6 only as a
documented knob; the contract tests should use the default.

**L2 (IMPORTANT). The threshold was chosen on the judged sample.** 15 chains, 74 links, one judge,
and the precision-by-similarity table that justifies 0.75 is computed on those links; the quoted
"two links in three" is optimistic. *Fix:* judge 15 new chains drawn at 0.75 (the script has
`--judge`), ideally by a second person, and report that figure.

**L3 (IMPORTANT). Pedagogy: five more unsolved problems.** A link carries `text` and `options` of
another problem and nothing else; the student sees up to five statements of other levels with no
answers and no steps. As an exploration ("the same idea at every age") it is a fine demo; as help
with the current problem it is the rung-1 objection five times over. The web proposal (read-only
thumbnails, click to open) fits the exploration use; the docs should not call it a hint.

**M1 (MINOR). Adjacent-level duplicates.** M3Kang repeats a problem at two neighbouring levels in
the same year (chains 8, 10, 14, 15); the doc suggests collapsing links with similarity above 0.98
and the code does not. Cheap to add in `lineage()`.

**M2 (MINOR). Topic filter.** With `topics.json` at 76% agreement, a mis-filed query gets a chain of
the wrong topic (chains 9 and 12 in the doc). `same_topic` could be relaxed when the best same-topic
link is below the threshold.

**M3 (MINOR). Not run on the board.** The doc says so; the cost is one embedding plus Python, and
`retrieval` is already verified on the board, so the risk is low. The demo chains need
`data/val.jsonl` on the board for the text lookup (it is there).

**Verified claims**: "108 languages" (used in `docs/bilingual-rung.md` and the Hub draft) is what the
M3Kang dataset card says, with 1,747 unique problems, 2007 to 2024, 8 levels, research-only license.

## Figures checked

| Claim | Recomputed | Status |
| --- | --- | --- |
| floor 0.653 (sd 0.074), best per level 0.751 | identical | ✓ |
| 0.60: 278/281, 6.78; 0.75: 181/281 = 64.4%, 3.65, 19.2% all levels | identical | ✓ |
| max_links=5: 4.93 at 0.60, 3.16 at 0.75 | identical | ✓ |
| boards row: 20/20, 6.80, 11/20, 3.50, 0.743 | identical | ✓ |
| cost: 1 embedding + 12.2 ms mean / 22.4 worst | 13.8 ms mean / 36.4 worst (shared laptop) | ✓ |
| training sample: 72/100, 4.29 | 72/100, 4.29 | ✓ |
| demo chains: levels (1,2,3,6,7), (1,2,3,5,6), (0,3,4,5,7) | identical, Catalan texts, no label | ✓ |
| 33/74 same idea, 6/15 chains | not re-judged | read only |

## Verdict

Solid engineering and an honest measurement; change the default to 0.75, add a second judgement,
and present it as exploration, not as a hint.
