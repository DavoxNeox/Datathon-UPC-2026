# Review of `origin/main` at c2de6d1, with the Reason track at 50% of the grade

The organisers now score 50% on `predict.py` against a hidden test and 50% on the jury. This
pass looks at the shipped Reason policy as an exam entry (robustness, the 60 s limit, the story
the documents tell) and at the two web changes the controller named (hints after the answer,
the settings popup). Nothing changed by me.

**Executed**: the suite (284 OK, 1 skipped); `predict.py` on 19 hand-written malformed rows,
together and one by one; the board estimate (`copilot/board_clock.estimate_tokens`, tokens from
the running server's `/tokenize`) of the family-solver extraction for statements of 90 to 1,000
prompt tokens; `config.env`, `docs/results-A.md`, `docs/reason-experiments.md`,
`docs/README-final-draft.md`, `docs/improvements/reason-eval.md`, the one-pager and the pitch
cross-read for every Reason figure; the sim web on port 7016 at 1280x800 for the two UI changes.
**Only read**: the hidden-test format in the organisers' README.

## Executive summary

1. **CRITICAL: `predict.py` aborts the whole run on a malformed row.** A row whose `options` is a
   list or a string, a row without `id`, or a line that is a JSON array raises inside `solve` and
   the script dies with no row written for that problem nor for any later one. The exam counts
   missing rows as wrong, or worse, rejects the file. The organisers' format promises only `id` and
   `text`; everything else is "when available". One `try/except` per problem (answer D, status
   `error`) and a guard for non-dict rows close it.
2. **IMPORTANT: the solver path has no time budget.** `pipeline.solve` calls the family solvers
   before the rule with no `remaining` seconds; `llm.extract_json` has a 60 s HTTP timeout and the
   prompt is the whole statement. Estimated on the board: an `ages` statement of about 530 prompt
   tokens costs 57 s, 770 tokens 78 s, 1,000 tokens 98 s. M3Kang's longest English statement is
   154 tokens, so the real validation set stays under 42 s, but a hidden-test row that is long or
   repeats its text would pass 60 s with status `ok`. Skip the solver when
   `estimate_tokens(prompt_tokens, 60) > TIME_LIMIT - MARGIN`, and pass the remaining time as the
   HTTP timeout.
3. **The documents agree with `config.env` except two stale spots.** `MIDDLE_VALUE=1`, 405/1466
   train (rule alone) and 406 (with the solvers) with the explanation, 77/281 val, 150/562 on the
   board, 243 fires, 367 always-D on train, the bootstrap interval: the same in `config.env`,
   `results-A.md`, `reason-experiments.md` and `improvements/reason-eval.md`. Still stale: the
   README draft keeps a `[[TODO official run on the board with MIDDLE_VALUE=1]]` that `results-A.md`
   already answers (150/562), and the one-pager and the pitch's numbers block still say 23.1%,
   "exactament sempre D" (assigned to demo-fixes-2, not landed). With Reason at 50%, that is the
   figure the jury will compare with the exam.
4. **Hints after the answer work, but the verdict goes.** After a wrong answer the hint button is
   live, each press adds a card, mastery stays as recorded, the fourth press is the lesson, the
   fifth is refused. But the first hint clears the sheet's message: "No és aquesta. La resposta
   correcta era la C." is gone while the student reads the hint (the commit says the verdict
   stays). The letters keep their green and red.
5. **The settings popup respects keyboard users now.** Full-screen translucent overlay with a 6 px
   blur, opened by click or keyboard, it stays open with focus inside (2.3 s measured), Tab moves
   inside it, Escape closes and returns focus to the menu button; a mouse user who opens it and
   does not move the cursor keeps it. F1 of the previous review is closed. Two small gaps: no
   `role="dialog"` / `aria-modal`, and two controls under 44 px ("Vista del professor" 23 px,
   "Canvia d'alumne" 40 px).

## Findings

