# Error signatures: what a wrong option says about the mistake

`copilot/signatures.py` compares, in code, the value of the option the student picked
with the value of the correct option (both read from the OCR `options`, with units,
decimal commas and fractions) and names the slip: a datum copied from the statement, a
doubling, an off-by-one, a dropped zero, swapped digits, a sign, a statement number not
added or subtracted, a sum where a product was needed. The student gets a bilingual
diagnostic that never states the correct value or letter (every text passes
`copilot/leak_filter.py`). No LLM is involved: the options are the knowledge, Kangaroo
designed each distractor to capture one error.

Measured with `python3 laptop/measure_signatures.py --out docs/error-signatures-coverage.md`
(full tables there). Ids only, no problem text.

## Coverage (val + train, English rows, 1747 ids)

| | n | share |
| --- | ---: | ---: |
| problems with OCR options | 1078 / 1747 | 62% |
| problems whose correct option is a single number | 938 / 1747 | 54% |
| numeric distractors of those problems | 3557 / 3752 | 95% |
| numeric distractors with a signature other than `none` | 1381 / 3557 | 39% |
| problems with at least one signed distractor | 696 / 938 | 74% |

By topic the share of signed distractors goes from 31% (angles, counting) to 57% (logic,
n=79 distractors); by level from 49% (level 0) down to 35-38% (levels 4-7): the harder
the problem, the more the distractors are "another wrong reasoning" rather than a slip on
the right one. Problems with at least one signed distractor: 82-85% at levels 0-3,
68-73% at levels 4-7.

## Distribution of signatures

Simulated student (each numeric distractor picked once, n=3557): plus_one 9%, minus_one
9%, statement_number 6%, double 3%, half 3%, missing_add 3%, missing_subtract 3%,
digits_swapped 1%, product_vs_sum 1%, sign / times_10 / div_10 / sum_vs_product under
1% each, none 61%.

Over the copilot's own wrong answers in `results/eval-*.csv` (7 runs, 765 wrong answers;
three of the runs are the same 281 val problems): 50% have no numeric pair to compare
(no OCR options), 28% `none`, and 22% get a signature (plus_one 6%, minus_one 4%,
statement_number 3%, double 3%, missing_subtract 3%, half 1%, the rest under 1%).
These are the model's errors, mostly the always-D fallback, not a student's: the
distribution says what the web would show, not what children do.

## Manual judgement of 20 signed distractors

Twenty signed distractors drawn at random (`--sample 20 --seed 1`, first version of the
order) and judged by looking at the problem image in `data/images`. Verdicts: **yes** =
the signature explains how a student would land on that option; **partial** = the
relation is true but the wording or the mechanism does not fit the problem; **no** =
coincidence (or the options are not quantities).

The judgement changed the module: in two rows (lvl-2_2019_14, lvl-7_2007_22) the chosen
value was a datum copied from the statement, but `minus_one` and `div_10` won the tie.
`statement_number` now ranks second, right after the sum/product mix-up, and stays silent
when the correct value is also written in the statement (lvl-0_2015_17, where every option
is a given number). The table shows the signature before and after the change; the
verdict is for the final one.

| # | id | level | topic | chosen | signature (v1 → final) | verdict | why |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | lvl-0_2018_4 | 0 | boards | E | plus_one | no | the options are point labels, not quantities |
| 2 | lvl-6_2019_4 | 6 | arithmetic | E | plus_one | yes | a count of consecutive sums: one end point too many |
| 3 | lvl-5_2014_2 | 5 | spatial | E | plus_one | yes | counting shapes in a figure: one region too many |
| 4 | lvl-3_2019_1 | 3 | arithmetic | D | plus_one | yes | the last jump counted once too often |
| 5 | lvl-0_2016_15 | 0 | arithmetic | D | missing_subtract | no | the difference equals a datum by coincidence |
| 6 | lvl-6_2007_2 | 6 | arithmetic | D | missing_subtract | yes | the wrong transfer was used: exactly that datum |
| 7 | lvl-5_2015_17 | 5 | areas | C | double | partial | the value is doubled, but nothing is "counted twice" |
| 8 | lvl-5_2020_13 | 5 | spatial | B | half | no | a different (wrong) construction, not half of the right one |
| 9 | lvl-7_2017_25 | 7 | digits | D | statement_number | yes | the "multiple of 7" copied as the answer |
| 10 | lvl-4_2022_8 | 4 | digits | B | missing_add | no | the datum is a bound, not a term; the dataset label itself looks wrong here |
| 11 | lvl-2_2019_14 | 2 | spatial | A | minus_one → statement_number | yes | the number of black pieces copied as the answer |
| 12 | lvl-7_2007_22 | 7 | spatial | E | div_10 → statement_number | yes | the radius copied as the answer |
| 13 | lvl-5_2024_2 | 5 | arithmetic | C | plus_one | yes | the date instead of the date plus one |
| 14 | lvl-3_2022_21 | 3 | arithmetic | C | statement_number | yes | an average from the statement copied as the age |
| 15 | lvl-4_2024_11 | 4 | arithmetic | D | missing_add | yes | one day's catch left out: exactly that datum |
| 16 | lvl-5_2013_1 | 5 | areas | C | minus_one | yes | one shaded small triangle left out |
| 17 | lvl-7_2009_12 | 7 | digits | B | half | partial | half is plausible (a symmetric case forgotten) but not certain |
| 18 | lvl-0_2015_17 | 0 | digits | C | minus_one | no | every option is a given number; the off-by-one is a coincidence |
| 19 | lvl-5_2014_7 | 5 | arithmetic | C | missing_add | partial | the datum is the key quantity, but it is not "added" |
| 20 | lvl-3_2020_3 | 3 | arithmetic | E | half | partial | half of a product: plausible, the sum (another option) would be sharper |

| verdict | n |
| --- | ---: |
| yes | 11 |
| partial | 4 |
| no | 5 |

Eleven of twenty signatures explain the error outright and four more state a true relation
in a loose wording: 15/20 would help a student who just failed. The five misses are of
three kinds, and each has a cheap guard that the next version could add:

1. **Options that are not quantities** (rows 1, 18): point labels, or every option is a
   number from the statement. A guard: when four or five options are statement numbers,
   or the options are 1..5 in order, return `none`.
2. **Small-number coincidences** (rows 5, 8): with answers under 10 an off-by-one, a half
   or a difference equal to a datum happen by chance. The evidence carries the values, so
   the web could show the generic text when the correct value is below 4.
3. **A datum that is a bound** (row 10): "between 100 and 300" is not a term to add.

## Limits

- The signature says what relation holds between two numbers, not what the student
  thought. It is a prompt for reflection ("check the end points"), not a verdict.
- Any relation hint narrows the five options: shown before the second attempt it works
  like a rung-3 hint and should count as one (an answer after it never raises mastery).
- 46% of the problems have no numeric correct option (pictures, letters, OCR failures):
  there the function returns `None` and the web shows nothing new.
- Catalan options and texts are the same OCR per image; the statement numbers are read
  from the row's own `text`, so the Catalan row gives the same signatures as long as the
  numbers are written with digits.
