# Review of reason-v2 (2c86cad): the OCR v2 data and `MIDDLE_VALUE_SKIP_ORDERED`

Asked by the controller: reproduce the v2 figures (always D, the shipped policy, the flag on) in
English and Catalan; check that the "printed in order" condition was decided on train and that
the flag never reads the label; paired bootstrap of the flag against the shipped policy and
against D; what the flag does on the v1 data; an opinion on turning it on for the exam.

## What I ran

| command | outcome | kind |
|---|---|---|
| `git diff 2d083df 2c86cad` on config, `copilot/ladder.py`, `copilot/pipeline.py`, tests; `git log` | the flag is 20 lines: `ladder.is_ordered(values)` and a `skip_ordered` argument of `middle_letter`, read in `pipeline.py:33, 181`; `predict.py` resumes by id and language (a9a35dc); three new test classes | read + ran |
| two worktrees at 2c86cad, one on `~/m3kang-data` (v2), one on `backup-v1-20261114` (v1); `python3 -m unittest discover tests` | 374 OK, 1 skipped | ran |
| `eval.py --limit 0 --languages {eng,cat}` three times per worktree: default config, `MIDDLE_VALUE_SKIP_ORDERED=1`, `SOLVERS=0 MIDDLE_VALUE=0` | 12 runs, table below | ran |
| my own paired bootstrap (10 000 resamples, seed 42) on the per-problem CSVs: flag − policy, flag − D, policy − D | table below | ran |
| the ordered / descending / unordered table recomputed from the data with `ladder.numeric_options`, `is_ordered`, `middle_letter`, scoring against the label only in my script | matches the document | ran |
| `grep` for an OCR engine in `predict.py` and `copilot/` | none: options must arrive in the exam file | ran |
| `docs/results-A.md` "Data v2", `docs/reason-experiments.md` lines 612-692, `config.env:78-85` | read | read only |

## Reproduction

Five-option coverage of `val.jsonl`: 500 of 562 versions in v2 against 339 in v1 (89 % against
60 %), as stated.

| data | language | always D | shipped policy | flag on | flag − policy, 95 %, P(gain <= 0) | flag − D | policy − D |
|---|---|---|---|---|---|---|---|
| v2 | eng | 64 (report 64) | 70 (70) | **79** (report **80**) | +9 [-4, +22] 0.11 | +15 [+5, +25] 0.002 | +6 [-11, +23] 0.26 |
| v2 | cat | 65 (65) | 70 (70) | 80 (80) | +10 [-4, +24] 0.09 | +15 [+5, +25] 0.002 | +5 [-12, +22] 0.30 |
| v1 | eng | 65 | 77 (77) | 77 (77) | 0 [-11, +11] 0.54 | +12 [+4, +21] 0.003 | +12 [-2, +26] 0.06 |
| v1 | cat | 65 | 73 (73) | 78 (78) | +5 [-7, +17] 0.22 | +13 [+5, +22] 0.002 | +8 [-6, +23] 0.16 |

Eleven of twelve totals equal the report; English v2 with the flag gives 79 here against 80
there. The only request-dependent row on that set is `lvl-3_2023_28` (the `average` family's
extraction, which abstains in both my runs); the data file (01:38) predates the commit (02:32),
so I cannot name the problem that differs. Call it 79 or 80: the interval does not move.

Where the flag changes an answer (94 problems in English v2, the ordered sets): 28 wins, 19
losses; Catalan 29 and 19; v1 English 17 and 17; v1 Catalan 20 and 15. Never a net loss in a
set, never a significant gain over the shipped policy on its own, and a significant gain over D
in every set, which the shipped policy no longer has on v2 (+6, P = 0.26).

## Train table and the decision