**R1 (CRITICAL). One bad row kills the exam file.** `predict.py:main` loops `solve(problem, ...)`
with no exception handling; `copilot/ladder.py:numeric_options` calls `options.get` (list and
string `options` raise `AttributeError`), `predict.py` reads `problem["id"]` (missing id raises
`KeyError`), a JSON array line is not a dict. Reproduced: rows written 0 of 1 in each of the four
cases; in a 10-row file the first bad row at position 10 lost nothing but a bad row in the middle
loses every row after it. *Fix:* in `predict.py`, wrap each problem: on any exception write
`id` (or the line number when absent), language, `FALLBACK_ANSWER`, elapsed seconds and
`status error:<type>`; in `pipeline.solve`, coerce `options` to a dict of strings (`{}` when not a
dict) before the solvers and the rule; add `tests/test_predict_robustness.py` with these 19 rows.

**R2 (IMPORTANT). No 60 s budget on the solver path.** `copilot/pipeline.py:solve` →
`solvers.solve_with_timings(problem)` → `llm.extract_json(problem["text"], ..., timeout=60)`.
Estimates on the board with the calibrated constants: 298 tokens 37 s, 532 tokens 57 s, 766
tokens 78 s, 1,000 tokens 98 s (prefill at 11.4 tok/s plus up to 60 generated at 5.6). The
classifier only needs the family keywords, so any long text that contains them goes to the model.
*Fix:* before `extract`, count the prompt's tokens (the server's `/tokenize` costs milliseconds,
or estimate 1 token per 4 characters) and skip the solver when the estimate passes
`TIME_LIMIT - MARGIN`; pass `remaining` as the HTTP timeout, as the letter path does.

**R3 (IMPORTANT). The official figure is still 23.1% in the pitch and the one-pager.**
`docs/demo/pitch.md` numbers block row 18 (CA and EN), `docs/demo/one-pager.md` table. The shipped
policy scores 150/562 = 26.7% on the board (`results-A.md`). Under the new weighting the speaker
would understate the team's own exam entry by 3.6 points and call it "exactly always D".

**R4 (MINOR). Stale TODO.** `docs/README-final-draft.md` §4.1 still asks for the board run with
`MIDDLE_VALUE=1`; `results-A.md` has it. Replace the TODO with the row (150/562, 26.7%, eng 77/281,
cat 73/281, worst 38.7 s).

**R5 (MINOR). The verdict disappears on the first post-answer hint.** `copilot/webapp.py:_finish_hint`
sets `message` to empty after every hint, including after an answer; the sheet's status line then
shows "Ja has respost. Si vols, mira la solució." without the correction. *Fix:* keep the verdict
when `self.answer` is set (store it apart from the hint progress message).

**R6 (MINOR). Popup semantics and sizes.** `#panel` has no `role="dialog"`, `aria-modal="true"`
or `aria-labelledby`; "Vista del professor" is a 23 px link and "Canvia d'alumne" 40 px. The hint
button is not disabled when `hints_left` is 0 after an answer (the server refuses, so no harm).

## Reason figures, one table, as the documents state them today

| Figure | config.env | results-A | reason-experiments | README draft | one-pager / pitch |
| --- | --- | --- | --- | --- | --- |
| rule on, default | 1 | yes | yes | yes | not mentioned |
| val eng 77/281 = 27.4% vs 65 | yes | yes | yes | yes | — |
| train 405 (rule) / 406 (with solvers) | 405 | 405 | both, explained | 405 | — |
| board 150/562 = 26.7%, 243 fires, worst 38.7 s | — | yes | — | **TODO** | **23.1%** |
| always D on train 367 | yes | yes | yes | — | — |
| bootstrap val [-2, +26], train [+2, +75] | ref | ref | yes | yes | — |

## In one line

The policy is right and documented; the exam entry is fragile: a single malformed row ends the
run, a long statement can pass 60 s, and the pitch still quotes the old score.
