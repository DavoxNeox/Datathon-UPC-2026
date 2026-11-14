# Error analysis

Accuracy by topic, family, language, level and text_only, from `results/eval-*.csv` joined with `data/val.jsonl` by id and language. Every percentage has its n next to it; the `always D` column is what answering the fallback letter scores on the same problems. Problem ids only, no text.

## eval-20261114-134204-A-baseline-eng281.csv

281 problems, 61 correct (22%); always D would score 23%, random 20%. Board estimate: mean 9.0 s, worst 16.7 s.

### Topic (visual = most problems need the figure)

| Topic | n | correct | accuracy | always D | random | board s (mean) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| arithmetic (text) | 53 | 11 | 21% | 19% | 20% | 9.8 |
| logic (text) | 13 | 2 | 15% | 23% | 20% | 10.9 |
| digits (text) | 55 | 14 | 25% | 25% | 20% | 8.8 |
| counting (text) | 10 | 2 | 20% | 30% | 20% | 9.5 |
| areas (visual) | 63 | 13 | 21% | 25% | 20% | 8.5 |
| angles (visual) | 6 | 2 | 33% | 0% | 20% | 10.4 |
| spatial (visual) | 61 | 12 | 20% | 21% | 20% | 8.5 |
| boards (visual) | 20 | 5 | 25% | 30% | 20% | 9.1 |
| **all** | 281 | 61 | 22% | 23% | 20% | 9.0 |

### Visual vs text topics

| Visual vs text topics | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| text topics | 131 | 29 | 22% | 23% | 20% |
| visual topics | 150 | 32 | 21% | 23% | 20% |
| **all** | 281 | 61 | 22% | 23% | 20% |

On the visual topics the copilot reads a text that describes a picture it cannot see: 21% on 150 problems against 23% for always D and 20% for random, at or below the guessing floors: chance level.

### Family (keyword family of text-only problems; (none) = no family)

| Family | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| (none) | 217 | 49 | 23% | 25% | 20% |
| digit_sum | 15 | 4 | 27% | 20% | 20% |
| divisibility | 6 | 3 | 50% | 50% | 20% |
| sharing | 5 | 1 | 20% | 40% | 20% |
| liars | 5 | 0 | 0% | 0% | 20% |
| speed_time | 4 | 1 | 25% | 25% | 20% |
| percent | 4 | 0 | 0% | 0% | 20% |
| sum_equations | 4 | 1 | 25% | 0% | 20% |
| ages | 4 | 0 | 0% | 0% | 20% |
| money | 4 | 1 | 25% | 0% | 20% |
| work_rate | 4 | 0 | 0% | 0% | 20% |
| average | 3 | 0 | 0% | 0% | 20% |
| clock | 3 | 0 | 0% | 0% | 20% |
| weights | 2 | 1 | 50% | 50% | 20% |
| consecutive | 1 | 0 | 0% | 0% | 20% |
| **all** | 281 | 61 | 22% | 23% | 20% |

### Language

| Language | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| eng | 281 | 61 | 22% | 23% | 20% |
| **all** | 281 | 61 | 22% | 23% | 20% |

### Level (0 = grade 5)

| Level | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 20 | 6 | 30% | 45% | 20% |
| 1 | 17 | 6 | 35% | 35% | 20% |
| 2 | 29 | 10 | 34% | 31% | 20% |
| 3 | 12 | 1 | 8% | 25% | 20% |
| 4 | 62 | 15 | 24% | 19% | 20% |
| 5 | 53 | 9 | 17% | 19% | 20% |
| 6 | 49 | 5 | 10% | 18% | 20% |
| 7 | 39 | 9 | 23% | 18% | 20% |
| **all** | 281 | 61 | 22% | 23% | 20% |

### text_only (M3Kang: the figure is not needed)

| text_only | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| True | 123 | 30 | 24% | 20% | 20% |
| False | 158 | 31 | 20% | 26% | 20% |
| **all** | 281 | 61 | 22% | 23% | 20% |

### OCR read the options

| OCR read the options | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| True | 167 | 37 | 22% | 20% | 20% |
| False | 114 | 24 | 21% | 27% | 20% |
| **all** | 281 | 61 | 22% | 23% | 20% |

### Letters

