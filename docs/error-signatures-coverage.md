# Error signatures: coverage on M3Kang

Rows: 1747 problems in `eng` from val.jsonl, train.jsonl; 1078 with OCR options (62%); 938 whose correct option is a single number (54%). Every distractor of those is diagnosed as if the student had picked it. `numeric` = the distractor is a single number too; `signed` = a signature other than `none`.

### Topic

| Topic | problems | distractors | numeric | signed | % signed | problems ≥1 signed | % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| arithmetic | 289 | 1156 | 1132 | 483 | 43% | 228 | 79% |
| logic | 21 | 84 | 79 | 45 | 57% | 18 | 86% |
| digits | 241 | 964 | 933 | 366 | 39% | 187 | 78% |
| counting | 42 | 168 | 164 | 52 | 32% | 30 | 71% |
| areas | 149 | 596 | 511 | 167 | 33% | 91 | 61% |
| angles | 39 | 156 | 135 | 42 | 31% | 24 | 62% |
| spatial | 119 | 476 | 461 | 188 | 41% | 89 | 75% |
| boards | 38 | 152 | 142 | 64 | 45% | 32 | 84% |
| **all** | 938 | 3752 | 3557 | 1407 | 40% | 699 | 75% |

### Level

| Level | problems | distractors | numeric | signed | % signed | problems ≥1 signed | % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 68 | 272 | 264 | 131 | 50% | 56 | 82% |
| 1 | 51 | 204 | 190 | 81 | 43% | 42 | 82% |
| 2 | 58 | 232 | 221 | 96 | 43% | 46 | 79% |
| 3 | 61 | 244 | 229 | 110 | 48% | 52 | 85% |
| 4 | 195 | 780 | 755 | 281 | 37% | 145 | 74% |
| 5 | 178 | 712 | 682 | 251 | 37% | 130 | 73% |
| 6 | 170 | 680 | 634 | 231 | 36% | 121 | 71% |
| 7 | 157 | 628 | 582 | 226 | 39% | 107 | 68% |
| **all** | 938 | 3752 | 3557 | 1407 | 40% | 699 | 75% |

### Source

| Source | problems | distractors | numeric | signed | % signed | problems ≥1 signed | % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train.jsonl | 799 | 3196 | 3021 | 1186 | 39% | 588 | 74% |
| val.jsonl | 139 | 556 | 536 | 221 | 41% | 111 | 80% |
| **all** | 938 | 3752 | 3557 | 1407 | 40% | 699 | 75% |

### Distribution, simulated student (each numeric distractor picked once)

| signature | n | % |
| --- | ---: | ---: |
| sum_vs_product | 6 | 0% |
| product_vs_sum | 18 | 1% |
| digits_swapped | 21 | 1% |
| sign | 8 | 0% |
| times_10 | 6 | 0% |
| div_10 | 14 | 0% |
| double | 125 | 4% |
| half | 138 | 4% |
| plus_one | 337 | 9% |
| minus_one | 350 | 10% |
| missing_add | 119 | 3% |
| missing_subtract | 112 | 3% |
| statement_number | 153 | 4% |
| none | 2150 | 60% |
| **numeric distractors** | 3557 | 100% |

### Distribution over the copilot's wrong answers in results/

7 runs, 998 rows, 765 wrong answers (`answer` != `label`); `(not numeric)` = the problem has no numeric pair to compare (pictures, OCR noise) or is not in the inputs. These are the model's errors, not a student's: they say what the web would show if the copilot were the student.

| run | rows |
| --- | ---: |
| eval-20261114-124904-A-sample-smoke.csv | 5 |
| eval-20261114-133810-A-baseline-eng50.csv | 50 |
| eval-20261114-133855-A-bias-eng50.csv | 50 |
| eval-20261114-134204-A-baseline-eng281.csv | 281 |
| eval-20261114-134548-A-solvers-plus-D-eng50.csv | 50 |
| eval-20261114-140931-A-solvers-plus-D-eng281.csv | 281 |
| eval-20261114-141057-A-solvers-plus-D-eng281-v2.csv | 281 |

### Signatures of the wrong answers

| signature | n | % |
| --- | ---: | ---: |
| product_vs_sum | 3 | 0% |
| times_10 | 2 | 0% |
| div_10 | 1 | 0% |
| double | 20 | 3% |
| half | 10 | 1% |
| plus_one | 48 | 6% |
| minus_one | 34 | 4% |
| missing_add | 3 | 0% |
| missing_subtract | 26 | 3% |
| statement_number | 22 | 3% |
| none | 211 | 28% |
| (not numeric) | 385 | 50% |
| **wrong answers** | 765 | 100% |

### Candidates dropped by the leak filter

A matching signature whose text would have named the correct value (a Catalan number word, a statement number equal to the answer); the next candidate was used.

| signature | dropped |
| --- | ---: |
| sum_vs_product | 12 |
| product_vs_sum | 3 |
| missing_add | 3 |
| missing_subtract | 1 |
