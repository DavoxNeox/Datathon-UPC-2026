# Review of `origin/main` at `2dbfbf5` (14 Nov 2026)

Reviewer role: critical reviewer. Nothing here was changed in code; this file is the only
deliverable. Every finding names the file and line, how it was reproduced, why it matters for
the jury or the student, and a concrete fix. Findings are ordered by severity:

- **CRITICAL**: breaks a rule (M3Kang data in git, non-stdlib dependency, the answer leaks to
  the student, over 60 s or the RAM, non-deterministic, an unmeasured number presented as measured).
- **IMPORTANT**: damages the demo, the pedagogy or the credibility of the figures.
- **MINOR**: everything else worth fixing.

**Executed** (laptop, shared llama-servers, Python 3.14; the board runs 3.13): the test suite,
the `predict.py` smoke test, the web app in sim mode on port 7005 driven with `curl`, 34
hand-written leak-filter cases, the hint ladder on a solver problem, a trainer determinism run,
`eval.py --limit 50` to reproduce the 50-problem baseline, four live LLM hints on `areas`
problems, and seven figures of the docs recomputed from `val.jsonl`, `train.jsonl` and
`data_curated/`. **Only read**: `copilot/simulate.py`, `copilot/hal/led.py`, `board/`,
`laptop/`, the deploy guides, the references of the Project Hub draft.

## Executive summary

1. The repository is clean of M3Kang data in the tree and in the whole history; the board code is
   stdlib-only and the guard sees it; `predict.py` answers at once and never over 60 s (worst
   measured path about 42 s estimated). The hard rules hold.
2. Eight commits on `origin/main` carry a `Co-Authored-By` trailer naming the tool, and one
   committed file (`data_curated/hint_quality.json`) names it too. This violates the team's own
   rule and reaches the public repository.
3. The hint ladder leaks nothing by accident, but **the app gives the answer away by design**: one
   wrong click shows the correct letter, and `/api/solution` reveals it with one unconfirmed GET
   before any attempt. The jury's criterion is "guide without revealing".
4. Rung 1 is not what the docs promise: the "easier solved neighbour" is a second **unsolved**
   problem (label stripped, no solution shown), often of the same level.
5. The leak filter misses compound number words, "dozen / half / pair / double", ordinal references
   to the letter and Roman numerals: 24 of 34 adversarial hints passed. The LLM rung is open for
   `areas` in English on the strength of **one** judged sample, and the English hints it produces
   restate the problem's question (verified live, 28 s of board time each).
6. The trainer is deterministic and robust to unknown students, but the diagnostic serves a
   level-2 problem to a student who chose "5è de primària", probes levels L+2 and L+4 whatever
   the chosen course, and after the diagnostic the chain continues from the last (hardest) problem.
7. **Starting a pseudonym wipes its history**: `/api/start/{student}/{level}` and
   `/api/student/{student}` call `start_student`, which resets. A returning student loses
   everything, and the "mastery lives on the board" and "spaced review" claims cannot be true.
8. The figures I recomputed match (always-D 65/281, level and topic counts, visual shares, 38/50
   topic agreement, 15/50 board baseline). But the documented `SOLVERS=0` switch does nothing, so
   the "baseline" timings were measured with the solvers on, and my rerun of the documented command
   gives mean 13.1 s / worst 54.4 s against the documented 9.1 / 16.7 s.
9. The Teach track has **no measured learning number**: `docs/teach-measurement.md` is a protocol
   that was never run. The jury asks for a before/after figure.
10. The public repository will contain no results CSV (`results/` is git-ignored), so the README's
    "all runs are in `results/ablations.csv`" is false for every reader.

## Findings

### CRITICAL

**C1. Tool attribution in eight commits on `origin/main` and in a committed file.**
`git log origin/main --format='%b' | grep -ci 'co-authored-by: claude'` → 8 (for example `18b414f`,
`2ede686`; also on `origin/trainer`: `515423a`, `79c6897`, `f0d504d`). `data_curated/hint_quality.json:40`
reads `"judge": "D draft (Claude, 2026-11-14) - the team must redo it"`. The team rule is no tool
mention in commits or files, and the repository goes public. *Fix:* rewrite the trailer out of
the affected commits before publishing (`git filter-repo --message-callback` or an interactive
rebase on a fresh clone, coordinated by the controller since every branch descends from them);
replace the `judge` string with the judge's initials.