| letter | predicted | true |
| --- | ---: | ---: |
| A | 92 | 55 |
| B | 51 | 62 |
| C | 1 | 52 |
| D | 135 | 65 |
| E | 2 | 47 |

## eval-20261114-141057-A-solvers-plus-D-eng281-v2.csv

281 problems, 65 correct (23%); always D would score 23%, random 20%. Board estimate: mean 0.8 s, worst 39.3 s.

### Topic (visual = most problems need the figure)

| Topic | n | correct | accuracy | always D | random | board s (mean) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| arithmetic (text) | 53 | 10 | 19% | 19% | 20% | 3.3 |
| logic (text) | 13 | 3 | 23% | 23% | 20% | 3.0 |
| digits (text) | 55 | 14 | 25% | 25% | 20% | 0.0 |
| counting (text) | 10 | 3 | 30% | 30% | 20% | 0.0 |
| areas (visual) | 63 | 16 | 25% | 25% | 20% | 0.0 |
| angles (visual) | 6 | 0 | 0% | 0% | 20% | 0.0 |
| spatial (visual) | 61 | 13 | 21% | 21% | 20% | 0.0 |
| boards (visual) | 20 | 6 | 30% | 30% | 20% | 0.0 |
| **all** | 281 | 65 | 23% | 23% | 20% | 0.8 |

### Visual vs text topics

| Visual vs text topics | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| text topics | 131 | 30 | 23% | 23% | 20% |
| visual topics | 150 | 35 | 23% | 23% | 20% |
| **all** | 281 | 65 | 23% | 23% | 20% |

On the visual topics the copilot reads a text that describes a picture it cannot see: 23% on 150 problems against 23% for always D and 20% for random, at or below the guessing floors: chance level.

### Family (keyword family of text-only problems; (none) = no family)

| Family | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| (none) | 217 | 55 | 25% | 25% | 20% |
| digit_sum | 15 | 3 | 20% | 20% | 20% |
| divisibility | 6 | 3 | 50% | 50% | 20% |
| sharing | 5 | 2 | 40% | 40% | 20% |
| liars | 5 | 0 | 0% | 0% | 20% |
| speed_time | 4 | 1 | 25% | 25% | 20% |
| percent | 4 | 0 | 0% | 0% | 20% |
| sum_equations | 4 | 0 | 0% | 0% | 20% |
| ages | 4 | 0 | 0% | 0% | 20% |
| money | 4 | 0 | 0% | 0% | 20% |
| work_rate | 4 | 0 | 0% | 0% | 20% |
| average | 3 | 0 | 0% | 0% | 20% |
| clock | 3 | 0 | 0% | 0% | 20% |
| weights | 2 | 1 | 50% | 50% | 20% |
| consecutive | 1 | 0 | 0% | 0% | 20% |
| **all** | 281 | 65 | 23% | 23% | 20% |

### Language

| Language | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| eng | 281 | 65 | 23% | 23% | 20% |
| **all** | 281 | 65 | 23% | 23% | 20% |

### Level (0 = grade 5)

| Level | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 20 | 9 | 45% | 45% | 20% |
| 1 | 17 | 6 | 35% | 35% | 20% |
| 2 | 29 | 9 | 31% | 31% | 20% |
| 3 | 12 | 3 | 25% | 25% | 20% |
| 4 | 62 | 12 | 19% | 19% | 20% |
| 5 | 53 | 10 | 19% | 19% | 20% |
| 6 | 49 | 9 | 18% | 18% | 20% |
| 7 | 39 | 7 | 18% | 18% | 20% |
| **all** | 281 | 65 | 23% | 23% | 20% |

### text_only (M3Kang: the figure is not needed)

| text_only | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| True | 123 | 24 | 20% | 20% | 20% |
| False | 158 | 41 | 26% | 26% | 20% |
| **all** | 281 | 65 | 23% | 23% | 20% |

### OCR read the options

| OCR read the options | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| True | 167 | 34 | 20% | 20% | 20% |
| False | 114 | 31 | 27% | 27% | 20% |
| **all** | 281 | 65 | 23% | 23% | 20% |

### Letters

| letter | predicted | true |
| --- | ---: | ---: |
| A | 0 | 55 |
| B | 0 | 62 |
| C | 0 | 52 |
| D | 281 | 65 |
| E | 0 | 47 |
