# Reason track and evaluation: contract, determinism, 60 s, middle-value rule, solvers, evidence

Written 14 Nov 2026 against `team/improvements-d18364` = `origin/main 5cc2ded`, after reading the
reviewer's findings on main (`origin/team/review-22fa88:docs/reviews/review-main-2026-11-14.md`:
I9, I11, I14, M1, M2 touch this area) and the unmerged branch `team/reason-predict-0ff6f3`.

**Summary (5 lines).**
1. The jury contract holds on the happy path (CSV `id,language,answer,seconds,status`, one letter, 0.0 s
   when no solver fires), but `predict.py` **dies mid-run** on a row without `id`, on a row without `text`
   when `LETTER_MODEL=1`, and on any server error that is not a timeout or a `URLError` (verified with
   mocks: `RuntimeError`, `ConnectionResetError`, `KeyError`, `ValueError` all escape `pipeline.solve`).
2. The 60 s limit is a per-request HTTP timeout, not a per-problem deadline: the solver path passes
   `timeout=60` (reviewer M2 confirmed), and `SOLVERS=0` is ignored (reviewer I9 confirmed). Worst case on
   val with the shipped flags is one 344-token extraction, 38 to 41 s on the board; with `LETTER_MODEL=1`
   it would be 53.7 s estimated (tokenized), with no margin for a queued server.
3. The middle-value rule of `copilot/ladder.py` is **verified by my own count**: val English 77/281 = 27.4%
   (+12 over always D), val Catalan 73/281 = 26.0% (+8, not reported on the branch), train English
   405/1466 = 27.6%, train Catalan 409/1466 = 27.9%. Deterministic (ties abstain, option order irrelevant).
   It is a prior on how Kangaroo distractors are built, not reasoning, and the README must say so.
4. Solvers: on val the keyword classifier routes 7 English problems (ages 3, average 4) and 0 Catalan; all
   7 extractions abstain (docs, and one re-run here), so the solvers cost up to 7 × 30 s of the official run
   for 0 problems gained. The `sample-1` answer is a hard-coded fixture (classifier returns None on it).
5. Nothing under `results/` reaches the public repository, so no figure is reproducible from the tree; the
   eval CSVs carry ids, letters, times and logprobs only and can be committed under `docs/runs/`.

## What I ran

All from the worktree, Python 3.14, shared servers untouched (`dev/start_servers.sh --status`: both OK).
Scratchpad: `/private/tmp/claude-501/-Users-lizard-Coding-Datathon-UPC-2026--claude-worktrees-improvements-d18364/56fd292b-4e9e-46ea-8d46-1af0ce443f0d/scratchpad/`.