**C2. `/api/solution` reveals the answer with one unconfirmed GET, before any attempt.**
`copilot/webapp.py:202-209`, `assets/app.js:158` (no `confirm()`), route at `webapp.py:320`.
Reproduced: `curl /api/start/Mar/0; curl /api/solution; curl /api/state` → `{"kind": "solution",
"label": "E", "value": "△OOO"}` with no answer given; then `curl /api/answer/E` → `correct: true`,
`mastery_after: 1`. The challenge text says the copilot "guides the student without giving away
the answer"; a 10-year-old finds this button in seconds. The rung-4 bookkeeping (no mastery past 1)
does not change what the student saw. *Fix:* require at least one answer, or rung 3 reached, before
`solution()` accepts; add a confirmation on the page; make the endpoint POST.

**C3. A wrong answer shows the correct letter at once, with no second attempt.**
`copilot/webapp.py:175-176` ("No és això. La resposta era D."), `assets/app.js:90` highlights the
right button, `app.js:96` disables the hint button once answered. Reproduced on `/api/answer/A`.
So the ladder is only reachable *before* answering; after a mistake the student is told the answer
and cannot use a hint to recover. This is the opposite of the Bastani et al. design the Project Hub
draft invokes (graduated hints instead of answers). *Fix:* on a wrong answer show only "No és
això", offer the next rung, allow one more attempt; reveal the letter only on rung 4 or after the
second miss; record both attempts.

### IMPORTANT

**I1. Rung 1 is an unsolved second problem, not a "solved neighbour".** `copilot/hints.py:186`
strips `label` and attaches nothing else; `INTERFACES.md` ("an easier solved neighbour problem"),
`docs/README-final-draft.md:13,30` and `docs/project-hub-draft.md:46` all say "solved". Reproduced:
the rung-1 payload has `text`, `options`, `image_b64`, no answer and no steps. A student stuck on
one problem now holds two. *Fix:* show the neighbour **with** its answer and, when a solver or the
demo set has one, its steps; otherwise call it what it is ("un problema semblant per comparar") in
the docs and the UI.

**I2. The leak filter misses whole classes of spellings the grammar allows.** `copilot/leak_filter.py:21-37`
covers 0-20, the tens, 100 and 1000 only. Reproduced with 34 hand-written hints: 24 passed, among
them `vint-i-quatre` / `twenty-four` (24), `noranta-nou` (99), `vuitanta-un` (81 cm²), `cent
vuitanta graus` (180°), `una dotzena` (12), `la meitat` / `half` (1/2), `un parell` (2), `el doble
de cinc` (10), `MMXXIV`, `2.024` (thousands separator), `1 0`, `la tercera opció` / `the third
option`, `l'opció del mig`, `la lletra que ve després de la B`, `És la c.` (lower case). The
`HINT_GRAMMAR` (`hints.py:300`) allows letters and hyphens, so every number word above is a
legal model output. The filter also guards the solver traces (`hints.py:240`), where digits do
appear. *Fix:* generate compound Catalan/English/Spanish number words up to 999 from the parts,
add dozen/half/pair/double/third-option/ordinal patterns, normalise `2.024` and spaced digits,
match the lower-case letter after "la" / "the"; add these cases to `tests/test_leak_filter.py`.

