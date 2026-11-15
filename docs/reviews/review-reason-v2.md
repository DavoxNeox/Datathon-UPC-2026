# Review of `reason-v2` on main (a7ee184 flag, 2c86cad docs; reviewed at 6464681)

Scope: the "Data v2" sections of `docs/results-A.md` and `docs/reason-experiments.md`, and the
new flag `MIDDLE_VALUE_SKIP_ORDERED` (`copilot/ladder.py`, `copilot/pipeline.py`, `config.env`,
`tests/test_ladder.py`), off by default. Reason-track protocol: reproduce with the branch's own
commands, check that the condition reads nothing of validation and was chosen on train, redo the
bootstrap, check that "off" changes nothing and that nothing can pass 60 s, then an opinion on the
exam setting. Nothing changed by me outside this file.

**Executed** (laptop, shared servers on 8081/8082, data `~/m3kang-data`, nothing moved):
`eval.py --input <val> --limit 0 --languages {eng,cat}` with `MIDDLE_VALUE_SKIP_ORDERED=0`, `=1`
and `SOLVERS=0 MIDDLE_VALUE=0`, on the v2 file and on `backup-v1-20261114/val.jsonl` (12 runs,
the v2 English flag run repeated twice more); `predict.py` on the 562 v2 validation rows at
6464681 with the flag off and on, and at a9a35dc (the commit before the flag) extracted with
`git archive`; the rule in-process on the v2 and v1 train and validation files, by stratum; an
independent paired bootstrap (10 000 resamples, seed 42) per language, over the 562 rows, and
clustered by id; the test suite (374 tests, OK, 12 skipped).

## Executive summary

1. **The figures reproduce, except English with the flag: 79, not 80.** `eval.py` gives always D
   64 / 65 (English 64 because a family solver fires, see N3), shipped 70 / 70, flag 79 / 80 (eng /
   cat), v1 shipped 77 / 73 and v1 flag 77 / 78. The documented 80 in English is the in-process
   rule without solvers; with the shipped solvers on, the `average` solver answers
   `lvl-3_2023_28` (label D) wrongly where the abstention would give D. Deterministic over three
   runs. `predict.py` on the 562 rows: **159 with the flag, 140 without, 130 always D** — the
   controller's board figures exactly (159 = 79 + 80). The board split "141/500 with image, 18/62
   without" is in fact 141/500 **with five options**, 18/62 without: every one of the 562 has an
   image file.
2. **The condition reads no label and nothing of validation.** `ladder.is_ordered(values)` looks
   at the five parsed option values only (strictly increasing or strictly decreasing in letter
   order); `middle_letter` calls it after `numeric_options`, so it never sees a label, an id or a
   file. In-process on the English training file: +11 of 1466 (95% [-23, +44], P(<=0) 0.275),
   which is the best of the five candidate conditions in the doc's table and the only positive
   one; validation in-process +10 [-3, +23], P 0.084, as written. That it was chosen on train
   before validation can only be read from the write-up and the commit order (flag 02:03, docs
   02:32); nothing in the code contradicts it.
3. **Off means off.** At 6464681 with the flag off, the 562 `predict.py` answers and statuses are
   identical to a9a35dc's (140/562). The flag is a key of `config.env`, so the environment
   override works (unlike `SOLVERS`, N3). The only code path added is a comparison of five
   numbers; the worst board estimate is 25.8 s in every run (the solver extraction, unchanged),
   none over 60 s, `predict.py` laptop worst 0.97 s.
4. **My bootstrap, flag against shipped:** eng +9 [-4, +22] P 0.106; cat +10 [-3, +23] P 0.084;
   562 rows +19 [0, +38] P 0.030; **clustered by id +19 [-8, +46] P 0.089**. Against always D:
   eng +14 [+4, +24], cat +15 [+5, +25], clustered +29 [+9, +49] P 0.002. The 562-row interval
   overstates the evidence: 278 of the 281 Catalan versions carry the same v2 options and the
   same label as their English version, so Catalan is a copy of English, not a second test (N2).