Recomputed on the 886 numeric English training problems of v2, middle value right / D right:
ascending 465, 133 / 132; descending 66, 11 / 23; unordered 355, 118 / 69. So "not ascending"
is 421, 129 / 92, as the document says. Validation v2: ascending 82, 18 / 27; descending 13,
1 / 2; unordered 73, 25 / 10 (the document's 86, 26 / 12 for "not ascending"). v1 has the same
shape (train ascending 354 at 99 / 100, unordered 258 at 93 / 46).

The two candidate conditions in the document, "ascending" (train −1) and "ascending or
descending" (train +11), were chosen by the training column; the descending sets are where the
middle value is worst (11 against 23), so the choice is right on its merits, not only by the
total. The validation column sits next to the training one in the same table, so validation was
looked at once, after. One honest qualification the document does not make: the hypothesis
itself came from the validation drop (results-A "the rule's drop comes from the 83 recovered
validation problems"), so the English v2 +9 is not an independent confirmation; the independent
looks are the training table (+11 of 1466, [-23, +44]) and the v1 sets (0 and +5). The flag
reads `numeric_options` only (`ladder.py:44-63`); no label, no text, nothing from the model.

## What the flag assumes about the exam file

Everything here, flag and middle value alike, needs the five options in the exam rows as text in
their printed order. There is no OCR on the board: `predict.py` and `copilot/` read `options`
from the file and nothing else, and the README (line 701) says the M3Kang `text` field has the
question only. Three cases for the organisers' file:

- options as text in printed order (like v2): the flag applies as measured, +0 to +10 of 281;
- options as text but sorted ascending (a common way to type them): every set is "ordered", the
  flag sends everything to D, and that is the right call, because on ordered sets the middle value
  is "always C" and C is the worst position (validation 18 against 27 for D, 14 against 21 in my
  count including descending); without the flag the shipped policy would be always-C there;
- options only in the image, or absent: no numeric rule fires, every answer is D, the flag is
  moot.

The flag never does worse than the shipped policy in the three cases, and protects it in the
second. Nobody has seen the hidden file's format; asking the organisers for one sample row
would settle more than any further experiment.

## Findings

### IMPORTANT

**V1. The shipped policy's advantage over D is gone on v2, and the document's headline figure
should say so.** On v2 the shipped policy beats D by +6 [-11, +23] in English (P = 0.26) and +5
in Catalan; the 150/562 on the board becomes about 140/562 against 129 for D. `config.env:78-80`
and the dashboard tile still carry 77/281 = 27.4 % and 26.7 %; `docs/results-A.md` "Data v2"
has the new numbers, the summary places do not yet. Fix: the same six places listed in the
dashboard's header comment, with "70/281 (v2 options)" and the board figure when the official
run lands.

### MINOR

**V2. One-problem difference in English v2 with the flag** (80 reported, 79 here). State the
run date and `eval.py` CSV name next to the 80, or re-run once and keep whichever repeats; a
jury member who reproduces will see 79 or 80, not both.

**V3. The hypothesis came from validation.** Say it in the "Data v2" section in one sentence,
next to the training table that then decided between the two conditions. The caveat costs
nothing and matches the care the think write-up took.

**V4. The pooled statements.** Any pooled eng + cat figure counts the same 281 problems twice
(the v2 options are shared across languages, so the ordered sets are identical: 69 + 99 in both);
the Catalan column is a second OCR of the same problems in v1 and the same options in v2. Report
the two languages, not their sum.

## Verified without findings

The flag is off by default and a test pins it (`tests/test_ladder.py`); the three worked
examples (ascending, descending, mixed with units) behave as the docstring says; 374 tests pass;
no run exceeded the board limit (worst estimate 28.8 s, the one extraction); `predict.py` now
resumes by id and language, which closes K1 of the think review for the exam run.

## Opinion: turn `MIDDLE_VALUE_SKIP_ORDERED=1` on for the exam?

Yes. It costs nothing (pure Python, fewer rule firings, no model call), it never lost in any of
the five sets measured (train +11, v2 validation +9 and +10, v1 validation 0 and +5), it turns
the policy's gain over D from "not distinguishable from zero" into +15 [+5, +25] on the v2
problems, and it is the only setting that is right in both plausible formats of the hidden file:
printed order, where it keeps the middle value's gain on unordered sets, and sorted order, where
it stops the rule from being "always C". The honest expected gain is +0 to +10 of 281 over the
shipped policy, with the hypothesis born on validation; the honest downside, measured, is zero
in the worst set. Keep the board's official run with the flag on as the number the pitch quotes,
and write the three-case paragraph above into results-A so the jury sees the assumption.

Praise: the drop from 77 to 70 was reported before the fix was looked for, the two candidate
conditions were separated on train with the descending sets justifying the choice, and every
figure reproduces with the flag's code reading nothing but the five values.