**I3. The LLM rung is open on one judged sample, and what it writes is the problem's question.**
`data_curated/hint_quality.json` has `areas: n=1, percent_en=100`; `hints.quality()`
(`hints.py:141-162`) only requires `n` truthy, so `llm_allowed("areas", "eng")` is `True` (verified).
Four live hints on real `areas` validation problems in English: "What is the perimeter of the
smaller square?", "What is the area of the square in the figure?", "What is the total length of
the sandcastle...": the model restates the question. Each costs about 28 s of estimated board
time (two calls, Catalan then English, `hints.py:60`), and the Catalan twin is noise ("ilit ilit
ilit..." up to the 40-token cap). The filter passed all four, correctly: they leak nothing because
they say nothing. *Fix:* require `n >= 10` in `quality()`; until the team judges 10 per topic,
set `percent_en` to 0 or delete the file; on the English page make one call, not two.

**I4. Starting or re-typing a pseudonym erases the student.** `copilot/webapp.py:111-114` calls
`trainer.start_student`, which begins with `reset_student` (`copilot/trainer.py:556`);
`/api/student/{student}` (`webapp.py:96-97`) does the same although `docs/app-lab-app.md` documents
it as "choose the student pseudonym and load their next problem". Reproduced: `Mar` with 2 answers
→ `/api/start/Mar/auto` → `answers: 0`, mastery all 0. Consequences: a returning student restarts
the diagnostic every session; the teacher view shows only the current session; "spaced review"
and "mastery lives in SQLite under a pseudonym" (`README-final-draft.md:27-28`) describe something
the app prevents. *Fix:* `start()` should call `start_student` only when the pseudonym is unknown
(or when the level selector changed), and otherwise continue; keep `/api/reset` as the only reset.

**I5. `/api/reset` is an unconfirmed GET that deletes a student.** `webapp.py:123-146,315`. The
page asks `confirm()` (`app.js:164`) but the server does not: any prefetch, link preview, a
second tab, or a curious student typing the URL wipes the pseudonym's history (reproduced with
one `curl`). *Fix:* POST with a token or a two-step confirm server-side; log the deletion in the
timeline.

**I6. The diagnostic ignores the chosen course and climbs two levels per problem.**
`trainer.py:99` `DIAGNOSTIC_LEVELS = (0, 2, 4, 6, 7)`, `trainer.py:375-390`. Reproduced:
`diagnostic_levels(0) = (0, 2, 4, 6, 7)`, `diagnostic_levels(2) = (2, 4, 6, 7, 7)`; a student who
picked "5è de primària" meets a 1r d'ESO and a 3r d'ESO problem as problems 2 and 3 (the minimum is
three, `trainer.py:434-438`). Worse: the first problem for `Mar` at level 0 was `lvl-2_2020_26`
(level 2, `angles`), because `_choose_diagnostic` rotates topics first and `candidates()` relaxes the
level when the topic has none at that level (`trainer.py:388`; B's index has no `angles` at levels
0-1). And after a failed diagnostic (base level 1) the adaptive chain continued from the last
problem: levels 2, 4, 6 → 5, 4, 3, 2, 1 (determinism run below), five more problems above the
student's level. *Fix:* in the diagnostic prefer the exact level over the topic rotation; when the
teacher picks a level, probe L, L+1, L-1 at most; after the diagnostic, restart the chain at the
target level, not at the last problem.

**I7. "Answers after rung 3 or 4 never raise mastery" is false as stated.** `INTERFACES.md`,
`README-final-draft.md:34-35`, `project-hub-draft.md:47-48`. Reproduced: solution shown, correct
answer at rung 4, `mastery_before 0 → mastery_after 1`; the LED bar grows and the teacher legend
(`assets/teacher.html:42`) reads "1 sempre falla" for a student who just answered correctly, and the
same "sempre falla" after a single wrong answer. `trainer.py:525-526` only caps at `before` when
`before` is non-zero. *Fix:* keep mastery 0 when `before == 0` and the rung is 3 or 4; rename
mastery 1 to "ha començat" / "started" in the legend and INTERFACES, or make 1 mean two misses.

**I8. The topic map is 76% right, so one student in four gets the wrong strategy card and the
wrong neighbour.** `data_curated/topics.json` agrees with the 50 hand labels on 38/50 (recomputed).
Rung 2 (`hints.py:199-210`) and rung 1's `same_topic=True` (`hints.py:180-181`) depend on it with no
fallback. On a wrong-topic problem the "Angles" card appears under a counting problem. *Fix:* say
so in the UI ("Estratègies d'angles", so the mismatch is visible), add a generic card first on every
topic, and report the 24% in the README's limitations.

