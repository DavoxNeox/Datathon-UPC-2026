# Review of `origin/main` at ac07b35 / d8f9c66 (14 Nov 2026, night)

Third pass over main after demo-fixes and content-fixes, on the four points the controller asked
for. Nothing changed by me.

**Executed**: the suite (284 OK, 1 skipped); `git ls-files docs/demo/local` and `git check-ignore`;
a scan of `docs/demo/*.md` and `one-pager.md` for the literal option lists, labels and paraphrase
words of the six script problems and for 5-word overlaps with their statements; the word count
of every pitch block; the 14 lessons through the leak filter against each script problem's label
and correct value, their word counts and the lesson `get_lesson` serves to each of the six;
`hints.get_hint(..., 3)` repeatedly on the six script problems (kind, step, leak filter on each
shown step, last step never shown); the sim web with `Mariona1` and six presses of Pista; the
middle-value fires recounted with the current `ladder.py`. **Only read**: the board figures in
`results-A.md` (the board run is the controller's).

## Executive summary

1. **License: clean.** `docs/demo/local/` is ignored (`.gitignore:37`) and holds nothing in git,
   now or in history. The five committed demo documents carry ids, levels, topics, neighbour ids
   and similarities; no option list, no label, none of the former paraphrase words ("777",
   "quaranta caselles", eggs, muffins, rings, folded twice); no 5-word run shared with a
   statement. `demo_set.json`'s six new entries share no 6-word run with the statements and quote
   no distractor value (the new test enforces it).
2. **The script fits.** 394 Catalan words and 394 English: 164 s at the document's own 2.4
   words/s, 16 s of margin; the demo block runs at 2.0 words/s with 14 s for clicks and LED. The
   row that promised the next problem is reworded ("quan acabi el diagnòstic"), and the rehearsal
   note says what the third problem really is.
3. **One figure in the script is now wrong.** The numbers block (row 18, CA and EN) and the
   one-pager still say the official run on the board is "23.1%, exactly always D". Since d8f9c66
   the shipped `predict.py` answers the middle value and the board run is **150/562 = 26.7%**
   (eng 77/281, cat 73/281). The jury scores the shipped policy; the pitch must say 26.7% and
   what it is (a prior about distractors, not reasoning), or the speaker contradicts the
   repository's own results.
4. **The 14 lessons are what INTERFACES asked for**: 99 to 110 Catalan words, an idea, why it
   works, a tiny example with its own numbers, a question; bilingual; none contains a correct
   value of the six script problems (filter run against each). Two are, by nature, the method of
   a script problem (`boards` for `lvl-1_2024_2`, `digits` for `lvl-4_2010_12`); that is the
   rung-3 accounting the design chose. One is mis-served: `lvl-2_2020_4` (eggs in boxes, divide
   and round up) gets the `money` lesson because `families.json` tags it `money`.
5. **The demo steps are right, and still mostly unreachable.** Each of the six has 5 steps; rung 3
   shows steps 1 to 4 one per request and never the fifth; the leak filter accepts every shown
   step (the earlier flag on step 2 of `lvl-2_2020_4` was my test's unit handling, not a leak). On
   the web, `Mariona1` gets `neighbour, strategy, demo_steps 1/4, lesson` and then nothing: steps 2
   to 4 are still only in `Solució` (L1 of the previous review, unchanged: `HINT_MAX_USES=4`).

## Findings

**N1 (IMPORTANT). Stale official figure in the pitch and the one-pager.** `docs/demo/pitch.md`
numbers block row 18 (CA and EN) "vint-i-tres coma u per cent, exactament sempre D";
`docs/demo/one-pager.md` table "130/562 = 23.1%". `docs/results-A.md` now leads with 150/562 =
26.7%. *Fix:* "La cursa oficial a la placa, cinc-cents seixanta-dos problemes: vint-i-sis coma set
per cent; sempre D en dóna vint-i-tres coma u. La diferència és una regla sobre com es construeixen
els distractors, no raonament." (28 words, 12 s: the block has 1 s of slack, trim the 0 s row by a
clause.) Same in English and in the one-pager; say in both that the rule never enters the hints.

**N2 (IMPORTANT, unchanged from review-main-296a017 L1). Three of the four hand-written steps never
reach the student before the solution.** Reproduced on main: `Mariona1`, six presses →
`neighbour, strategy, demo_steps 1, lesson`, `hints_left 0`. The content branch wrote 24 pre-final
steps for the six problems; the stage shows one per problem. *Fix* (any one): a press on a problem
with remaining demo steps does not consume a use; or `HINT_MAX_USES` becomes `3 + demo steps`
when `demo_steps(id)` exists; or rung 3 runs before rungs 1 and 2 on demo problems. Note the pitch
itself presses Pista twice per problem, so the pitch is safe; the jury's own clicks are not.

**N3 (MINOR). `lvl-2_2020_4` gets the money lesson.** `hints.family_of` → `money`
(`data_curated/families.json`, keyword "buy"); the problem's idea is division with rounding up.
The `arithmetic/sharing` or the topic lesson fit better. *Fix:* in `get_lesson` prefer the topic
lesson unless the family is one of the solver families (`ages`, `average`, `consecutive`,
`digit_count`) or the entry carries a validated `family`; or correct the tag for this id.

**N4 (MINOR). Two counts in `results-A.md`.** "The rule fired on 223 problems": with the current
`ladder.py` the rule fires on 243 of 562 (eng 120, cat 123); 223 is the number of answers other
than D (339 D of 562). "Train 405/1466 against 366 for always D": always D on the English training
set is 367. Both cosmetic, both quoted by the jury if they read the table.

**N5 (MINOR). The lesson label.** The book dot's title is still "Lliçó" with INTERFACES' "not a hint"
wording in the kind line for rung 0 only; fine. The `boards` lesson for the demo's first problem
is the problem's method with different numbers (6 by 10, one row, one column): acceptable as rung 3,
and the pitch never reaches it (two presses). Keep it that way on stage.

## Checks

| Check | Result |
| --- | --- |
| `docs/demo/local/` | ignored, 0 tracked files, never in history |
| option lists / labels / paraphrase words in `docs/demo/*.md`, one-pager | none |
| 5-word overlaps of the docs with the six statements | none |
| `demo_set.json` six entries: 6-word overlaps, distractor values | none / none (test) |
| pitch words CA / EN | 394 / 394 → 164 s at 2.4 w/s; blocks 2.4 / 2.0 / 2.3 / 2.4 w/s |
| pitch figures vs `results-A.md` | all current except the official run (23.1% → 26.7%) |
| lessons: count, words, bilingual, script values | 14, 99-110, yes, none leaks |
| lesson served per script problem | boards, spatial, **money**, digits, areas, counting |
| demo steps via rung 3 | 4 of 5 shown, never the last, filter clean, then strategy |
| demo steps via the web (`HINT_MAX_USES=4`) | step 1 only, then the lesson |
| middle-value recount on 562 | 243 fires, 150 correct (board: 150) |
| tests | 284 OK, 1 skipped |

## In one line

The documents are license-clean and the script fits with margin; change the one number the jury
will score you on, and let the hand-written steps through the hint cap.
