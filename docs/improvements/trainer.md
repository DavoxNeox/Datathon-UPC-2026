# Adaptive trainer and mastery: review and proposals (14 Nov 2026)

Scope: `copilot/trainer.py`, `copilot/simulate.py`, `tests/test_trainer.py`, the Mastery / trainer sections of
`INTERFACES.md`, `docs/teach-measurement.md`, the trainer lines of `docs/results-A.md`, the unmerged branch
`team/innov-difficulty-8199cc`, and the reviewer's findings I6, I7, I12, M7 (`docs/reviews/review-main-2026-11-14.md`
on `origin/team/review-22fa88`). Everything was run from the worktree at `5cc2ded`; no code or data file was changed.

**Summary**

1. The rules are sound and deterministic (34 tests green, no repeat in 60 steps, path settles in 3 steps on the real
   bank), but the adaptive staircase and the mastery scale fight each other: "one level up after a right answer" makes
   every second answer wrong for a student at their level, so **mastery 4 is unreachable on the topic they practise**
   (threshold students: max mastery 3 after 60 steps, 47 % accuracy), while a **guesser at 20 % reached mastery 4**.
   A 2-up-1-down staircase with "3 of the last 4 right without hints" fixes both (measured: 60 % accuracy, mastery 4-5,
   guessers capped at 2).
2. The one-sentence rule the jury would hear ("mastery is read from the last six answers on the topic") is broken by
   three exceptions: a correct answer after the solution raises 0 to 1 (reviewer I7, reproduced), a failed review
   lowers mastery for exactly one answer and the next wrong answer raises it back (2 -> 1 -> 2, reproduced), and the
   student's "base level" is frozen at the diagnostic, so an improving student jumps 2 -> 5 on a level-3 review.
3. Cold start: the chosen level is used (first problem at L, base level L), but the diagnostic climbs two bands per
   problem (reviewer I6, reproduced: level 0 students meet a level-2 and a level-4 problem; level 6 students get 6, 7, 7),
   topic rotation beats the level when a topic has nothing at that level (angles has 0 problems at levels 0-1), and the
   chain restarts from the last diagnostic problem, not from the student's level (4 more problems above level).
4. Review is "one in five, the worked topic practised longest ago" (reviewer I12 is right): 96 reviews measured, 57-65 %
   fell on the weakest worked topic, median 11 problems since that topic was last seen, no interval rule. A stdlib
   spaced rule (intervals by mastery, in answers not clock time) is 30 lines.
5. SQLite is safe as written (a connection per call, nothing shared across threads, prefetch never touches it; 1 writer
   + 3 readers for 4 s: 1227 writes, 427 reads, 0 errors), the teacher report lacks time on task, hints per correct answer,
   trends and failed problems, the simulator's figures are in no document, and an exhausted bank repeats the **same**
   problem forever (bug).

## What I ran

| command | outcome | kind |
|---|---|---|
| `python3 -m unittest tests.test_trainer` | 34 tests OK, 0.8 s | ran |
| `python3 -m copilot.simulate --bank data --neighbors index --steps 60 --path` | bank 1747 problems, 8 students x 60 steps, 20 s wall; table below; trajectories in the scratchpad (`sim_data_index_60.txt`) | ran |
| scratch `probe_start.py`: `start_student` at level 0, 6 and None on the real bank, 3 student types, first 8 problems | levels/topics/base below (section "Cold start") | ran |
| scratch `probe_rules.py`: exhaustion on a 12-problem bank, rung-4 first answer, failed-review penalty, `derive_mastery` edge cases, 1 writer + 3 reader threads for 4 s, `PRAGMA journal_mode`, column lists | results quoted in the proposals | ran |
| scratch `variant_sim.py`: baseline vs a monkeypatched 2-up-1-down staircase + "3 of last 4" mastery 4, with and without `start_student(level=3)`, plus review-targeting statistics | tables in P1 and P4 | ran |
| `git show origin/team/innov-difficulty-8199cc:docs/difficulty.md`, `copilot/difficulty.py`, `git diff main..origin/team/innov-difficulty-8199cc -- copilot/trainer.py config.env` | read; the branch's own measurement says the trainer hook does not help (kept off) | read only |
| reviewer I6, I7, I12, M7, "What can fail live" | read; I6, I7, I12 reproduced here, M7 confirmed | read + ran |
| `INTERFACES.md` 55-100, 135-165, 195-228; `webapp.py` Session, `teacher()`, `_normalise_report`, routes; `assets/teacher.html`; `python/main.py`; `docs/teach-measurement.md`; `docs/results-A.md` 95-147 | read | read only |
| bank census (Catalan rows of train + val, `topics.get_topic`) | per (topic, level) counts below | ran |

