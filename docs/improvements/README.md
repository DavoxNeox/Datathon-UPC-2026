# Improvements: the consolidated list

**Status: PROVISIONAL. Round 1 (eight area explorers) is complete; round 2 (three cross-cutting
integrators: wrong-answer flow and rung 3, demo robustness and the 60 s budget, trainer and retrieval
policy) is in progress and will update this file in a separate commit.**

Written 14 Nov 2026 against `origin/main` **d8f9c66** (284 tests, 1 skipped on macOS). The eight area
reports were written at `5cc2ded`; main moved 50 commits since, so every proposal below carries a status
checked against the current files:

- **open**: nothing on main does it;
- **done** (commit): main does it; do not redo;
- **partly** (commit): a piece landed, the rest is open;
- **superseded**: main decided otherwise or the premise is gone.

Nothing here was implemented by the explorers: they read, ran, measured and wrote. Each report says
what it verified by running and what it only read.

| area | report | proposals |
| --- | --- | --- |
| hint ladder and pedagogy | [hints-pedagogy.md](hints-pedagogy.md) | 11 |
| adaptive trainer and mastery | [trainer.md](trainer.md) | 9 |
| retrieval, topics, embeddings | [retrieval-topics.md](retrieval-topics.md) | 8 |
| web app and App Lab app | [web-app.md](web-app.md) | 11 |
| board and deployment | [board-deploy.md](board-deploy.md) | 11 |
| Reason track and evaluation | [reason-eval.md](reason-eval.md) | 8 |
| tests and code quality | [tests-quality.md](tests-quality.md) | 11 |
| data, licence, reproducibility | [data-licence.md](data-licence.md) | 10 |

The explorers also read the independent review of main (`docs/reviews/review-main-2026-11-14.md` on
`origin/team/review-22fa88`) and build on it. One correction to it: its C1 counts eight tool trailers on
`origin/main`; those eight commits are the organizers' (`upstream/main`, author `mpous`), not the team's.
The team's own trailers are on three stale public branches (`origin/data`, `origin/hints-app`,
`origin/trainer`) and in `data_curated/hint_quality.json:40` (data-licence P1).

## Top 15, by impact over effort

"Merges" names the area proposals folded into the item. "Safe before the demo" is the explorers' current
judgement; round 2 refines it. Effort: S under 1 h, M 1-2 h, L more.

