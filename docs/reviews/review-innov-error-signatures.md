# Review of `team/innov-error-signatures-3b1c96` (42564f4, 14 Nov 2026)

Scope: `copilot/signatures.py`, `laptop/measure_signatures.py`, `tests/test_signatures.py`,
`docs/error-signatures.md`, `docs/error-signatures-coverage.md`, INTERFACES section. Not wired into
the web app (a two-line proposal in INTERFACES.md). Nothing changed by me.

**Executed**: the branch's tests (OK); `laptop/measure_signatures.py` (coverage tables regenerated);
the 20 rows of the manual judgement run through `diagnose()`; every numeric distractor of the 938
problems diagnosed to measure how often the text pins the exact answer; the leak filter over every
text produced. **Only read**: the verdicts themselves (I did not open the 20 images).

## Executive summary

1. The brief promised a diagnosis of the slip behind a wrong numeric option with leak-filtered texts,
   and a coverage figure. Delivered and honest: 39% of numeric distractors and 74% of problems with a
   numeric correct option get a signature (recomputed exactly), the 20 judged rows give the signature
   the table says (20/20), the leak filter flags none of the texts (0 of 3,557), stdlib only.
2. The texts do not state the answer, but **83% of them hand it over in one arithmetic step**:
   1,150 of 1,381 signed diagnoses name a relation (double, half, one too many, one too few,
   "add the 7 of the statement") that identifies exactly one option. The leak filter cannot see
   this, and a second attempt after such a text is not a second attempt. Wired as proposed (options
   re-enabled for one more try) this would be a CRITICAL leak; as a post-mortem explanation after
   the problem is closed, it is a good feature.
3. Precision is modest and the sample small: 11 yes, 4 partial, 5 no of 20, one judge; 56% of the
   signed distractors have a correct value under 10, where off-by-one, half and "difference equals
   a datum" happen by chance (three of the five misses are of that kind).

## Findings

**S1 (IMPORTANT; CRITICAL if wired for a second attempt). The relation pins the answer.**
`copilot/signatures.py:_candidates` texts for `double`, `half`, `plus_one`, `minus_one`, `sign`,
`times_10`, `div_10`, `missing_add`, `missing_subtract`, `sum_vs_product`, `product_vs_sum` and
`digits_swapped` each name an operation on the chosen value. Measured over every numeric
distractor of the 938 problems: 1,150 of 1,381 signed diagnoses (83%) leave exactly one option
consistent with the text (plus_one 315/321, minus_one 334/336, double 114/115, half 124/124,
missing_add 104/104, missing_subtract 105/105, digits_swapped 14/21, times_10 3/6, div_10 7/13).
`docs/error-signatures.md` ("any relation hint narrows the five options") understates it: it does
not narrow, it names. *Fix:* use the diagnosis **after** the problem is closed (with the correction,
as the "why" of the wrong option), never before a retry; if a retry is wanted, show only the
`statement_number` and `none` texts and a neutral "revisa els extrems del recompte" for the rest,
and count the retry at rung 4.

**S2 (IMPORTANT). Small-number coincidences are the majority of the signed cases.** 774 of 1,381
signed distractors (56%) have a correct value below 10. The manual judgement's misses 5, 8 and 18
are of this kind, and the doc proposes the guard itself. *Fix:* return `none` when the correct value
is below 4, or require two signatures to agree for values below 10; re-measure coverage after it.

**S3 (IMPORTANT). Precision claim: 15/20 "would help" from one judge on 20 rows.** The sample was
drawn with the first version of the order and the order was then changed after reading it, so the
final verdicts are on a rule adjusted to the sample. *Fix:* a second draw of 20 at the final order,
a second judge, and report precision per signature (plus_one and minus_one are two thirds of the
volume).

**M1 (MINOR). `evidence` carries `correct_value` and `difference`.** INTERFACES says never to send
it to the browser; the future web code must strip it (today `/api/state` serializes whole hint
dicts). Add a test on `webapp` when wiring.

**M2 (MINOR). Row 10 of the judgement says "the dataset label itself looks wrong here"
(`lvl-4_2022_8`).** A public document that accuses M3Kang of a wrong label needs the check written
down (the statement, the computation) or the sentence removed.

**M3 (MINOR). Catalan.** Correct and natural overall ("relliscada", "et sobra el primer o el
darrer"). "T'has menjat xifres" is colloquial; the `statement_number` text is two clauses long for a
ten-year-old; "Revisa les unitats" is a guess (a factor of ten is not always a unit slip). The
avoidance of "un/una" to dodge the leak filter is the filter's problem, not the text's: the filter
should treat "un/una" as the number 1 only when the correct value is 1 (it already does, since
`_spellings(1)` is only consulted then), so the constraint can be dropped.

**M4 (MINOR). The distribution over the copilot's wrong answers is the model's, not a child's.**
The doc says so; keep that sentence when the figure moves to the README.

## Figures checked

| Claim | Recomputed | Status |
| --- | --- | --- |
| 1078/1747 with options, 938 numeric correct, 3557 numeric distractors, 1381 signed (39%), 696 problems (74%) | identical, `measure_signatures.py` | ✓ |
| signatures of the 20 judged rows | 20/20 as in the table | ✓ |
| texts never flagged by the leak filter | 0 of 3557 | ✓ |
| 34 tests | suite OK | ✓ |

## Verdict

Keep the module and the measurement; change where it is shown. As the explanation of a wrong answer
after the fact it is the most honest use of M3Kang's options the team has. As a pre-retry hint it
gives the answer away in 83% of the cases.
