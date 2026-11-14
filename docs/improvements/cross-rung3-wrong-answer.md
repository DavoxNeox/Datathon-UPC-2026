# After a wrong answer, and what rung 3 contains: one design, end to end

Second-round integration, 14 Nov 2026, worktree `team/improvements-d18364` at `4bea6d4` (= `origin/main` `d8f9c66` plus
the eight area reports). Suite: **284 tests OK, 1 skipped** (ran with `STUDENTS_DB` in the scratchpad). Read only, ran
things, changed no code. Merges `hints-pedagogy.md` (all), `web-app.md` P1/P4/P5/P8, `retrieval-topics.md` P1/P2,
`tests-quality.md` P8, `data-licence.md` P2 + addendum, and reviewer C2, C3, I13, M3, M4 (`origin/team/review-22fa88`).
Ids only, never text, never a letter or a value of a real problem.

The area reports were written at `5cc2ded`; main moved twice since. Re-checked here, **already on main**: `copilot/signatures.py`
(merged, shown by `webapp._diagnose` after the reveal, with INTERFACES' own pin measurement "every signature except
`statement_number` pins the correct option: 1176/1381"); rung 3 reads `data_curated/demo_set.json` first (`kind:
"demo_steps"`, `step`, `steps_total`) and rung 4 shows its steps (`source: "demo_set"`); the six demo ids of
`docs/demo/demo-problems.md` are in the set (19 entries, all `draft`, 5 steps each); `HINT_MAX_USES=4` with the fourth press
a **lesson** (`hints.get_lesson`, `HINT_LESSON_ON_LAST=1`, counts as rung 3); letters and option values moved out of
`demo-problems.md` into the ignored `docs/demo/local/`. **Still open** (verified by running): reviewer C3, hints P1, the
leak filter in both directions, the runtime filtering of the demo steps, INTERFACES' kinds, and two label leaks in docs.

**Summary (5 lines)**
1. Verified in sim (`Mariona1`, course 1 -> `lvl-1_2024_2`, then `lvl-3_2019_18`): four presses give neighbour, card,
   **demo step 1 of 4**, lesson; one wrong click still puts `label` into `/api/state`, the message names the letter,
   `hint()` answers `already answered`, `record_answer` is called once with rung 3, 0 LLM calls. The demo script shows only
   rungs 1-2, so the hand-written steps that now exist are never on stage.
2. The error signature must **not** become the rung-3 content before the reveal (hints P3 as written): on val, a
   high-confidence signature read with its direction determines the correct option in 95/95 pairs and a direction-free
   rewording still leaves one candidate in 51/75 relation pairs (68%). `statement_number` (20/95) is the one leak-free key:
   it goes to rung 3 after a miss; the rest stay where main puts them. On the scripted wrong clicks the module says
   `none`/low, so nothing is shown today either way.
3. The leak filter is the shared prerequisite and fails both ways on the sources this theme adds: 75/110 adversarial
   strings pass, 12/40 harmless fail (reran the corpus), 35/339 real glued-unit values pass (tests P8), and with the raw
   options `hints.py` holds it would **wrongly drop 2 of the 152 non-final demo steps plus 4 figure/mistake fields** of
   `lvl-1_2024_8` (`_numbers_in("…cm2")` reads the unit's digit as the value 2; the texts say "two"). Main does not filter
   the demo steps at runtime at all (the solver trace is filtered, the demo step is not), and `test_content.py` strips
   units before calling the filter, so the suite cannot see this.
4. Design: two attempts, label private until the problem is closed, one `record_answer` (attempt 1), second attempt in the
   timeline and a counter file; rung 3 after a miss = `statement_number` diagnosis > demo step > (LLM) > option check >
   card; reveal = rung 4 pushed automatically (demo steps + figure line + the post-reveal signature). The fourth press stays
   the lesson; a miss neither resets nor consumes presses.
5. About 3.75 h of code in five steps; P1, P2, P4 and P7 are safe before the demo (the stage flow does not change);
   P3 changes the pitch at second 60 and needs one rehearsal; option checks and the rung-1 gate wait.

## What I ran

All from the worktree root, data linked, `HINT_PREFETCH=off`, `STUDENTS_DB` in the scratchpad, servers never touched.
Everything was first run at `a1afa6b` and rerun at `4bea6d4` after the fast-forward; the numbers below are the reruns.

| Command / action | Outcome | Status |
| --- | --- | --- |
| `STUDENTS_DB=<scratch>/tests2.db python3 -m unittest discover tests` | 284 tests, OK, 1 skipped, 8.6 s | ran |
| `dev/start_servers.sh --status` | both servers up; `copilot.client.post` patched with a counter in every script: **0** LLM and 0 embedding calls made by me | ran |
| Sim replay, chain B: `Session().start("Mariona1","1")`, five `hint()` + `_compute_hint`, wrong `answer_letter`, `hint()`, `next()`, four more hints | problem `lvl-1_2024_2`; hints `(1,neighbour) (2,strategy) (3,demo_steps step 1 of 4) (lesson,lesson)`, 5th press `no hints left`, `hints_left` 0, `HINT_MAX_USES` 4; `"label"` in `json.dumps(state)`: 0 before the answer, **1 after the wrong answer**; message contains "era la <letter>"; `answer["signature"]` None; `hint()` after -> `already answered`; **`record_answer` called once, `hint_rung_used=3`**; second problem `lvl-3_2019_18`: neighbour, strategy, demo_steps, lesson | ran |
| Six demo ids: `retrieval.neighbors(id,-1,True,"cat",5)[0]["similarity"]`, `get_hint(id,1)`, `llm_allowed(topic, lang)` | 0.935, 0.914, 0.827, 0.810, 0.859, **0.729** (`lvl-5_2022_30`; same-level best 0.771 = `lvl-5_2019_12`); all `easier=True`; the neighbours are the ones demo-problems.md names. LLM gate: Catalan all closed; English open for `areas` only (`lvl-3_2021_20`) | ran |
| `demo_set.json` | 19 entries; `demo_core` = the four script ids, `demo_reserve` = the two reserve ids; all 19 `status: draft`; 4 ids in val (`lvl-0_2015_14`, `lvl-0_2015_17`, `lvl-0_2016_8`, `lvl-0_2019_22`) | ran |
| Leak filter over the demo set: every non-final step (ca+en) through `leak_reason(step, label, options)` with the **raw** options (what `hints.py` holds) and with the unit-stripped options `tests/test_content.py` uses | 152 texts; **raw: 2 dropped** (`lvl-1_2024_8` step 4 ca+en) + its 4 `figure_*`/`common_mistake_*` fields; stripped: 0. Cause: `_numbers_in` on a value whose unit carries a digit yields {value, 2}; the texts contain "dos"/"dues"/"two" | ran |
| `hints.get_lesson` for the 19 demo-set ids, with the candidates re-filtered by hand | 18 get their topic/family lesson; **`lvl-0_2016_6` gets None** because the only `boards` lesson's tiny example uses a number equal to that problem's answer (a correct drop; the page then shows a card with `fallback: "no lesson"`, nothing tells the author) | ran |
| `PYTHONPATH=. python3 <scratch>/leak_adv.py` (explorer D's corpus) | **75/110 adversarial pass, 12/40 harmless rejected** | ran |
| `copilot.signatures.diagnose` on the six demo ids, every distractor | high confidence for **one distractor of `lvl-4_2010_12` only** (`statement_number`); the two wrong clicks the script makes -> `none`/low; `lvl-3_2021_20` -> `None` (English options empty, Catalan values not single numbers) | ran |
| Same over the 281 English val rows | 139 with a numeric correct option; 536 (problem, distractor) pairs; **95 high (18%)**: statement_number 20, minus_one 16, missing_subtract 15, plus_one 14, half 11, missing_add 8, double 6, digits_swapped 3, times_10 1, div_10 1; 56 problems (20%) with >= 1 high | ran |
| Pin test on the 75 relation pairs: options other than the chosen one that satisfy the same family relation in either direction | **exactly one: 51 (68%)**; two: 19; three or more: 5; with the direction stated (as the texts do) the correct option is determined in 95/95 | ran |
| Projection of rung-3 first-press sources on val under the proposed order (demo_steps > option check > card) | Catalan: demo 4, check 119 (parity 44, progression 36, factor 19, magnitude 14, units 6), card 158; English: 4 / 115 / 162. Today: demo 4, card 277 | ran |
| `grep -cE '\| [A-E] \|' docs/content-review.md`; `docs/demo/contingency.md:40` | **19** label rows still there; the contingency row still quotes the correction message with the letter of `lvl-3_2019_18` (data-licence P2 + addendum: half done) | ran |
| INTERFACES.md:109 kinds, :80-81 rung table | kinds still `neighbour | strategy | trace | llm | solution`: `demo_steps` and `lesson` missing; rung 3 and 4 rows do not mention the demo steps | read |
| Read: `copilot/hints.py` (`_rung3`, `_rung4`, `demo_steps`, `get_lesson`), `copilot/webapp.py` (`answer_letter`, `hint`, `_compute_lesson`, `_diagnose`), `copilot/leak_filter.py`, `copilot/trainer.py` (`record_answer`), `assets/app.js` (`renderAnswer`), tests, `INTERFACES.md`, `config.env`, `docs/demo/*.md`, the five reports, reviewer C2/C3/I13/M3/M4 | | read only |

## 1. The problem state machine

```
SHOWN ──Pista (uses 1..3 climb, use 4 = lesson; rung 0 free)──> rung 1 neighbour ─> rung 2 card ─> rung 3 (order A) ─> ...
  │
  ├─ letter, correct ──────────────────> CLOSED: tick, label public, "Molt bé"; Solució offers the explanation
  │
  └─ letter, wrong (attempt 1) ─> record_answer(student, id, letter, self.rung)        <- the ONLY trainer call
        MISSED: cross on the LED, label private, letter marked wrong, tried=[letter],
        message "No és aquesta. Demana una pista o prova una altra lletra.", Pista enabled while hints_left > 0
        │
        ├─ Pista ──> rung 3, order B: diagnosis (statement_number, once) > demo step > (LLM) > option check > card;
        │            the 4th use is still the lesson
        ├─ letter, correct (attempt 2) ──> CLOSED: "Ara sí!", label public, timeline answer2:<L>:right, recovered += 1
        ├─ letter, wrong (attempt 2) ────> CLOSED: label public; rung 4 pushed automatically as the explanation
        │                                  (demo steps or solver trace, figure line first for visual topics, the
        │                                  post-reveal signature of attempt 1 appended); timeline answer2:<L>:wrong
        └─ Solució ──> confirm() ──> CLOSED the same way (allowed only after attempt 1 or rung 3: web P5 / reviewer C2)
```

Source order A (no wrong attempt yet), one item per press: demo step (filtered, survivors counted) > solver trace step on
the **English** row (hints P1) > LLM (gate as today, after hints P8) > option check (hints P4, later) > card. Order B
(after a miss): `statement_number` diagnosis once, then order A. One shared cursor for the demo steps (a miss does not
restart them). Main already has order A minus the filter, the English row and the checks.

**Merged, by file and number.** hints P1 (English row for the solvers), P2 (what is left of it: filter the demo steps
before counting, M4; figure line first in rung 4; `source`), P3 **narrowed to `statement_number`**, P4 (option checks,
after the demo), P6+P7 (filter), P8 (gate on n >= 10, one call; untouched by this design, keep), P11 (`measure_ladder.py`);
web P4 (two attempts, label private), P5 (Solució gated + confirm), P8 (one `log()` line when a source is skipped:
`hint.leak_dropped kind=demo_steps id=… step=n`, and for the lesson `fallback: "no lesson"`); tests P8 (glued units, the
sweep); retrieval P1+P2 as P6 here, after the demo; data-licence P2 + addendum (the two files still open).

**Dropped, and why.** hints P5 (rung 1 as a faded worked example): L, a second answer flow on the page that collides with
the two-attempt letter buttons; after the datathon. hints P9/P10: not this theme. web P1 (20 s LLM budget): the gate is
closed in Catalan for all six demo topics (ran) and no source in order A or B adds a model call; it stays in the web
report. Reviewer C3's "record both attempts": the trainer contract forbids it; section 3 says where attempt 2 goes.
The brief's "signature if numeric and confident" as rung 3: dropped for every relation key (pin rate above); INTERFACES
on main already says the same with its own count.

**Contradictions resolved.**
- *hints P3 (signature before the reveal) vs main (`_diagnose` after it) vs the module docstring.* Main is right for
  75/95 high-confidence pairs. `statement_number` ("your answer is a number written in the statement") says nothing
  about the correct value and eliminates only the option the student already knows is wrong: it is the one key allowed
  before the reveal. All other keys stay as the explanation after the close, now next to the demo steps.
- *web P4 (second attempt) vs the trainer's one `record_answer` per problem.* Attempt 1 is the graded one (mastery is
  about the first honest try, and `pending` is deleted on the first call, `trainer.py`); attempt 2 is practice: a
  timeline row `answer2:<letter>:right|wrong`, a counter file `data/attempts.json` (class `AttemptStats`, the shape of
  `Rung0Stats`: `second_attempts`, `recovered`, per student and session) and `/api/teacher.attempts`. `hint_rung_used`
  is `self.rung` at attempt 1; presses after the miss never reach the trainer (the row is written). The lesson after a
  miss still "counts as rung 3" only in the sense main gives it; the trainer no longer hears about it.
- *`HINT_MAX_USES=4` + lesson on the last press vs "hints still open after a miss".* The cap is per problem; a miss
  neither resets nor consumes a press. Order-B rung 3 is served only through Pista, so a student who spent four presses
  before the miss gets the message and the letter buttons, nothing more; the reveal after the second miss still carries
  the full explanation. In the demo (two presses, then the wrong click) two presses remain: rung 3 (demo step 1 of 4, or
  the diagnosis) and the lesson. A free rung 3 on the miss was rejected: a wrong click must not be a fifth hint.
- *`hint()` refuses after any answer.* Becomes "refuse when `self.answer["closed"]`". `solution()` becomes "allowed when
  `self.answer` or `self.rung >= 3`" with `confirm()` on the page.
- *Rung 4 and the reveal.* Main's `_rung4` already shows the demo steps; add `figure_ca/en` as the first line for visual
  topics and push it automatically after the second miss. For ids outside the set the reveal stays the one-liner plus the
  solver trace when one exists; README limitations say so.
- *Filtering.* Main filters the solver trace step but **not** the demo step (`_rung3` returns it unfiltered). The design
  filters every text source with the raw options and `lang`, and counts "Pas i de n" over the survivors (M4). That is
  why P1 comes first: with today's filter `lvl-1_2024_8` would lose a step and its figure line to a false rejection.

## 2. The leak filter as the shared prerequisite (hints P6 + P7, tests P8, one spec)

**Signature.** `leak_reason(hint, label, options, lang=None) -> None | "value:<option>" | "letter" | "phrase:<match>"`;
`leaks()` unchanged. `lang=None` keeps today's behaviour so callers migrate one by one: `llm_hint` passes `call_lang`;
the demo-step, trace, diagnosis, check and lesson callers pass `"cat"` for `text_ca` and `"eng"` for `text_en`.

**Normalisation, in this order** (steps 2 and 3 fix the two measured directions):
1. Hint: NFKC, fold accents and case (today); any-script digits via `unicodedata.digit(ch, None)`.
2. Hint: a space between a digit and a unit, `re.sub(r"(?<=\d)(" + _UNITS + r")", r" \1", folded)`, `_UNITS` extended
   (`km/h`, `m/s`, `cm3`, `m3`, `cm³`, `years`, `anys`, `€` either side) and **without** the trailing `\b` (tests P8:
   `12cm` -> `12 cm`). `\d{1,3}[.\s]\d{3}` read as one number, `\d[.,]\d` both readings.
3. Option: `_core(value)` strips the units **including digit-carrying ones** (`cm2`, `m2`, `cm3`, `km2`, `m³`) **before**
   `_numbers_in` (the signatures module's `_UNIT_WITH_DIGIT` regex does this; reuse it). Removes the demo-set false
   rejections (2 steps + 4 fields -> 0, ran) and the same class for any lesson or card.
4. Phrases: today's list.
5. Letter: today's patterns + positions (`first|second|third|fourth|fifth|middle|last|smallest|largest` and the Catalan
   and Spanish forms) resolved to a letter by option order or value, the lower-case letter in prose, "not" + the other
   four; the bare-letter end rule not after `vertex|vèrtex|punt|point|angle|costat|side`.
6. Value: core token (today); `_number_words(n, lang)` for 0-999 in the three languages (`vint-i-`, `-anta-`, `-cents`;
   `twenty-four`/`twenty four`/`one hundred and`; `veinti-`, `y`); a `_QUANTITY` table (dozen 12, half dozen 6, pair 2,
   score 20, half 1/2, third 1/3, `double|doble|twice` + word -> 2n, `and a half|i mig` -> n+0.5); ordinals from the
   parts; Roman numerals per token; `a (x|*|·|+|-|/|^|per|by|times) b` evaluated.
7. Text options of several words: every word of length >= 4 present -> leak.
8. Language-aware function words (hints P7): with `lang`, that language's words only; `un|una` only in `un sol|una sola|
   només un|exactament un|un únic`; `deu` not before `ser|haver|de`; `nou` not after a noun or in `de nou`; `cent` not in
   `per cent|percent`; `set` never for `eng`, `once` never for `cat`.

**One corpus, three parts** (`tests/leak_corpus.py`, data only, the filter's own example options 12/15/18/20/24 and C):
- `ADVERSARIAL`: the 110 strings of the explorer's `leak_adv.py` (in this session's scratchpad; classes in hints P6).
  Assertion: every one returns a reason (today 35).
- `HARMLESS`: the 40 strings of hints P7. Assertion: None with their `lang` (today 28).
- `tests/test_leak_filter_val.py`, `@skipUnless(HAS_DATA)`: every val+train correct value, plain and glued to its unit,
  in a Catalan and an English carrier, is caught (ids only; today 35/339 val misses); every demo-set non-final step,
  figure and mistake field passes with the **raw** options (today 6 fail); every lesson passes for every demo-set id
  except where the lesson's example equals the answer (printed, not asserted). False rejections of a plainly written
  wrong option: printed as a number.
- `tests/test_content.py`: drop `_clean_options` once step 3 lands (`test_no_text_gives_the_answer_before_the_last_step`,
  `test_option_values_stay_out_of_the_texts`, `test_lessons_never_hold_a_demo_answer`), so the content tests call the
  filter the way `hints.py` does.

**Order.** Filter -> runtime filtering of the demo steps and the other sources -> two attempts -> diagnosis. A source
added before the filter needs a second pass over the corpus; the filter added first needs none.

## 3. INTERFACES.md changes, one list

1. Hint result `kind` (line 109): add **`"demo_steps"`** (already produced by main, with `step`, `steps_total`) and
   **`"lesson"`** (already produced, documented only in its own section), plus **`"check"`** and **`"diagnosis"`**;
   `"solution"` carries `source: "demo_set" | "solver" | None` (main) and optional `figure_ca/en`; every rung-3/4 result
   may carry `fallback_reason` (`leak:value:…`, `no lesson`, `llm:…`).
2. Rung table (lines 80-81): row 3 "a hand-written demo step, or a solver-trace step, or (after a wrong attempt) a
   diagnosis that names no value, or a one-sentence LLM hint, or an option check, or a second strategy; the fourth press
   is a lesson"; row 4 "letter, value, the demo steps or the solver trace, a figure description first for visual topics".
3. `hints.note_attempt(problem_id: str, letter: str) -> None`; `reset()` and `prefetch()` clear it. `get_hint` unchanged.
4. `copilot/leak_filter.py` enters the file: `leak_reason(hint, label, options, lang=None)`, `leaks(...)`.
5. `/api/state.answer`: `{"letter", "correct", "attempt": 1|2, "tried": [...], "closed": bool}`; **`label` only when
   `closed`**. Timeline rows `answer2:<letter>:right|wrong`, `reveal:solution`. `/api/solution` -> `{"error": "answer
   first or climb to rung 3"}` otherwise.
6. `/api/teacher` adds `"attempts": {"second_attempts", "recovered", "by_student": {name: {...}}}`.
7. Trainer section, one sentence under `record_answer`: called once per problem, at the first attempt; a second attempt
   is not graded (web `AttemptStats`). Signature unchanged.
8. (P6, after the demo) `retrieval.neighbors(..., skip_duplicates: bool = True)`, rung-1 payload `similarity`, rung 1 may
   return `problem: None, skip: True`.

## 4. Implementation order, effort, what is safe before the demo

| step | what | effort | before the demo? |
| --- | --- | ---: | --- |
| P1 | Filter v2 + corpus + sweeps; `test_content.py` on raw options | 75 min | **yes**: adds rejections except step 3, which removes a measured false rejection; rerun `tests.test_content` and one `dev/demo_rehearse.py` pass |
| P2 | `_rung3`: filter each demo step with `lang`, count survivors (M4), `fallback_reason` + log line; `_solved` on `problem_for(id, "eng")`; `_rung4` figure line first; INTERFACES items 1-2 | 30 min | **yes**: the six demo ids' steps all pass the filter today (ran), so the stage shows the same "Pas 1 de 4"; optional and recommended: one more Pista on problem 1 in the script so the jury sees a hand-written step |
| P3 | Two attempts in `webapp.py` (`_graded` private, `tried`, `closed`, `AttemptStats`, `hint()`/`solution()` conditions, automatic rung 4 after the second miss, `confirm()`) and `app.js` (`b.disabled = s.busy \|\| a?.tried?.includes(l) \|\| a?.closed`, `right` only with `a.label`, hint button on `closed`) | 60 min | **only with one rehearsal**: `pitch.md` second 60 ("la correcció arriba només ara" stays true, the letter no longer appears), `contingency.md:40`, `demo-problems.md` steps 2 and 4 ("cross, no letter; one Pista; a second letter or Solució reveals"); `dev/demo_rehearse.py` takes a second letter. Worth it: reviewer C3 is the jury's first criterion |
| P4 | `hints.note_attempt`; order B with the `statement_number` diagnosis (module on main; `_diagnose` unchanged for the reveal) | 30 min | **yes**: fires on stage only if the presenter clicks the distractor copied from the statement on `lvl-4_2010_12` (`dev/demo_pick.py --show` tells which); zero model time |
| P7 | `laptop/measure_ladder.py`; table in `docs/teach-measurement.md`; `contingency.md:40` and the 19-row table of `content-review.md` scrubbed into `docs/demo/local/`; `tests/test_no_labels_in_docs.py` | 30 min | **yes** |
| P5 | Option checks (`copilot/option_checks.py`, `kind: "check"`) | 45 min | **no** (after): changes rung 3 on 119/281 problems; none of the six demo ids needs it |
| P6 | Rung-1 gate 0.75 + same-level fallback + `skip_duplicates`, `RUNG1_MIN_SIMILARITY` in `config.env` | 45 min | **no**: 5/6 demo ids pass; reserve `lvl-5_2022_30` (0.729) would switch to `lvl-5_2019_12` (0.771), not in the demo doc |

Core path P1 + P2 + P3 + P4 + P7: about 3.75 h. What the demo shows, checked against the new flow: problems 1 and 3
(correct after two Pista) unchanged; problems 2 and 4 (wrong click) change with P3 only: cross stays, no letter, two
presses left (demo step, lesson), then a second letter or Solució shows letter, value and the five steps. LED, mastery
(0 -> 1 from attempt 1) and the teacher view unchanged; no model call anywhere (gate closed in Catalan for all six, ran).

## 5. Tests to add, and the before/after measurement

`tests/test_leak_filter.py` / `tests/leak_corpus.py` / `tests/test_leak_filter_val.py`
- `test_adversarial_corpus_is_caught`: all 110 return a reason (today 35).
- `test_harmless_corpus_passes_with_lang`: all 40 return None with their `lang` (today 28).
- `test_glued_unit_in_the_hint_is_caught`: `leak_reason("Pensa en 12cm.", "C", {"C": "12cm"})` == `value:12cm`.
- `test_unit_digit_is_not_a_value`: `leak_reason("Hi ha dos quadrats.", "C", {"C": "18cm2"})` is None (the filter's own example options, not a real problem's).
- `test_lang_none_keeps_today_s_behaviour`: the 14 existing tests pass unchanged.
- `test_every_real_correct_value_is_caught` (data-gated): val+train, plain and glued, 0 misses, ids only.
- `test_demo_set_and_lessons_pass_with_raw_options` (data-gated): 0 drops over steps[:-1], figure and mistake fields.

`tests/test_hints.py`
- `test_rung3_trace_uses_the_english_text`: patched `solvers.solve` receives `language == "eng"` for a Catalan reader.
- `test_demo_step_that_leaks_is_skipped_and_the_count_is_right`: a fixture step naming the value is dropped, `steps_total` shrinks, `fallback_reason` starts with `leak:`.
- `test_rung4_puts_the_figure_line_first_for_visual_topics`.
- `test_note_attempt_gives_a_statement_number_diagnosis_once`: wrong letter whose value is in the statement -> `kind == "diagnosis"`; second press -> `demo_steps`/`strategy`; no value or letter in the text.
- `test_relation_signatures_never_reach_rung_3`: a `double` distractor after `note_attempt` -> `kind != "diagnosis"`.
- `test_prefetch_and_reset_forget_the_attempt`.

`tests/test_webapp.py`
- `test_first_miss_hides_the_label_and_keeps_hints_open`: `"label" not in json.dumps(state)`, `hint()` ok, `tried == ["A"]`.
- `test_second_miss_closes_reveals_and_pushes_rung_4`: `answer["closed"]`, `label` present, last hint `kind == "solution"`, `source == "demo_set"` on a demo id.
- `test_trainer_gets_exactly_one_record_answer_per_problem`: mock counts 1 across two attempts, `hint_rung_used` = rung at attempt 1.
- `test_second_attempt_is_a_timeline_row_and_a_counter`: `answer2:B:right`, `recovered == 1`, teacher block present.
- `test_miss_does_not_change_hints_left_and_the_lesson_stays_last`: 4 -> 2 before the miss -> 2 after -> rung 3 -> lesson.
- `test_solution_needs_an_attempt_or_rung_3`: fresh session -> error; after `rung == 3` -> thread started.
- `test_signature_explanation_only_after_close`: with the fake module, the text appears only when `closed`.

`tests/test_no_labels_in_docs.py` (data-licence P2): no `lvl-…` id within 20 characters of `(answer|label|resposta)[^.\n]{0,20}\b[A-E]\b` in `docs/**/*.md`, no `| id | … | [A-E] |` row, no id-and-label JSON pair outside `tests/`.

**Measurement: `laptop/measure_ladder.py --input data/val.jsonl --lang cat|eng [--attempt wrong]`** (hints P11; the
explorer's `val_ladder.py` cleaned, `llm_hint` patched to a counter). Per id: the kind of four presses, the rung-4 trace
length and source, and with `--attempt wrong` the kind after `note_attempt` with each distractor; ids-only JSON to
`results/ladder-val.json` (git-ignored). The table the docs quote:

| measure (val, 281 ids per language) | today at `4bea6d4` (ran) | after this design (projected on the same data, ran) |
| --- | --- | --- |
| rung 3, first press: demo_steps / trace / check / card (Catalan) | 4 / 0 / 0 / 277 | 4 / 0 / 119 / 158 (4 / 0 / 0 / 277 without P5) |
| rung 3, first press (English) | 4 / 0 / 0 / 277 (gate open for 63, patched) | 4 / <= 7 / 115 / rest |
| rung 3 after a wrong attempt: `diagnosis` share of the 536 numeric pairs | n/a (no second attempt) | 20 (3.7%, `statement_number`); the 95 (18%) "confident signatures" are the leak this design refuses |
| rung 4 with an explanation (demo steps or trace) | 4 / 281 on val; 6 / 6 on the demo ids | same (content, not code) |
| demo-set texts a runtime filter would wrongly drop (raw options) | 6 (2 steps + 4 fields; not filtered today) | 0 |
| label in `/api/state` after one wrong click | yes | no until `closed` |
| `record_answer` calls per problem | 1 | 1 |
| leak filter: adversarial caught / harmless passed / real glued values caught | 35/110, 28/40, 304/339 | 110/110, 40/40, 339/339 |

## Proposals

### P1. Leak filter v2 with one corpus and a `lang` parameter (the prerequisite)
- **Where**: `copilot/leak_filter.py:21-37` (`_WORDS`), `:52` (`_UNITS`), `:62-73` (`_numbers_in`), `:98-102` (`_core`), `:105-109` (`_contains_token`), `:113-150` (`leak_reason`); `tests/test_leak_filter.py`; `tests/test_content.py` (`_UNIT`, `_clean_options`); new `tests/leak_corpus.py`, `tests/test_leak_filter_val.py`.
- **Problem / opportunity**: 75/110 adversarial pass, 12/40 harmless fail (reran), 35/339 real glued values pass (tests P8), and with the raw options the filter drops 2 of the 152 non-final demo steps plus 4 fields of `lvl-1_2024_8` because the digit of `cm2` becomes a value 2 (ran). `test_content.py` strips units first, so the suite cannot see it; `get_lesson` already filters with raw options at runtime and would hit the same class on any area lesson. Every source of sections 1-3 relies on this function.
- **Proposal**: section 2: signature with `lang`, normalisation steps 1-8, `tests/leak_corpus.py` (110 + 40), the data-gated sweep over val+train values and over the demo set and lessons with raw options, `test_content.py` without `_clean_options`. Reviewer I2's strings fold into the corpus.
- **Impact (jury)**: high; "never reveals" is the criterion, and the demo steps cannot be filtered at runtime without the unit fix.
- **Effort**: M (75 min). **Risk**: more rejections on the LLM path (closed in Catalan); the unit fix removes one false-rejection class only; INTERFACES only documents the function. Safe before the demo.
- **How to measure**: last rows of the table in section 5; `python3 -m unittest tests.test_leak_filter tests.test_leak_filter_val tests.test_content`.
- **Verified**: ran (all counts).

### P2. Filter the demo steps at runtime, count the survivors, solve on the English row, figure line first
- **Where**: `copilot/hints.py` `_rung3` step "(0)" (returns the demo step **without** `leak_reason`, unlike the trace branch below it), `_solved` (Catalan text to English-keyword solvers, hints P1), `_rung4` (no `figure_*`), `INTERFACES.md:80-81,109`.
- **Problem / opportunity**: main added the demo steps (hints P2 done in part) but every other text source is filtered and this one is not; a future entry whose step names the value (the content tests catch it only when the data is linked) would reach the page. `solvers.classify` is 0/281 on Catalan text (hints report), so rung 3a is dead on the demo page. The kinds `demo_steps` and `lesson` exist in the code and not in INTERFACES. Reviewer M4 (count then skip) applies as soon as filtering is added.
- **Proposal**: in `_rung3` compute `survivors = [s for s in steps[:-1] if leak_reason(s["text_ca"], label, options, "cat") is None and leak_reason(s["text_en"], …, "eng") is None]`, serve `survivors[state["demo_step"]]` with `steps_total = len(survivors)`, `fallback_reason` and one `log()` line per dropped step; `_solved` calls `solvers.solve(problem_for(problem["id"], "eng") or problem)`; `_rung4` prepends the figure description for `topics.is_visual(topic)` and returns `figure_ca/en`; INTERFACES items 1-2 of section 3. Tests: section 5, `test_hints.py` first three.
- **Impact (jury)**: medium; it makes the "never reveals" claim true for the one source the demo shows, and the docs match the code.
- **Effort**: S (30 min). **Risk**: none for the stage: all six demo ids' steps pass the filter today (ran), so the texts shown are identical. Safe before the demo.
- **How to measure**: `measure_ladder.py`: `demo_steps` 4/281 on val and 6/6 on the demo ids before and after; `fallback_reason` present on a fixture with a leaking step.
- **Verified**: ran (unfiltered path by reading `_rung3`; 152-text pass count; classify counts from the hints report).

### P3. Two attempts: no letter on the first miss, the trainer still called once
- **Where**: `copilot/webapp.py:285-311` (`answer_letter`: `self.answer = {"letter": letter, **result}` publishes `label`; message names it), `:346-352` (`hint()` refuses after any answer), `:371-377` (`solution()` unconditional), `assets/app.js:144-160` (`renderAnswer`: `b.disabled = !!a`, `right` by `a.label`, hint button disabled when answered), `docs/demo/pitch.md` second 60, `docs/demo/contingency.md:40`, `docs/demo/demo-problems.md` steps 2 and 4, `dev/demo_rehearse.py`.
- **Problem / opportunity**: reproduced at `4bea6d4`: one wrong click puts `label` into the state, writes "era la <letter>", refuses Pista (`already answered`). Reviewer C3; web P4. The trainer contract (one `record_answer`) is what blocked the fix.
- **Proposal**: web P4 plus the contract: at attempt 1 `record_answer(student, id, letter, self.rung)` once (today), `self._graded` private, `self.answer = {"letter", "correct", "attempt": 1, "tried": [letter], "closed": correct}`; message "No és aquesta. Demana una pista o prova una altra lletra."; `hint()` refuses only when `closed`; attempt 2 (`letter not in tried`) sets `closed`, publishes `label`, appends `answer2:<L>:right|wrong`, counts in `AttemptStats` (`data/attempts.json`, `Rung0Stats` shape, `/api/teacher.attempts`) and, when wrong, pushes `get_hint(id, 4)` into `self.hints` (demo steps, figure line, then `_diagnose` of attempt 1 appended as today). `solution()` allowed when `self.answer or self.rung >= 3`, `confirm()` on the page (web P5). `app.js`: disable only `tried` letters until `closed`, `right` only when `a.label` exists, `$("hint").disabled = a?.closed || s.busy || left <= 0`, status "Encara pots demanar una pista.". Docs and rehearsal script as in section 4.
- **Impact (jury, student)**: high; the first criterion, and the presenter can show the cross and the ladder on the same problem.
- **Effort**: M (60 min). **Risk**: INTERFACES state line and the teacher block; the pitch changes at second 60. Safe before the demo **only with one rehearsal** of both chains.
- **How to measure**: section 5 tests; `curl /api/answer/A; curl /api/state | grep -c '"label"'` -> 0; second letter -> 1; the trainer mock receives one call.
- **Verified**: ran (reproduction and the one-call count); the fix is designed.

### P4. `note_attempt` and the one signature that may precede the reveal
- **Where**: `copilot/hints.py` (`_st`, `_rung3`), `copilot/webapp.py:102-114` (`_diagnose`, keep), `copilot/signatures.py` (on main; `statement_number` at step 2 of `_candidates`), `INTERFACES.md` signatures section.
- **Problem / opportunity**: hints P3 proposes the signature as rung-3 content; main and INTERFACES say "post-answer only". Measured on val: with direction 95/95 pin the correct option, direction-free 51/75; `statement_number` (20/95) is the exception. On the two scripted wrong clicks the module says `none`/low, so merging alone changed nothing on stage.
- **Proposal**: `hints.note_attempt(problem_id, letter)` stores `state["attempt"]`; `_rung3` order B: when an attempt exists, `signatures.diagnose(problem, letter)` is `statement_number` with high confidence and not yet shown -> `kind: "diagnosis"` with the module's text (filtered with `lang`); every other key falls through. The reveal keeps the full directional text. INTERFACES: `"diagnosis"` kind and the rule "a diagnosis before the reveal must not determine the correct option from the chosen one". Tests: section 5 (`test_hints.py` 4-6). Optional: the script clicks that distractor on problem 4 so the jury sees a diagnosis that leaks nothing.
- **Impact (student)**: medium; specific to the slip, 0 s, Kangaroo's favourite distractor; the other 75% still teach, after the reveal.
- **Effort**: S (30 min after P3). **Risk**: one INTERFACES kind; zero model time. Safe before the demo.
- **How to measure**: `measure_ladder.py --attempt wrong`: `diagnosis` on 20/536 val pairs, none with a relation key; every text passes `leak_reason` with raw options.
- **Verified**: ran (pin rates, key distribution, demo-id confidences).

### P5. Option-derived checks as the rung-3 source between the demo steps and the card (after the demo)
- **Where**: new `copilot/option_checks.py` (stdlib), `_rung3` after the LLM slot; hints P4 content unchanged.
- **Problem / opportunity**: after P2 rung 3 is still a card on 277/281 val problems (4 val ids in the demo set). The option set is a teaching object on 119/281 Catalan rows: parity 44, arithmetic progression 36, common factor 19, magnitude 14, mixed units 6 (ran with hints P4's rules).
- **Proposal**: hints P4 as written (units > magnitude > progression > factor > parity, one per press, questions not statements, the magnitude text omits the numbers when the correct value is the min or max, every text through `leak_reason(..., lang)` with raw options; `kind: "check"`). Tests: one synthetic set per rule; a text naming the value is dropped.
- **Impact (student)**: medium; rung 3 stops being rung 2 on 42% of problems with no model and no content hour.
- **Effort**: M (45 min). **Risk**: one INTERFACES kind; changes rung 3 for ids outside the demo set, so not the six. After the pitch.
- **How to measure**: `measure_ladder.py`: `check` 119/281 cat, 115/281 eng; 0 leaks over every produced text.
- **Verified**: ran (counts); texts are hints P4's proposal.

### P6. Rung-1 gate at 0.75 with the same-level fallback, duplicates skipped (retrieval P1 + P2), after the demo
- **Where**: `copilot/retrieval.py:127-151` (`neighbors`, `similarity` returned), `copilot/hints.py` `_rung1`, `copilot/trainer.py` `_choose_adaptive`, `config.env`.
- **Problem / opportunity**: 41% of val rung-1 neighbours score below 0.75 (retrieval report). For this theme: five of six demo ids pass (0.935, 0.914, 0.827, 0.810, 0.859); reserve `lvl-5_2022_30` is at 0.729 and under P1(b) would switch to `lvl-5_2019_12` (0.771), which the demo doc does not describe (ran).
- **Proposal**: retrieval P1 and P2 as written (`SAME_IDEA_SIMILARITY = 0.75`, `NEAR_DUPLICATE = 0.97`, `skip_duplicates=True`, `similarity` in the payload, `skip: True` lets the card come first) behind `RUNG1_MIN_SIMILARITY` in `config.env`, 0 until the pitch.
- **Impact (jury)**: medium (the rung before the one this design fixes); 44% -> 63% precision is a README number.
- **Effort**: M (45 min). **Risk**: INTERFACES (`neighbors` argument, payload key, skippable rung 1); changes the reserve chain. Not before the demo, or with the key at 0.
- **How to measure**: the four core ids keep their neighbours (all >= 0.81 today); `measure_retrieval.py --judge 20`.
- **Verified**: ran (the six similarities and the fallback).

### P7. `measure_ladder.py`, the measured table, and the last two label leaks in docs
- **Where**: new `laptop/measure_ladder.py`, `docs/teach-measurement.md` (new section), `docs/README-final-draft.md` limitations, `docs/demo/contingency.md:40` (quotes the correction message with the letter of `lvl-3_2019_18`), `docs/content-review.md` (19 rows with a letter column), new `tests/test_no_labels_in_docs.py`.
- **Problem / opportunity**: the ladder has no measured table (hints P11) and this design needs a before/after. `demo-problems.md` was scrubbed on main, but the public repo still states a demo answer in `contingency.md` and all 19 in `content-review.md` (ran: `grep -cE '\| [A-E] \|'` = 19); P3 makes it worse in spirit (the page hides the letter, the docs show it).
- **Proposal**: the script and the table of section 5 (ids-only JSON to `results/`); move the two leaks to `docs/demo/local/` (already ignored, `.gitignore:37`) and replace the column by `verified`; the regex test of data-licence P2 with the addendum's pattern.
- **Impact (jury)**: medium; a measured claim and a closed "reveals the answer" finding in the repo itself.
- **Effort**: S (30 min). **Risk**: none to code. Safe before the demo.
- **How to measure**: the doc's table equals the script's output at the commit; `git grep -nE '\| [A-E] \|' docs/` -> 0; `git grep -n "resposta era" docs/` -> 0; the new test passes.
- **Verified**: ran (the before numbers and the two greps); the edits are read.

## Discarded

- **Any relation signature as rung-3 content before the reveal** (hints P3 as written; the brief's "signature if numeric
  and confident"): pins the correct option in 95/95 val pairs with direction and 51/75 without (ran). An answer the
  filter cannot see; INTERFACES on main reaches the same conclusion with 1176/1381.
- **A free rung 3 on the miss when no press is left**: a wrong click must not be a fifth hint.
- **A second `record_answer` for attempt 2**: the trainer contract is one row per problem (`pending` deleted on the first
  call); mastery grades the first honest try; attempt 2 goes to `AttemptStats`.
- **`record_answer` deferred to the close with the first letter**: loses the tick/cross at attempt 1 and the LED timing
  the pitch rehearsed.
- **Removing the lesson from the fourth press after a miss**: it is the newest thing on main and the only press that
  teaches the idea; order B keeps it last.
- **LLM-written explanations for rung 4**: the model never reasons; one hint already costs 28 s of board time.

## Table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | Leak filter v2: glued units both ways, word generators, positions, `lang`, one corpus + sweeps | high | M | yes |
| P2 | Filter the demo steps at runtime, count survivors, solve on the English row, figure line, INTERFACES kinds | medium | S | yes |
| P3 | Two attempts, label private until closed, one `record_answer`, `AttemptStats`, Solució gated | high | M | only with one rehearsal |
| P4 | `note_attempt` + `statement_number` diagnosis at rung 3; relation signatures stay post-reveal | medium | S | yes |
| P5 | Option-derived checks as a rung-3 source | medium | M | no (after) |
| P6 | Rung-1 gate 0.75 + fallback + skip duplicates (`RUNG1_MIN_SIMILARITY`) | medium | M | no (reserve chain changes) |
| P7 | `measure_ladder.py`, measured table, the two remaining label leaks in docs | medium | S | yes |