Bank per topic and level (Catalan rows, train + val, 1747 ids):

| topic | L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7 | total |
|---|---|---|---|---|---|---|---|---|---|
| angles | 0 | 0 | 2 | 9 | 13 | 15 | 16 | 20 | 75 |
| areas | 9 | 6 | 22 | 20 | 54 | 60 | 75 | 63 | 309 |
| arithmetic | 55 | 36 | 35 | 31 | 96 | 84 | 63 | 51 | 451 |
| boards | 8 | 7 | 6 | 6 | 19 | 12 | 9 | 9 | 76 |
| counting | 4 | 3 | 2 | 4 | 10 | 11 | 14 | 12 | 60 |
| digits | 14 | 17 | 23 | 25 | 66 | 65 | 86 | 82 | 378 |
| logic | 3 | 2 | 8 | 4 | 10 | 7 | 5 | 7 | 46 |
| spatial | 49 | 35 | 48 | 24 | 71 | 42 | 37 | 46 | 352 |
| all | 142 | 106 | 146 | 123 | 339 | 296 | 305 | 290 | 1747 |

Simulator, real bank, index neighbours, 60 steps (the figures nobody has written in `docs/` yet; `README-final-draft.md:199`
still quotes "about 0.24 s per step (estimate, old constants)"):

| student | acc | settled levels | expected | converged | steps to settle | same topic after fail | topics >=3 | rises to >=3 | max mastery | reviews | repeats | laptop ms/step | emb/step | board s/step (est.) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| threshold2 | 47% | 2-3 | 2-3 | yes | 3 | 100% (22/22) | 1 | 7 | 3 | 14 | 0 | 2.5 | 0.72 | 0.09 |
| threshold5 | 53% | 5-6 | 5-6 | yes | 3 | 100% (26/26) | 4 | 6 | 4 | 4 | 0 | 3.4 | 0.87 | 0.11 |
| random20-1 | 15% | 0-1 | - | n/a | 7 | 92% (35/38) | 0 | 0 | 2 | 15 | 0 | 2.1 | 0.70 | 0.09 |
| random20-2 | 23% | 0-1 | - | n/a | 17 | 92% (33/36) | 0 | 2 | 2 | 12 | 0 | 2.2 | 0.75 | 0.09 |
| random20-3 | 20% | 0-6 (unsettled) | - | n/a | - | 97% (33/34) | 1 | 3 | **4** | 15 | 0 | 2.2 | 0.70 | 0.09 |
| always | 100% | 7-7 | 7-7 | yes | 4 | - | 8 | 8 | 4 | 14 | 0 | 4.2 | 0.68 | 0.09 |
| improving | 67% | 6-7 | - | n/a | 32 | 89% (16/18) | 6 | 6 | 5 | 14 | 0 | 3.1 | 0.72 | 0.09 |
| hints_only | 100% | 7-7 | - | n/a | 4 | - | 0 | 0 | 2 | 8 | 0 | 4.6 | 0.78 | 0.10 |

### Answers to the questions asked

- **Mastery in one sentence.** Today it is almost "mastery is read from the last six answers on the topic: one right
  answer with at most a strategy card is 2, two different problems right with one of them without hints is 3, three
  right in a row without hints is 4, and one of those a level above the student's level is 5". Three exceptions
  break the sentence (P2) and the staircase makes level 4 unreachable in practice (P1).
- **Cold start.** The chosen level is respected for the first problem and for `base_level` (verified: level 0 -> first
  problem L0; level 6 -> first problem L6, `base_level` 6 from the start). The rest is not (P3).
