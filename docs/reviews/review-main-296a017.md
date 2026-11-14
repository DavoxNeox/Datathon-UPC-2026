# Review of `origin/main` at 296a017 (14 Nov 2026, evening)

Second pass over main after the merges of reason-predict, hints-demo-set, ui-lesson and the four
corrected innovation branches. Scope as the controller asked: the lesson rung (filter, mastery),
the demo-set steps in rung 3, the control borders in the manipulatives, and the middle-value rule
in `predict.py`. Nothing changed by me.

**Executed**: the suite (280 tests OK, 1 skipped); `predict.py` twice on the full `val.jsonl`
(562 problems) and a cell-by-cell diff; the sim web on port 7009 with the pseudonym `Carla`
(whose first problem, `lvl-0_2016_8`, has five hand-written steps): five hint presses, a wrong
answer, the SQLite `answers` row, `Solució`; `hints.get_lesson` against a temporary
`lessons.json` with one leaking and one clean lesson; the leak filter over every pre-final
demo step; contrast of `--control` on the page and the computed border of the buttons in
`rotate.html`, `dice.html` and `paths.html`; the five new captures. **Only read**: the four
innovation branches' fixes (each matches what the previous reviews asked), `theme.css`.

## Executive summary

1. **`predict.py` with `MIDDLE_VALUE=1` is sound.** Two full runs give identical answers (only
   the `seconds` column differs), every answer is a letter, every status `ok`, worst 1.34 s on the
   laptop (the solver extractions; the rule itself costs nothing). 150/562 = 26.7% on validation
   against 130 for always D (+12 English, +8 Catalan). Letters: D 339, C 155, B 35, A 19, E 14.
   `tests/test_reason_policy.py` keeps the ladder from importing the rule and checks the fallback
   with the server down.
2. **The lesson cannot become the answer.** `get_lesson` runs every title and text through the
   leak filter against the problem's label and options: a lesson that says "dinou" for a problem
   whose answer is 19 is skipped and the next one used; with only leaking lessons it returns
   `None` and the page falls back to a strategy card. The lesson is recorded as rung 3:
   `Carla`'s answer row holds `hint_rung = 3`.
3. **The hand-written steps work, but the cap hides them.** With `HINT_MAX_USES=4` and the lesson
   on the fourth press, the presses give neighbour, strategy, **step 1 of 4**, lesson. Steps 2, 3
   and 4 of the demo set never reach the student before the solution; `Solució` shows all five
   (last one included, as designed). The content branch's best work is one card deep.
4. **Captures clean; borders fixed.** The five new PNGs show the lesson card (own text), the dot
   row and the letters strip: no M3Kang content. `--control` measures 3.72:1 on the card and 3.39:1
   on the page in light, 3.74 / 4.16 in dark; `rotate.html` and `dice.html` buttons 3.74:1;
   `paths.html` uses the same token (my first probe hit its filled primary button). The verdict
   band has `aria-live`, the topic's progress sits under the letters, the drawer pushes the page
   left at 1000 px and more, the label is "Àlies" again, the text fold follows the width.
5. The post-answer error signature reaches the page as text appended to the verdict and a key;
   `evidence` and `correct_value` never appear in `/api/state` (checked).

## Findings

**L1 (IMPORTANT). Three of the four demo steps are unreachable before the solution.**
`copilot/webapp.py:hint` (lesson on press `HINT_MAX_USES`), `copilot/hints.py:_rung3` (one demo
step per press), `config.env` `HINT_MAX_USES=4`. Reproduced with `Carla`/level 0: kinds
`neighbour, strategy, demo_steps 1/4, strategy(rung "lesson", fallback "no lesson")`. The pitch
problems will get entries with 3 to 4 pre-final steps (content-fixes) and show one. *Fix:* either
count the demo steps outside the cap (a press on a problem with remaining demo steps does not
consume a use), or raise the cap to 6 when `demo_steps(id)` exists, or let rung 3 show the demo
steps before rungs 1 and 2 on demo problems. State in INTERFACES which.

**L2 (IMPORTANT). The lesson text is allowed to be the recipe.** INTERFACES says the lesson is
"never a formula that produces the answer"; `dev/fixtures/lesson_hint.json`, written for the
demo's first problem, reads "suma les caselles de les files i les de les columnes i resta les que
es toquen", which is the whole method of `lvl-1_2024_2`. Counting it as rung 3 is the right
bookkeeping, but the jury hears "lesson, not a hint" (the book icon says so) while the card solves
the problem's class. *Fix:* keep the rung-3 accounting, drop "not a hint" from the dot's label
("Lliçó" is enough), and ask content to keep the problem's own numbers and the exact operation
order out of the lesson that matches a demo problem.

**L3 (MINOR). Demo steps are not filtered at runtime.** `_rung3` passes the solver trace through
`leak_reason` but not the demo steps; the guard is `tests/test_content.py`, which strips units
before filtering because `leak_filter._numbers_in("27cm2")` yields 27 **and 2** (so step 4 of
`lvl-1_2024_8`, which says "dos rectangles", would be rejected by the raw filter). Fix the unit
parsing in `leak_filter.py` and add the runtime check to `_rung3`, as for the trace.

**L4 (MINOR). Without `lessons.json` the fourth press shows a strategy card under a book icon.**
The card says "Una estratègia" and the dot shows the book; harmless until content-fixes lands, but
the demo must not run without the file or the fourth press is a repeat.

**L5 (MINOR). The verdict disappears after `Solució`.** `_finish_hint` sets `message` to empty,
so "No és aquesta. La resposta correcta era la C. <signature>" vanishes when the solution card
appears (seen in the browser). Keep the verdict when the hint is the solution.

**L6 (MINOR). `--ok` on `--ok-bg` is still 4.68:1 in light** (doc now says measured). Passes AA;
`#16703f` would give the 5:1 margin the other pairs have.

## Checks

| Check | Result |
| --- | --- |
| predict.py, two runs on 562 | answers identical; letters only; 562 `ok`; worst 1.34 s laptop |
| accuracy on val (cat+eng) | 150/562 = 26.7% vs 130 always D |
| lesson leak filter | leaking lesson skipped, clean one used, none → `None` |
| lesson counted as rung 3 | `answers.hint_rung = 3` for `Carla` |
| demo steps before the solution | 1 of 4 (cap), all 5 on `Solució`, `source = demo_set` |
| `evidence` / `correct_value` in `/api/state` | absent |
| `--control` light / dark | 3.72 (card) 3.39 (bg) / 3.74 (card) 4.16 (bg) |
| manipulatives' button borders | rotate 3.74, dice 3.74, paths same token (primary is filled) |
| new captures | 5/5 free of M3Kang content |
| tests | 280 OK, 1 skipped |

## In one line

The rule, the lesson and the borders do what they promise; raise or bypass the hint cap on demo
problems or the hand-written steps will never be seen.
