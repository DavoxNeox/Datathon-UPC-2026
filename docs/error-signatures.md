# Error signatures: what a wrong option says about the mistake

**Post-answer explanation only, never a hint.** `copilot/signatures.py` compares, in
code, the value of the option the student picked with the value of the correct option
(both read from the OCR `options`, with units, decimal commas and fractions) and names
the slip: a datum copied from the statement, a doubling, an off-by-one, a dropped zero,
swapped digits, a sign, a statement number not added or subtracted, a sum where a
product was needed. The text never states the correct value or letter (every text passes
`copilot/leak_filter.py`), but it states a *relation*: "your result is double the right
one" lets a student with the options in front of them find the correct one in one step.
All signatures except `statement_number` pin the correct value this way (1176/1381, 85%).
So the web shows the text only once the problem is closed, next to "La resposta era C",
as the explanation of the error. No LLM is involved: the options are the knowledge,
Kangaroo designed each distractor to capture one error.

Measured with `python3 laptop/measure_signatures.py --out docs/error-signatures-coverage.md`
(full tables there). Ids only, no problem text.

## Coverage (val + train, English rows, 1747 ids)

| | n | share |
| --- | ---: | ---: |
| problems with OCR options | 1078 / 1747 | 62% |
| problems whose correct option is a single number | 938 / 1747 | 54% |
| numeric distractors of those problems | 3557 / 3752 | 95% |
| numeric distractors with a signature other than `none` | 1381 / 3557 | 39% |
| of which `confidence: high` | 577 / 3557 | 16% |
| problems with at least one signed distractor | 696 / 938 | 74% |
| problems with at least one high-confidence signature | 360 / 938 | 38% |

By topic the share of signed distractors goes from 31% (angles, counting) to 57% (logic,
n=79 distractors); by level from 49% (level 0) down to 35-38% (levels 4-7): the harder
the problem, the more the distractors are "another wrong reasoning" rather than a slip on
the right one.

## Distribution of signatures

Simulated student (each numeric distractor picked once, n=3557): plus_one 9%, minus_one
9%, statement_number 6%, double 3%, half 3%, missing_add 3%, missing_subtract 3%,
digits_swapped 1%, product_vs_sum 1%, sign / times_10 / div_10 / sum_vs_product under
1% each, none 61%.

Over the copilot's own wrong answers in `results/eval-*.csv` (7 runs, 765 wrong answers;
three of the runs are the same 281 val problems): 50% have no numeric pair to compare
(no OCR options), 28% `none`, and 22% get a signature (plus_one 6%, minus_one 4%,
statement_number 3%, double 3%, missing_subtract 3%, half 1%, the rest under 1%).
These are the model's errors, mostly the always-D fallback, not a student's.

## Small values, confidence and false positives

The reviewer's observation, reproduced: **56% of the signed distractors (774/1381) sit on
a correct value below 10**, where an off-by-one, a half or a difference equal to a datum
happen by chance. Another 10% (134/1381) match two signatures at once. The output field
`confidence` is `"low"` in both cases and for `none`, `"high"` otherwise: 577 distractors
(42% of the signed ones, 16% of all numeric distractors).

False-positive estimate, null model: every numeric distractor is replaced by a numeric
distractor of another problem of the same level and the same size (below 10, two digits,
more), so the number scale stays and only Kangaroo's design goes; whatever signature fires
on that pair is a coincidence. The null rate divided by the real rate is the share of real
signatures that a random option of the same size would also have earned (seed 1; seeds 2
and 3 move the totals by two points):

| correct value | real signed | null signed | FP share | real high | null high | FP share (high) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| < 10 (n=1381) | 56% | 44% | 78% | 0% | 0% | - |
| ≥ 10 (n=2176) | 28% | 13% | 47% | 27% | 13% | 47% |
| all (n=3557) | 39% | 25% | 64% | 16% | 8% | 47% |

Reading: below 10 most signatures are coincidences (78%), which justifies the `low`
confidence there; above 10 about half of the signatures, high confidence included, would
also fire on a random option of the same size. The explanation shown after a closed
problem is therefore right about one time in two by this estimate, and 11/20 (plus 4
partial) in the manual judgement below. It is a plausible reading of the error, offered
as such ("potser..."), not a verdict about what the student did.

## Manual judgement of 20 signed distractors

Twenty signed distractors drawn at random (`--sample 20 --seed 1`, first version of the
order) and judged by looking at the problem image in `data/images`. Verdicts: **yes** =
the signature explains how a student would land on that option; **partial** = the
relation is true but the wording or the mechanism does not fit the problem; **no** =
coincidence (or the options are not quantities); **inconclusive** = the label cannot be
trusted, so the signature cannot be judged.

The judgement changed the module: in two rows (lvl-2_2019_14, lvl-7_2007_22) the chosen
value was a datum copied from the statement, but `minus_one` and `div_10` won the tie.
`statement_number` now ranks second, right after the sum/product mix-up, and stays silent
when the correct value is also written in the statement (lvl-0_2015_17, where every option
is a given number). The table shows the signature before and after the change and the
`confidence` of the final one; the verdict is for the final signature.