- **Topic with no problems at a low level.** `_choose_diagnostic` picks the topic first and `candidates()` relaxes the
  level, so an `angles` turn at level 0 serves a level-2 problem (reviewer I6's `Mar`); only when the topic has
  nothing at any level does it fall to any topic at the exact level (`trainer.py:388`). After the diagnostic the same
  relaxation applies to a wrong answer on `logic` at level 1 (2 problems): the next problem is level 0 (3 problems),
  then any topic one level down (`trainer.py:420-423`), so the student leaves the topic after two misses.
- **Review.** Random 20 % of steps, then the worked topic with the oldest `updated_at`, not by mastery and with no
  interval (P4).
- **Use of the start-screen level.** `webapp.Session.start` passes it to `start_student`; diagnostic at
  L, L+2, L+4, L+6, L+7 clamped (`diagnostic_levels(6) = (6, 7, 7, 7, 7)`, `(7) = (7, 7, 7, 7, 7)`: no information at the
  top), base = highest passed, else L-1.
- **Teacher report.** Per student: `base_level`, `start_level`, `diagnostic_done`, totals (answers, correct, reviews),
  per topic (mastery, practice level, target level, answers, correct, correct at rung 0), per level (answers, correct).
  Missing: seconds per problem (nothing is stored; `pending.issued_at` is deleted on answer), hints per correct answer
  (the `hint_rung` column exists but is only used as "rung 0 or not"), any trend, the list of failed problems, the
  diagnostic's outcome. "Failed twice" cannot happen: a problem is never served twice while the bank has unseen
  problems. The web page also drops `by_topic` (`webapp._normalise_report` passes only `mastery`, `by_level` and five
  scalars; `assets/teacher.html` renders two tables plus rung 0). (P6)
- **Repeats.** Never while unseen problems remain (`_seen_ids` includes `pending`; 0 repeats in 60 steps on 1747
  problems). When everything is seen, `_least_recent` returns the first answer's problem **every time** (verified on a
  12-problem bank: steps 13-20 were all the same id). This bites the `stub` bank (5 sample problems) at once. (P5)
- **After 100+ answers.** Mastery only ever reads the last `WINDOW = 6` answers per topic (100 wrong then 3 right at
  rung 0 -> mastery 4), so a long history is forgotten quickly, which is defensible ("current state"). Costs grow
  linearly (`_topic_history`, `_seen_ids` are full scans per call) but at 2-4 ms per step on the laptop this is not a
  board concern before thousands of answers. `test_review_rate_is_about_one_in_five` already runs 105 steps.
- **SQLite and threads.** `sqlite3.connect(path)` per call, closed in `finally`; no connection crosses a thread, so
  `check_same_thread` never matters; journal mode `delete`, default 5 s busy timeout; `executescript(SCHEMA)` on every
  connect (`CREATE TABLE IF NOT EXISTS`, cheap). `hints.prefetch` threads touch `data/index.db` and the LLM, never
  `students.db`. The web session holds `Session.lock` around every trainer call except `Session.teacher()`
  (`webapp.py:375-390`), which runs on a `ThreadingHTTPServer` thread concurrently with `record_answer`. Measured: 1
  writer + 3 reader threads for 4 s, 1227 writes and 427 reads, 0 errors. Safe; small hardening in P8.
- **What the simulator proves.** With deterministic students it proves the rules: the path settles in 3 steps inside the
  expected band for threshold students, wrong answers stay on topic 100 % on the main path, 0 repeats, hints-only
  students cap at mastery 2, and a step costs about 0.1 s on the board. It does not prove learning (students have fixed
  thresholds), it does not exercise `start_student(level)` at all, it does not model hints affecting correctness, it
  does not use B's embedding retrieval (index stop-gap), the "improving" student's path is governed by the `improving`
  formula not by teaching, and the 20 % guessers show the scale's false positives rather than hide them (random20-3:
  mastery 4). The difficulty branch's own doc says `DIFFICULTY_ADJUST=1` does not help simulated students (28/27/27 wrong
  vs 29/29/26) and keeps it off: nothing to merge into the trainer, only `report()` for the teacher.

## Proposals

### P1. Staircase 2-up-1-down and mastery 4 = "3 of the last 4 right without hints"
- **Where**: `copilot/trainer.py:405-424` (`_choose_adaptive`), `:309-329` (`derive_mastery`), `:96-97` (`WINDOW`, `STREAK`),
  docstring `:30-34` and `:64-65`; `INTERFACES.md:58-69` (Mastery table wording); `tests/test_trainer.py:114-121, 41-48, 170-175`;
  `docs/project-hub-draft.md:65`, `docs/README-final-draft.md:27`.
- **Problem / opportunity**: "correct -> one level up" guarantees that a student exactly at level N alternates
  N ok, N+1 KO, N ok, N+1 KO (threshold2 trajectory: steps 7-21 are exactly that). Mastery 4 needs "the last 3 answers
  correct at rung 0" (`trainer.py:322-324`), which the staircase never allows on the practised topic: threshold2 and
  threshold5 end 60 steps with max mastery 3 and 4 (the 4 came from a review at level 4), accuracy 47-53 %. Meanwhile
  random20-3 (20 % correct) reached mastery 4 on `arithmetic` at step 47 with three lucky rung-0 answers at levels 0-2.
  A student who is always right only sees 3 in a row at the level-7 ceiling. So the LED bar that the jury watches cannot
  reach 4 for a normal student, and can for a guesser.