| what | command | outcome |
| --- | --- | --- |
| Module tests (VERIFIED) | `python3 -m unittest tests.test_solvers tests.test_bias tests.test_board_clock` | 37 tests OK, 0.02 s |
| Full suite (VERIFIED) | `python3 -m unittest discover tests` | 168 OK, 1 skipped, 0.93 s |
| Help texts (VERIFIED) | `python3 predict.py --help`, `python3 eval.py --help` | both print; predict: `--input --output --rag K --index`; eval: `--input --limit --languages --rag --index --name --simulate-latency` |
| Smoke, no LLM (VERIFIED) | `LETTER_MODEL=0 python3 predict.py --input <5 eng val rows, none classified> --output smoke5.csv` | 5 rows, all `D`, `0.0` s, `ok`; **0.07 s wall for the whole run** |
| Edge rows, no LLM (VERIFIED) | made-up rows: no options, Catalan, blank line, no `text`, duplicate id, options as a list, `text: null` | 6 rows written, all `D ok`; blank line skipped; duplicate id written twice |
| Empty input (VERIFIED) | `: > empty.jsonl; predict.py ...` | exit 0, header only |
| Row without `id` (VERIFIED) | one made-up row | **`KeyError: 'id'` traceback, run stops** |
| Row without `text`, `LETTER_MODEL=1` (VERIFIED, no server call: the KeyError fires before `post`) | `LETTER_MODEL=1 LLM_PORT=1 predict.py` | **`KeyError: 'text'` traceback, run stops** |
| Server down, `LETTER_MODEL=1` (VERIFIED) | `LLM_PORT=1` | `D`, status `error: [Errno 61] Connection refused`, run continues |
| Exceptions inside a solver (VERIFIED with `mock`) | patch `ages.extract` to raise `RuntimeError`, `ConnectionResetError`, `KeyError('choices')`, `ValueError`; patch `compute` to raise `ZeroDivisionError`, `RecursionError` | the first four and `RecursionError` **propagate out of `pipeline.solve`**; `ZeroDivisionError` is caught (it is an `ArithmeticError`) |
| Solver-path timeout (VERIFIED with `mock` on `llm.post`) | | `extract_json` is called with `timeout=60`, whatever time has passed |
| `SOLVERS=0` (VERIFIED) | `SOLVERS=0 python3 -c "from copilot import pipeline; print(pipeline.USE_SOLVERS)"` | `True` (reviewer I9) |
| Classifier coverage (VERIFIED, no LLM) | `solvers.classify` over val and train, both languages | val eng: ages 3 (`lvl-1_2020_23`, `lvl-4_2008_22`, `lvl-5_2019_29`), average 4 (`lvl-3_2021_13`, `lvl-3_2022_21`, `lvl-3_2023_28`, `lvl-4_2011_2`); val cat: 0; train eng: ages 19, average 24, digit_count 5, consecutive 2; train cat: 0 |
| Worst extraction, 1 real LLM call (VERIFIED) | `LETTER_MODEL=0 predict.py` on `lvl-4_2008_22` alone | `D ok`, 1.19 s laptop, **38.1 s board estimate** (abstained) |
| Prompt sizes, 2 `/tokenize` requests (VERIFIED, no generation) | extraction and letter prompts of `lvl-4_2008_22` | 344 and 144 tokens: 40.9 s + 12.8 s = **53.7 s** estimated if both ran |
| Middle-value count (VERIFIED) | `PYTHONPATH=. python3 <scratchpad>/middle_count.py` with the branch's `ladder.py` copied verbatim | table below |
| Mixed units among fired options (VERIFIED) | same script | 11 of 783 fired English problems (train+val); 10 are OCR noise units (`b`, `qqq`, `x`), 1 genuine (`lvl-3_2016_9`: km against m) |
| `sample-1` routing (VERIFIED) | `solvers.classify` / `solvers.solve` on `data/sample_problems.jsonl` | classify `None` for all five; `solve` returns `C` for `sample-1` only, from `_SAMPLE_1` |

READ ONLY: `copilot/rag.py`, `copilot/embed.py` (timeout 60 per call, not budgeted), `calibrate_bias.py`,
`laptop/error_analysis.py`, `copilot/votes.py`, `docs/reason-experiments.md`, the organizers' README
lines 807-842 (the contract: CSV `id, language, answer, seconds, status`; one letter; 60 s; same answers
every time).

LLM budget used: 1 generation + 2 tokenize requests.

### The middle-value rule, recounted

Branch `ladder.py` code unchanged; `data/val.jsonl` and `data/train.jsonl`; always-D counted on the same rows.

| set | n | always D | rule fires | rule right (precision) | D right on fired | rule + D elsewhere | gain |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| val eng | 281 | 65 (23.1%) | 120 (21 with a unit) | 36 (30.0%) | 24 (20.0%) | **77 = 27.4%** | +12 |
| val cat | 281 | 65 (23.1%) | 123 | 34 (27.6%) | 26 (21.1%) | **73 = 26.0%** | +8 |
| train eng | 1466 | 367 (25.0%) | 663 | 201 (30.3%) | 163 (24.6%) | 405 = 27.6% | +38 |
| train cat | 1466 | 367 (25.0%) | 687 | 207 (30.1%) | 165 (24.0%) | 409 = 27.9% | +42 |

