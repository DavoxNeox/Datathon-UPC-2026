# Retrieval, topics and embeddings: what the neighbour is worth, where the topic map fails, what it costs

Explorer area: `copilot/retrieval.py`, `copilot/topics.py`, `copilot/rag.py`, `copilot/embed.py`,
`build_index.py`, `data_curated/topics*.json`, `laptop/{build,cluster}_topics.py`,
`laptop/measure_retrieval.py`, the unmerged `team/innov-lineage-82f1a4` and the reviewer's I8.
Branch `team/improvements-d18364` = `origin/main 5cc2ded`, 14 Nov 2026. Problems are named by id only.

## Summary

1. The rung-1 neighbour (same topic, one level down, top-1) is "the same idea" about **44% of the time** on validation (estimate from the lineage branch's 74 hand-judged links applied to the measured similarity distribution: 59% of val queries and 70% of train queries reach cosine 0.75; below 0.70 only 1 link in 17 is the same idea). A 0.75 gate with a fallback raises the expected precision to about 63% and tells the student the truth the rest of the time.
2. The 24% topic disagreement is not spread evenly: `logic` is never recovered (0/4 hand-labelled logic problems, shipped produces 0 `logic` on the 50) and the three figure topics `boards`/`spatial`/`areas` are confused with each other (5 of the 12 errors). No cheap automatic fix helps: embedding centroid 70%, kNN vote 66-68%, Catalan vectors 41-48%, keywords+kNN 77%, all within noise of the shipped 76% on 44-50 labels. Hand labels for the ~400 low-level ids (levels 0-2, train+val) are the only real fix, and the 50 that already exist are **not even used** by `get_topic`.
3. Cost on the board is a non-issue: 0 embeddings per step for a training id, 1 (0.12 s, cached per process) for a validation id; the catalog loads once in 0.11 s / 11.6 MB (RSS 55 MB) on the laptop, a rung-1 pool is 4.6 ms and the full 1466 x 384 scan is 70 ms of pure Python (about 0.05 s and 0.7 s on the board). Caching query vectors in SQLite is not worth a table; precomputing the 281 validation vectors into `index.db` is, because it also removes the embed server as a runtime dependency (today a dead server makes `neighbors()` raise `URLError` on any validation id).
4. The Catalan query mismatch is handled correctly by the id bridge (the English row of the same id is embedded; read and verified by tests); the Catalan vectors stored in the index are never searched. Index freshness is unguarded: with `index.db` missing, rung 1 shows the made-up `sample-4` as "Un problema semblant, més fàcil (nivell 1)" (reproduced), and an index built with a different model or dimension would be dot-multiplied through `zip()` truncation without a complaint (read).
5. Ties are deterministic on one machine (sort key `(-score, id)`, 0 exact ties in 50 queries, one duplicate vector pair `lvl-1_2024_1`/`lvl-5_2024_1` at different levels). 32 of 1466 training ids get a near-duplicate (>= 0.95, same year, adjacent level) as their rung-1 neighbour: the same problem again, useless as a hint; 14 are above 0.98.

## What I ran

All from the worktree, shared servers up (`dev/start_servers.sh --status`: LLM 8081 OK, embeddings 8082 OK; never stopped).

| command | outcome | kind |
| --- | --- | --- |
| `python3 -m unittest tests.test_retrieval tests.test_topics -v` | 14 tests OK (IndexSearchTest ran against the real `data/index.db`, one embedding call for the val id) | VERIFIED |
| `python3 laptop/measure_retrieval.py --help` and `--timing 20` | train id 0.5 ms mean / 1.3 worst; val id 9.9 ms mean / 20.0 worst (embedding request included); catalog load 0.01 s warm (2932 rows, 1466 English vectors) | VERIFIED |
| `sqlite3 data/index.db` schema, counts | one table `problems(key, problem JSON, vec BLOB)`, 2932 rows = 1466 eng + 1466 cat, vec 1536 bytes = 384 float32, file 6.4 MB (1571 pages of 4 KB; JSON 1.1 MB + vectors 4.5 MB), no metadata table | VERIFIED |
| Python: confusion `topics.json` vs `topics_manual.json` | 38/50 agree (keywords only 36/50), matrix below | VERIFIED |
| Python: English index rows per level x topic; rung-1 top-1 similarity for all 281 val ids and 100 random train ids (seed 42); fallbacks; duplicate vectors; exact ties | tables below | VERIFIED |
| Python: `tracemalloc` on `Catalog()`, `_english_text()`, dot-product timings (`sum(a*b)`, array query, `math.sumprod`) | 0.110 s / 11.6 MB traced (peak 14.2); `_TEXTS` 0.016 s / 2.3 MB for 1747 rows of which 1466 are already in the catalog; 1466 dots 70.3 ms, L4-arithmetic pool (85 rows) 4.56 ms, all-arithmetic pool (398 rows) 21.8 ms; `math.sumprod` 442 ms (slower with `array('f')` rows on 3.14) | VERIFIED |
| Python: centroid / kNN / Catalan-vector topic classifiers against the 44 hand labels that are in the index | see P3 | VERIFIED |
| `INDEX_DB=/nonexistent python3 -c "hints._rung1(...)"` for a real id | returned `sample-4`, `easier: True`, text "Un problema semblant, més fàcil (nivell 1)" | VERIFIED |
| `EMBED_PORT=1 python3 -c "retrieval.neighbors('lvl-2_2016_22', ...)"` (a val id) | `URLError: Connection refused` propagates out of `neighbors()` | VERIFIED |
| `git show origin/team/innov-lineage-82f1a4:{copilot/lineage.py,docs/lineage.md}`, `git diff main..origin/team/innov-lineage-82f1a4 -- INTERFACES.md` | 74 links judged by hand, precision by similarity bin (used below) | READ |
| `git show origin/team/review-22fa88:docs/reviews/review-main-2026-11-14.md` | I8 (76% topic map, no fallback), I1 (rung 1 is an unsolved second problem), I6 (trainer relaxes level when the topic is empty), M6 (neighbour image on every poll) | READ |
| `copilot/{retrieval,topics,rag,embed,hints,trainer,webapp,llm,config}.py`, `build_index.py`, `laptop/*topics*.py`, `laptop/measure_retrieval.py`, `laptop/catalan_bridge.py`, `INTERFACES.md`, `docs/results-A.md`, `docs/README-final-draft.md` 4.3 and 6 | `results-A.md` holds no retrieval or topic figure at all; they are in `README-final-draft.md` 4.3 | READ |

Not run: anything on the board (`ssh unoq` does not resolve from this session); board seconds below are laptop x10 or the measured `BOARD_EMBED_SECONDS=0.12`.

### The numbers

English index rows per level x topic (`Catalog.english`), the pool rung 1 and the trainer draw from:

| level | arithmetic | logic | digits | counting | areas | angles | spatial | boards | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 49 | 2 | 11 | 3 | 7 | 0 | 43 | 7 | 122 |
| 1 | 32 | 1 | 16 | 3 | 5 | 0 | 27 | 5 | 89 |
| 2 | 32 | 6 | 18 | 2 | 12 | 2 | 40 | 5 | 117 |
| 3 | 28 | 3 | 23 | 3 | 17 | 7 | 24 | 6 | 111 |
| 4 | 85 | 7 | 55 | 6 | 41 | 12 | 58 | 13 | 277 |
| 5 | 68 | 4 | 57 | 10 | 47 | 14 | 32 | 11 | 243 |
| 6 | 57 | 4 | 71 | 13 | 62 | 15 | 29 | 5 | 256 |
| 7 | 47 | 6 | 72 | 10 | 55 | 19 | 38 | 4 | 251 |

Empty: `angles` at levels 0 and 1. Under 5 rows: `logic` at 0, 1, 3, 5, 6; `counting` at 0, 1, 2, 3; `angles` at 2; `boards` at 7.

Rung-1 top-1 similarity (`neighbors(id, level_delta=-1, same_topic=True, k=1)`):

| queries | n | mean | >= 0.65 | >= 0.70 | >= 0.75 | >= 0.80 | >= 0.85 | level moved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation ids | 281 | 0.759 | 94% | 79% | 59% | 24% | 10% | 0 |
| training ids (100, seed 42) | 100 | 0.775 | 99% | 89% | 70% | 31% | 7% | 0 |

By topic (val, share >= 0.75): areas 79% (n=63), digits 75% (55), angles 67% (6), spatial 66% (61), boards 55% (20), arithmetic 30% (53), counting 30% (10), logic 15% (13). By level (val): L0 55%, L1 47%, L2 41%, L3 42%, L4 61%, L5 70%, L6 65%, L7 62%. The low levels, where the demo and the trainer start, are the weakest.

Lineage branch, precision of a same-topic link by similarity (74 links, one judge, `docs/lineage.md`): 0.60-0.70 1/17 = 6%, 0.70-0.75 5/17 = 29%, 0.75-0.80 11/20 = 55%, 0.80-0.85 5/8 = 62%, >= 0.85 11/12 = 92%. Applied to the val distribution above (60 links below 0.70, 54 in 0.70-0.75, 100 in 0.75-0.80, 39 in 0.80-0.85, 28 above): **expected 124/281 = 44% same idea with no gate; 63% of the 167 shown with a 0.75 gate; 55% of the 221 shown with a 0.70 gate.** For 55 of the 281 val ids whose rung-1 neighbour is below 0.75, a same-level same-topic or an any-topic one-level-down neighbour reaches 0.75 (mean gain of the best alternative 0.035).

Confusion of the shipped map against the 50 hand labels (rows = hand, columns = shipped):

| hand \ shipped | arithmetic | logic | digits | counting | areas | angles | spatial | boards | recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arithmetic (14) | 14 | . | . | . | . | . | . | . | 1.00 |
| logic (4) | 2 | . | 1 | . | . | . | . | 1 | **0.00** |
| digits (7) | 1 | . | 6 | . | . | . | . | . | 0.86 |
| counting (6) | 1 | . | . | 5 | . | . | . | . | 0.83 |
| areas (4) | . | . | . | . | 2 | . | 1 | 1 | 0.50 |
| angles (2) | . | . | . | . | . | 2 | . | . | 1.00 |
| spatial (9) | 1 | . | 1 | . | . | . | 7 | . | 0.78 |
| boards (4) | . | . | . | . | . | . | 2 | 2 | 0.50 |

Precision of the shipped `arithmetic` is 0.74 (19 assigned, 14 right): it is the catch-all that absorbs logic, counting, digits and spatial. By level: 7/7, 4/6, 3/5, 3/4, 4/6, 8/10, 6/9, 3/3. Of the 12 errors, 7 had a confident keyword score (best >= 4, margin >= 2), so the k-means fallback never touched them; the 12 ids: `lvl-1_2015_16`, `lvl-1_2024_19`, `lvl-2_2019_20`, `lvl-2_2023_13`, `lvl-3_2020_11`, `lvl-4_2011_19`, `lvl-4_2022_24`, `lvl-5_2007_5`, `lvl-5_2017_2`, `lvl-6_2008_28`, `lvl-6_2014_3`, `lvl-6_2015_11`.

Alternative classifiers on the 44 hand-labelled ids that are in the index (centroids and votes computed from the shipped topics over the 1466 English vectors):

| classifier | agreement |
| --- | --- |
| shipped (keywords + k-means) | 33/44 = 75% |
| keywords only | 31/44 = 70% |
| nearest topic centroid, English vector | 31/44 = 70% |
| nearest topic centroid, **Catalan** vector | 21/44 = 48% |
| kNN vote k=10 / k=5, English vector | 29/44 = 66% / 30/44 = 68% |
| kNN vote k=10, Catalan vector | 18/44 = 41% |
| keywords when confident, else kNN-10 | 34/44 = 77% |

The centroid would relabel 282 of the 1466 index ids (mostly arithmetic -> counting 42, arithmetic -> logic 36, spatial -> areas 19, spatial -> boards 16): a different map, not a better one on the evidence we have.

## Proposals

### P1. Gate rung 1 on similarity 0.75, with a fallback chain and honest wording
- **Where**: `copilot/hints.py:208-233` (`_rung1`), `copilot/retrieval.py:127-151` (`neighbors` already returns `similarity`), `INTERFACES.md:78` and `:109-111` (rung 1 row and payload), `tests/test_hints.py:23-60`.
- **Problem / opportunity**: `_rung1` takes `fitting[0]` whatever its similarity. On validation 41% of those neighbours score below 0.75, where the lineage judgement found 6-29% "same idea"; the expected share of rung-1 neighbours that are the same idea is 44%. For `logic`, `arithmetic` and `counting` queries it is below 30%. The student reads "Un problema semblant" over a problem that merely shares the topic word list (reviewer I1 says the neighbour is not solved; this says it is often not similar either).
- **Proposal**: add `SAME_IDEA_SIMILARITY = 0.75` to `retrieval.py` (the lineage branch's `RECOMMENDED_MIN_SIMILARITY`, same calibration, one constant for both). In `_rung1`: (a) best hit at level-1 same topic with `similarity >= 0.75` -> today's text; (b) else best hit at the same level, same topic (`level_delta=0`, k=3) with `similarity >= 0.75` -> "del mateix nivell" text (already exists); (c) else return `{"kind": "neighbour", "problem": None, "skip": True}` and let the ladder serve rung 2 (strategy card) as the first hint, with `text_ca` "No tinc cap problema prou semblant; prova una estratègia." Keep the gated neighbour available as rung 2's second card ("un problema del mateix tema, per comparar") so nothing is lost, only renamed. Expose `similarity` in the rung payload (`INTERFACES.md:109`) so the page can show "semblança 0.81" to the teacher view. Tests: in `tests/test_hints.py` add `test_rung1_skips_a_weak_neighbour` (fake neighbour with `similarity 0.62` -> `problem is None`, `skip True`) and `test_rung1_prefers_a_same_level_strong_neighbour_over_a_weak_easier_one`.
- **Impact (jury or student)**: high. "Guide without revealing" also means not calling unrelated problems similar; the measured 44% -> 63% precision is a before/after number for the README.
- **Effort**: M.
- **Risk**: touches `INTERFACES.md` (payload gains `similarity`, rung 1 may be skipped); the demo script must be re-run because a demo problem may now open on the strategy card. Safe before the demo only after checking the three demo ids' similarities (`neighbors(id, -1, True, 'cat', 1)[0]['similarity']`).
- **How to measure**: `python3 laptop/measure_retrieval.py --judge 20` with 20 new pairs judged by B (the people protocol), split by above/below 0.75; expect >= 60% same idea above and <= 30% below. Coverage: 59% of val and 70% of train problems keep a rung-1 neighbour.
- **Verified**: ran (distribution, alternatives); the precision estimate reuses the lineage branch's judgement (read).

### P2. Skip near-duplicate neighbours (the same problem one level down)
- **Where**: `copilot/hints.py:213-214` (`hits` with k=5, `fitting`), `copilot/trainer.py:405-416` (`_choose_adaptive`, the wrong-answer branch), `copilot/retrieval.py:65-75` (`Catalog.search`).
- **Problem / opportunity**: Kangaroo reuses a problem at two adjacent levels in the same year. 32 of the 1466 training ids (2.2%) get a rung-1 neighbour with similarity >= 0.95, all from the same year, 12 with the same label; 14 are above 0.98 (7 and 2 on validation). The "easier similar problem" is then the problem itself with a different level badge, and after a wrong answer the trainer's "same topic, one level down" can serve the problem the student just failed, which is also where a leaked label would hurt most (same label in 12 of 32).
- **Proposal**: `NEAR_DUPLICATE = 0.97` in `retrieval.py`; `neighbors()` gains a keyword argument `skip_duplicates=True` that drops hits above it before truncating to k (the search already scores the whole pool, so it costs nothing). `_rung1` and `_choose_adaptive` inherit it. Test: `tests/test_retrieval.py` IndexSearchTest, query `lvl-5_2024_1` (its duplicate `lvl-1_2024_1` has an identical vector): with `skip_duplicates` the duplicate never appears in `neighbors(pid, level_delta=-4, same_topic=False, k=3)`; a unit test on `Catalog.search` with two hand-made vectors (one equal to the query) for the no-index case.
- **Impact (jury or student)**: medium. Rare (2%) but the failure mode is embarrassing in a live demo and touches the no-leak rule.
- **Effort**: S.
- **Risk**: `INTERFACES.md:130` signature gains an optional argument (compatible). Safe before the demo.
- **How to measure**: the count of rung-1 neighbours with similarity >= 0.97 over all 1466 training ids goes from 14 to 0 (the snippet in "What I ran").
- **Verified**: ran.

### P3. Let hand labels win, then hand-label the ~400 low-level ids
- **Where**: `copilot/topics.py:40-61` (`_load`, `get_topic`), `data_curated/topics_manual.json`, `laptop/cluster_topics.py:164-183` (reports agreement, never merges), `docs/README-final-draft.md:209-216`.
- **Problem / opportunity**: reviewer I8 (76%, no fallback). The 50 hand labels exist but `get_topic` reads only `topics.json`, so the 12 ids known to be wrong are still served wrong (verified: `topics._load` never opens `topics_manual.json`). The errors concentrate where a child meets them: `logic` recall 0/4 (the smallest topic, 46 ids, 1-6 index rows at levels 0-3) and `boards`/`spatial`/`areas` confusion (5/12); levels 1-2 agree 7/11. Every automatic alternative measured (centroid, kNN, Catalan vectors, combinations) is at or below the shipped map, so the keyword map is at its ceiling. The population that matters is small: 328 training + 66 validation English ids at levels 0-2 (517 for levels 0-3) feed the demo and the trainer's first problems.
- **Proposal**: (1) `topics._load` reads `topics_manual.json` after `topics.json` and overrides (manual wins), `counts()` unchanged; `topics.json["method"]` and the README say so. (2) B labels the 394 ids of levels 0-2 (English text + figure; about 15 s each, roughly 1 h 40 of one person, or 25 min each for four people), appending to `topics_manual.json` with `"method"` updated and a `"levels": [0,1,2]` note; the file stays ids + keys. (3) `laptop/cluster_topics.py` gets `--merge-manual` so the agreement report keeps measuring the automatic map on the labels (hold out the 50 original ones as the test set; the new 394 are training labels for the keyword rules if anyone retunes them). Tests: `tests/test_topics.py` `test_manual_labels_override_the_table` (write a temp manual file with one id, assert `get_topic` returns it) and keep `test_table_is_committed_and_holds_only_ids_and_keys` running on both files.
- **Impact (jury or student)**: high. It is the reviewer's top complaint on the Teach track and the fix is content, not code; the before/after is "76% -> 100% on the labelled low levels, 76% above".
- **Effort**: S for the code, L for the labelling (people time, parallelisable).
- **Risk**: no interface change. Changing a demo problem's topic changes its strategy card and its neighbour pool: re-run the demo flow after merging. Safe before the demo if the demo ids are labelled first.
- **How to measure**: `python3 laptop/cluster_topics.py --manual data_curated/topics_manual.json` agreement on the held-out 50 unchanged; `python3 -c` confusion snippet shows 0 disagreements on the labelled ids; `topics.counts()` per level 0-2 reported in the README.
- **Verified**: ran (confusion, alternatives); the override gap is read from `topics.py`.

### P4. No index, no fake neighbour; stamp the index and check it at load
- **Where**: `copilot/retrieval.py:136-138` (`_fallback` for any unknown id), `:164-168`, `copilot/rag.py:9-28` (schema, `build`), `copilot/retrieval.py:44-55` (`Catalog.__init__`), `tests/test_retrieval.py:21-31`.
- **Problem / opportunity**: with `index.db` missing, `neighbors("lvl-2_2016_22", ...)` returns the made-up `sample-4` and `_rung1` shows it as "Un problema semblant, més fàcil (nivell 1)" (reproduced). Nothing in `webapp.py` or `python/main.py` checks that the index exists (grep: no `INDEX_DB`/`index.db` outside `retrieval.py`); on a board where the `adb push` of `deploy-board.md:31` failed, the demo would show invented problems with no error. Separately, `index.db` carries no metadata: an index built with another embedding model or dimension is accepted and `zip(query_vec, vec)` silently truncates (read, `retrieval.py:73`); an index built from a different `train.jsonl` cannot be told apart either (validation ids would then be treated as training ids: harmless for cost, but `test_val_id_is_embedded_once_and_cached` would fail without explanation).
- **Proposal**: `_fallback` only for ids that are themselves sample problems (`problem_id.startswith("sample-")`), else `[]`; `_rung1` already handles `[]` ("No tinc cap problema semblant"). `rag.build` writes a `meta(key, value)` table: `model_file` (`CONFIG["EMBED_FILE"]`), `dim`, `rows`, `source` (input path), `source_sha256`, `built` (date); `Catalog.__init__` reads it and raises `ValueError` with a clear message when `dim != len(vec)` or `model_file != CONFIG["EMBED_FILE"]`, and `_catalog()` logs once and returns `None` (rung 1 then says it has nothing, the trainer uses the bank). `webapp` startup prints "retrieval: index <rows> rows, model <file>" or "retrieval: no index, rung 1 disabled" (and the teacher page shows it). Tests: `FallbackTest.test_real_id_without_index_returns_nothing` (monkeypatch `retrieval._INDEX=None, INDEX_DB="/nonexistent"`), `test_index_with_wrong_dimension_is_refused` (build a 3-row temp db with 8-float vectors via `rag.build`'s SQL, no server).
- **Impact (jury or student)**: medium. A deploy mistake becomes a visible message instead of invented maths in front of the jury.
- **Effort**: M (S without the metadata table).
- **Risk**: the metadata table requires rebuilding `index.db` once (laptop, 1466 x 2 embeddings, about 2 minutes on the shared server) and pushing 6.4 MB to the board; make the check tolerant of a missing `meta` table (warn, do not refuse) so the current file keeps working. No interface change. Safe before the demo if the old index is accepted with a warning.
- **How to measure**: the reproduction command above returns `problem: None`; `python3 build_index.py --db /tmp/x.db` then `sqlite3 /tmp/x.db "select * from meta"` lists the six keys.
- **Verified**: ran (missing index); truncation path read.

### P5. Precompute the validation vectors: zero embeddings per step, no embed server in the loop
- **Where**: `build_index.py:27-31`, `copilot/rag.py:9-28` (schema), `copilot/retrieval.py:44-55` (`Catalog`, `candidates`), `:111-124` (`query_vector`), `:93-108` (`_english_text`), `tests/test_retrieval.py:73-84`.
- **Problem / opportunity**: cost today is 0 embeddings for a training id and 1 for a validation id (0.12 s measured on the board, cached per process; `_QUERY_CACHE` dies with the process, and App Lab restarts the app on every `app start`). Small, but the dependency is not: with the embed server unreachable, `neighbors()` on a validation id raises `URLError` (reproduced), `trainer.py` has no `except` around `_neighbors` (read), so `/api/next` after an answer on a validation problem would fail the request; `webapp._compute_hint` catches it and shows an error instead of a hint. Every id the demo can show is in `train.jsonl` or `val.jsonl`, so every query vector can be known in advance. A SQLite cache of query vectors (the question asked) would save the same 0.12 s only after the first visit and keep the dependency.
- **Proposal**: `build_index.py --input data/train.jsonl --queries data/val.jsonl`: validation English rows are embedded and stored with a `split` column (`train`/`val`; `ALTER TABLE ... ADD COLUMN split TEXT DEFAULT 'train'` keeps old files readable). `Catalog.english` keeps only `split == 'train'` rows (so validation problems never become neighbours and never retrieve themselves, the rule in `build_index.py:7-8`); `Catalog.query_vectors` holds both; `query_vector` looks there before `_english_text`, and `_english_text` reads `val.jsonl` only (today it also parses the 1466 training rows it never uses). `embed()` is then called only for an id outside M3Kang. `tests/test_retrieval.py:74` becomes `test_val_id_uses_the_stored_query_vector` (`embeds == 0`); keep the embedding path tested with a made-up id and a fake `embed`.
- **Impact (jury or student)**: medium. Rung 1 and the adaptive step become deterministic file lookups that survive a dead or busy embed server; the README can state "0 model calls per hint for every M3Kang problem".
- **Effort**: M.
- **Risk**: index rebuilt once (281 more embeddings), pushed to the board; `rag.Index.search` (used by `pipeline.py` RAG, off by default) must also filter `split == 'train'`. No interface change. Safe before the demo once the new file is on the board and `tests/test_retrieval.py` passes there.
- **How to measure**: `python3 laptop/measure_retrieval.py --timing 30` shows "val id" at the train id's 0.5 ms with 0 embeddings; `EMBED_PORT=1 python3 -c "neighbors('lvl-2_2016_22', -1)"` returns a neighbour instead of raising.
- **Verified**: ran (cost, `URLError`); the trainer's missing guard is read.

### P6. Thin cells: a related-topic second pass for the trainer, said so
- **Where**: `copilot/retrieval.py:61-75` (`candidates`, `search`), `copilot/trainer.py:405-420` (`_choose_adaptive`), `copilot/topics.py:19-28`.
- **Problem / opportunity**: the index has no `angles` at levels 0-1 and 1-3 rows of `logic` and `counting` at levels 0-3 (table above). After a wrong answer on a level-2 `logic` problem the trainer asks "same topic, one level down": the pool is one problem (`lvl-1`, `logic`), so every such student meets the same one, and once it is seen the trainer falls through to `bank().candidates(level, None, ...)`, any topic, with no word to the student. Rung 1 is honest here ("No tinc cap problema semblant"), the trainer is silent. The reviewer's I6 shows the same mechanism (level relaxed, topic kept) serving a level-2 `angles` problem to a level-0 student.
- **Proposal**: `topics.RELATED = {"angles": ["areas"], "logic": ["counting", "arithmetic"], "counting": ["logic", "boards"], "boards": ["spatial"], ...}` (ids only, eight keys). `neighbors()` gains `topic=` override (today the topic is always `get_topic(problem_id)`), and `_choose_adaptive` on the wrong branch tries the own topic, then each related topic, at the wanted level, before any-topic; the served problem's payload gets `"topic_note": "tema proper"` so the page can say "Un problema d'un tema proper". Test in `tests/test_trainer.py` with the synthetic bank: a topic with no candidate at the wanted level yields a related-topic problem at that level rather than an own-topic problem at another level.
- **Impact (jury or student)**: low to medium. It only bites in 11 cells, but those are the small-topic low-level cells a primary-school demo lives in.
- **Effort**: M.
- **Risk**: `INTERFACES.md:130` optional argument; interacts with reviewer I6's fix (level before topic in the diagnostic): do I6 first. Not before the demo unless the demo avoids `logic`/`angles`/`counting` at levels 0-3.
- **How to measure**: `trainer.stats["neighbor_calls"]` plus a new counter `related_topic_served`; on the determinism run of the review, no served problem is more than one level away from the wanted level.
- **Verified**: cells ran; trainer path read.

### P7. Put the retrieval and topic figures in `docs/results-A.md` and fix the k-means provenance
- **Where**: `docs/results-A.md` (no retrieval or topic section), `docs/README-final-draft.md:209-216` and `:262-264`, `data_curated/topics.json["method"]` ("k=8"), `laptop/cluster_topics.py:127` (default `--k 12`, docstring `--k 12`).
- **Problem / opportunity**: the brief and the README point to `results-A.md` for retrieval figures; it has none. The README's 4.3 table has the 17% Catalan-overlap figure and the 76% agreement but no cost on the board, no neighbour quality, no coverage. `topics.json` says k=8, the script that wrote it defaults to k=12 and the commit (`c7e29d9`) does not record the command, so the shipped map is not reproducible by the documented command. Nothing in the docs says that 41% of rung-1 neighbours score below 0.75.
- **Proposal**: a "Phase 3 bis: retrieval and topics" section in `results-A.md` with: the cell table; the similarity table (val/train, by topic); the 44% / 63% estimate with its source (lineage branch, 74 links, one judge) and the "32 near-duplicates" count; the costs (catalog 0.11 s and 11.6 MB laptop, RSS 55 MB; 0.5 ms train id, 9.9 ms val id laptop; pool 4.6 ms, full scan 70 ms; board x10); the confusion matrix and the classifier comparison, so the README's limitation line can say where the 24% is. Record the exact regeneration command in `topics.json["method"]` and the README (`python3 laptop/cluster_topics.py --k 8 --out data_curated/topics.json`, after confirming with `--manual` that it reproduces 38/50). Add `--timing` numbers from the board to `measure_retrieval.py`'s docstring once run there.
- **Impact (jury or student)**: medium. "Measure before/after" and "error analysis" are jury criteria; the retrieval half of the Teach track is currently undocumented.
- **Effort**: S.
- **Risk**: none; docs only. Safe before the demo.
- **How to measure**: the reviewer's recompute table (`review-main-2026-11-14.md:270-280`) gains rows for these figures.
- **Verified**: ran (every number above); the provenance gap is read.

### P8. Make near-ties platform-stable
- **Where**: `copilot/retrieval.py:73-74` (`scored`, sort key), `copilot/lineage.py:40-43` (same comparison, unmerged).
- **Problem / opportunity**: ties are deterministic on one machine (`(-score, id)` sort; 0 exact ties in 50 queries) but the score is a float64 sum of float32 products in Python order, and `results-A.md:94` records 3/50 near-ties flipping between laptop and board for the LLM's logits; the same can flip a neighbour whose score differs from the runner-up in the 6th decimal, so a demo rehearsed on the laptop may show a different neighbour on the board. The returned `similarity` is already rounded to 4 decimals.
- **Proposal**: sort on `(-round(score, 4), pid)` in `Catalog.search` (and `_best_per_level` when lineage merges): neighbours within 0.0001 resolve by id on both platforms. Test: `tests/test_retrieval.py` unit test on `Catalog.search` with two candidates at scores differing by 1e-6, the lower id wins.
- **Impact (jury or student)**: low. Only the rehearsal-vs-demo consistency.
- **Effort**: S.
- **Risk**: none; a rounding boundary can still split, but far less often than raw bits. Safe before the demo.
- **How to measure**: run `neighbors` for the demo ids on the laptop and the board and diff the ids (`laptop/measure_retrieval.py --judge 20` prints them).
- **Verified**: ran (ties, duplicates); the board flip is read from `results-A.md`.

## Table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | Gate rung 1 on similarity 0.75 with a fallback chain and honest wording | high | M | yes, after checking the demo ids |
| P2 | Skip near-duplicate neighbours (the same problem one level down) | medium | S | yes |
| P3 | Hand labels win in `get_topic`; label the ~400 ids of levels 0-2 | high | S code + L people | yes, demo ids first |
| P4 | No index, no fake neighbour; stamp and check the index | medium | M | yes, with a tolerant check |
| P5 | Precompute validation vectors: 0 embeddings, no embed server in the loop | medium | M | yes, once the new index is on the board |
| P6 | Related-topic second pass for the trainer's thin cells | low-medium | M | no |
| P7 | Retrieval and topic figures in `results-A.md`; fix the k-means provenance | medium | S | yes |
| P8 | Platform-stable near-ties (round before sorting) | low | S | yes |

## Discarded

- **Automatic topic fixes** (embedding centroid, kNN vote, Catalan vectors, keyword+kNN, using the Catalan text): measured on the 44 labelled ids in the index at 41-77% against the shipped 75%, all inside the noise of 44 labels; the Catalan vectors are far worse (bge-small is English-only), which closes the "use the cat text too" idea. Only hand labels move the number (P3).
- **A multilingual embedding model** (bge-m3 or similar, 500+ MB) to search with the Catalan text: not needed, the id bridge already gives the English neighbour for a Catalan student at no cost (verified by reading `query_vector`), and it would eat a fifth of the 2.6 GB available for no student-visible gain.
- **`math.sumprod` or numpy for the dot products**: `sumprod` measured 442 ms against 70 ms for the generator sum with `array('f')` rows on Python 3.14; numpy is not stdlib (`tests/test_stdlib_only.py`). The pure-Python cost is 4.6 ms per rung-1 pool (about 0.05 s on the board) and 70 ms for a full scan (about 0.7 s), far under the 60 s step; nothing to optimise.
- **A SQLite cache of query vectors by id**: it would save 0.12 s per validation id after its first visit in a new process and nothing else; P5 stores the same vectors at build time and also removes the runtime dependency, so the cache is superseded.
- **Lowering the gate to 0.70 for coverage**: 79% of val problems keep a neighbour but the expected precision drops to 55%; the 0.75 knee (63%) is the lineage branch's conclusion too, and P1's fallback chain recovers 55 of the 114 problems below it with a stronger same-level or any-topic neighbour.
- **Changing the rung order for the word-problem topics** (`logic`, `arithmetic`, `counting`, where under 30% of neighbours reach 0.75) as a separate rule: P1's gate does it per problem instead of per topic, with the same effect where it matters.