5. **What the flag really is: "C → D on ordered sets".** On an ordered set the middle value is
   always C, so the flag only ever replaces a C with a D. Its gain is (#D − #C) among ordered
   numeric problems: train 155 − 144 = +11 of 531, validation 29 − 19 = +10 of 95. It is a
   letter prior, the same bet as the fallback letter, not a property of the values (N1). Pooled
   English train + validation, in-process: +21 of 1747, [-16, +57], P 0.13.

## Findings

**N1 (MAJOR, documentation). The strata in the write-up are mislabelled, and the train gain
comes from the descending sets, the validation gain from the ascending ones.** Both docs say
"where the five values are printed in ascending **or descending** order the middle value does no
better than D (train 133 against 132); where they are not, it keeps its gain (129 against 92)".
The 133/132 row is *ascending only* (465 problems) and the 129/92 row is *not ascending*, which
includes the 66 descending sets. Recomputed (v2, rule where it fires, middle right / D right):

| stratum | train eng | val eng (= cat) |
| --- | --- | --- |
| ascending | 465: 133 / 132 | 82: 18 / 27 |
| descending | 66: 11 / 23 | 13: 1 / 2 |
| neither (truly unordered) | 355: 118 / 69 | 73: 25 / 10 |

So on train the ordered sets are *not* neutral: abstaining there gains +11, and the whole +11 is
the 66 descending sets (+12), while abstaining on ascending alone is -1 (the doc's own first
candidate). On validation the +10 is the ascending sets (+9) and descending adds +1. Train and
validation agree in sign on the aggregate but not on which stratum carries it, which is what a
letter-frequency effect (D a little more frequent than C) looks like, and not what "the middle
value is a position on ordered sets, so drop it" predicts. *Fix:* replace the two sentences in
`docs/results-A.md` (Data v2) and `docs/reason-experiments.md` (Data v2, the strata table and
"The prior holds there…") by the three-row table above, and say the flag is C → D on ordered
sets.

**N2 (MAJOR, statistics). "+10 in both languages" is one result shown twice.** The v2 options
are language-neutral: 278/281 validation ids (1458/1466 train) have identical options in eng
and cat, and labels are identical by construction. The Catalan +10 and the 562-row "+19, P 0.03"
are not independent confirmations; the honest pooled figure is the id-clustered one, P 0.089.
*Fix:* quote one validation figure (eng, or clustered), not two.

**N3 (MINOR, recurring). `SOLVERS=0` is still a no-op, so the "always D" and "middle value,
else D" rows are not what their flags say.** `SOLVERS` is not a key of `config.env`, so
`config.load` ignores the environment variable (review-main-2026-11-14, I9, still open). With
v2 options the `average` solver now fires on one English problem and is wrong (0/1), which is
why English always D reads 64 (pure always D is 65) and why the flag reads 79 under `eval.py`
and `predict.py`. *Fix:* add `SOLVERS=1` to `config.env`; and either correct the English flag
figure to 79 or state that the 80 is the rule without solvers.

**N4 (MAJOR, data rule). Committed files quote real option sets.** `docs/reason-experiments.md`
lines 620-621 give the five option values of `lvl-0_2022_2` and the range of `lvl-1_2016_11`,
and lines 666-667 quote three real option sets; the first of them is also the `MIXED` fixture of
`tests/test_ladder.py` (`SkipOrderedTest`), which is the option set of a training problem. The
team rule is to reference problems by id and commit no problem content. *Fix:* keep the ids,
drop the values; replace the fixture by a synthetic unordered set (e.g. 7, 3, 9, 5, 4).

**N5 (MINOR). The board split label.** The "141/500 with image, 18/62 without" in the board
report is "five options / not five options": all 562 rows have an image file. Worth correcting
wherever it is quoted.

## Checks

| Claim | Branch | Reproduced | Status |
| --- | --- | --- | --- |
| always D, v2 val eng / cat | 64 / 65 | 64 (solver fires) / 65; pure D 65 / 65 | ✓ (N3) |
| shipped, v2 eng / cat | 70 / 70 | 70 / 70 (eval.py and predict.py) | ✓ |
| shipped, v1 eng / cat | 77 / 73 | 77 / 73 | ✓ |
| flag on, v2 eng / cat | 80 / 80 | **79** / 80 by eval.py and predict.py; 80 / 80 in-process without solvers | ✗ eng (N3) |
| flag on, v1 eng / cat | 77 / 78 | 77 / 78 | ✓ |
| train strata ordered / not | 133 vs 132 / 129 vs 92 | numbers ✓, labels wrong: ascending / not ascending | ✗ (N1) |
| train gain | +11 [-23, +44] P 0.28 | +11 [-23, +44] P 0.275 | ✓ |
| val gain (in-process) | +10 [-3, +23] P 0.08 | +10 [-3, +23] P 0.084; eval.py +9 [-4, +22] P 0.106 | ✓ |
| condition reads no label / val | yes | `is_ordered` reads five option values only | ✓ |
| chosen on train | yes | best of the five train candidates; order from commits and write-up | ✓ (read) |
| board 562: flag / shipped / D | 159 / 140 / 130 | predict.py on the laptop 159 / 140 / 130 | ✓ |
| board split | 141/500 with image, 18/62 without | 141/500 five options, 18/62 not five | ✗ label (N5) |
| flag off identical | yes | 562 answers + statuses identical to a9a35dc | ✓ |
| 60 s | no cost | worst board estimate 25.8 s, unchanged | ✓ |
| tests | | 374 OK, 12 skipped | ✓ |
| no problem content | | option values quoted in docs and a test fixture | ✗ (N4) |

## Opinion: turn it on for the exam?

**Yes, turn it on, for a small expected gain with a bounded downside, and say in the docs that it
is a letter bet.**

- *Expected gain.* The flag changes only ordered numeric sets, and there only C into D. On the
  M3Kang distribution about a third of the problems are ordered numeric sets (train 531/1466,
  val 95/281), and D beats C on them by 2.1 points on train and 10.5 on validation. Weighting
  the 1747 English problems we have: +21, about **+1.2 points of accuracy, +3 or +4 problems on
  a 281-problem exam**. Validation's +9/+10 is the optimistic end; train's +11 of 1466 (+2 on
  281) is the cautious one.
- *Tail below zero.* Real: train alone P 0.28, validation P 0.08 to 0.11, pooled English P 0.13.
  On a hidden test of 281 the flag decides roughly 50 problems (those with an ordered set and a
  C or D label), so a loss of 5 to 8 is entirely possible. It is not a gain the hidden test is
  owed; it is a bet with positive expectation on every set we have, including v1 (train +9).
- *Exam with options always ordered* (clean, typeset options, Kangaroo usually prints numbers
  in increasing order): the shipped policy becomes "C on every numeric problem", the flag "D on
  every numeric problem". The rule's real gain (unordered sets) is gone in both; what is left is
  D against C over perhaps 60% of the exam. On our data D wins (train ordered 155 vs 144), and D
  is the letter the team already bets on everywhere else; the stake is larger (more problems
  change) but the expectation keeps its sign. This is also the scenario where the flag matters
  most, because "always C" there is pure position.
- *Exam with options never ordered*: the flag changes nothing; no risk.
- *Cost*: none in time, RAM or code paths; off restores today's answers exactly.

If the controller wants the safer reading of the evidence, leaving it off costs about +1 point in
expectation and nothing else; I would turn it on, after fixing N1/N3/N4 so the docs describe the
setting truthfully (79 + 80 on validation, a C → D letter bet on ordered sets).