Rank of the labelled value among the five sorted values, train eng: smallest 56, 2nd 150, **middle 201**,
4th 181, largest 75 (val eng: 12 / 30 / 36 / 29 / 13). The extremes hold the answer 20% of the time
against 40% for a uniform draw: that is the whole effect. The branch's figures match (77/281; 406 on
train = my 405 plus one solver hit in its eval run; `ladder.py` says 650 fired on train, I count 663 with
its current regex: the docstring is one revision stale). Determinism: shuffling the option dict order
changed 0 of 562 val answers; five equal values or a non-numeric option make it abstain; letters
tie-break `(value, letter)`. The rule differs between the English and the Catalan row of the same id on
16 val ids (OCR read different option strings), so the Catalan gain is smaller.

## Proposals

### P1. Make `predict.py` unable to die: a catch-all per problem and tolerant row access
- **Where**: `copilot/pipeline.py:91-97` (only `socket.timeout`, `TimeoutError`, `URLError` are caught);
  `predict.py:38-40` (`problem["id"]`), `copilot/llm.py:14` (`problem["text"].strip()`),
  `copilot/solvers/ages.py:39` and the three other `extract` (`problem["text"]`).
- **Problem / opportunity**: the official run is one process over the whole hidden file. Verified: a row
  without `id` kills it (`KeyError: 'id'`); with `LETTER_MODEL=1` a row without `text` kills it; a
  server reply without `choices`, a reset connection (`ConnectionResetError`, `http.client.RemoteDisconnected`
  are not `URLError`), or a non-JSON body (`ValueError` from `json.loads` in `client.post`) kills it from
  inside a solver extraction. Rows already written are flushed, the rest are missing: an unanswered
  problem scores 0 where `D` scores 23%. Today the shipped flags make the LLM path reachable only through
  the 7 classified problems, which is exactly where the risk sits.
- **Proposal**: in `solve()` add a final `except Exception as error: result["status"] = f"error: {type(error).__name__}"`
  after the existing handlers (answer stays `FALLBACK`); in `predict.py` read `problem.get("id", f"row-{n}")`
  and `problem.setdefault("text", "")`, `problem.setdefault("options", {})`, and wrap `solve()` in a
  try/except that writes `FALLBACK, 0.0, "error: ..."` as a last resort; in `llm.format_problem` use
  `(problem.get("text") or "")`. Test: `tests/test_pipeline.py` with `mock.patch.object(ages, "extract",
  side_effect=RuntimeError)` asserting `answer == "D"` and `status.startswith("error")`; a
  `tests/fixtures/edge_rows.jsonl` (made-up rows: no id, no text, options as list, duplicate id, blank
  line) run through `predict.main` via `subprocess`, asserting one output row per input row and a letter
  in A-E each. Document in `predict.py` docstring: "every row gets a letter, whatever happens".
- **Impact (jury)**: high. It is the only path by which the hidden-set score can fall below the always-D floor.
- **Effort**: S.
- **Risk**: none for the demo (the app does not use `predict.py`); INTERFACES.md unchanged. Safe before the demo.
- **How to measure**: the new tests; `python3 predict.py --input tests/fixtures/edge_rows.jsonl` writes 6 rows, exit 0.
- **Verified**: ran (the failures); the fix is read-only reasoning.

### P2. One deadline per problem: honour `SOLVERS=0`, pass the remaining budget to the solver path, skip calls that cannot fit
- **Where**: `copilot/config.py:19-21` (env wins only for keys present in `config.env`), `config.env` (no
  `SOLVERS` line), `copilot/pipeline.py:53` (`solvers.solve_with_timings(problem)` without a budget),
  `copilot/solvers/__init__.py:54` and each family's `extract`, `copilot/llm.py:93` (`timeout=60`).
- **Problem / opportunity**: reviewer I9 and M2, both confirmed here. Measured facts: the shipped
  worst case is one extraction, 38.1 s board estimate on `lvl-4_2008_22` (40.0 s real on the board per
  `results-A.md`); with `LETTER_MODEL=1` the same problem costs 344 + 144 prompt tokens and 61 written:
  53.7 s estimated, 54.4 s in the reviewer's rerun. The HTTP timeout is per socket operation, not per
  problem, and `urllib` applies it to connect and to each read: a server that answers in 59 s twice passes
  both timeouts and the row is written with status `ok` after 118 s. Also `pipeline.py:89` overwrites
  `prompt_tokens` with the letter call's count (I9), so the CSV under-reports the solver's cost.