| # | item | merges | impact | effort | depends on | safe before demo | status on main |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **A wrong answer does not reveal the letter: one more try, hints still open; `/api/solution` only after an attempt or rung 3, with a confirmation** (reviewer C2, C3) | web P4, web P5, hints P3 | high | M | 2 for the signature text | yes with the two tests and one rehearsal of the wrong-then-hint path; the demo script answers wrong on purpose on problem 2, so re-time that scene | **open**: `webapp.py:302` still says "La resposta correcta era la X" on the first miss; `solution()` (`:371`) has no gate; the signature (merged in `c1238ec`) is shown only after the reveal |
| 2 | **Leak filter v2**: compound number words in three languages, dozen/half/pair/double, expressions, Roman numerals, ordinals, option positions, glued units (`12cm`), the lower-case letter; language-aware words so `set`, `nou`, `deu`, `un/una`, `once` stop blocking harmless hints; one test corpus (110 adversarial, 40 harmless, every real option value of val and train) | hints P6, hints P7, tests P8 | high | M | none; prerequisite of every new text source (1, 3, demo steps, lessons) | yes | **open**: `copilot/leak_filter.py` unchanged since the reports; 75/110 adversarial strings pass, 35/339 real correct values with a glued unit pass |
| 3 | **Rung 3 without the LLM on every problem**: option-derived sanity questions (units, magnitude, common factor, step, parity as a question), the error signature after a wrong attempt, the solver trace on the English twin on the Catalan page | hints P4, hints P3, hints P1 | high | M | 1, 2 | yes for P4 and P1 (deterministic, 0 s); P3 only with 1 | **partly**: demo-set steps are read first at rung 3 and 4 (`1b85037`) and the fourth press is a lesson (`6af15f0`), so the demo ids are covered; on the other 275 val ids rung 3 is still a second card; the Catalan solver path still classifies 0/281 |
| 4 | **The student survives "Comença"**: `start()` resets a pseudonym only when it is unknown or the level selector changed; a blank name is an error, not `demo`; `/api/reset` stays the only reset | web P6 | high | S | the demo chains rely on the reset (see round 2: reset via the runbook's `/api/reset` or when the level is chosen) | yes, only together with the runbook step that forgets the rehearsal aliases (`78e4eb1` already adds it) | **open**: `webapp.py:225` `or "demo"`, `:231-234` unconditional `start_student` |
| 5 | **The page never freezes and never crashes**: a 20 s budget for the hint thread (prefetch join and own call) with the reason in the fallback card, answer buttons enabled while busy; `app.js` handles `{"error"}`, a 4 s fetch timeout, back-off and a "la placa no respon" banner | web P1, web P2, hints P8 (close the LLM gate on n >= 10, one call) | high | M | none | yes | **open**: `hints.quality()` still accepts `n` >= 1 (`:274`), `_llm_langs` still makes two calls; `app.js` was redesigned (`43ff1e3`) but `render()` still assumes a state object: re-verify on the new file |
| 6 | **`predict.py` cannot die and holds 60 s by construction**: catch-all per problem, tolerant `id`/`text`/`options`, `SOLVERS=1` in `config.env` so `SOLVERS=0` works (reviewer I9), the remaining budget threaded into the solver extraction, skip a call that cannot fit, accumulate `prompt_tokens` | reason P1, reason P2, board P7 | high | S-M | none | yes (the app does not call `predict.py`) | **open**: `pipeline.py:137-143` catches only timeouts and `URLError`; `predict.py:45` `problem["id"]`; `SOLVERS` absent from `config.env` (`pipeline.py:21` reads it); the solver path still gets `timeout=60` |
| 7 | **Evidence and labels in the public tree**: `docs/runs/` with the ids-only eval CSVs and `ablations.csv` (reviewer I11), `.gitignore` for `*.jsonl`/images/parquet everywhere, the 13-row id -> answer table out of `docs/content-review.md`, a test that no doc pairs an id with a letter, delete the three stale branches with tool trailers, fix `hint_quality.json:40` | reason P5, data P7, data P2 (+addendum), data P1 | high | S | none | yes | **partly**: option values and labels left `docs/demo/` (`8db6754`); `docs/content-review.md` still holds 19 rows with a letter column; no `docs/runs/`; `.gitignore` still only `data/*` and `results/*`; `hint_quality.json:40` unchanged; branches still on origin |
| 8 | **One mastery sentence and no endless repeat**: `derive_mastery` is the single source (no 0 -> 1 after rung 4, no one-answer review penalty, INTERFACES/legend aligned: reviewer I7, M7); `_least_recent` picks the problem whose latest answer is oldest (today the first answer, forever) | trainer P2, trainer P5 | high | S | none | yes (the demo flow is unchanged) | **open**: `trainer.py:548-550`, `:451` |
| 9 | **The suite is harmless and runs everywhere**: `tests/__init__.py` redirects `STUDENTS_DB` to a temp dir (today a run writes `Mar`, `Pau`, `student-test`, `test-webapp` into the demo database), mock the one network test, `board/07_run_tests.sh`, a GitHub Actions matrix on 3.13 and 3.14 with no data (exact yaml in the report), honest test counts in the docs (284 today, "125" in two docs) | tests P1, P2, P3, P4; reason P8 | medium | S | none | yes | **open**: `tests/__init__.py` empty; no `.github/`; "125 tests" still in `docs/results-A.md:74` and the README draft |
| 10 | **Demo-day health check and units that survive memory pressure**: `board/07_demo_check.sh` (units, `/health` on loopback and `docker0`, data counts, `students.db` ownership, one timed real completion against the 60 s budget, app page without `label`, RAM, Wi-Fi state); `OOMScoreAdjust`/`Nice`/`Restart=always` in the three units; relay accept-loop guard, keepalive, a clear message when `docker0` is missing, `target_port` so the relay test runs on macOS | board P9, board P4, board P2, board P3 | high | M | none | yes on the rehearsal day, not the morning of | **open**: `board/` unchanged since the reports |
| 11 | **Honest neighbours**: skip near-duplicates (>= 0.97: the same problem one level down, 32/1466 train ids), gate rung 1 on similarity 0.75 with a fallback chain and honest wording (expected precision 44% -> 63%), no invented `sample-4` when the index is missing, hand labels override `topics.json` (the 50 that exist are not read today) | retrieval P2, P1, P4, P3 (code part) | high | S+M | check the six demo ids' similarities first (`dev/demo_pick.py` already filters < 0.95) | duplicates/fallback/hand labels yes; the 0.75 gate only after checking the demo ids | **open**: `retrieval.py` has no `skip_duplicates`, no gate, `_fallback` for any id; `topics._load` never opens `topics_manual.json` |
| 12 | **Teacher report a teacher can use**: seconds per problem (stored at `record_answer`), hints per right answer, per-topic trend, last failed problems (ids), the diagnostic's outcome, `by_topic` rendered on the teacher page, plus `difficulty.report()` (merged in `014bf37`) | trainer P6, difficulty branch | high | M | none | yes (additive keys, same migration pattern as `start_level`) | **open** (the `difficulty` module is on main but not on the page) |
| 13 | **Problem selection that respects the chosen course**: diagnostic L, L+1, L-1 when a level is chosen, exact level before topic rotation, chain restarts at the student's level (reviewer I6); 2-up-1-down staircase with mastery 4 = 3 of the last 4 right without hints (measured: accuracy 47% -> 60%, guessers capped at 2); review spaced in answers (3/5/8/13/21) | trainer P3, P1, P4 | high | M-L | 11 (duplicates) | **no**: every change here re-picks the deterministic demo chains (`docs/demo/demo-problems.md`); do it after the demo or re-run `dev/demo_pick.py` and the rehearsal | **open**: `DIAGNOSTIC_LEVELS = (0, 2, 4, 6, 7)`, `REVIEW_RATE = 0.2` coin |
| 14 | **Measured, reproducible, pinned**: `laptop/measure_ladder.py` and the ladder table (rung-3 sources on val before/after), the retrieval and topic figures in `results-A.md`, the M3Kang revision `e772e61` pinned in `prepare_m3kang.py` with a committed text-free manifest, `requirements.txt` pinned with Python 3.11-3.12 stated, `calibrate_speed.py --write` writing the per-request embed figure (today per text: 0.05 instead of 0.12), the stale header of `results-A.md`, the simulator table published | hints P11, retrieval P7, data P5, data P6a, data P10, board P1, reason P8, trainer P8 | medium | S each | none | yes | **open** (results-A gained the middle-value board run in `d8f9c66`, nothing else) |
| 15 | **The public README's data and licence section**: where M3Kang comes from (not gated, revision, 393 MB shard, 38 min OCR, 36 s index), Python versions, "not in this repository", MIT for the code, the stale `[[TODO add LICENSE]]`, the organizers' guide kept as credited setup doc, the root README swapped once the TODOs close | data P9, data P4 | high | M | 7, 14 | yes; the root swap after the demo | **open** |

### Not in the top 15 but worth doing after the demo

- Rung 1 as a faded worked example (hints P5, L): the student answers the neighbour first, then sees its
  answer and the card. The strongest pedagogical change; touches the page, the server and INTERFACES.
- LED "thinking" chaser and rung marker, `Bridge.call` guarded (web P7); polling with a version number
  and the neighbour image by id (web P10, reviewer M6); state-changing endpoints as POST (web P3, needs one
  test of the brick on the board); readable sizes and child words on the page (web P9); the endpoint table
  (web P11).
- Strategy cards: two risky facts (`angles/4`, `spatial/2`), eight missing Kangaroo moves, the topic in the
  card header (hints P9); the rung-1 board clock and school-year wording (hints P10).
- Base level that follows the student (trainer P7), related-topic second pass for thin cells (retrieval P6),
  validation vectors precomputed into the index (retrieval P5), platform-stable ties (retrieval P8), SQLite
  hardening (trainer P9).
- Board: thread oversubscription measured before choosing `EMBED_THREADS` (P5), `id -un` in the scripts (P6),
  host fallback to the default gateway plus a startup health log (P8), the fresh-board gaps in
  `deploy-board.md` (P10), idempotence edges (P11).
- Tests: stdlib guard gaps (3.14-only names and syntax, dynamic imports: P5), INTERFACES signatures checked
  (P6), pipeline and 60 s tests (P7), web error paths and `hal/web.py` (P9), `predict.py` determinism (P10),
  the `sample-1` fixture out of board code (P11, reason P4).
- Data: the near-verbatim statement in `tests/test_solvers.py:89` and the repo-wide text-leak test (P3),
  commit e-mail (P8), `rapidocr>=3` migration (P6b, after the demo: it changes OCR output).
- Reason: precise determinism statement and test (P6), "copied, not invented" check in the solvers (P7).

## Done on main since the reports were written (do not redo)

| area proposal | what landed | commit |
| --- | --- | --- |
| reason P3 (middle-value rule) | `MIDDLE_VALUE=1` default, measured on the board: 150/562 = 26.7% | `199f6ab`, `d8f9c66` |
| reason "Discarded: merge votes.py" | superseded: `votes.py` merged behind `VOTE_SHIFTS=0`, `VALUE_MODEL=0` | `7d8a8d9`, `a94194d` |
| hints P2 (demo steps at rung 3 and 4) | `hints._demo_steps`, rung 3 walks them (never the last), rung 4 shows all; six script problems in `demo_set.json` | `1b85037`, `8343a2a` |
| hints P2 (step count, reviewer M4) | partly: the count follows the demo steps; the trace path is unchanged | `1b85037` |
| web (hint cap) | the fourth press is a short lesson (`hints.get_lesson`), `HINT_MAX_USES=4` | `6af15f0`, `c6b27ee`, `f15e8f1` |
| hints P3 premise | `signatures.py` merged; shown only after the answer, never as a hint, with a confidence flag | `c1238ec`, `9513842`, `6257246` |
| data P2 addendum (`docs/demo`) | option values, labels and descriptions moved to the ignored `docs/demo/local/` | `8db6754` |
| web P6 (demo side) | runbook forgets the rehearsal aliases and warms the index with a first Pista | `78e4eb1` |
| hints P9 (wording, reviewer M8) | Catalan fixes and the 15-word cap on the cards; `tests/test_content.py` | `179b96e`, `daf1997` |
| web P9 (part) | one-column page, 3:1 control borders, progress under the letters, dark mode | `43ff1e3`, `adb83af` |
| trainer "Discarded: DIFFICULTY_ADJUST" | merged as decided: flag off, `report()` recommended, read once per step | `014bf37`, `e481120`, `1d51483` |
| retrieval P1 constant | `lineage.py` merged with `min_similarity` 0.75 as exploration, not a hint | `95c41c7`, `fcd28ab` |

## Discarded: they contradict a project rule

- LLM-written worked solutions, LLM translation of hints into Catalan, LLM in the trainer or in mastery:
  the LLM never reasons; one hint is 28 s of board time; its Catalan is the failure mode.
- Elimination hints that state a property of the answer ("it is even", "not A or E"), and the middle-value
  rule as a hint: they leak bits of the label before the student answers.
- Qwen3.5 2B on the board: 5 of 281 prompts over 60 s, about 1.6 GB RAM, no gain.
- numpy or `math.sumprod` for the dot products: numpy is not stdlib; `sumprod` was slower; the pure-Python
  cost is 4.6 ms per rung-1 pool.
- `MemoryMax` on the LLM unit: a flat RSS plus a cgroup limit turns a spike into a certain kill.
- Wall-clock spaced repetition: sessions last 10-30 minutes; counting answers keeps the idea.
- Storing age or class to set the start level: minors, no personal data.
- Rewriting `origin/main` history for the eight trailers: they are the organizers' commits.
- Committing `val.jsonl` "ids only", the OCR cache, or problem images for the Project Hub: research-only
  licence.
- A `--board` test flag, pytest or coverage on the board: the suite already self-gates on data; the board
  has no pip.

## Dependencies in one picture

```
2 leak filter v2 ──> 1 wrong answer / solution gate ──> 3 rung-3 sources
                 └─> (demo steps, lessons, signature texts all pass through it)
11 duplicates + hand labels ──> 13 trainer policy (after the demo; re-pick the chains)
7 evidence + 14 measurements ──> 15 README
4 start() ──┐
5 budget   ─┼─> 10 demo check script (round 2 writes the day plan)
6 predict  ─┘
```

Round 2 will replace the "safe before demo" column with a verified day plan (night before, morning of,
never on demo day) and the exact re-pick procedure for the trainer changes.
