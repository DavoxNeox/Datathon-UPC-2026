# How the next problem is chosen: the trainer's policy and the retrieval it draws from, as one spec

Second-round integration of `docs/improvements/trainer.md` (P1-P9), `docs/improvements/retrieval-topics.md`
(P1-P8), `docs/improvements/hints-pedagogy.md` P10 and `docs/demo/demo-problems.md`, re-checked on the worktree at
`7a67b77` (suite: 181 tests OK, 1 skipped, 7.1 s). Problems are named by id only; nothing was changed but this file.

**Summary**

1. One policy, one page (section 1): diagnostic at the exact chosen level `(L, L+1, L-1)`; adaptive step "two
   rights to go up one level, one wrong to go down one, same topic", neighbours ranked by similarity but filtered
   only by level and by near-duplicate; review due in answers (3/5/8/13/21); exhaustion repeats the least-recently
   answered problem; base level follows the median of the last ten levels; retrieval guarantees `skip_duplicates`,
   `similarity` in every hit, hand labels first, no invented problem, no exception, platform-stable ties.
2. Two contradictions resolved with numbers: **the near-duplicate constant is 0.95, not 0.97** (all 32 train ids whose
   rung-1 neighbour scores >= 0.95 are the same year at the adjacent level; the 13 in [0.95, 0.97) are too), shared by
   retrieval, hints, trainer and `dev/demo_pick.py`; and **the 0.75 gate is for rung 1 only**: the trainer skips
   duplicates but keeps weak neighbours (31 % of its wrong-branch steps are below 0.75; gating them would hand a third
   of the path to a random bank pick that is, in expectation, less similar still).
3. Measured on the real bank with the real `retrieval.neighbors` wrapped (8 students x 60 steps, 355 adaptive calls):
   7 served problems (2.0 %) were near-duplicates of the problem just answered (3 above 0.97, 0.9971 at worst), 63
   (18 %) below 0.75, 10 bank fallbacks (all eight neighbours already seen, never a thin cell), 0 level relaxations,
   8 embeddings (validation ids). Thin cells are reached from the diagnostic's topic rotation, not from the adaptive step.
4. The demo: today's chains (`Mariona1 1`, `Guillem 2`, `Pau 3`) are exactly those in `demo-problems.md`. Problem 1 of
   each survives every proposal; **problem 2 changes in all three chains as soon as the diagnostic changes** (it is
   "two levels up" today), so the chains must be re-picked and re-rehearsed (procedure in section 2, about one hour).
   The near-duplicate skip, the hand-label override of the existing 50 labels and the exhausted-bank fix leave the
   chains and their neighbours untouched (verified by re-picking with each rule patched in).
5. Order: before the demo only the exhausted-bank fix, the shared duplicate constant with `skip_duplicates`, the
   hand-label override (50 labels, not the 394 new ones), the no-fake-fallback and never-raise guards, and the
   measurement harness. Diagnostic, staircase, review, base level and the related-topic pass wait for the morning after,
   with the re-pick.

## What I ran

All from the worktree, shared servers up (`dev/start_servers.sh --status`: LLM 8081 OK, embeddings 8082 OK, never
stopped; the embed server was used for 8 validation ids only). Scratch scripts in the session scratchpad.