- **Proposal**: (a) add `SOLVERS=1` to `config.env` next to `LETTER_MODEL`, so the env override works;
  (b) give `solve_with_timings(problem, timeout=60)` a `timeout` and thread it to `module.extract(problem,
  timeout)` and `llm.extract_json(..., timeout=timeout)`; in `pipeline.solve` compute `remaining` before
  the solver call and pass `max(remaining, 1.0)`; (c) before every LLM call check the clock:
  `if clock.seconds() + board_clock.estimate_tokens(len(prompt_chars) / 3.8, max_tokens) > time_limit -
  MARGIN: skip` (on the board `clock.seconds()` is real time; in sim it is the estimate), so a long
  extraction followed by a letter call is never started when it cannot finish; (d) `result["prompt_tokens"] +=`
  instead of `=` at line 89. Tests: extend `tests/test_solvers.py::TimingsTest` with a mock asserting the
  `timeout` reaching `llm.post` equals the pipeline's `remaining`; a `board_clock` test for the skip rule
  with `RUNTIME=sim` and a 1,100-token fake prompt. Docs: `results-A.md` Phase 10 "worst 40.0 s" stays;
  add "the budget is enforced per problem since <commit>".
- **Impact (jury)**: medium. The 60 s rule is a hard criterion; today it holds by measurement, not by construction.
- **Effort**: S for (a) and (d), M for (b)+(c) with tests.
- **Risk**: `solve_with_timings` gains an optional keyword: INTERFACES.md lists `solve(problem)` only, so add
  one line there. `hints.py:249` calls `solvers.solve(problem)` with no budget and keeps working. Safe before the demo.
