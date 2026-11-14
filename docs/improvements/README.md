# Improvements: the consolidated list

Written 14 Nov 2026 against `origin/main` **d8f9c66** (284 tests, 1 skipped on macOS). Two rounds of exploration,
nothing implemented: eight area explorers read, ran and measured, then three integrators resolved the cross-cutting
themes and checked every claim again on the current main.

| round | report | what it holds |
| --- | --- | --- |
| 1 | [hints-pedagogy.md](hints-pedagogy.md) | the ladder on all 281 validation problems, the leak filter corpus, the cards (11 proposals) |
| 1 | [trainer.md](trainer.md) | mastery rules, cold start, review, the simulator on the real bank (9) |
| 1 | [retrieval-topics.md](retrieval-topics.md) | neighbour quality, the 24% topic disagreement, cost on the board (8) |
| 1 | [web-app.md](web-app.md) | robustness in the demo, silent errors, threads, polling, LED, usability (11) |
| 1 | [board-deploy.md](board-deploy.md) | boot, relay, units, calibration, a fresh board (11) |
| 1 | [reason-eval.md](reason-eval.md) | the jury contract, determinism, 60 s, the middle-value rule recounted (8) |
| 1 | [tests-quality.md](tests-quality.md) | what is untested, fragile tests, the board and CI (11) |
| 1 | [data-licence.md](data-licence.md) | leak risk over the whole history, reproducibility, pins, the public README (10) |
| 2 | [cross-rung3-wrong-answer.md](cross-rung3-wrong-answer.md) | what the student sees after a miss and what rung 3 holds, end to end; the leak filter as the prerequisite |
| 2 | [cross-demo-robustness.md](cross-demo-robustness.md) | one `Deadline` for the 60 s rule, the degradation table, demo day as code, night-before / morning-of / never |
| 2 | [cross-trainer-retrieval.md](cross-trainer-retrieval.md) | one problem-selection policy, the near-duplicate constant, the demo re-pick procedure, the measurement harness |

The area reports were written at `5cc2ded`; main moved 50 commits since, so every item carries a status checked against
the current files: **open** (nothing on main does it), **partly** (a piece landed), **done** (do not redo),
**superseded** (main decided otherwise). The explorers also read the independent review of main
(`docs/reviews/review-main-2026-11-14.md` on `origin/team/review-22fa88`) and build on it. One correction to it: its C1
counts eight tool trailers on `origin/main`; those commits are the organizers' (`upstream/main`, author `mpous`). The
team's own trailers are on three stale public branches (`origin/data`, `origin/hints-app`, `origin/trainer`) and in
`data_curated/hint_quality.json:40`.

## Top 15, by impact over effort

"Merges" names the proposals folded into the item (area report: P-number; cross report: X-number). Effort: S under
1 h, M 1-2 h, L more. "Before the demo" is round 2's verified verdict: **yes** (the stage flow is unchanged, suite
green), **rehearsal slot** (changes something the pitch shows or depends on: only with a full re-run of both chains, never
the morning of), **after** (changes the rehearsed chains or needs a push to the board).