| # | id | level | topic | chosen | signature (v1 → final) | conf. | verdict | why |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | lvl-0_2018_4 | 0 | boards | E | plus_one | low | no | the options are point labels, not quantities |
| 2 | lvl-6_2019_4 | 6 | arithmetic | E | plus_one | high | yes | a count of consecutive sums: one end point too many |
| 3 | lvl-5_2014_2 | 5 | spatial | E | plus_one | low | yes | counting shapes in a figure: one region too many |
| 4 | lvl-3_2019_1 | 3 | arithmetic | D | plus_one | high | yes | the last jump counted once too often |
| 5 | lvl-0_2016_15 | 0 | arithmetic | D | missing_subtract | high | no | the difference equals a datum by coincidence |
| 6 | lvl-6_2007_2 | 6 | arithmetic | D | missing_subtract | low | yes | the wrong transfer was used: exactly that datum |
| 7 | lvl-5_2015_17 | 5 | areas | C | double | high | partial | the value is doubled, but nothing is "counted twice" |
| 8 | lvl-5_2020_13 | 5 | spatial | B | half | low | no | a different (wrong) construction, not half of the right one |
| 9 | lvl-7_2017_25 | 7 | digits | D | statement_number | low | yes | the "multiple of 7" copied as the answer |
| 10 | lvl-4_2022_8 | 4 | digits | B | missing_add | high | inconclusive | see the note below the table |
| 11 | lvl-2_2019_14 | 2 | spatial | A | minus_one → statement_number | low | yes | the number of black pieces copied as the answer |
| 12 | lvl-7_2007_22 | 7 | spatial | E | div_10 → statement_number | low | yes | the radius copied as the answer |
| 13 | lvl-5_2024_2 | 5 | arithmetic | C | plus_one | low | yes | the date instead of the date plus one |
| 14 | lvl-3_2022_21 | 3 | arithmetic | C | statement_number | high | yes | an average from the statement copied as the age |
| 15 | lvl-4_2024_11 | 4 | arithmetic | D | missing_add | high | yes | one day's catch left out: exactly that datum |
| 16 | lvl-5_2013_1 | 5 | areas | C | minus_one | low | yes | one shaded small triangle left out |
| 17 | lvl-7_2009_12 | 7 | digits | B | half | high | partial | half is plausible (a symmetric case forgotten) but not certain |
| 18 | lvl-0_2015_17 | 0 | digits | C | minus_one | low | no | every option is a given number; the off-by-one is a coincidence |
| 19 | lvl-5_2014_7 | 5 | arithmetic | C | missing_add | low | partial | the datum is the key quantity, but it is not "added" |
| 20 | lvl-3_2020_3 | 3 | arithmetic | E | half | high | partial | half of a product: plausible, the sum (another option) would be sharper |

| verdict | all 20 | confidence high (9) | confidence low (11) |
| --- | ---: | ---: | ---: |
| yes | 11 | 4 | 7 |
| partial | 4 | 3 | 1 |
| no | 4 | 1 | 3 |
| inconclusive | 1 | 1 | 0 |

Row 10 (lvl-4_2022_8): the English and the Catalan images print the same question (count
the integers between two given bounds whose digits are all odd) and the same five options;
enumerating that question in code gives the value of option A, while the dataset label is
E. We cannot tell whether the label, the transcription or our reading of the printed text
is at fault, so the row is marked inconclusive and not counted against the signature. (The
Catalan OCR also misreads option D of this problem, "10" instead of "100".)

Eleven of twenty signatures explain the error outright and four more state a true relation
in a loose wording. On this sample the confidence flag does not separate the verdicts
(4 yes of 9 high, 7 yes of 11 low): n=20 is too small to see the 78% vs 47% gap of the
null model, and three of the four "no" are of kinds the flag does not target:

1. **Options that are not quantities** (rows 1, 18): point labels, or every option is a
   number from the statement. A cheap guard: when four or five options are statement
   numbers, or the options are 1..5 in order, return `none`.
2. **Coincidences** (rows 5, 8): the null model says about half of the signatures above 10
   and three quarters below are of this kind.
3. **A datum that is a bound** (row 10, if the label were right): "between 100 and 300" is
   not a term to add.

## Limits

- The signature says what relation holds between two numbers, not what the student
  thought. Shown after the solution, it is a plausible reading of the error, not a verdict.
- It is never a hint: shown with the options enabled it gives the answer away in one step.
- 46% of the problems have no numeric correct option (pictures, letters, OCR failures):
  there the function returns `None` and the web shows nothing new.
- Catalan options and texts are the same OCR per image; the statement numbers are read
  from the row's own `text`, so the Catalan row gives the same signatures as long as the
  numbers are written with digits.