- **How to measure**: `SOLVERS=0 python3 -c "from copilot import pipeline; print(pipeline.USE_SOLVERS)"` → `False`;
  `LETTER_MODEL=1 python3 eval.py --limit 50 --languages eng` must report `over 60 s: 0` with the solvers
  on and the real worst-case column replaced in `results-A.md:88-100` (I9's stale 16.7 s).
- **Verified**: ran (the flag, the 60 s timeout, the token counts); fix read-only.

### P3. Adopt the middle-value rule (`MIDDLE_VALUE=1`), report it honestly, and tighten units
- **Where**: `origin/team/reason-predict-0ff6f3:copilot/ladder.py` (47 lines), `tests/test_ladder.py`,
  `config.env:+75` (`MIDDLE_VALUE=0`), `copilot/pipeline.py` (the branch's `USE_MIDDLE_VALUE` block only),
  `docs/README-final-draft.md:167-187` (table 4.1 and the paragraph "The Reason track stays at the always-D floor").
- **Problem / opportunity**: the branch's claim is right and under-reported. My recount: +12 on val English
  (27.4%), **+8 on val Catalan (26.0%)**, +38 / +42 on train; precision when it fires 30% against 20 to 25%
  for D on the same problems; at no model cost (0.0 s). The hidden test may contain Catalan rows, where
  today nothing but `D` ever answers (the solvers' keywords are English): the rule is the only
  language-independent gain available. Honesty: the rule reads no mathematics, it exploits how Kangaroo
  distractors are generated around the right value (the labelled value is an extreme 20% of the time
  against 40% for a uniform draw). It also shows a small genuine weakness: with mixed units the raw
  numbers are compared (1 of 783 fired problems, `lvl-3_2016_9`, km against m); 10 more carry OCR
  noise units (`b`, `qqq`) that would better abstain.
- **Proposal**: merge only `copilot/ladder.py`, `tests/test_ladder.py` and the `USE_MIDDLE_VALUE` block of
  `pipeline.py` from the branch (not `votes.py`, see Discarded); set `MIDDLE_VALUE=1` in `config.env`; in
  `ladder.numeric_options` require the five unit strings (the text after the number, lower-cased, `2`→`²`)
  to be identical, else abstain; fix the `ladder.py` docstring (663 fired on train with the current regex,
  not 650) and make `config.env`'s 405 and `reason-experiments.md`'s 406 agree (406 = 405 + one solver hit).
  README 4.1: add two rows, "Middle value when the five options are distinct numbers, D elsewhere: 281 eng
  val 27.4% (77/281), 281 cat val 26.0% (73/281), 0 s"; replace the floor sentence by: "`predict.py`
  answers with a prior, not with reasoning: a family solver when one of four templates applies (never on
  validation), otherwise the middle of five numeric options, a property of how Kangaroo distractors are
  written (the right value is an extreme in 20% of training problems), otherwise D. The language model
  is not consulted: its letter is 21.7% right and its confidence runs the wrong way. We report this as a
  measured floor-beating heuristic, +4.3 points over always D, not as solving problems." Keep the rule
  out of the Teach track: it must never become a hint (it would steer the student to the answer with 30%
  precision and teach nothing).
- **Impact (jury)**: medium-high. "Measure before/after" on the Reason track becomes 23.1% → 27.4% with a
  one-line, reproducible explanation; honest framing protects the credibility of the Teach numbers.
- **Effort**: S (merge + unit check + docs).
- **Risk**: `pipeline.solve` gains `rule` and `extra` keys (additive; `eval.py` on the branch writes them).
  No INTERFACES.md change. Safe before the demo: the app never calls `pipeline.solve`.
- **How to measure**: `MIDDLE_VALUE=1 python3 eval.py --limit 0 --languages eng --name middle-eng281` → 77/281;
  `--languages cat` → 73/281 (minus the few mixed-unit abstentions); `tests/test_ladder.py` plus a new case
  `{"A": "1 km", "B": "500 m", ...}` → `None`.
- **Verified**: ran (the counts, determinism, units); merge read-only.

### P4. Move the `sample-1` fixture out of board code (reviewer I14) into the demo set
- **Where**: `copilot/solvers/__init__.py:49-50, 70-80` (`_SAMPLE_1`); dependents `tests/test_solvers.py:69`,
  `tests/test_interfaces.py:53`, `tests/test_hints.py:16-132` (rungs 3 and 4 on `sample-1` go through
  `hints.py:249 solvers.solve(problem)`), `copilot/topics.py:34` (`_SAMPLE_TOPICS`, the same pattern).
- **Problem / opportunity**: verified: `classify(sample-1)` is `None`, so the smoke test's `C` for `sample-1`
  and the rung-3 "Pas 1 de 3" in the hint tests come from a constant keyed on an id, inside the file the
  jury reads first. Its `family` is `arithmetic_words`, which does not exist. A reader of `predict.py`
  cannot tell it from a lookup table of answers.
- **Proposal**: put the three-step trace into `data_curated/demo_set.json` (the template
  `demo_set.template.json` already has the shape) under `sample-1` with `answer`, `value`, `trace`; in
  `hints.py` read the demo set before calling `solvers.solve` (the reviewer's I13 asks for the same lookup
  for the demo problems, so one change serves both); delete `_SAMPLE_1` and the `if problem.get("id") ==
  "sample-1"` branch; in `tests/test_solvers.py` replace `test_solve_keeps_the_sample_fixture` by
  "`solve` returns `None` on `sample-1` (no family)"; in `tests/test_interfaces.py:53` assert the shape
  on a mocked solver; `tests/test_hints.py` keeps passing through the demo-set path. Leave
  `topics._SAMPLE_TOPICS` (it maps to a topic, not to an answer) but mention it in the same commit.
- **Impact (jury)**: medium. Credibility: the official entry point must contain no per-id answers.
- **Effort**: M (touches D's hint tests).
- **Risk**: `hints.get_hint` on `sample-1` must keep returning a trace, or `test_hints` breaks; no
  INTERFACES.md change (the Solver trace shape is reused). Do it with the full suite green; safe before the demo
  only if the demo problems' rung 3 is checked afterwards in the app (`python3 -m copilot.webapp` sim).
- **How to measure**: `grep -rn "sample-1" copilot/` → only `topics.py`; 168 tests still green;
  `predict.py --input data/sample_problems.jsonl` now answers `D` on `sample-1` (status `ok`).
- **Verified**: ran (the routing); fix read-only.

### P5. Commit the evidence: `docs/runs/` with the per-problem CSVs (ids only) and `ablations.csv` (reviewer I11)
- **Where**: `.gitignore:7-8` (`results/*`), `docs/README-final-draft.md:164` ("All runs are in
  `results/ablations.csv`"), `docs/error-analysis.md:7,155` (cites two CSV files), `results/` (empty in
  this fresh worktree, `.gitkeep` only).
- **Problem / opportunity**: every number in `results-A.md`, `error-analysis.md` and the README points at
  files that no reader of the public repository will have. `eval.py`'s CSV columns are `id, language,
  level, has_options, label, answer, correct, seconds, board_seconds, status, prompt_tokens, retrieved,
  raw_letter, margin, family, letter_logprobs` (branch: `rule, extra`): no text, no image. The licence
  forbids problem text and images, not ids and letters. The jury criterion is "measure before/after";
  without the files it is "trust us".
- **Proposal**: create `docs/runs/` and copy from the team's laptops and the board:
  `eval-20261114-134204-A-baseline-eng281.csv`, `eval-20261114-141057-A-solvers-plus-D-eng281-v2.csv`,
  the board `predictions.csv` (562 rows), the board 50-problem baseline CSV, the branch's
  `R-middle-eng281` and `R-middle-train-eng1466` CSVs, and `ablations.csv`; add `docs/runs/README.md`
  with one line per file (command, commit, machine, date) and the sentence "ids and letters only; the
  problems are in the M3Kang dataset". If the team prefers not to ship the `label` column, keep `correct`
  and drop `label` with one `csv` one-liner; `laptop/error_analysis.py` needs the labels, so document
  that it then reads them from the local `val.jsonl`. Point README 4, `error-analysis.md` and
  `results-A.md` at `docs/runs/`. Un-ignoring `results/*.csv` is the alternative; it risks committing
  scratch runs, so prefer the explicit copy.
- **Impact (jury)**: high. It turns every figure into something the jury can open.
- **Effort**: S (mostly collecting files; 10 minutes of the controller's coordination).
- **Risk**: none for code. Check with `grep -c` that no CSV contains a `text` column before `git add`;
  add a guard in `tests/test_no_data_in_tree.py` (or wherever the licence test lives) that the CSV headers
  under `docs/runs/` contain no `text` column. Safe before the demo.
- **How to measure**: a fresh `git clone` has `docs/runs/*.csv`; `python3 laptop/error_analysis.py
  docs/runs/eval-20261114-141057-A-solvers-plus-D-eng281-v2.csv` reproduces `docs/error-analysis.md`.
- **Verified**: ran (`ls results/` empty; CSV columns read from `eval.py`); copying read-only.

### P6. State determinism precisely and guard it with a test
- **Where**: `predict.py:12` ("deterministic"), `copilot/llm.py:46-48, 72-74, 112-114` (`temperature 0`,
  `seed 42`, `cache_prompt: True`), `copilot/bias.py:56` (alphabetical tie-break), `eval.py:59`
  (`random.Random(42).shuffle`), `docs/results-A.md:94` ("47/50 answers identical, 3 near-ties flip with
  the platform's float arithmetic").
- **Problem / opportunity**: I found no unseeded randomness, no set iteration and no time-dependent branch
  in the answer path (dict orders are insertion orders: `FAMILIES` by import order at
  `solvers/__init__.py:82`, options by letter; `ladder` and `bias` tie-break by letter; the only
  time-dependent branch is the timeout, which yields `D`). Two honest caveats are not written anywhere a
  reader will see: (1) the LLM path is deterministic **per platform** (3/50 flips laptop vs board); (2)
  `prompt_n`, hence `seconds` and `board_seconds`, vary by about 33 tokens / 3 s with the server's prompt
  cache state (`results-A.md` "Known measurement artifact"). With the shipped flags the answer path has no
  model call unless a solver fires, so `predict.py` is bit-for-bit deterministic on the 281 and the
  reader should know that too.
- **Proposal**: README 4.1 one paragraph: "Determinism: seed 42, temperature 0, grammar-constrained
  output, alphabetical tie-breaks; two runs on the same machine give identical letters (checked on 562
  rows); across machines the 0.8B model's near-ties can flip (3 of 50 between the laptop and the board);
  times vary by about 3 s with the prompt cache." Add `tests/test_predict_determinism.py`: run
  `pipeline.solve` twice over `data/sample_problems.jsonl` with `LETTER_MODEL=0` (no server) and over
  a mocked `llm.post` that returns a fixed `choices`/`logprobs` payload with `LETTER_MODEL=1`, asserting
  identical `answer` lists; assert `bias.choose` and `ladder.middle_letter` are invariant to the option
  dict order (the shuffle check I ran, 0 flips on 562 rows).
- **Impact (jury)**: low-medium. "Same answers every time" is in the organizers' rules (README 1143); a
  precise sentence beats an absolute one that a reviewer can falsify with the 3/50 flips.
- **Effort**: S.
- **Risk**: none; safe before the demo.
- **How to measure**: the test; `python3 predict.py` twice on the 562 rows on the board, `diff` of the
  `answer` column empty.
- **Verified**: ran (the shuffle check; code reading for randomness); test read-only.

### P7. Solvers: a "copied, not invented" check and a coverage table that matches the current classifier
- **Where**: `copilot/solvers/__init__.py:54-66` (`extract` → `compute` → `match_option`),
  `copilot/solvers/common.py:28-40`, `docs/results-A.md:48-58` (the four-family table: consecutive
  "classified 11"), `docs/README-final-draft.md:181-184`.
- **Problem / opportunity**: coverage recounted today: val English 7 classified (ages 3, average 4,
  consecutive 0, digit_count 0), val Catalan 0, train English ages 19, average 24, digit_count 5,
  consecutive 2. The docs table says consecutive 11: it predates the tightened regex. Precision when a
  solver fires is protected only by "the value equals exactly one option" (`match_option`), which let one
  false positive through on train (consecutive, `results-A.md:53`). The extraction prompt tells the model
  to copy numbers "written in the problem", but nothing checks it did. Cost of the solvers on the official
  run: 7 extraction calls × 25 to 41 s on the board (all abstain) for 0 problems gained; acceptable under
  60 s each, but worth stating.
- **Proposal**: in `solve_with_timings`, after `extract`, reject the parameters when any integer parameter
  other than the `kind`/`letter` fields and other than 0 does not occur as a whole number in the problem
  text (`re.search(rf"(?<!\d){n}(?!\d)", text)`), returning `None, spent` ("the model invented a number").
  Add to `tests/test_solvers.py`: a fake extraction with a number absent from the text abstains; one
  with all numbers present proceeds. Update the table in `results-A.md` with today's classifier counts
  for train (1466 eng: 19 / 24 / 2 / 5) and val (3 / 4 / 0 / 0, Catalan 0 because the keywords are
  English), and the cost line "7 extraction calls on val, 25 to 41 s each on the board, all abstained".
- **Impact (jury)**: low-medium. Precision is the solvers' only selling point ("never answers wrong");
  the check makes the claim structural, and the honest coverage line pre-empts the reviewer's question.
- **Effort**: S.
- **Risk**: could reject a correct extraction when the problem writes a number in words ("five
  consecutive"): `consecutive` fired 3 times on train with `count` possibly written in words, so apply the
  check to `sum`/`total`-type fields only, or allow the number words zero to twelve. No INTERFACES.md change.
  Safe before the demo (hint traces come from the same `solve`; a rejected extraction falls back to a
  strategy card, as today when the value matches no option).
- **How to measure**: `python3 eval.py --input data/train.jsonl --limit 0 --languages eng --name solvers-copycheck`
  shows the same `Family solvers: k/1466 routed, k/k correct` line as before with 0 wrong (about 50 LLM
  calls, 25 minutes on the laptop, to be run by the owner, not here).
- **Verified**: ran (the counts); check read-only.

### P8. Stale measurement text (reviewer M1 and three more)
- **Where**: `docs/results-A.md:3-5` ("All board seconds below are estimates ... 11 tok/s, 5.5, 0.25"),
  `results-A.md:74` and `README-final-draft.md:111` ("125 tests"), `results-A.md:88-100` (board baseline
  timing columns measured with the solvers on, reviewer I9), `results-A.md:48-58` (solver table, P7),
  branch `config.env` 405 against `reason-experiments.md` 406 (P3).
- **Problem / opportunity**: a jury member who reads the first paragraph of the results file is told that
  everything is an estimate, then meets real board numbers in Phase 10. The suite has 168 tests (ran),
  not 125. The only board worst-case figure for the letter model (16.0 s) was measured with `SOLVERS=0`
  silently ignored, so its meaning is "no solver fired on those 50", which is true but accidental.
- **Proposal**: rewrite the header: "Seconds marked *(estimate)* come from token counts with the
  constants calibrated on the board on 14 Nov (`BOARD_PREFILL_TPS=11.4`, `BOARD_GEN_TPS=5.6`,
  `BOARD_EMBED_SECONDS=0.12`); seconds marked *(board)* were measured on the UNO Q"; replace "125 tests"
  by "168 tests (1 skipped on macOS)" in both files; in Phase 10 add one sentence "`SOLVERS=0` was not
  honoured in this run (fixed in <commit>); no solver fired on these 50, so the figures are the letter
  model alone"; refresh the solver table (P7).
- **Impact (jury)**: low. Cheap credibility.
- **Effort**: S.
- **Risk**: none. Safe before the demo.
- **How to measure**: `grep -n "estimate" docs/results-A.md | head -3` reads the new header; `grep -rn "125 tests" docs/` empty.
- **Verified**: read only (the test count ran).

## Summary table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | Catch-all per problem; tolerant `id`/`text`/`options` access in `predict.py` | high | S | yes |
| P2 | Honour `SOLVERS=0`; per-problem budget on the solver path; skip calls that cannot fit; accumulate `prompt_tokens` | medium | S-M | yes |
| P3 | Merge and switch on the middle-value rule; identical-unit check; honest README wording incl. Catalan 26.0% | medium-high | S | yes |
| P4 | Move the `sample-1` fixture into `demo_set.json`, read it from `hints.py` | medium | M | yes, with the suite green and rung 3 re-checked in sim |
| P5 | `docs/runs/` with the ids-only CSVs and `ablations.csv`; docs point at them | high | S | yes |
| P6 | Precise determinism statement (per platform; times vary with the cache) and a determinism test | low-medium | S | yes |
| P7 | "Copied, not invented" check in the solvers; coverage table with today's classifier counts | low-medium | S | yes |
| P8 | Stale header, 125→168 tests, the `SOLVERS=0` footnote in Phase 10, 405/406 | low | S | yes |

## Discarded

- **Merge `copilot/votes.py` (value grammar, cyclic-shift votes)**: measured on the branch at 23.5% and
  22.4% on the 281 (no gain), with 6 problems over 60 s for the votes; the code would ship two dead flags
  and 95 lines the jury may read as "we also ask the model five times". Keep the experiment in
  `docs/reason-experiments.md` only.
- **Qwen3.5 2B on the board**: 5 of 281 prompts over 60 s at 2.6 tok/s prefill, about 1.6 GB RAM in place
  of the 0.8B, 26% on 50 against 34% for always D on the same 50. Breaks the 60 s rule.
- **Catalan keyword solvers** (translate `_MATCH` regexes to `edat`, `mitjana`, `consecutius`): the
  extraction prompt and the 0.8B's Catalan are unmeasured; the English solvers fire on 0 of 281 anyway, so
  the expected gain is 0 and the cost is up to 7 more 40 s calls. Not worth the risk before the deadline.
- **Switch `LETTER_MODEL=1` back on or ship the bias calibration**: 21.7% and 17.8% on the 281 against
  23.1%; `data_curated/letter_prior.json` is absent, so `BIAS` is `None` and the pipeline is already the
  raw baseline when the flag is on. Nothing to do; the config comment is right.
- **Expose the middle-value rule as a hint ("the answer is rarely an extreme")**: it steers the student
  to one option with 30% precision and teaches no mathematics; it also reveals two options as "unlikely"
  before the student answers. Against the design principle.
- **Un-ignore `results/*` wholesale**: scratch runs with the laptop's path names would land in the public
  tree; P5's explicit copy under `docs/runs/` is safer.