| command | outcome | kind |
| --- | --- | --- |
| `STUDENTS_DB=<scratch>/x.db python3 -m unittest discover tests` | 181 tests OK, 1 skipped, 7.1 s | ran |
| `STUDENTS_DB=<scratch>/x.db python3 -m copilot.simulate --bank data --neighbors index --steps 60` | 1.5 s wall; the table is the trainer report's baseline to the row (threshold2 47 % / max mastery 3; random20-3 max mastery 4; 0 repeats; 4-15 reviews) | ran |
| `python3 dev/demo_pick.py --chain Mariona1 1`, `--chain Guillem 2`, `--chain Pau 3` | ids below, identical to `docs/demo/demo-problems.md`; neighbour similarities 0.9353 / 0.9143, 0.8266 / 0.8102, 0.8589 / 0.7292 | ran |
| scratch `dup_sim.py`: the 8 simulated students x 60 steps with `trainer.configure(neighbors_fn=wrapper)` around the real `retrieval.neighbors`, recording every call's hits and similarities and the id the trainer served | 355 adaptive calls: 345 served from the hits, 10 bank fallbacks; similarity of the served problem mean 0.798; >= 0.95: 7, >= 0.97: 3; < 0.75: 63 (wrong branch 51/162, right branch 12/183); 0 relaxed-level calls, 0 empty; hits >= 0.95 anywhere in the k=8 lists: 12 of 2778; 8 embeddings | ran |
| scratch `dup_census.py`: rung-1 top-1 (same topic, one level down) for all 1466 index ids | >= 0.90: 52 (47 same year); >= 0.95: 32 (32 same year, 32 adjacent level, 12 same label); >= 0.97: 19; >= 0.98: 14; the 13 ids in [0.95, 0.97) are all same year, adjacent level, 3 same label; second-best after dropping the duplicate: 0.66-0.87 | ran |
| scratch `demo_cells.py`: the six demo ids' k=5 rung-1 lists and the trainer's `+1 any-topic` and `0 any-topic` k=8 lists; the 12 manual-vs-shipped topic disagreements against the cells the chains draw from; the chains re-picked with (a) the diagnostic `(L, L+1, L-1)` + exact level first and (b) the manual labels patched into the bank | no hit >= 0.95 in any demo list; 5 of 12 relabelled ids sit in a demo cell but the re-pick with labels gives the same problems 1 and 2 in all three chains (only Guillem's 3rd changes); the proposed diagnostic keeps problem 1 and changes problem 2 in all three chains (ids in section 2) | ran |
| `trainer.py`, `retrieval.py`, `simulate.py`, `topics.py`, `hints.py:208-229`, `dev/demo_pick.py`, `INTERFACES.md:58-160`, `tests/test_trainer.py`, `tests/test_retrieval.py`, `docs/demo/{demo-problems,runbook}.md`, reviewer I6/I8/I12 and "What can fail live" | read | read only |

Demo chains on `7a67b77` (ids, level, topic; rung-1 neighbour, similarity):

| chain | problem 1 | problem 2 | problem 3 (never shown) |
| --- | --- | --- | --- |
| `Mariona1` L1 | `lvl-1_2024_2` L1 boards; `lvl-0_2024_3` 0.9353 | `lvl-3_2019_18` L3 spatial; `lvl-2_2019_9` 0.9143 | `lvl-5_2011_18` L5 areas |
| `Guillem` L2 | `lvl-2_2020_4` L2 arithmetic; `lvl-1_2021_21` 0.8266 | `lvl-4_2010_12` L4 digits; `lvl-3_2016_29` 0.8102 | `lvl-6_2019_24` L6 spatial |
| `Pau` L3 | `lvl-3_2021_20` L3 areas; `lvl-2_2022_15` 0.8589 | `lvl-5_2022_30` L5 counting; `lvl-4_2016_11` 0.7292 | `lvl-7_2008_3` L7 boards |

## 1. The problem-selection policy, as it should be

The trainer decides **which** problem; retrieval ranks **within** the cell the trainer asks for. Every rule below is
deterministic given `SEED`, the pseudonym and the number of answers so far (today's `_rng`), and the LLM is never
involved. A served problem is never one the student has seen (`_seen_ids`, pending included) while unseen ones remain.

**Diagnostic** (trainer P3, reviewer I6; resolves retrieval P6's "I6 first").
- With a chosen level `L` (the start screen): exactly three problems at levels `(L, L+1, L-1)`, clamped; base level =
  highest level passed, else `L-1` (today's `(L, L+2, L+4, L+6, L+7)` serves 1r and 3r d'ESO problems to a 6è child).
  Without a level: today's `(0, 2, 4, 6, 7)`, stop at the first wrong answer after three.
- **Exact level before topic**: `bank().at_level(level, topic)` then `at_level(level, None)` then today's `candidates`.
  Topic rotation stays (shuffled by pseudonym), so a topic with an empty cell (angles L0-L1, logic/counting L0-L3) yields
  its turn to another topic at the right level instead of a level-2 problem. This is where thin cells bite (0 of 355
  adaptive calls relaxed the level in the simulation; the diagnostic's topic turn is the only path that does).
- After the diagnostic the chain starts at the base level with a bank pick, not from the last diagnostic problem.

**Adaptive step** (trainer P1; retrieval P2 and P6; hints P10 for the clock).
- Last answer right: if the previous main-path answer was also right, a neighbour **one level up, any topic**; else a
  neighbour **at the same level, any topic**. Last answer wrong: a neighbour **same topic, one level down**. Sentence for
  the jury: "two right answers in a row take you up a level, one wrong answer takes you down one on the same topic".
  Measured in the trainer report (monkeypatched, real bank): threshold students 47 -> 60 % accuracy, mastery 4 reachable,
  guessers capped at 2, same convergence (3 steps).
- `neighbors(last_id, level_delta, same_topic, lang="cat", k=8)` (default `skip_duplicates=True`): the first hit that is
  unseen, not the query, and **on the wanted side of the level** (today's filter) is served. Near-duplicates (>= 0.95
  of the query) never appear in the list (retrieval guarantee below). **Weak neighbours are kept**: see the resolution
  below. The hit's `similarity` is recorded in `trainer.stats` (harness, section 3), never shown to the student.
- When the hits are exhausted (all seen) or empty: today's bank fallback at the wanted level in the wanted direction,
  own topic first, then any topic. When the served problem's topic differs from the wanted one (wrong branch only), the
  Problem dict carries `topic_note: "any"` and the page says "Un problema d'un altre tema" (retrieval P6's honesty).
  The `RELATED` topic map of retrieval P6 is **deferred** until the hand labels of retrieval P3 make the eight topics
  trustworthy enough to say which are "near"; the explicit word costs 5 lines and tells the truth today.
- Mastery (trainer P1b, P2): read from the last six answers on the topic, no post-hoc exceptions; 4 = "3 of the last 4
  right without hints on 3 distinct problems"; 5 = one of those at a level above the student's level.

**Review** (trainer P4, reviewer I12): no coin. Intervals in main-path answers `{1: 3, 2: 5, 3: 8, 4: 13, 5: 21}` by the
topic's mastery; the worked topic (other than the current one) with the largest `answers_since_last_seen / interval
>= 1` is reviewed at its practice level (bank pick, no neighbour call); at most one review in a row; the student is not
told, `record_answer` keeps `review: True`. Sentence: "a topic comes back after 3, 5, 8, 13 or 21 problems, sooner the
weaker it is".

**Exhaustion** (trainer P5): when every problem is seen, repeat the problem whose **most recent** answer is the oldest
(`GROUP BY problem_id ORDER BY MAX(id)`), not the first answer forever. Near-duplicates are skipped only relative to
the query, not to the whole history (see Discarded).

**Base level** (trainer P7): seeded by the diagnostic, then the median level of the last ten main-path answers after
every answer; `target_level` and mastery 5 read it; the teacher report shows it as `level_now`.

**What retrieval must guarantee** (retrieval P2, P3, P4, P5, P8; hints P10):
1. `skip_duplicates=True` by default: no hit with similarity >= `NEAR_DUPLICATE = 0.95` of the query, dropped before
   truncating to `k` (the whole pool is scored anyway).
2. Every returned dict carries `similarity` (4 decimals, already true) and `topic` (already true): this becomes a
   contract line, because the trainer's harness, the teacher view and `dev/demo_pick.py` read it.
3. `topics.get_topic` returns the hand label when `data_curated/topics_manual.json` has one (manual wins).
4. No invented problem: `_fallback` only for `sample-*` ids; any other id without a vector or text returns `[]`.
5. `neighbors` never raises: a dead embed server or a missing index gives `[]` (and one log line); the trainer then
   uses the bank. Preferred form: the validation vectors precomputed into `index.db` (retrieval P5), so no embed call
   remains in the loop at all; minimum form: `try/except OSError` around `embed` in `query_vector`.
6. Ties resolved by id after rounding the score to 4 decimals, so a chain rehearsed on the laptop is the chain on the
   board (retrieval P8).
7. `neighbors` exposes the embedding count of the call (`last_cost` or a tuple-returning sibling) so rung 1 can report
   0.12 s instead of 0.0 for a validation id (hints P10).

**Merged and resolved.** Merged: trainer P1, P3, P4, P5, P7 (policy), P2 (mastery sentence), P8 (harness); retrieval
P2, P3, P4, P5, P6 (the word, not the map), P8; hints P10. Resolved: (a) **0.97 vs 0.95**: retrieval P2 proposed
`NEAR_DUPLICATE = 0.97`, `dev/demo_pick.py` filters at `MAX_SIM = 0.95`; the census says every one of the 32 ids at
>= 0.95 is the same year at the adjacent level (the signature of a Kangaroo reuse), including the 13 in [0.95, 0.97),
while [0.90, 0.95) is mixed (15 of 20 same year). One constant, 0.95, in `retrieval.py`, imported by `demo_pick.py`.
(b) **The 0.75 gate**: retrieval P1 gates rung 1 at `SAME_IDEA_SIMILARITY = 0.75` because a hint called "semblant"
must be the same idea (44 % -> 63 % precision). The trainer **does not gate**: its neighbour is the next practice
problem at a promised level and topic, never announced as similar; 51 of its 162 wrong-branch steps (31 %) are below
0.75 and the only alternative is an unranked bank pick from the same cell, whose expected similarity is lower than the
ranked top; a gate would make a third of the LED path depend on `rng` for no student-visible gain. Both rules read the
same ranked list and the same `similarity` field; they differ because a hint and a practice problem are different
promises. (c) **Topic vs level when a cell is thin**: level wins in the diagnostic (trainer P3b); in the adaptive wrong
branch the topic wins at the wanted level, then the level wins with the word `topic_note: "any"` (retrieval P6 minus the
`RELATED` map). (d) **"Correct -> one level up"** in `results-A.md:132-135`, `README-final-draft.md:27` and the demo
narration becomes the two-in-a-row sentence; the demo's two mastery moves (tick 0 -> 2, cross 0 -> 1) are unchanged.

## Proposals

### P1. One near-duplicate constant, 0.95, in `retrieval.py`, used by `neighbors`, `_rung1`, the trainer and `demo_pick`
- **Where**: `copilot/retrieval.py:65-75` (`Catalog.search`), `:127-151` (`neighbors`), `copilot/hints.py:213`,
  `copilot/trainer.py:407` (`_neighbors`), `dev/demo_pick.py:33` (`MAX_SIM = 0.95`), `INTERFACES.md:130-137`.
- **Problem / opportunity**: retrieval P2 says 0.97, `demo_pick.py` says 0.95, nothing in the runtime skips anything.
  Census over the 1466 index ids: 32 rung-1 neighbours >= 0.95, all the same year at the adjacent level, 12 with the same
  label; the 13 in [0.95, 0.97) are all same-year reuses too (3 same label), so 0.97 would let 13 copies through.
  In the wrapped simulation 7 of 345 served problems were such copies of the problem just answered (threshold2 step 48:
  `lvl-2_2021_29 -> lvl-3_2021_24` at 0.9971, one step after the label was shown on the page).
- **Proposal**: `NEAR_DUPLICATE = 0.95` in `retrieval.py`; `Catalog.search(..., skip_above=None)` drops scored pairs
  with `score >= skip_above` before `[:k]`; `neighbors(..., skip_duplicates=True)` passes it; `_rung1` and `_neighbors`
  use the default; `demo_pick.py` does `from copilot.retrieval import NEAR_DUPLICATE as MAX_SIM`. The second-best hit
  is 0.66-0.87 for the 32 affected ids, so a neighbour still exists for every one of them.
- **Impact (jury or student)**: medium: rare (2 %) but it is the "same problem again, with the answer just revealed" case.
- **Effort**: S.
- **Risk**: `INTERFACES.md` signature gains an optional argument. Safe before the demo: no hit in the six demo ids'
  k=5 rung-1 lists or k=8 trainer lists is >= 0.95 (max 0.9353), so nothing the demo shows changes.
- **How to measure**: `dup_census.py`'s ">= 0.95" count over the top-1 after the change is 0; the wrapped simulation's
  "served >= 0.95" is 0 of about 345.
- **Verified**: ran (census, simulation, demo lists).

### P2. The trainer skips duplicates, keeps weak neighbours, and records the similarity it served
- **Where**: `copilot/trainer.py:405-424` (`_choose_adaptive`), `:171` (`stats`), `copilot/simulate.py:283-300`
  (columns), `INTERFACES.md:139-148`.
- **Problem / opportunity**: retrieval P1's gate is written for `_rung1`; left unsaid, an implementer would apply it to
  the trainer too. Measured: 63 of 345 served neighbours (18 %) are below 0.75, 51 of 162 on the wrong branch (31 %;
  spatial 28/115, arithmetic 9/23, counting 7/15). A gate there replaces a ranked pick by `rng` over the same cell.
- **Proposal**: no gate in `_choose_adaptive`; add `stats["served_similarity"]` (list), `stats["duplicates_skipped"]`,
  `stats["bank_fallbacks"]`, `stats["topic_left"]` (served topic != wanted topic on the wrong branch), reset in
  `configure()`; the simulator prints `mean sim`, `<0.75`, `dups`, `fallbacks`, `topic left` columns. Write the
  decision in the trainer docstring ("neighbours are ranked, not gated") and in `INTERFACES.md`.
- **Impact (jury or student)**: medium: it is the number that tells the jury the trainer's neighbour is measured, and it
  stops a well-meant gate from randomising the LED path.
- **Effort**: S.
- **Risk**: none for the board (`stats` is a dict). Safe before the demo.
- **How to measure**: the simulator's new columns on `--bank data --neighbors retrieval`: `<0.75` about 18 %, `dups` 0
  after P1, `fallbacks` about 10 per 480 steps.
- **Verified**: ran (the figures); the gate decision is reasoning.

### P3. Diagnostic at the exact chosen level, `(L, L+1, L-1)`, chain restarts at the base level, and the demo re-pick that follows
- **Where**: `copilot/trainer.py:99-100, 375-390, 434-438, 456-462, 514-523`; `dev/demo_pick.py:46-60` (`first_problems`
  mirrors `_choose_diagnostic` and must mirror the new one); `docs/demo/demo-problems.md:7-13, 29-35`;
  `docs/demo/runbook.md:92-97`; `tests/test_trainer.py:102-112, 221-246`; `INTERFACES.md:155-158`.
- **Problem / opportunity**: trainer P3 as written, plus the fact it did not state: the rehearsed chains depend on it.
  Re-picked with the proposed levels and exact-level-first: `Mariona1 1` -> `lvl-1_2024_2`, **`lvl-2_2019_24`**
  (neighbour `lvl-1_2016_19`, 0.783), `lvl-0_2018_20`; `Guillem 2` -> `lvl-2_2020_4`, **`lvl-3_2017_15`** (`lvl-2_2017_27`,
  0.8116), `lvl-1_2022_15`; `Pau 3` -> `lvl-3_2021_20`, **`lvl-4_2024_23`** (`lvl-3_2016_4`, 0.6257, which retrieval P1
  would gate to a strategy card), `lvl-2_2016_3`. Problem 1 survives in all three (same cell, same `rng`, same list);
  problem 2 changes in all three and the new ones are unchecked for Catalan text, clean options and pictures.
- **Proposal**: trainer P3 (a)(b)(c) unchanged, and `demo_pick.first_problems` rewritten to call a new pure function
  `trainer.diagnostic_plan(student_id, start_level, seen)` that both use, so the script can never drift from the
  trainer again (today it re-implements the choice). Then the re-pick procedure of section 2.
- **Impact (jury or student)**: high: the first three problems are the demo; a 6è child today meets a 2n d'ESO problem
  as problem 2.
- **Effort**: M for the trainer, plus about 1 h of re-pick and rehearsal (section 2).
- **Risk**: changes the rehearsed chains, `demo-problems.md`, `runbook.md` step 6, the contingency video; touches
  `INTERFACES.md`. **Not safe the day of the demo**; the morning after, or only with a full re-pick slot.
- **How to measure**: `start_student(sid, 0)`, all wrong, 8 steps: max level <= 1; `diagnostic_levels(6) == (6, 7, 5)`;
  `dev/demo_pick.py --chain <name> <L>` equals what `dev/demo_rehearse.py` sees in sim and on the board.
- **Verified**: ran (the re-pick); the trainer change is read only.

### P4. Adaptive step: two rights to go up, one wrong to go down, duplicates skipped, level kept, "any topic" said
- **Where**: `copilot/trainer.py:405-424`, `:309-329` (`derive_mastery`), `:96-97`; `copilot/webapp.py` (the problem
  payload passes `topic_note` through), `assets/` student page (one line of text); `INTERFACES.md:58-69, 139-148`;
  `tests/test_trainer.py:114-121, 41-48, 170-175`; `docs/results-A.md:132-135`, `docs/README-final-draft.md:27`.
- **Problem / opportunity**: trainer P1 and retrieval P6 touch the same ten lines from two sides and nobody wrote the
  combined rule. Today: mastery 4 unreachable for threshold students (max 3 after 60 steps), a 20 % guesser reached 4;
  after a wrong answer in a one-problem cell the student silently leaves the topic.
- **Proposal**: as in section 1: `up = last two main-path answers correct`; `level_delta = +1 if up else 0` on a right
  answer with `same_topic=False`, `-1` and `same_topic=True` on a wrong one; keep today's wanted-side filter; the
  neighbour call inherits `skip_duplicates`; bank fallback own topic then any topic, with `problem["topic_note"] =
  "any"` when the topic changed on the wrong branch. `derive_mastery`: 4 = three of the last four correct at rung 0 on
  three distinct problems. The `RELATED` map waits for the labels (retrieval P3).
- **Impact (jury or student)**: high: accuracy 47 -> 60 % for a student at their level, a reachable and guess-proof
  LED bar, and no silent topic change.
- **Effort**: M.
- **Risk**: three tests rewritten; `INTERFACES.md` mastery wording; the demo narration sentence. The demo's two problems
  are both diagnostic, so the chains do not change, but the sentence V2 says does: **after the demo**, or with P3 in one
  re-pick slot.
- **How to measure**: `python3 -m copilot.simulate --bank data --neighbors retrieval --steps 60`: threshold2 >= 58 %,
  max mastery >= 4 for threshold2/5, <= 2 for every random20, `topic left` reported, `dups` 0.
- **Verified**: ran (trainer report's monkeypatched variant, re-read); the merge is read only.

### P5. Review due in answers, bank-picked, at most one in a row
- **Where**: `copilot/trainer.py:101, 393-402, 464-467`; `INTERFACES.md:139-150`; `docs/README-final-draft.md:27, 291`,
  `docs/project-hub-draft.md:69-73`; `tests/test_trainer.py:152-175`.
- **Problem / opportunity**: trainer P4 as written (coin at 20 %, oldest topic, 57-65 % on the weakest topic, median gap
  11). Added here: the review never calls `neighbors` (bank pick at the practice level), so it is outside P1/P2 and must
  stay so (a review is "the same topic again", not "a neighbour of the last problem").
- **Proposal**: trainer P4's rule verbatim; `_choose_review` keeps `bank().candidates(level, topic, exclude=seen)`;
  `stats["reviews_due"]` for the harness.
- **Impact (jury or student)**: medium: a claimed feature becomes true and explainable in one sentence.
- **Effort**: M.
- **Risk**: deterministic paths change (same-id determinism holds). Unreachable in a three-click chain (the diagnostic is
  not finished), so technically safe before the demo, but it brings nothing to the demo: do it after.
- **How to measure**: reviews on the weakest worked topic >= 80 %; gap for mastery-1 topics <= 4, mastery-4 >= 13.
- **Verified**: read only (the measurement is the trainer report's).

### P6. Exhausted bank: repeat the least recently answered problem; base level follows the student
- **Where**: `copilot/trainer.py:427-431` (`_least_recent`), `:514-523`, `:327-334`; `tests/test_trainer.py:183-189`;
  `INTERFACES.md:155-158`.
- **Problem / opportunity**: trainer P5 (the same first problem forever on a 12-problem bank, reproduced in that report;
  it bites the `stub` bank and any small cell once P3 makes exact levels bind) and trainer P7 (base frozen at the
  diagnostic: an improving student jumps 2 -> 5 on a review).
- **Proposal**: `SELECT problem_id FROM answers WHERE student_id=? GROUP BY problem_id ORDER BY MAX(id) LIMIT 1`;
  `students.base_level` recomputed after every main-path answer as the median of the last ten main-path levels, the
  diagnostic only seeds it; `teacher_report` adds `level_now`.
- **Impact (jury or student)**: medium (exhaustion: high in stub/demo-set mode; base level: removes a visible LED jump).
- **Effort**: S (exhaustion) + M (base level).
- **Risk**: exhaustion: none, no interface change, **safe before the demo**. Base level: `INTERFACES.md` text and the
  `start_student` paragraph; only together with P3, so after the demo.
- **How to measure**: `test_repeats_only_when_the_bank_is_exhausted` extended (`ids[12:20]` has 8 distinct ids in the
  order of first answering); simulator `base_level` column rises with the `improving` student's threshold.
- **Verified**: read only (reproductions are the trainer report's).

### P7. Retrieval guarantees the trainer relies on: hand labels first, no invented problem, never raise, stable ties
- **Where**: `copilot/topics.py:40-61` (`_load`), `copilot/retrieval.py:136-138` (`_fallback`), `:111-125`
  (`query_vector`), `:73-74` (sort key), `copilot/rag.py:9-28` (metadata), `tests/test_topics.py`, `tests/test_retrieval.py`.
- **Problem / opportunity**: retrieval P3, P4, P5, P8 as written. Added here, the demo check they asked for: the 12 ids
  where the 50 hand labels disagree with `topics.json` include 5 that sit in cells the chains draw from
  (`lvl-1_2024_19` arithmetic -> spatial L1, `lvl-3_2020_11` spatial -> boards L3, `lvl-4_2011_19` digits -> logic L4,
  `lvl-2_2023_13`, `lvl-1_2015_16`), yet re-picking with the labels patched in gives the same problems 1 and 2 in all
  three chains (only Guillem's never-shown 3rd moves, `lvl-6_2019_24 -> lvl-6_2020_25`); no demo id is relabelled and
  none of their k=5 neighbours is. So the override of the **existing** 50 is safe; adding the 394 low-level labels
  changes cell sizes and therefore `rng.randrange(len(ids))`: not before the demo.
- **Proposal**: `topics._load` reads `topics_manual.json` after `topics.json` and overrides; `_fallback` only for
  `sample-*`; `query_vector` catches `OSError`/`URLError` from `embed` and returns `None` (so `neighbors` returns `[]`),
  with the precomputed validation vectors (retrieval P5) as the full fix; `Catalog.search` sorts on
  `(-round(score, 4), pid)`; `webapp` prints the index status at start.
- **Impact (jury or student)**: medium-high: a dead embed server or a failed `adb push` stops being invented maths or a
  500 on `/api/next`; the 12 known-wrong strategy cards are fixed by content.
- **Effort**: M (S each).
- **Risk**: no signature change; `INTERFACES.md` gains the guarantees as text. Safe before the demo **for the 50
  labels** (verified), the fallback, the guard and the rounding (ties within 0.0001 do not occur in the demo lists).
- **How to measure**: `INDEX_DB=/nonexistent` rung 1 on a real id -> `problem: None`; `EMBED_PORT=1` `neighbors` on a
  val id -> `[]` not `URLError`; confusion snippet on the 50 labels -> 0 disagreements; `demo_pick.py --chain` unchanged.
- **Verified**: ran (the demo re-pick with labels, the demo lists); the guards are read only.

### P8. The measurement harness: simulator `--start-level`, wrapped neighbours with counters, guessers test, and the table in `results-A.md`
- **Where**: `copilot/simulate.py:200-217, 283-300, 319-360`; new `tests/test_trainer.py::test_guessers_never_reach_mastery_four`;
  `docs/results-A.md` (new section "Trainer and retrieval on simulated students"); `docs/README-final-draft.md:199`.
- **Problem / opportunity**: trainer P8 as written, plus: the simulator's `--neighbors index` stop-gap returns no
  `similarity`, so duplicates and weak neighbours are invisible to it; `emb/step` assumes one embedding per call while
  the real figure was 8 embeddings in 355 calls (validation ids only). The before table exists only in scratch files.
- **Proposal**: (a) `--start-level N` calls `start_student(name, N)` first and adds a `base_level` column; (b)
  `--neighbors retrieval` becomes the default for `--bank data` and the simulator wraps the function as `dup_sim.py`
  does, printing per student `mean sim`, `<0.75`, `dups served`, `fallbacks`, `relaxed`, `topic left`, `embeddings`
  (from `len(retrieval._QUERY_CACHE)` or P7's cost hook); (c) the guessers test on the synthetic bank (three random20
  seeds, 60 steps, `max_mastery <= 3`; `expectedFailure` until P4 lands); (d) the before/after table of section 3
  pasted into `results-A.md` with the command and the commit; fix the README's "0.24 s per step".
- **Impact (jury or student)**: medium: "measure before/after" is a jury criterion and today the trainer has no figure
  in any document.
- **Effort**: M.
- **Risk**: none for the board. Safe before the demo (the before half can be published now).
- **How to measure**: the table in `results-A.md` equals the simulator's output on the stated commit.
- **Verified**: ran (every "before" number in section 3).

## 2. Impact on the rehearsed demo chains, and the re-pick procedure

What each rule does to the three chains (both shown problems are **diagnostic** problems; the adaptive step, the review
and the exhaustion rule are never reached in a two-problem chain):

| rule | problem 1 (x3) | problem 2 (x3) | rung-1 neighbours | verdict |
| --- | --- | --- | --- | --- |
| P1 near-duplicate skip at 0.95 (or 0.97) | same | same | same (top hits 0.73-0.94, no hit >= 0.95 in any k=5 list) | safe |
| P6 exhausted-bank fix | same | same | same | safe |
| P7 hand labels override, the existing 50 | same | same | same (no demo id or neighbour relabelled; re-pick verified) | safe |
| P7 hand labels, +394 low-level ids | **changes** (cell sizes change the `randrange` index) | changes | changes | after |
| P7 no fake fallback, never raise, rounded ties | same | same | same | safe |
| P3 diagnostic `(L, L+1, L-1)`, exact level first | same | **changes in all three**: `lvl-2_2019_24`, `lvl-3_2017_15`, `lvl-4_2024_23` | new: 0.783, 0.8116, **0.6257** | re-pick |
| P4 staircase, P5 review, P6 base level | same | same | same | the narration changes, not the ids |
| retrieval P1 rung-1 gate at 0.75 | same | same | `Pau` problem 2 (0.7292) opens on a strategy card; the new `Pau` problem 2 under P3 (0.6257) too | re-check |

**Plainly: the demo chains must be re-picked after any trainer change that touches `_choose_diagnostic`,
`diagnostic_levels`, `_Bank` cell contents (topics) or `_pick`. P3 and the 394 labels are therefore NOT safe the day
of the demo.** `docs/demo/runbook.md:95-97` already says that a chain mismatch on the board cannot be fixed by the
laptop script; a mismatch created on purpose the night before is the same accident.

Re-pick procedure (laptop with `~/m3kang-data` linked, servers up; about one hour including the board):

1. Land the trainer change; `STUDENTS_DB=<scratch>/x.db python3 -m unittest tests.test_trainer tests.test_hints` green;
   `dev/demo_pick.py` must use the shared `trainer.diagnostic_plan` (P3) so it mirrors the new rule.
2. `python3 dev/demo_pick.py --chain Mariona1 1`, `--chain Guillem 2`, `--chain Pau 3`. If problems 1 and 2 of a chain
   both print `ok: True`, keep the pseudonym. Otherwise `python3 dev/demo_pick.py --levels 1,2,3 > <scratch>/picks.txt`
   and take the first rows with `OK | ... OK`; `--find lvl-1_2024_2` lists the pseudonym/level pairs that still open on
   the current opening problem, if the team wants to keep the opening slide.
3. For every new id: `python3 dev/demo_pick.py --show <id>` (team eyes only: never paste the output in a file) and check
   the Catalan text, the five options as the OCR read them, the picture, and the neighbour's similarity in
   `[0.75, 0.95)` so that neither the duplicate skip nor a future rung-1 gate changes the hint. Read the correct letters
   from the same output; they go into the rehearsal command, not into any document (data-licence P2).
4. Update `docs/demo/demo-problems.md` (the table and the six per-problem blocks: ids, neighbour id and similarity,
   rungs, clicks; no labels or option values), `docs/demo/runbook.md` step 6 (the two ids and two neighbours),
   `docs/demo/pitch.md:18` if the chain name changes, and `docs/demo/contingency.md:26` (the video must be re-recorded
   if the chain changed).
5. Rehearse in sim as `demo-problems.md` "Rehearsal in sim" did: `python3 dev/demo_rehearse.py --base
   http://127.0.0.1:<SIM_WEB_PORT> <name> <level> <letter1> <letter2> --hints 2 --hints2 2`; the printed ids and
   neighbours must equal step 2; mastery moves tick 0 -> 2 and cross 0 -> 1 as before.
6. Deploy (`docs/deploy-board.md`), then runbook step 6 against the board over `adb forward`; the ids must match; the
   script ends with `Reinicia` so the pseudonyms are clean.
7. Record the re-pick in `demo-problems.md` ("Checked with the real data on <date>, commit <sha>").

## 3. The measurement harness and the before/after table

Harness = trainer P8 + P2's counters + P8(b)'s wrapper, all stdlib, in `copilot/simulate.py`:

- `--start-level N` (calls `start_student` first; `base_level` column), `--students` as today, `--steps 60`.
- Default neighbours for `--bank data` = the real `retrieval.neighbors` wrapped: per call it records the wanted level,
  the hits' levels and similarities, and after `next_problem` whether the served id was a hit (its similarity), a bank
  fallback, from a relaxed level, or a `topic_note: "any"`. `duplicates_skipped` comes from `retrieval` (a counter
  incremented in `Catalog.search` when `skip_above` drops a pair) and `embeddings` from the query cache.
- The guessers test and a `test_simulator_counters_are_zero_on_the_synthetic_bank` (no duplicates, no fallbacks).

Table to publish in `docs/results-A.md` ("Trainer and retrieval on simulated students", command
`STUDENTS_DB=<scratch>/x.db python3 -m copilot.simulate --bank data --neighbors retrieval --steps 60` and the
`--start-level 0` / `--start-level 6` probes). "Before" is `7a67b77`, measured here; "after" is the target the
proposals must meet, to be filled from the same command:

| metric | before (7a67b77, 14 Nov 2026) | after (target) | from |
| --- | --- | --- | --- |
| accuracy threshold2 / threshold5 | 47 % / 53 % | >= 58 % / >= 65 % | P4 |
| settled band threshold2 / threshold5 | 2-3 / 5-6 (converged in 3 steps) | unchanged | P4 |
| max mastery threshold2 / threshold5 | 3 / 4 | >= 4 / >= 4 | P4 |
| max mastery random20-1/2/3 (guessers) | 2 / 2 / **4** | <= 2 each (test: <= 3) | P4 |
| rises to >= 3, threshold2 | 7 | >= 7 | P4 |
| repeats in 60 steps | 0 (x8) | 0; on a 12-problem bank, steps 13-20 = 8 distinct ids | P6 |
| near-duplicates served (similarity >= 0.95 of the last problem) | 7 of 345 (2.0 %; 3 above 0.97, max 0.9971) | 0 | P1 |
| weak neighbours served (< 0.75) | 63 of 345 (18 %); wrong branch 51/162 | reported, not gated (about the same) | P2 |
| served similarity, mean | 0.798 (right branch 0.814, wrong 0.780) | reported | P2 |
| bank fallbacks (eight hits all seen) | 10 of 355 | reported; `topic_note: "any"` count alongside | P4 |
| level relaxations in adaptive calls | 0 of 355 | 0 | P4 |
| level-0 student, all wrong, max level in the first 8 problems (`--start-level 0`) | 4 (levels 0, 2, 4, then 3, 2, 1, 0) | <= 1 | P3 |
| `diagnostic_levels(6)` | (6, 7, 7, 7, 7) | (6, 7, 5) | P3 |
| reviews on the weakest worked topic / median gap mastery 1 | 57-65 % / 11 answers | >= 80 % / <= 4 | P5 |
| base level of `improving` after 60 steps | 0 (frozen at the diagnostic) | rises with the threshold (median of the last 10) | P6 |
| embeddings in 480 steps | 8 (validation ids) | 0 with retrieval P5, else 8 | P7 |
| laptop ms per step / board estimate | 2-4 ms / 0.09-0.11 s | unchanged | - |

## 4. INTERFACES.md changes, implementation order, what is safe before the demo

INTERFACES.md, one list:

1. `retrieval.neighbors(problem_id, level_delta=0, same_topic=True, lang="cat", k=1, skip_duplicates=True)`; text:
   "every hit carries `similarity` (cosine, 4 decimals) and `topic`; with `skip_duplicates` no hit scores >=
   `NEAR_DUPLICATE` (0.95) against the query; ties resolve by id after rounding; returns `[]`, never raises, when the
   index or the embedding server is unavailable; only `sample-*` ids fall back to the sample problems". Add
   `NEAR_DUPLICATE` and `SAME_IDEA_SIMILARITY` (0.75, rung 1 only) as named constants.
2. `topics.get_topic`: "hand labels in `data_curated/topics_manual.json` override the computed table".
3. Mastery table: 1 "started, no right answer yet", 2 "right once (hints allowed)", 4 "three of the last four right
   without hints", 5 "...at a level above the student's current level"; one sentence on the failed-review rule or its
   removal (trainer P2).
4. `start_student` paragraph: with a level, the diagnostic is exactly three problems at `(L, L+1, L-1)` clamped, exact
   level first; base level = highest passed else `L-1`, then the median of the last ten main-path levels.
5. `next_problem`: the Problem dict may carry `topic_note: "any"`; the web shows it. The chain rule in one sentence
   ("two right answers in a row: one level up, any topic; one wrong: same topic, one level down; neighbours are ranked
   by similarity, filtered by level and near-duplicate, never gated").
6. Review paragraph: the due rule in answers and "at most one review in a row".
7. `teacher_report`: `level_now` per student; `trainer.stats` keys listed for the simulator.

Order, effort, and the demo line:

| step | what | effort | before the demo? |
| --- | --- | --- | --- |
| 1 | P6a exhausted-bank query + extended test | S | yes |
| 2 | P1 `NEAR_DUPLICATE = 0.95`, `skip_duplicates`, `demo_pick` import, tests | S | yes (demo lists checked: unchanged) |
| 3 | P7 hand labels override (50 labels), `_fallback` only for samples, `query_vector` guard, rounded ties, startup line | M (S each) | yes (re-pick with labels verified unchanged) |
| 4 | P2 + P8 harness: counters, wrapped simulator, `--start-level`, before table into `results-A.md`, guessers test as `expectedFailure` | M | yes |
| 5 | trainer P2 mastery sentence (I7, review penalty) | S | yes (tick 0 -> 2 and cross 0 -> 1 unchanged) |
| 6 | P3 diagnostic + `diagnostic_plan` shared with `demo_pick` + **re-pick (section 2)** | M + 1 h | **no** |
| 7 | P4 staircase + mastery 4 + `topic_note`; update the narration sentence in `results-A.md`, README, pitch | M | no (narration) |
| 8 | P6b base level follows; P5 review due in answers | M + M | no (with 6) |
| 9 | retrieval P5 precomputed validation vectors (new `index.db` on the board) | M | no (needs a push) |
| 10 | the 394 low-level hand labels, then the `RELATED` map if still wanted | L (people) + M | no (changes every cell) |

## 5. Tests to add

- `tests/test_retrieval.py`: `test_skip_duplicates_drops_hits_at_or_above_0_95` (unit, two hand-made vectors in a
  `Catalog`-like object, one equal to the query); `IndexSearchTest.test_duplicate_vector_pair_never_returned`
  (`lvl-5_2024_1` / `lvl-1_2024_1`, `level_delta=-4`, `same_topic=False`, k=3); `test_every_hit_has_similarity_and_topic`;
  `test_real_id_without_index_returns_nothing` (`INDEX_DB=/nonexistent`); `test_embed_server_down_returns_empty_not_error`
  (fake `embed` raising `OSError`); `test_near_ties_resolve_by_id_after_rounding` (scores differing by 1e-6).
- `tests/test_topics.py`: `test_manual_labels_override_the_table` (temp manual file with one id).
- `tests/test_trainer.py`: `test_repeats_only_when_the_bank_is_exhausted` extended (`ids[12:20]` 8 distinct, order of
  first answering); `test_adaptive_step_never_serves_a_near_duplicate_of_the_last_problem` (fake neighbour function
  returning a 0.99 hit first: the trainer must not serve it once `skip_duplicates` is inherited, i.e. the fake honours
  the flag); `test_two_correct_in_a_row_go_up_one_correct_stays_level` (replaces
  `test_correct_goes_one_level_up...`); `test_three_of_last_four_clean_is_four`; `test_guessers_never_reach_mastery_four`
  (synthetic bank, three seeds, 60 steps, `max_mastery <= 3`); `test_diagnostic_with_level_is_exactly_three_at_L_Lplus1_Lminus1`
  (`diagnostic_levels(6) == (6, 7, 5)`); `test_level0_failing_student_never_sees_level_above_1_in_8_problems`;
  `test_empty_topic_cell_yields_another_topic_at_the_same_level` (angles at level 0 on the synthetic bank with that
  cell removed); `test_topic_note_any_when_the_topic_is_left`; `test_review_is_due_by_interval_and_never_twice_in_a_row`;
  `test_rung_four_first_answer_keeps_zero`; `test_base_level_follows_the_median_of_the_last_ten`;
  `test_demo_pick_mirrors_the_trainer` (in `tests/`, data-gated: `first_problems(name, L)` equals the ids served by a
  fresh `start_student(name, L)` for one pseudonym).
- `tests/test_simulate.py` (new, synthetic bank): `test_counters_are_zero_on_the_synthetic_bank`,
  `test_start_level_option_calls_start_student`.
- `tests/test_interfaces.py`: the `neighbors` signature with `skip_duplicates` (tests-quality P6).

## Table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | One near-duplicate constant 0.95 shared by retrieval, hints, trainer and `demo_pick` | medium | S | yes (demo lists unchanged) |
| P2 | Trainer skips duplicates, keeps weak neighbours, records the similarity served | medium | S | yes |
| P3 | Diagnostic at the exact chosen level `(L, L+1, L-1)` + the demo re-pick it forces | high | M + 1 h | no |
| P4 | Adaptive step: two rights up, one wrong down, level kept, "any topic" said | high | M | no (narration) |
| P5 | Review due in answers, bank-picked, one in a row | medium | M | unreachable in the demo; do after |
| P6 | Exhausted bank repeats the least recent; base level follows the student | medium | S + M | exhaustion yes; base level no |
| P7 | Retrieval guarantees: hand labels first (50), no fake fallback, never raise, stable ties | medium-high | M | yes for the 50 labels; the 394 after |
| P8 | Harness: `--start-level`, wrapped neighbours with counters, guessers test, table in `results-A.md` | medium | M | yes |

## Discarded

- **Gating the trainer's neighbour at 0.75** (an extension of retrieval P1 to the trainer): 31 % of wrong-branch steps
  would fall to an unranked bank pick from the same cell, whose expected similarity is below the ranked top; the trainer
  never calls its problem "similar", so no promise is broken by a weak one. Reported, not gated (P2).
- **Skipping near-duplicates of every seen problem, not only of the query** (a history-wide `_seen_ids` extension):
  it needs a similarity between the candidate and up to 60 history ids per call (60 x 384 products per candidate, about
  0.5 s per step of pure Python on the board) for a case the simulation never showed (every duplicate served was a
  duplicate of the problem just answered). Query-relative skipping covers the embarrassing case.
- **`NEAR_DUPLICATE = 0.90`**: [0.90, 0.95) holds 20 ids, 5 of which are other-year problems, i.e. genuine easier
  siblings (the opening demo neighbour scores 0.9353 and is the clearest "easier sibling" in the bank); 0.90 would
  remove it.
- **A `RELATED` topic map now** (retrieval P6): with a 76 % topic map the "near" topic is as likely wrong as the own
  one; the word to the student (`topic_note`) is kept, the map waits for the hand labels.
- **Any LLM involvement in choosing the next problem** and **wall-clock spaced repetition**: discarded for the reasons
  given in the trainer report (design principle; 10-30 minute sessions).