- **Proposal**: (a) in `_choose_adaptive`, go one level up only when the last two main-path answers are correct;
  after a single correct answer serve a neighbour at the same level, any topic (`_neighbors(..., level_delta=0,
  same_topic=False)`, filtered to `p["level"] == level`, fallback `bank().candidates(level, None, exclude=seen)`);
  wrong stays "same topic, one level down". (b) in `derive_mastery`, mastery 4 when at least 3 of the last 4 answers
  are correct at rung 0 on 3 distinct problems (keep the 3-rule and the half-window rule as they are); mastery 5 when one of
  those is at `base_level + 1` or above. Update the docstring, the INTERFACES table ("4: three of the last four right
  without hints"), `test_correct_goes_one_level_up...` (expect same level after one correct, +1 after two),
  `test_three_clean_in_a_row_is_four` (3 of 4), `test_review_resumes_the_main_path`.
- **Impact (jury or student)**: high. Measured with the monkeypatched variant on the real bank (scratch `variant_sim.py`):

  | student | acc before -> after | band | max mastery before -> after | rises to >=3 before -> after |
  |---|---|---|---|---|
  | threshold2 | 47% -> 60% | 2-3 both | 3 -> 4 | 7 -> 8 |
  | threshold5 | 53% -> 68% | 5-6 both | 4 -> 5 | 6 -> 5 |
  | random20-1/2/3 | 15/23/20% -> 12/10/20% | 0-1 / 0-1 / 0-6 unsettled -> 0-1 / 0-0 / 0-0 | 2/2/4 -> 2/2/2 | 0/2/3 -> 0/0/2 |
  | improving | 67% -> 77% | 6-7 -> 7-7 | 5 -> 5 | 6 -> 7 |
  | hints_only | 100% both | 7-7 | 2 -> 2 | 0 -> 0 |

  Same convergence (3 steps), fewer failures for the student (a 50 % failure rate is demotivating for a minor), the
  mastery scale becomes reachable and guess-proof.
- **Effort**: M.
- **Risk**: changes the demo sentence "a right answer brings a problem one level up" (`results-A.md:132-135` verified
  the old flow on the board) and INTERFACES.md's mastery wording; 3 tests to rewrite. Do it before the demo only if the
  rehearsal is re-run in sim mode; otherwise the morning after.
- **How to measure**: `python3 -m copilot.simulate --bank data --neighbors index --steps 60`: threshold2 accuracy >= 58 %,
  max mastery >= 4 for threshold2 and threshold5, max mastery <= 2 for every random20, band unchanged.
- **Verified**: ran (monkeypatched variant, tables above).

### P2. One mastery sentence with no exceptions: fix I7, drop the one-answer review penalty, align M7
- **Where**: `copilot/trainer.py:525-528`, `:36-37` (docstring), `:623-625` (`mastery_scale`); `INTERFACES.md:58-69, 83`;
  `assets/teacher.html:42` legend; `tests/test_trainer.py:152-162`.
- **Problem / opportunity**: three deviations from "mastery is a function of the last six answers on the topic":
  (1) reviewer I7, reproduced: first answer correct at rung 4 gives `mastery 0 -> 1` because `trainer.py:526` only caps
  when `before` is non-zero; the legend then says "sempre falla" for a student who just answered right. (2) The
  failed-review penalty (`:527-528`) is applied to the returned value only; the next answer recomputes from history.
  Reproduced: failed review on `arithmetic` 2 -> 1, then a **wrong** non-review answer on the same topic 1 -> 2. A wrong
  answer raised the LED bar. (3) M7: mastery 2 is "correct with hints" in INTERFACES but is given after one correct
  answer without hints; INTERFACES does not mention the review rule.
- **Proposal**: in `record_answer` replace lines 525-528 with nothing but `after = derive_mastery(...)` and make
  `derive_mastery` the single source: it already ignores rung 3-4 answers for the rise and counts them in the window,
  so the failed review is already a wrong answer in the window. If a penalty for failed reviews is wanted, make it
  part of the history (store `review` in the rows `_topic_history` returns and count a wrong review as two wrong
  answers in `recent`), not a post-hoc `min`. Rename the scale: 1 "started: no right answer yet / ha començat",
  2 "right once (hints allowed) / un encert", keep 3-5. Update the INTERFACES table, the docstring, `mastery_scale`,
  the teacher legend, and add `test_rung_four_first_answer_keeps_zero` and `test_failed_review_penalty_is_not_undone_by_a_wrong_answer`
  (or delete `test_review_is_flagged_and_a_failed_review_lowers_mastery`'s penalty assertion if the penalty goes).
- **Impact (jury or student)**: high: the jury hears one sentence and can check it on the LED matrix; today a live
  "show the solution then answer" raises the bar.
- **Effort**: S.
- **Risk**: INTERFACES wording only; one test changes. Safe before the demo (the demo flow is unchanged).
- **How to measure**: `python3 -m unittest tests.test_trainer`; in sim mode: solution, correct answer -> mastery stays 0.
- **Verified**: ran (both reproductions).

### P3. Diagnostic that respects the chosen level and does not restart above it (reviewer I6)
- **Where**: `copilot/trainer.py:99-100` (`DIAGNOSTIC_LEVELS`, `DIAGNOSTIC_MIN`), `:375-390` (`diagnostic_levels`,
  `_choose_diagnostic`), `:434-438`, `:456-462` (`last` after the diagnostic), `:514-523`; `tests/test_trainer.py:102-112, 221-246`;
  `INTERFACES.md:155-158`.
- **Problem / opportunity**: reproduced on the real bank (scratch `probe_start.py`): start level 0, all wrong:
  levels 0, 2, 4, then review L0, then the chain from the last diagnostic problem: 3, 2, 1, 0 (four more problems above
  the student). Start level 0, right up to level 1: 0 ok, 2 KO, 4 KO, base 0, then 3, 2, 1 (three problems above).
  Start level 6: 6, 7, 7 (two of three at the top band); start level 7: 7, 7, 7 (no information). Topic rotation
  beats the level (`:388`): `angles` has no problem at levels 0-1, `counting` 4 and 3, `logic` 3 and 2, so a level-0
  diagnostic turn on those topics serves a level-2 problem. The reviewer's "What can fail live" 2 says the jury will
  only see the diagnostic in three minutes.
- **Proposal**: (a) with a teacher-chosen level probe `(L, L+1, L-1)` clamped, exactly three problems, base = highest
  passed, else L-1 (keep `(0, 2, 4, 6, 7)` only for `start_level is None`); (b) in `_choose_diagnostic` try
  `bank().at_level(level, topic, seen)` then `bank().at_level(level, None, seen)` before `candidates()`, so the exact
  level wins over the topic; (c) when `_diagnostic_finished` fires, insert into `topic_state` nothing but set the
  student's `base_level`, and in `next_problem` when the last main-path answer belongs to the diagnostic (`id <=` the
  diagnostic's last row, or a new `answers.diagnostic` flag), start the chain at `target_level(base, 0)` with
  `bank().candidates(base, None, exclude=seen)` instead of `_choose_adaptive(last)`. Tests: `diagnostic_levels(6) ==
  (6, 7, 5)`, level-0 all-wrong student never sees a level > 1 in the first 8 problems, first diagnostic problem on an
  `angles` turn at level 0 is level 0 of another topic.
- **Impact (jury or student)**: high: the first three problems are what the jury sees; a 10-year-old who picked
  "5è de primària" today meets 1r and 3r d'ESO problems.
- **Effort**: M.
- **Risk**: touches INTERFACES.md (`start_student` paragraph); changes the deterministic paths the tests pin
  (`test_diagnostic_is_three_to_five_increasing_levels`, `test_start_student_level_sets_...`). Safe before the demo if the
  demo pseudonym is re-seeded afterwards (reviewer "What can fail live" 1-2).
- **How to measure**: the scratch probe (`start_student(sid, 0)`, all wrong, 8 steps): max level served <= 1;
  `start_student(sid, 6)`: levels 6, 7, 5.
- **Verified**: ran (reproduction); fix read only.

### P4. Review as cheap spaced repetition (reviewer I12), deterministic and in one sentence
- **Where**: `copilot/trainer.py:101` (`REVIEW_RATE`), `:393-402` (`_choose_review`), `:464-467`; `INTERFACES.md:139-150`;
  `docs/README-final-draft.md:27, 291`, `docs/project-hub-draft.md:69-73`; `tests/test_trainer.py:152-175`.
- **Problem / opportunity**: measured on 96 reviews (8 students x 60 steps, real bank): 55-62 fell on the weakest worked
  topic (57-65 %), the gap since the topic was last seen had median 11 problems, min 3, max 36; the trigger is
  `rng.random() < 0.2`. Nothing is spaced and mastery plays no role, while the README and the Project Hub draft say
  "spaced review of weak topics".
- **Proposal**: replace the coin by a due rule in answers (sessions are 10-30 minutes, so clock time is useless):
  `INTERVAL = {1: 3, 2: 5, 3: 8, 4: 13, 5: 21}` main-path answers; for every worked topic other than the current one,
  `due = answers_since_last_seen / INTERVAL[mastery]`; serve a review of the topic with the largest `due >= 1`, at its
  practice level, and none when nothing is due; cap at one review in a row. `answers_since_last_seen` = count of
  `answers` rows with `id >` the topic's last row. Sentence for the jury: "a topic comes back after 3, 5, 8, 13 or 21
  problems, sooner the weaker it is". Keep `review: True` in the result. Tests: a topic at mastery 1 comes back within
  4 problems; a topic at mastery 4 does not come back before 13; no two reviews in a row; the share of reviews stays
  10-30 % over 105 steps (reuse `test_review_rate_is_about_one_in_five`). Update the two docs to the new sentence,
  or, if this is not done, to the honest one ("one problem in five revisits the topic practised longest ago").
- **Impact (jury or student)**: medium: it makes a claimed feature true and explainable; for the student it brings weak
  topics back sooner.
- **Effort**: M.
- **Risk**: deterministic paths change (`test_deterministic_for_the_same_student_id` still holds); INTERFACES only gains a
  sentence. Safe before the demo (reviews are invisible to the student).
- **How to measure**: the scratch statistic above: reviews on the weakest worked topic >= 80 %, median gap for mastery-1
  topics <= 4, for mastery-4 topics >= 13.
- **Verified**: ran (measurement); rule read only.

### P5. An exhausted bank repeats the same first problem forever
- **Where**: `copilot/trainer.py:427-431` (`_least_recent`), `:470-471`; `tests/test_trainer.py:183-189`.
- **Problem / opportunity**: `SELECT problem_id FROM answers WHERE student_id=? ORDER BY id LIMIT 1` is the student's
  first answer, which stays the oldest row after it is answered again. Reproduced on a 12-problem bank, 20 steps: steps
  13-20 served the same id eight times. `test_repeats_only_when_the_bank_is_exhausted` asserts `len(ids) == 15` and
  misses it. With the `stub` bank (5 sample problems) or the demo set this happens within minutes.
- **Proposal**: `SELECT problem_id FROM answers WHERE student_id=? GROUP BY problem_id ORDER BY MAX(id) LIMIT 1`
  (the problem whose most recent answer is the oldest), and extend the test: `ids[12:20]` has 8 distinct ids and equals
  `ids[:8]` in the order of first answering.
- **Impact (jury or student)**: medium (low on 1747 problems, high in stub/demo mode and for a weak student stuck on a
  small topic-level cell such as `logic` level 0-1 once P3's "exact level first" makes cells bind).
- **Effort**: S.
- **Risk**: none; no interface change. Safe before the demo.
- **How to measure**: the extended test; the scratch probe's "ids 13..20" line shows 8 distinct ids.
- **Verified**: ran (bug); fix read only.

### P6. Teacher report: time on task, hints per right answer, trend, failed problems, and show `by_topic` on the page
- **Where**: `copilot/trainer.py:117-129` (schema), `:177-189` (`_connect` migration pattern), `:485-534`
  (`record_answer`), `:580-626` (`teacher_report`); `copilot/webapp.py:397-418` (`_normalise_report`); `assets/teacher.html:26-33, 70-89`;
  `docs/teach-measurement.md:17-19` (asks for seconds per problem but points at the 12-row `timeline`).
- **Problem / opportunity**: the report has mastery, counts and "correct at rung 0" per topic and level, nothing else.
  A teacher cannot see (1) seconds per problem (nothing stored; the people protocol in `teach-measurement.md` relies on
  the page's 12-entry `timeline`), (2) hints per right answer (`hint_rung` is stored but only tested `== 0`), (3) whether
  a topic is improving (mastery is a point value), (4) which problems were failed and at what level, (5) the diagnostic's
  result in words. The page drops `by_topic` entirely.
- **Proposal**: (a) add `seconds REAL` to `answers`, migrated like `start_level` (`:186-188`), filled in `record_answer`
  with `now - pending["issued_at"]` (NULL when no pending), and report `median_seconds` per student and per topic;
  (b) per topic add `rung_mean_on_correct`, and `hints: {"0": n, "1-2": n, "3-4": n}` over correct answers;
  (c) per topic `trend`: `derive_mastery(history[:-WINDOW//2])` vs now, reported as -1/0/+1 ("baixa / igual / puja");
  (d) `failed: [{"problem_id", "level", "hint_rung", "review"}]` for the last 10 wrong answers (ids only, no text, so the
  licence is respected); (e) `diagnostic: {"levels": [...], "correct": [...]}` from the first rows. (f) In
  `_normalise_report` pass `by_topic` through as `out["by_topic"][name]` and in `teacher.html` render one row per topic
  per student (mastery, trend arrow, right/answers, hints per right answer, median seconds). Tests: `teacher_report`
  keys present, `seconds` within 0-60 after a `next_problem`/`record_answer` pair, `failed` ids are the wrong ones.
- **Impact (jury or student)**: high for the "teacher" part of the Teach track: these are the four numbers a teacher
  asks for, and (a) is also what `docs/teach-measurement.md` needs to report seconds per problem from the board.
- **Effort**: M (trainer S, web + page M).
- **Risk**: schema migration on an existing `students.db` (same pattern as `start_level`, tested in
  `test_old_database_without_start_level_is_migrated`); the `/api/teacher` shape only gains keys. Safe before the demo.
- **How to measure**: `python3 -c "from copilot import trainer; import json; print(json.dumps(trainer.teacher_report(), indent=1))"`
  shows `median_seconds`, `trend`, `hints`, `failed` for the demo pseudonym; the teacher page shows a per-topic table.
- **Verified**: read only (columns verified by `PRAGMA table_info`).

### P7. Base level that follows the student, so target level and mastery 5 mean something
- **Where**: `copilot/trainer.py:514-523` (base set once), `:327-328` (mastery 5), `:332-334` (`target_level`), `:400`;
  docstring `:39-44`; `INTERFACES.md:155-158`.
- **Problem / opportunity**: `base_level` is written once at the end of the diagnostic and never again. The `improving`
  student failed the diagnostic (base 0), then at step 30 a level-3 review on `counting` took it `2 -> 5` ("one level
  above the student's level" is true of any level >= 1 forever) while it was working at levels 4-5. At base 7
  (`always`, or any student who passes the diagnostic) mastery 5 is unreachable (`derive_mastery` of three clean level-7
  answers with base 7 = 4, base 6 = 5). `target_level`, used for reviews without a practice level and in the report, is
  stale for the same reason.
- **Proposal**: recompute the student's level after every main-path answer as the median level of the last 10 main-path
  answers (`SELECT level FROM answers WHERE student_id=? AND review=0 ORDER BY id DESC LIMIT 10`), stored in
  `students.base_level`, and let the diagnostic only seed it. Mastery 5 then reads "right without hints at a level above
  where the path has settled"; for a settled band N..N+1 that is N+2 or an N+1 answer when the median is N. Tests: the
  improving student's base rises with its threshold; `always` reaches base 7 and mastery 5 stays reachable only via
  levels above the median (so at 7 it is 4, documented). Teacher report: add `level_now` next to `base_level`.
- **Impact (jury or student)**: medium: it removes the 2 -> 5 jump a jury member could see on the LED bar and gives the
  teacher a live level.
- **Effort**: M.
- **Risk**: INTERFACES (`start_student` text) and the docstring; `test_start_student_level_sets_the_diagnostic_and_the_base_level`
  checks `base_level` after the diagnostic (still true). Safe before the demo only together with P3; otherwise after.
- **How to measure**: simulator: `improving` never rises more than one mastery step per answer; `rises to >=3` unchanged
  for threshold students; add a `base_level` column to the simulator row.
- **Verified**: ran (reproductions); rule read only.

### P8. Simulator: exercise `start_student(level)`, guard against false rises, and publish the figures
- **Where**: `copilot/simulate.py:200-217` (`run_student`), `:319-360` (`main`), `:283-288` (columns);
  `docs/results-A.md` (no simulator figure anywhere; the trainer appears only at 132-135), `docs/README-final-draft.md:199`
  ("0.24 s per step, estimate, old constants"), `docs/teach-measurement.md:3`.
- **Problem / opportunity**: the simulator never calls `start_student`, so the demo path (start screen with a level) is
  unmeasured; nothing in `docs/` carries the simulator table although the README draft cites it; the README's 0.24 s is
  stale (0.09-0.11 s estimated now, 2-5 ms of Python on the laptop plus 0.7-0.9 neighbour calls at 0.12 s). The
  "false rise" of a guesser to mastery 4 (random20-3) is visible in the table but no test guards it.
- **Proposal**: add `--start-level N` (calls `trainer.start_student(name, N)` before the run) and a `base_level`
  column; add `tests/test_trainer.py::test_guessers_never_reach_mastery_four` on the synthetic bank (three random20 seeds,
  60 steps, `max_mastery <= 3`; it fails today on the real bank and should pass after P1); paste the table above and the
  `--start-level 3` table into `docs/results-A.md` under a "Trainer on simulated students" heading with the exact
  command and the honest list of what it does not prove (section above); fix `README-final-draft.md:199`.
- **Impact (jury or student)**: medium: "measure before/after" is a jury criterion and the before table exists only in a
  scratch file.
- **Effort**: S.
- **Risk**: none for the board. Safe before the demo.
- **How to measure**: `python3 -m copilot.simulate --bank data --neighbors index --steps 60 --start-level 3` prints the
  table; the new test is green.
- **Verified**: ran (both tables exist in the scratchpad: `sim_data_index_60.txt`, `variant_sim.py` output).

### P9. SQLite hardening (no bug found): busy timeout, schema once, and the teacher endpoint under the lock
- **Where**: `copilot/trainer.py:177-189` (`_connect`); `copilot/webapp.py:375-390` (`Session.teacher`).
- **Problem / opportunity**: nothing is wrong today (measured 0 errors with 1 writer + 3 readers for 4 s; connection per
  call; the prefetch thread never opens `students.db`). Two things could bite on a slow SD card: the default 5 s busy
  timeout with journal mode `delete` while `record_answer` commits, and `executescript(SCHEMA)` + `PRAGMA table_info` on
  every call (both fine at 2-4 ms per step on the laptop, unmeasured on the board). `Session.teacher()` is the only
  trainer call outside `Session.lock`.
- **Proposal**: `sqlite3.connect(path, timeout=10)`; run `executescript(SCHEMA)` and the `start_level` migration once per
  process per path (a module-level `set` of initialised paths; `configure()` clears it); optionally `PRAGMA
  journal_mode=WAL` set once (two extra files next to `students.db`, both git-ignored by the `*.db` rule? check `.gitignore`
  for `-wal`/`-shm`); wrap `Session.teacher()`'s report call in `with self.lock`. Add a threaded test (writer + reader,
  2 s, no exception) to `tests/test_trainer.py`.
- **Impact (jury or student)**: low.
- **Effort**: S.
- **Risk**: WAL adds files the board's `deploy-board.md` does not mention; without WAL the change is invisible. Safe
  before the demo (timeout and lock only); leave WAL for after.
- **How to measure**: the threaded test; `python3 -m copilot.simulate --bank synthetic --steps 200` laptop ms/step
  unchanged or lower.
- **Verified**: ran (concurrency and PRAGMA).

## Table

| n | title | impact | effort | safe before demo |
|---|---|---|---|---|
| P1 | Staircase 2-up-1-down and mastery 4 = 3 of the last 4 right without hints | high | M | yes only with a sim-mode rehearsal; otherwise no |
| P2 | One mastery sentence: fix I7, drop the one-answer review penalty, align M7 | high | S | yes |
| P3 | Diagnostic respects the chosen level and restarts at the student's level (I6) | high | M | yes, re-seed the demo pseudonym |
| P4 | Review as cheap spaced repetition in answers (I12) | medium | M | yes |
| P5 | Exhausted bank repeats the same first problem forever | medium | S | yes |
| P6 | Teacher report: seconds, hints per right answer, trend, failed problems, `by_topic` on the page | high | M | yes |
| P7 | Base level follows the student (mastery 5 and target level) | medium | M | only with P3; otherwise no |
| P8 | Simulator: `--start-level`, guessers test, publish the table in results-A | medium | S | yes |
| P9 | SQLite hardening: timeout, schema once, teacher under the lock | low | S | yes (WAL after) |

## Discarded

- **Merge `DIFFICULTY_ADJUST=1` into the trainer** (branch `team/innov-difficulty-8199cc`): the branch's own
  measurement shows no gain (28/27/27 wrong answers against 29/29/26) and a slower step (3 -> 10 ms with a 3000-answer
  history); the trainer hook amplifies guessing noise as the doc says. Only `difficulty.report()` for the teacher is worth
  merging, and that is outside the trainer.
- **Spaced repetition by wall-clock intervals (1 day, 3 days, ...)**: sessions on the board are 10-30 minutes and the
  demo is 3 minutes; the `created_at` timestamps exist but a day-based schedule would never fire. Counting answers (P4)
  keeps the idea and works within a session.
- **Repeating a failed problem later so the teacher can see "failed twice"**: it conflicts with "never serve a seen
  problem" (`trainer.py:66`), which the tests and the README promise, and with the leak risk (the solution was shown at
  rung 4). P6 lists failed problems instead.
- **Any LLM involvement in choosing the next problem or judging mastery**: breaks the design principle (the LLM never
  reasons) and the 60 s budget (one rung-3 hint is 28 s on the board).
- **Storing anything about the student beyond the pseudonym (age, class) to set the start level**: minors, no personal
  data (`test_no_personal_data_columns`); the start-screen level already carries what is needed.