**I9. The documented `SOLVERS=0` switch does nothing, so the baseline timings were measured with
the solvers on.** `copilot/pipeline.py:21` reads `CONFIG.get("SOLVERS", "1")`, but `config.load`
(`copilot/config.py:19-21`) only honours environment variables for keys present in `config.env`,
and `SOLVERS` is not one. Verified: `SOLVERS=0 python3 -c ...` → `USE_SOLVERS = True`.
`docs/results-A.md:88` documents the board baseline as `LETTER_MODEL=1 SOLVERS=0 eval.py --limit 50
--languages eng`. Rerun of that command here: 15/50 = 30.0% (matches) but mean 13.1 s and worst
54.4 s estimated (documented 9.1 s / 16.7 s laptop, 10.3 s / 16.0 s board). The worst problem,
`lvl-4_2008_22`, is classified `ages`: a 350-token extraction (about 42 s) plus the letter call. The
`ages` solver (`1bd7b4c`, 14:09) predates the board results commit (`f157dff`, 14:45), so either the
board ran older code or the worst-case column is wrong. Also `pipeline.py:89` overwrites
`prompt_tokens` with the letter call's count, hiding the solver's tokens in the CSV. *Fix:* add
`SOLVERS=1` to `config.env` so the override works; rerun the 50-problem baseline on the board with
the solvers really off and replace the timing columns; accumulate `prompt_tokens`.

**I10. No measured teaching outcome.** `docs/teach-measurement.md` is a protocol; no run, no
`results/teach-people.json`, no before/after number anywhere. `README-final-draft.md` §4.2 lists
latencies and "settles in 3 to 4 steps" on simulated students whose answers are a threshold on the
level (`copilot/simulate.py:22,156-176`), which is circular: the simulator is built to converge.
The jury's criterion is a number before and after. *Fix:* run the 30-minute protocol on the board
with the three authors today, report n=15 per condition plainly, and put the JSON (ids only) in
`docs/runs/`.

**I11. The public repository will hold no evidence for the figures.** `.gitignore:7-8` ignores
`results/*`; `README-final-draft.md:164` says "All runs are in `results/ablations.csv`";
`docs/error-analysis.md` cites two CSV file names that are not in the tree. The CSVs contain ids,
letters, times and logprobs, no text, so the license allows them. *Fix:* commit the two 281-problem
CSVs, the board `predictions.csv` and `ablations.csv` under `docs/runs/` (or un-ignore
`results/*.csv`), and point the docs at them.

**I12. "Spaced review of weak topics" is neither spaced nor about weak topics.** `trainer.py:393-402`
picks, with probability 0.2, the worked topic whose last answer is oldest, at its practice level;
no interval schedule, no mastery criterion. `README-final-draft.md:27` and `project-hub-draft.md:72-73`
oversell it. *Fix:* either implement "review the lowest-mastery topic not seen in the last k
problems" or describe the rule as it is ("one problem in five revisits the topic practised longest ago").

**I13. Rung 3 is unreachable as advertised on real problems.** With the Catalan page the LLM gate
is closed for every topic; the four solver families fired on 0 of 281 validation problems
(`results-A.md:64`), and the trainer never serves the hand-traced `sample-1` when real data is
present (`trainer.py:294-297`). So on the demo rung 3 is a second strategy card, indistinguishable
from rung 2 (reproduced: rungs 2 and 3 on `lvl-2_2020_26` were both "Angles" cards). The README
draft and the pitch describe "one step of a worked solution or a one-question nudge". *Fix:* fill
`data_curated/demo_set.json` with hand-written steps for the demo problems and let rung 3 read it
(the template exists, `data_curated/demo_set.template.json`); say in the docs how often each rung-3
source actually fires on validation.

**I14. `sample-1` is answered by a hard-coded fixture inside board code.** `copilot/solvers/__init__.py:49-50,70-80`
returns `_SAMPLE_1` for `id == "sample-1"`, so the smoke test's "5/5 letters" and the trace demo on
the sample rely on a constant, not on the pipeline. A reader of `predict.py` would call this a
back door. *Fix:* move the fixture to `tests/` and to the demo set; let `sample-1` go through the
real solver (its family, `arithmetic_words`, does not exist).

