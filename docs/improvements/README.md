# Improvements: the consolidated list

Written 14 Nov 2026 against `origin/main` **d8f9c66** (284 tests, 1 skipped on macOS); the top 15 was re-weighted the
same evening on `bdf7afc` after the organizers set the grade at 50% Reasoning exam and 50% Teaching jury. Two rounds of exploration,
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

## Top 15, weighted 50% Reasoning and 50% Teaching

**Regraded 14 Nov 2026 (evening), main `bdf7afc`.** The organizers now score the entry **50% on the Reasoning exam**
(the hidden set corrected from `predict.py`'s CSV) **and 50% on Teaching** (the jury, three minutes). The list below
re-orders the same proposals with those weights: up goes whatever raises the exam score or makes `predict.py` unable to
lose points (time per problem, a letter on every row, odd inputs) and whatever the jury sees on stage; down goes what
touches neither. Two Reason tracks are already running elsewhere and are **not** repeated here: a short reasoning step of
the 0.8B per stratum (`reason-think`) and a learned prior over the options (`reason-prior`). The section after the table
lists the Reason ideas from the area reports that neither covers, with their cost in tokens and board seconds.

"Merges" names the proposals folded in (area report: P-number; cross report: X-number). Effort: S under 1 h, M 1-2 h.
"Before the demo": **yes** (stage flow unchanged, suite green), **rehearsal slot** (changes what the pitch shows; full
re-run of both chains, never the morning of), **after**. Status checked on `bdf7afc`.

| # | track | item | merges | effort | before the demo | status on main |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Reason | **`predict.py` writes a letter for every row, whatever happens**: catch-all per problem (`RuntimeError`, `ConnectionResetError`, `KeyError('choices')`, `ValueError` escape today), `problem.get("id", f"row-{n}")`, `setdefault` for `text`/`options`, a last-resort `D, 0.0, error: ...` row, `tests/fixtures/edge_rows.jsonl` (7 made-up rows) run through `subprocess`. An unanswered row scores 0 where D scores 23% | reason P1; demo X2 | S | yes | **open**: a row without `id` kills the run with the header only written |
| 2 | Reason + Teach | **The 60 s rule by construction: `board_clock.Deadline`** per `predict.py` problem and per student step, passed to `letter_scores`, `extract_json`, `embed`, `llm_hint`, `_prefetched`; `fits()` before every model call (never start what cannot finish), `timeout = remaining`, `SOLVERS=1` in `config.env` so `SOLVERS=0` works (reviewer I9), `prompt_tokens` accumulated; the hint thread bounded by `HINT_BUDGET_SECONDS`, a running prefetch never doubled | reason P2; web P1; hints P8; tests P7; demo X1 | M (2 h) | yes | **open**: the solver path gets `timeout=60`; worst val case 344 + 144 prompt tokens and 61 generated = 53.7 s with no margin for a queued server; a hung LLM holds the page 1x-2x the limit |
| 3 | Reason | **Precision guards that cost 0 tokens**: the middle-value rule abstains when the five unit strings differ (1 genuine km/m case and 10 OCR-noise units among 783 fired problems; today raw numbers are compared), the docstring's 650/663 fixed; the solvers reject an extraction whose integers do not occur in the statement ("copied, not invented": the one false positive on train), and the coverage table says 7 classified / 0 solved on val | reason P3 (unit check), P7 | S | yes | **open** (`MIDDLE_VALUE=1` itself landed in `199f6ab`, measured 150/562 on the board) |
| 4 | Teach | **A wrong answer does not reveal the letter**: two attempts, label private until the problem is closed, one `record_answer` (attempt 1), attempt 2 in the timeline and an `AttemptStats` counter, rung 4 pushed after the second miss, `/api/solution` only after an attempt or rung 3 with a confirmation (reviewer C2, C3: the jury's first criterion) | web P4, P5; rung3 X3 | M | rehearsal slot (pitch second 60, `contingency.md:40`, `demo-problems.md` steps 2 and 4) | **partly**: hints stay available after the answer (`b6e04b8`); `webapp.py:302` still names the letter on the first miss, `solution()` has no gate |
| 5 | Teach | **Leak filter v2**: glued units both ways (`12cm`; `cm2` is not a 2), number words 0-999 in three languages, dozen/half/pair/double, expressions, Roman numerals, ordinals, option positions, the lower-case letter, `lang` to stop blocking `set`/`nou`/`deu`/`un`/`once`; one corpus (110 adversarial, 40 harmless, every real option value, every demo step and lesson with raw options). Prerequisite of 4, 6, 9 | hints P6, P7; tests P8; rung3 X1 | M | yes | **open**: 75/110 adversarial pass, 12/40 harmless fail, 35/339 real values pass, 2 demo steps + 4 fields of `lvl-1_2024_8` would be wrongly dropped |
| 6 | Teach | **Rung 3 filtered and honest on stage**: demo steps through `leak_reason` at runtime with `lang`, "Pas i de n" over the survivors (M4), solver trace on the English row, figure line first in rung 4, `demo_steps`/`lesson`/`fallback_reason` in INTERFACES | hints P1, P2; rung3 X2 | S | yes (the six demo ids' steps pass today: same text on stage) | **partly**: steps read at rung 3/4 and the lesson exist; nothing filters the steps at runtime |
| 7 | Teach | **The page never crashes in front of the jury**: `api()` turns `{"error"}` into a status line, 4 s fetch timeout, polls that never overlap and back off, a "la placa no respon" banner after three failures, letters usable while a hint is pending, no exception text from `hal/web.py` | web P2, P8; demo X3 | M | yes (one browser check) | **open**: `render()` throws on `{"error": "already answered"}` (a double click, a second tab) |
| 8 | Teach | **"Comença" keeps the student, the bank never loops**: reset only when a course was chosen or the pseudonym is new, a blank name is an error instead of `demo`; `_least_recent` picks the problem whose latest answer is oldest | web P6; trainer P5; demo X5 | S | yes (every chain names a course) | **open**: a blank start wiped `demo` (answers 1 -> 0) |
| 9 | Reason + Teach | **Demo day and exam day as code**: `board/07_demo_check.sh` (units, `/health` on loopback and `docker0`, data counts, index rows, one **timed real letter call** against the 60 s rule, `estimate_tokens(300, 40) < 57`, app page without `label`, RAM, Wi-Fi); an honest `05_smoke_test.sh` (`LETTER_MODEL=1 SOLVERS=0 predict.py` on the samples, today the budget check runs on 0.0 s rows); `tests/__init__.py` redirecting `STUDENTS_DB` (a suite run writes four test pupils into the demo database); units with `OOMScoreAdjust` 500/200/-200 and `Restart=always`, no `Nice` | board P9, P4; tests P1, P2; demo X6, X7 | M | yes; the units on the rehearsal day, then `calibrate_speed.py` within 5% | **open** |
| 10 | Teach | **Degrade, never invent**: `neighbors()` never raises (embed server down) and never returns `sample-4` for a real id (index missing), the 50 hand labels override `topics.json`, `Bridge.call` guarded, a startup health line and `servers` in `/api/state`, `NEAR_DUPLICATE = 0.95` with `skip_duplicates` shared by rung 1, the trainer and `demo_pick` | retrieval P2, P3 (code), P4, P8; web P7 (guard); board P8; demo X4; trainer-retrieval X1, X2, X7 | M | yes (chain problems and neighbours are training ids; no demo list has a hit >= 0.95) | **open** |
| 11 | Reason + Teach | **Evidence in the public tree**: `docs/runs/` with the ids-only eval CSVs, the official-run `predictions.csv` (562 rows) and `ablations.csv` (reviewer I11), `.gitignore` for `*.jsonl`/images/parquet everywhere, the id -> letter rows out of `docs/content-review.md` and `contingency.md:40`, a test that no doc pairs an id with a letter, the three stale branches with tool trailers deleted, `hint_quality.json:40` reworded | reason P5; data P1, P2, P7; rung3 X7 | S | yes | **partly**: `demo-problems.md` scrubbed; the rest open |
| 12 | Teach | **The one diagnosis before the reveal**: `hints.note_attempt`, the `statement_number` signature at rung 3 after a miss; every relation signature stays after the close (with direction they pin the correct option in 95/95 validation pairs) | hints P3 (narrowed); rung3 X4 | S | yes | **partly**: signatures shown after the reveal only |
| 13 | Reason + jury reading | **Measured, pinned, honest numbers**: a precise determinism statement (per platform; 3/50 near-ties flip laptop vs board; times vary 3 s with the cache) and a two-run test on the sample file; `laptop/measure_ladder.py` and the ladder table; the stale `results-A.md` header and "125 tests"; the M3Kang revision `e772e61` pinned with a text-free manifest; `requirements.txt` pinned with Python 3.11-3.12; `calibrate_speed.py --write` per request, not per text; the README's data and licence section | reason P6, P8; hints P11; data P5, P6a, P9, P10; board P1; retrieval P7 | S each | yes; the root README swap after | **open** |
| 14 | Teach | **One mastery sentence**: `derive_mastery` the single source (no 0 -> 1 after rung 4, no one-answer review penalty undone by the next wrong answer; reviewer I7, M7), INTERFACES and the teacher legend aligned | trainer P2 | S | yes (tick 0 -> 2 and cross 0 -> 1 unchanged) | **open**: `trainer.py:548-550` |
| 15 | Teach | **Teacher report a teacher can use**: seconds per problem, hints per right answer, per-topic trend, last failed ids, the diagnostic's outcome, `by_topic` on the page, `difficulty.report()` rendered | trainer P6 | M | yes (additive keys) | **open** (`difficulty` merged in `014bf37`, not on the page) |

Moved out of the top 15 by the new weights: the trainer's selection policy (diagnostic `(L, L+1, L-1)`, 2-up-1-down,
spaced review, base level; trainer P1, P3, P4, P7; trainer-retrieval X3-X6, X8). It is right and measured (accuracy 47% ->
60% for a student at their level) but the jury cannot see it in three minutes, it re-picks every demo chain, and it adds
nothing to the exam. It stays first in the "after the demo" list with its one-hour re-pick procedure.

## Reason ideas the area reports hold that neither `reason-think` nor `reason-prior` covers

Costs use the board constants (11.4 tok/s prefill, 5.6 tok/s generation, 0.12 s per embedding). "0" means no model call.

| idea | where it comes from | what it changes on the exam | cost per problem | risk |
| --- | --- | --- | --- | --- |
| **A. No row ever missing** (item 1) | reason P1 (verified: `KeyError` on a row without `id`, four exception types escape a solver) | removes the only way to score below the always-D floor on a hidden file with an odd row; each lost row is 0 where D is 23% | 0 | none |
| **B. A per-problem deadline that skips calls that cannot fit** (item 2) | reason P2, demo X1 | today a 344-token extraction (30.2 s prefill + 60 tokens 10.7 s) followed by a 144-token letter call (12.6 s + 0.2 s) is 53.7 s estimated and 54.4 s measured by the reviewer; one queued request on the server pushes a row over 60 s with status `ok`. `fits()` makes the second call conditional on the remaining budget, and `timeout = remaining` ends a hung socket inside the limit | 0 (a length estimate before the call) | a skipped call falls back to the middle value or D, which is what the row would have scored anyway when late |
| **C. Cap the solver prompt** | reason P2 (c), new here | the four family extractions are the longest prompts of the exam (up to 344 tokens, all 7 abstained on val). A `SOLVER_MAX_PROMPT_TOKENS=300` guard (skip the extraction above it) bounds the solver path at 26.3 + 10.7 = 37 s and leaves 20 s for any later step; if `reason-think` wins its slot, the solver can be turned off (`SOLVERS=0`, item 2 makes the switch real) at 0 loss on val | 0; saves up to 41 s on the 7 classified val problems | a long classified problem loses a solver that has solved 0 of them on val |
| **D. Identical units or abstain** (item 3) | reason P3 | the middle-value rule compares raw numbers across `1 km` and `500 m` (1 genuine case, 10 OCR-noise units like `b`, `qqq` among 783 fired problems); abstaining hands them to the fallback | 0 | about 1 problem either way; it removes a wrong pick class |
| **E. "Copied, not invented"** (item 3) | reason P7 | an extraction whose integer parameters do not occur as whole numbers in the statement abstains; protects the solvers' only selling point (one false positive on train, `results-A.md:53`) | 0 (a regex over the statement) | a number written in words ("five consecutive") must be allowed (zero to twelve) |
| **F. Catalan rows are half the hidden set** | reason P3 recount (new number: val cat 73/281 = 26.0% for the middle value, 65/281 for D); hints P1 (solvers classify 0/281 Catalan rows) | every per-language figure in the docs is English; the exam is `eng + cat`. The middle value is the only language-independent gain today; the solvers never fire on Catalan. Any `reason-think` or `reason-prior` measurement must report `cat` separately (OCR read different option strings on 16 val ids, so the two rows of one id can disagree) | 0 | none; a reporting rule |
| **G. Prompt cache checkpoints for `reason-think`** | the hints-app hand-over note (Qwen3.5 is a hybrid model: llama-server restores the cache only at the start of the last user message and 4 tokens before the end) | a stable instruction block saves its prefill only if it sits in its **own earlier message** and the problem is the last user message; a shared prefix inside one message is re-read every time. For a 150-token instruction block that is 13 s per problem on the board, or 5 of the 60 s budget for free | saves up to 150 tokens / 13 s per problem | none; measured on the shared server by the hints session (`cache_n` stayed at the system prompt otherwise) |
| **H. Determinism stated per platform** (item 13) | reason P6 | the organizers ask for "same answers every time"; 3/50 near-ties flipped laptop vs board on the letter path and times vary about 3 s with the cache. Say so, test the two-run identity on the sample file, and keep every tie-break alphabetical (`bias.choose`, `ladder.middle_letter`, shuffle-invariant on 562 rows) | 0 | none |
| **I. Evidence the exam can be audited against** (item 11) | reason P5, data P7 | the official-run `predictions.csv` (562 rows, ids and letters) and the eval CSVs under `docs/runs/`, so the 26.7% and the per-language rates are reproducible from the public tree | 0 | a CSV with a text column would leak: a header check in the test |

Not proposed again because the running tracks own them: anything that asks the 0.8B to reason (`reason-think`), any
prior over option values, positions or letter frequencies beyond the middle value (`reason-prior`), the value grammar and
the cyclic-shift votes (measured on the branch at 23.5% and 22.4%, 6 problems over 60 s), Catalan keyword solvers
(0 expected gain, up to 7 more 40 s calls), and the 2B model (5 of 281 prompts over 60 s).

### Worth doing after the demo, not in the top 15

- The trainer's selection policy as one spec (diagnostic `(L, L+1, L-1)` with the exact level before topic rotation,
  two rights to go up and one wrong to go down with mastery 4 = 3 of the last 4 right without hints, review due in
  answers, base level as the median of the last ten, `trainer.diagnostic_plan` shared with `dev/demo_pick.py`, the
  simulator harness and its before/after table): [cross-trainer-retrieval.md](cross-trainer-retrieval.md) §1-§3 and
  the one-hour re-pick procedure in §2.
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

From [cross-demo-robustness.md](cross-demo-robustness.md) §3 and [cross-trainer-retrieval.md](cross-trainer-retrieval.md) §2
(item numbers are the weighted top 15 above).

| when | do | never |
| --- | --- | --- |
| **Now, no stage effect** | 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15; the night-before items of 9 | |
| **Rehearsal slot** (full re-run of both chains, then `demo_rehearse.py`) | 4 (update `pitch.md` second 60, `contingency.md:40`, `demo-problems.md` steps 2 and 4); the three units of 9, then `calibrate_speed.py` within 5% of 11.4 / 5.6 | `calibrate_speed.py --write`; `config.env` edits other than `HINT_BUDGET_SECONDS` and `SOLVERS` |
| **Morning of** | power on, `adb devices`, `./board/07_demo_check.sh`, `adb forward`, one `demo_rehearse.py Mariona1 1 C A`, `/api/reset`, type the pseudonym and course | tests, `git pull`, `app stop/start` unless the check fails, any `board/01-06` script |
| **Exam day** | `./board/07_demo_check.sh` (the timed letter call and the `estimate_tokens` check), then `predict.py` with items 1-3 landed and `SOLVERS` set by the val measurement of the running Reason tracks | a `config.env` not measured on val |
| **After the demo** | the trainer policy with the re-pick; option checks; the rung-1 gate; POST; polling; the 394 labels; a new `index.db`; the root README swap | |

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
1 predict never dies ─┐
2 Deadline ───────────┼─> 9 demo and exam check (timed letter call, honest smoke test, fallback_reason)
3 precision guards ───┘
5 leak filter v2 ──> 6 rung 3 filtered ──> 4 two attempts ──> 12 statement_number diagnosis
                 └─> (demo steps, lessons, signature texts all pass through it)
10 degrade-never-invent + duplicate constant ──> trainer policy (after the demo; re-pick the chains)
11 evidence + 13 measurements ──> the public README
```