| # | item | merges | impact | effort | depends on | before the demo | status on main |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Leak filter v2**: a space between a glued digit and its unit (`12cm`), digit-carrying units stripped from the option before reading values (`cm2` is not a 2), number words 0-999 in three languages, dozen/half/pair/double, expressions, Roman numerals, ordinals, option positions, the lower-case letter; `lang` so `set`, `nou`, `deu`, `un/una`, `once` stop blocking harmless hints; one corpus (110 adversarial, 40 harmless, every real option value of val and train, every demo step and lesson with raw options) | hints P6, P7; tests P8; rung3 X1 | high | M (75 min) | none; prerequisite of 2, 3, 4 | **yes** | **open**: `leak_filter.py` unchanged; 75/110 adversarial pass, 12/40 harmless fail, 35/339 real glued values pass, and with raw options the filter would wrongly drop 2 demo steps and 4 fields of `lvl-1_2024_8` |
| 2 | **Rung 3 filtered and honest**: the demo steps pass `leak_reason` at runtime with `lang` and "Pas i de n" counts the survivors (reviewer M4); the solver trace runs on the English row so it can fire on the Catalan page; rung 4 puts the figure description first; `demo_steps`, `lesson`, `fallback_reason` enter INTERFACES | hints P1, P2 (remainder); rung3 X2 | medium | S (30 min) | 1 | **yes** (all six demo ids' steps pass today, so the stage text is identical) | **partly**: demo steps read at rung 3/4 (`1b85037`) and the lesson on the fourth press (`6af15f0`) are done; the steps are not filtered at runtime; `solvers.classify` is 0/281 on Catalan text |
| 3 | **A wrong answer does not reveal the letter**: two attempts, label private until the problem is closed, hints still open after a miss (a miss neither resets nor consumes a press), exactly one `record_answer` (attempt 1), attempt 2 in the timeline and an `AttemptStats` counter file, rung 4 pushed automatically after the second miss, `/api/solution` only after an attempt or rung 3 with a confirmation (reviewer C2, C3) | web P4, P5; rung3 X3 | high | M (60 min) | 1 | **rehearsal slot**: the pitch at second 60 and `contingency.md:40` assume the letter appears; `demo-problems.md` steps 2 and 4 and `dev/demo_rehearse.py` take a second letter | **open**: `webapp.py:302` names the letter on the first miss, `hint()` answers `already answered`, `solution()` has no gate |
| 4 | **The one diagnosis that may precede the reveal**: `hints.note_attempt` and, after a miss, the `statement_number` signature ("your answer is a number written in the statement") at rung 3; every relation signature stays after the close, because with its direction it pins the correct option in 95/95 validation pairs (51/75 without) | hints P3 (narrowed); rung3 X4 | medium | S (30 min) | 3 | **yes** (fires on stage only if the presenter clicks the statement distractor of `lvl-4_2010_12`) | **partly**: `signatures.py` merged and shown after the reveal (`c1238ec`, `9513842`); nothing before it |
| 5 | **`board_clock.Deadline`**: one budget per student step (`HINT_BUDGET_SECONDS`) and per `predict.py` problem (`TIME_LIMIT_SECONDS` minus a margin), passed to `llm.post`, `extract_json`, `letter_scores`, `embed`, `hints.llm_hint`, `_prefetched`, consulted before every model call (`fits()`), a running prefetch never doubled, `finally: busy = False`, the reason in the fallback card; the LLM gate needs `n >= 10` and one call in the shown language | reason P2; web P1; hints P8; tests P7; reviewer M2, M3; demo X1 | high | M (2 h) | none | **yes** (suite green, the hang test, one rehearsal; the Catalan gate is closed so the demo never enters the LLM branch) | **open**: a hung server keeps the page busy 1x or 2x the limit (3.0 s and 6.1 s measured at a 3 s limit), the solver path gets `timeout=60`, `quality()` accepts `n` >= 1, `_llm_langs` makes two calls |
| 6 | **`predict.py` never dies, `SOLVERS=0` works**: a catch-all per problem, tolerant `id`/`text`/`options`, a last-resort row `D, 0.0, error`, `SOLVERS=1` in `config.env` (reviewer I9), `prompt_tokens` accumulated | reason P1; board P7; demo X2 | high | S | none | **yes** | **open**: a row without `id` kills the run (`KeyError`, header only); `pipeline.py:137-143` catches timeouts and `URLError` only; `SOLVERS` absent from `config.env` |
| 7 | **The page never crashes**: `api()` turns `{"error"}` into a status line, 4 s fetch timeout, self-rescheduling polls with back-off, a "la placa no respon" banner after three failed polls, the letters usable while a hint is pending, no exception text from `hal/web.py` | web P2, P8 (part); demo X3 | high | M | none | **yes** (one browser check) | **open**: `render()` throws on `{"error": "already answered"}`, a double click or a second tab triggers it; `/api/led/path/abc` returns the exception text |
| 8 | **The student survives "Comença", the bank never loops**: `start()` resets only when a course was chosen or the pseudonym is new ("auto" on a known pseudonym continues), a blank name is an error instead of `demo`; `_least_recent` picks the problem whose latest answer is oldest | web P6; trainer P5; demo X5; trainer-retrieval X6a | high | S | none | **yes** (every demo chain names a course, so "Comença" on stage still resets; `demo_rehearse.py` once) | **open**: `webapp.py:225` `or "demo"`, unconditional `start_student`; a blank start wiped `demo` (answers 1 -> 0); `trainer.py:451` `ORDER BY id LIMIT 1` |
| 9 | **Degrade, never invent**: `neighbors()` never raises (embed server down) and never returns `sample-4` for a real id (index missing), hand labels override `topics.json` (the 50 that exist are not read), ties rounded before sorting, `Bridge.call` guarded, a startup health thread logging `servers: llm ok / embed ok` and `servers` in `/api/state` | retrieval P3 (code), P4, P8; web P7 (guard); board P8; demo X4; trainer-retrieval X7 | medium-high | M | none | **yes** (the four chain problems and neighbours are training ids; the 50 labels leave the chains unchanged, verified by re-picking) | **open**: `INDEX_DB` missing shows `sample-4` as an easier neighbour; `EMBED_PORT=1` raises `URLError` out of `get_hint` on a validation id; `topics._load` never opens `topics_manual.json` |
| 10 | **One near-duplicate constant, 0.95**: `NEAR_DUPLICATE` in `retrieval.py`, `neighbors(..., skip_duplicates=True)`, inherited by rung 1 and the trainer, imported by `dev/demo_pick.py`; the trainer records the similarity it served and does **not** gate weak neighbours (31% of its wrong-branch steps are below 0.75; a gate would hand them to an unranked bank pick) | retrieval P2; trainer-retrieval X1, X2 | medium | S | none | **yes** (no hit >= 0.95 in any demo list; max 0.935) | **open**: 32/1466 training ids get the same problem one level down as their neighbour (all the same year, 12 the same label); 7 of 345 simulated adaptive steps served one |
| 11 | **Evidence and labels in the public tree**: `docs/runs/` with the ids-only eval CSVs and `ablations.csv` (reviewer I11), `.gitignore` for `*.jsonl`/images/parquet everywhere, the 19-row id -> answer table out of `docs/content-review.md` and the letter out of `contingency.md:40`, a test that no doc pairs an id with a letter, the three stale branches with tool trailers deleted, `hint_quality.json:40` reworded | reason P5; data P1, P2 (+addendum), P7; rung3 X7 | high | S | none | **yes** | **partly**: `docs/demo/demo-problems.md` scrubbed (`8db6754`); `content-review.md` and `contingency.md` still state demo answers; no `docs/runs/`; `.gitignore` only `data/*` and `results/*`; branches and the judge string unchanged |
| 12 | **Demo day as code**: `board/07_demo_check.sh` (units, `/health` on loopback and `docker0`, data counts, index rows, `students.db` ownership, one timed real letter call against the 60 s rule, app page without `label`, RAM, disk, Wi-Fi), `tests/__init__.py` redirecting `STUDENTS_DB` (today a suite run writes four test pupils into the demo database), an honest `05_smoke_test.sh`, two asserts in `demo_rehearse.py` (no invented neighbour, no `fallback_reason`); units with `OOMScoreAdjust` 500/200/-200 and `Restart=always`, no `Nice`, no `MemoryMax` | board P9, P4; tests P1, P2; demo X6, X7 | high | M | 5 (for `fallback_reason`) | **yes**; the units on the rehearsal day only, then `calibrate_speed.py` within 5% | **open**: `board/` and `tests/__init__.py` unchanged |
| 13 | **One mastery sentence**: `derive_mastery` is the single source (no 0 -> 1 after rung 4, no one-answer review penalty that the next wrong answer undoes; reviewer I7, M7), INTERFACES and the teacher legend aligned ("1 ha començat") | trainer P2; trainer-retrieval order step 5 | high | S | none | **yes** (the demo's tick 0 -> 2 and cross 0 -> 1 are unchanged) | **open**: `trainer.py:548-550` |
| 14 | **Problem selection that respects the chosen course** (after the demo): diagnostic `(L, L+1, L-1)` with the exact level before topic rotation and the chain restarting at the base level (reviewer I6); two rights to go up, one wrong to go down, mastery 4 = 3 of the last 4 right without hints (measured: accuracy 47% -> 60%, guessers capped at 2); review due in answers (3/5/8/13/21); base level follows the median of the last ten; `trainer.diagnostic_plan` shared with `dev/demo_pick.py`; the harness (`--start-level`, wrapped neighbours with counters, guessers test, the before/after table in `results-A.md`) | trainer P1, P3, P4, P7, P8; retrieval P6 (the word, not the map); trainer-retrieval X3, X4, X5, X6b, X8 | high | M-L | 10 | **after**: problem 2 of every chain changes (re-picked: `lvl-2_2019_24`, `lvl-3_2017_15`, `lvl-4_2024_23`); the re-pick procedure takes about one hour and is written in the cross report; the harness and its "before" table can land now | **open**: `DIAGNOSTIC_LEVELS = (0, 2, 4, 6, 7)`, `REVIEW_RATE = 0.2` coin, base level frozen |
| 15 | **Measured, pinned, written down**: `laptop/measure_ladder.py` and the ladder table (rung-3 sources on val before/after), the retrieval and topic figures in `results-A.md`, the M3Kang revision `e772e61` pinned in `prepare_m3kang.py` with a committed text-free manifest, `requirements.txt` pinned with Python 3.11-3.12 stated, `calibrate_speed.py --write` writing the per-request embed figure (today per text: 0.05 for 0.12), the stale header of `results-A.md`, "125 tests" -> the real count, the simulator table published, and the public README's data and licence section (where M3Kang comes from, not gated, 38 min OCR, 36 s index, Python versions, MIT for the code, the stale `[[TODO add LICENSE]]`) | hints P11; retrieval P7; data P5, P6a, P9, P10; board P1; reason P8; trainer P8; rung3 X7 | medium-high | S each, M in all | 11 | **yes**; the root README swap after the demo | **open** (`results-A.md` gained the middle-value board run in `d8f9c66`, nothing else) |

### Worth doing after the demo, not in the top 15

- Option-derived sanity questions as a rung-3 source (units, magnitude, progression, factor, parity as a question):
  rung 3 stops being a second card on 119/281 Catalan validation problems with no model and no content hour (hints P4,
  rung3 X5).
- Rung-1 gate at 0.75 with a same-level fallback and honest wording: expected precision 44% -> 63%; five of six demo ids
  pass, the reserve `lvl-5_2022_30` (0.729) would switch neighbour (retrieval P1, rung3 X6). Behind
  `RUNG1_MIN_SIMILARITY=0` until then.
- Rung 1 as a faded worked example (hints P5, L), the strongest pedagogical change; it collides with the two-attempt
  letter buttons, so after the datathon.
- Validation vectors precomputed into `index.db` so no embedding call remains in the loop (retrieval P5, needs a push);
  the 394 hand labels of levels 0-2 (retrieval P3 people part; changes every cell); the `RELATED` topic map once the
  labels make the topics trustworthy (retrieval P6).
- Teacher report a teacher can use: seconds per problem, hints per right answer, per-topic trend, last failed ids, the
  diagnostic's outcome, `by_topic` on the page, plus `difficulty.report()` (merged in `014bf37`) (trainer P6).
- Web: state-changing endpoints as POST after one `adb forward` test of the brick (web P3); version-based polling and the
  neighbour image by id (web P10, reviewer M6); the LED "thinking" chaser and rung marker (web P7); readable sizes and
  child words (web P9); the endpoint table and the favicon (web P11).
- Strategy cards: two risky facts (`angles/4`, `spatial/2`), eight missing Kangaroo moves, the topic in the card header
  (hints P9); the rung-1 board clock and school-year wording (hints P10).
- Board: thread oversubscription measured before choosing `EMBED_THREADS` (P5), `id -un` in the scripts (P6), the
  fresh-board gaps in `deploy-board.md` (P10), idempotence edges and the `ExecStart` drift test (P11), relay hardening
  (P2, P3).
- Tests: stdlib guard gaps (3.14-only names and syntax, dynamic imports: P5), INTERFACES signatures checked (P6), web
  error paths and `hal/web.py` (P9), `predict.py` determinism (P10), the `sample-1` fixture out of board code (P11,
  reason P4), CI on GitHub Actions with the exact yaml (P4), `board/07_run_tests.sh` (P3).
- Data: the near-verbatim statement in `tests/test_solvers.py:89` and a repo-wide text-leak test (P3), the real example
  problem in `data/README.md` (P4), commit e-mail and `.mailmap` (P8), `rapidocr>=3` migration (P6b: changes OCR output).
- Reason: a precise determinism statement and test (P6), a "copied, not invented" check in the solvers (P7).
- SQLite hardening (trainer P9), platform-stable ties (retrieval P8, folded into 9 above).

## Demo day: when each item lands

From [cross-demo-robustness.md](cross-demo-robustness.md) §3 and [cross-trainer-retrieval.md](cross-trainer-retrieval.md) §2.

| when | do | never |
| --- | --- | --- |
| **Now, no stage effect** | 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15; the harness half of 14; the night-before items of 12 | |
| **Rehearsal slot** (full re-run of both chains, then `demo_rehearse.py`) | 3 (update `pitch.md` second 60, `contingency.md:40`, `demo-problems.md` steps 2 and 4); the three units of 12, then `calibrate_speed.py` within 5% of 11.4 / 5.6 | `calibrate_speed.py --write`; `config.env` edits other than `HINT_BUDGET_SECONDS` |
| **Morning of** | power on, `adb devices`, `./board/07_demo_check.sh`, `adb forward`, one `demo_rehearse.py Mariona1 1 C A`, `/api/reset`, type the pseudonym and course | tests, `git pull`, `app stop/start` unless the check fails, any `board/01-06` script |
| **After the demo** | 14 with the re-pick; option checks; the rung-1 gate; POST; polling; the 394 labels; a new `index.db`; the root README swap | |

## Done on main since the reports were written (do not redo)

| area proposal | what landed | commit |
| --- | --- | --- |
| reason P3 (middle-value rule) | `MIDDLE_VALUE=1` default, measured on the board: 150/562 = 26.7% | `199f6ab`, `d8f9c66` |
| reason "Discarded: merge votes.py" | superseded: `votes.py` merged behind `VOTE_SHIFTS=0`, `VALUE_MODEL=0` | `7d8a8d9`, `a94194d` |
| hints P2 (demo steps at rung 3 and 4) | `hints._demo_steps`, rung 3 walks them (never the last), rung 4 shows all; the six script problems in `demo_set.json` (19 entries, all draft) | `1b85037`, `8343a2a` |
| web (hint cap) | the fourth press is a short lesson (`hints.get_lesson`), `HINT_MAX_USES=4` | `6af15f0`, `c6b27ee`, `f15e8f1` |
| hints P3 premise | `signatures.py` merged; shown only after the answer, with a confidence flag and its own pin measurement (1176/1381) | `c1238ec`, `9513842`, `6257246` |
| data P2 addendum (`docs/demo`) | option values, labels and descriptions moved to the ignored `docs/demo/local/` | `8db6754` |
| web P6 (demo side) | the runbook forgets the rehearsal aliases and warms the index with a first Pista | `78e4eb1` |
| hints P9 (wording, reviewer M8) | Catalan fixes and the 15-word cap on the cards; `tests/test_content.py` | `179b96e`, `daf1997` |
| web P9 (part) | one-column page, 3:1 control borders, progress under the letters, dark mode | `43ff1e3`, `adb83af` |
| trainer "Discarded: DIFFICULTY_ADJUST" | merged as decided: flag off, `report()` recommended, read once per step | `014bf37`, `e481120`, `1d51483` |
| retrieval P1 constant | `lineage.py` merged with `min_similarity` 0.75 as exploration, not a hint | `95c41c7`, `fcd28ab` |

## Contradictions between reports, resolved in round 2

- **Near-duplicate threshold 0.97 (retrieval P2) vs 0.95 (`dev/demo_pick.py`)**: 0.95. All 32 training ids whose
  neighbour scores >= 0.95 are the same year at the adjacent level, including the 13 in [0.95, 0.97); [0.90, 0.95) is
  mixed and holds the opening demo neighbour (0.935).
- **The 0.75 similarity gate**: rung 1 only (a hint called "semblant" must be the same idea); the trainer skips duplicates
  but keeps weak neighbours and records their similarity.
- **The error signature as rung-3 content (hints P3) vs after the reveal (main)**: main is right for every relation key;
  only `statement_number` says nothing about the correct value and may precede the reveal.
- **Two attempts (web P4) vs one `record_answer` per problem (trainer contract)**: attempt 1 is graded; attempt 2 is a
  timeline row and a counter file, never a trainer call.
- **`start()` must not reset (web P6) vs deterministic demo chains**: reset when a course was chosen or the pseudonym is
  new; every chain names a course.
- **`warm` as default prefetch (hints P8) vs bounded `full` (web P1)**: with `Deadline` the join is bounded and a running
  prefetch is never doubled, so `full` stays; the one-call and `n >= 10` rules of P8 stay.
- **`Nice=5` on the LLM unit (board P4) vs calibration**: dropped before the demo; `OOMScoreAdjust` and `Restart=always`
  are worth the rehearsal-day re-calibration.
- **Reviewer C1 (rewrite `origin/main`)**: the eight trailers are upstream's; delete the three stale team branches instead.

## Discarded: they contradict a project rule

- LLM-written worked solutions or rung-4 explanations, LLM translation of hints into Catalan, LLM in the trainer or in
  mastery: the LLM never reasons; one hint is 28 s of board time; its Catalan is the failure mode.
- Elimination hints that state a property of the answer, any relation signature before the reveal, and the middle-value
  rule as a hint: they leak bits of the label before the student answers.
- Qwen3.5 2B on the board: 5 of 281 prompts over 60 s, about 1.6 GB RAM, no gain.
- numpy or `math.sumprod` for the dot products: numpy is not stdlib; `sumprod` was slower; 4.6 ms per rung-1 pool in pure
  Python.
- `MemoryMax` on the LLM unit; killing the hint thread or the in-flight request (urllib cannot; the `Deadline` bounds what
  the page waits for instead).
- Gating the trainer's neighbour at 0.75; skipping near-duplicates of the whole history (0.5 s per step on the board for a
  case the simulation never showed).
- Wall-clock spaced repetition; storing age or class; per-tab sessions.
- Rewriting `origin/main` history; committing `val.jsonl` "ids only", the OCR cache or problem images.
- A `--board` test flag, pytest or coverage on the board; a `/api/health` proxy for the page.

## Dependencies in one picture

```
1 leak filter v2 ──> 2 rung 3 filtered ──> 3 two attempts ──> 4 statement_number diagnosis
                 └─> (demo steps, lessons, signature texts, option checks all pass through it)
5 Deadline ──> 12 demo check (fallback_reason, honest smoke test)
6 predict  ─┘
10 duplicate constant ──> 14 trainer policy (after the demo; re-pick the chains)
9 degrade-never-invent (hand labels, no fake fallback) ──> 14
11 evidence + 15 measurements ──> the public README
```