### MINOR

**M1. `docs/results-A.md:3-4` says every board figure is an estimate with the old constants
(11 / 5.5 / 0.25)**, then reports real board measurements from Phase 10 on. Stale header; fix the
first paragraph. Likewise "our 125 tests pass on the board" (`results-A.md:74`,
`README-final-draft.md:111`): the suite now has 149 (1 skipped here).

**M2. The 60 s limit is not enforced on the solver path.** `pipeline.py:53-61` passes no budget;
`llm.extract_json` uses `timeout=60` of HTTP time. Worst estimated case on the 57 classified
problems of train+val is 42 s (`lvl-5_2016_26`, 357 prompt tokens + 60 generated), so it holds today,
but a queued server (the 54 s and 41 s wall times in `results-A.md:99-102`) would push a problem
over 60 s with status `ok`. *Fix:* pass `remaining - MARGIN` to `extract`, as the letter path does.

**M3. Rung-3 prefetch can wait longer than 60 s.** `hints.py:386-391` joins the prefetch thread for
up to 60 s and, if the result is not there, `hints.py:245` starts `llm_hint` again (up to four more
calls of 60 s each) while `busy` stays `True` and the page is frozen (`app.js:89,96`). Reachable
only with the LLM gate open. *Fix:* one budget for the whole rung (`TIME_LIMIT - elapsed`), fall
back to a strategy card when it runs out.

**M4. "Pas 2 de 3" then a strategy card.** The trace head counts the steps to show
(`hints.py:224,233`), but the leak check skips a step that contains the answer (`hints.py:240-243`),
so the student reads "Pas 1 de 3", "Pas 2 de 3" and then a generic card (reproduced on the
consecutive-numbers problem). Fix the count or the wording.

**M5. The timeline footer says "portàtil" on the board.** `app.js:13,25` labels measured time
"laptop"; on the UNO Q the measured column *is* board time, and the jury sees "portàtil 0.004 s ·
placa (est.) –". Use `RUNTIME` to label it "placa (mesurat)".

**M6. `/api/state` ships the neighbour's image on every poll.** 63 KB per response twice a second
with one rung-1 hint (measured), over `adb forward` or Wi-Fi from the board. Serve the neighbour
image from `/api/image/{id}` once, like the problem image.

**M7. INTERFACES vs trainer semantics.** Mastery 2 is "correct with hints" in INTERFACES and the
legend, but `derive_mastery` (`trainer.py:315-321`) gives 2 after one correct answer *without*
hints; INTERFACES does not mention the review rule or the mastery penalty on a failed review
(`trainer.py:527-528`). Align the table or the code.

**M8. Catalan wording in `data_curated/strategies.json`** (all 40 cards read; none gives an
answer; the Catalan is good overall): `logic/0` "tatxa" → "ratlla"; `arithmetic/4` "línia de
nombres" → "recta numèrica"; `arithmetic/2` "operació contrària" → "operació inversa"; `digits/1`
"compta'ls amb cura" is fine. Pedagogically, `counting/1` (paths) states the whole algorithm and
`angles/0,2` and `spatial/2` state facts rather than strategies: acceptable at rung 2, but they
are the only "hint" a student will get after a wrong card topic (I8). Rung-1 text shows "nivell 1"
to a child who was shown school years everywhere else (`hints.py:191`).

**M9. The stdlib guard reads imports only.** `tests/test_stdlib_only.py` would not see
`importlib.import_module("numpy")` in board code; today only `hal/web.py` uses `importlib`, and it
is listed. Add a grep for `import_module(` outside the HAL.

**M10. Unverified claims in the drafts.** `project-hub-draft.md:25` "108 languages" and the
PISA figures (`:18-20`), the NBER working-paper number (`:53`): I could not check them offline;
the draft's own `[[TODO check every reference]]` must be done before publishing. Section 5 of
the README draft is still the sample (`:227-233`) and the `[[TODO]]`s number 20.

**M11. Teacher view is public to the student.** `assets/index.html:17` links to `/teacher`, which
lists every pseudonym's mastery and attempts with no gate. Fine for a demo, worth a sentence in
the privacy paragraph.

## Figures checked

| Claim (where) | How I checked | Result |
| --- | --- | --- |
| Always D = 65/281 = 23.1% on English val (`results-A.md:28`) | counted labels in `val.jsonl` | 65 D of 281 ✓ |
| Level counts 20/17/29/12/62/53/49/39 and always-D per level (`error-analysis.md:65-72`) | recomputed | identical ✓ |
| Topic counts 53/13/55/10/63/6/61/20 and always-D per topic (`error-analysis.md:13-20`) | recomputed from `topics.json` | identical ✓ |
| OCR options 167/114, text_only 123/158 with always-D 20/26% (`error-analysis.md:77-89`) | recomputed | identical ✓ |
| Visual shares areas 86% (309) … logic 15% (46) (`README-final-draft.md:212`) | recomputed on 1,747 English ids | identical ✓ |
| Topic agreement 38/50 (`README-final-draft.md:211`) | `topics.json` vs `topics_manual.json` | 38/50 ✓ |
| Board baseline 15/50 = 30.0% (`results-A.md:93`) | `LETTER_MODEL=1 SOLVERS=0 eval.py --limit 50 --languages eng` here | 15/50 ✓ accuracy; **timing differs** (13.1 / 54.4 s vs 9.1 / 16.7 s), see I9 |
| Organizers' baseline 22.5% (9/40), 8.7 s, 12.7 s (`README-final-draft.md:171`) | `README.md:851` | ✓ |
| Leak filter 3/66 rejected, 1 after retry (`README-final-draft.md:197`) | `results/hints_val.jsonl` is not in the repository | **not reproducible from the tree** |
| Trainer "settles in 3 to 4 steps" (`README-final-draft.md:199`) | read `simulate.py` | circular evidence, see I10 |

## Determinism and robustness (executed)

- Two fresh databases, pseudonym `det`, level 2, the same ten letters: identical sequences of
  problems, topics, reviews and verdicts. Rung 1 and 2 are deterministic; the LLM rung uses
  temperature 0 and seed 42 (3/50 near-ties flipped between platforms per `results-A.md:94`).
- Unknown pseudonym: `mastery_map` returns eight zeros, `next_problem` creates the student and
  starts the diagnostic; `record_answer` for an unknown problem grades against `?` and never raises.
- Path traversal on the sim static server (`/../config.env`, `/%2e%2e/config.env`): 404.
- `/api/state` never carries `label` for the problem or the neighbour (checked keys).
- Tests: 149 run, all pass, 1 skipped on macOS (`test_relay`, needs a second loopback address;
  Linux only). Smoke test: 5 rows, status `ok`, 0.0 s each.

## What can fail live (3-minute demo)

1. Starting the demo pseudonym wipes it (I4), so the LED mastery map is empty for the whole demo
   unless the pseudonym is prepared and never re-started: rehearse with a pre-seeded pseudonym and
   press nothing on the start screen except "Comença" *with the same level*.
2. The diagnostic takes 3 to 5 problems before anything adaptive happens (I6); in three minutes the
   jury will only see the diagnostic. Seed the pseudonym past the diagnostic the day before.
3. Rung 3 will be a second card (I13); do not promise a solver step unless the demo problem is in
   `demo_set.json` and the ladder reads it.
4. A visual problem with no OCR options and no image copied to `data/images` shows bare A-E
   buttons and nothing to look at: check `ls data/images | wc -l` on the board (3,494 expected).
5. One wrong click ends the problem and shows the answer (C3): a presenter who "tests a wrong
   answer" to show the cross cannot then show the ladder on that problem.
6. The footer says "portàtil" on the board (M5); the jury will ask.
7. Both model servers are idle in the Catalan demo; if the pitch claims "the model writes hints",
   switch the page to English on an `areas` problem and expect a 28 s wait for a restated question
   (I3). Better not to claim it.

## In one line

The hard rules (license, stdlib, 60 s, RAM, determinism) are met and documented with real board
numbers, the recomputable figures all recompute, and the code reads cleanly; what needs work is
the gap between what the drafts promise about teaching and what the app does.
