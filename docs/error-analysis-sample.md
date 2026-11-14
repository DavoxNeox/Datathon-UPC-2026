# Error analysis

Accuracy by topic, family, language, level and text_only, from `results/eval-*.csv` joined with `data/val.jsonl` by id and language. Every percentage has its n next to it; the `always D` column is what answering the fallback letter scores on the same problems. Problem ids only, no text.

## eval-20261114-133802-B-eng50.csv + eval-20261114-133827-B-cat50.csv

100 problems, 27 correct (27%); always D would score 34%, random 20%. Board estimate: mean 9.9 s, worst 21.6 s.

### Topic (visual = most problems need the figure)

| Topic | n | correct | accuracy | always D | random | board s (mean) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| arithmetic (text) | 14 | 4 | 29% | 14% | 20% | 11.3 |
| logic (text) | 2 | 0 | 0% | 0% | 20% | 11.9 |
| digits (text) | 20 | 4 | 20% | 40% | 20% | 10.3 |
| counting (text) | 10 | 3 | 30% | 40% | 20% | 9.2 |
| areas (visual) | 22 | 8 | 36% | 36% | 20% | 8.8 |
| angles (visual) | 4 | 2 | 50% | 0% | 20% | 11.8 |
| spatial (visual) | 16 | 3 | 19% | 38% | 20% | 9.0 |
| boards (visual) | 12 | 3 | 25% | 50% | 20% | 10.1 |
| **all** | 100 | 27 | 27% | 34% | 20% | 9.9 |

### Visual vs text topics

| Visual vs text topics | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| text topics | 46 | 11 | 24% | 30% | 20% |
| visual topics | 54 | 16 | 30% | 37% | 20% |
| **all** | 100 | 27 | 27% | 34% | 20% |

On the visual topics the copilot reads a text that describes a picture it cannot see: 30% on 54 problems against 37% for always D and 20% for random, at or below the guessing floors: chance level.

### Family (keyword family of text-only problems; (none) = no family)

| Family | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| (none) | 76 | 22 | 29% | 37% | 20% |
| digit_sum | 6 | 1 | 17% | 33% | 20% |
| divisibility | 4 | 2 | 50% | 100% | 20% |
| average | 4 | 0 | 0% | 0% | 20% |
| speed_time | 2 | 2 | 100% | 0% | 20% |
| sharing | 2 | 0 | 0% | 0% | 20% |
| percent | 2 | 0 | 0% | 0% | 20% |
| sum_equations | 2 | 0 | 0% | 0% | 20% |
| ages | 2 | 0 | 0% | 0% | 20% |
| **all** | 100 | 27 | 27% | 34% | 20% |

### Language

| Language | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| eng | 50 | 15 | 30% | 34% | 20% |
| cat | 50 | 12 | 24% | 34% | 20% |
| **all** | 100 | 27 | 27% | 34% | 20% |

### Level (0 = grade 5)

| Level | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 8 | 4 | 50% | 75% | 20% |
| 1 | 4 | 2 | 50% | 100% | 20% |
| 2 | 10 | 5 | 50% | 80% | 20% |
| 3 | 2 | 0 | 0% | 0% | 20% |
| 4 | 18 | 6 | 33% | 22% | 20% |
| 5 | 14 | 4 | 29% | 29% | 20% |
| 6 | 20 | 3 | 15% | 10% | 20% |
| 7 | 24 | 3 | 12% | 25% | 20% |
| **all** | 100 | 27 | 27% | 34% | 20% |

### text_only (M3Kang: the figure is not needed)

| text_only | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| True | 52 | 10 | 19% | 27% | 20% |
| False | 48 | 17 | 35% | 42% | 20% |
| **all** | 100 | 27 | 27% | 34% | 20% |

### OCR read the options

| OCR read the options | n | correct | accuracy | always D | random |
| --- | ---: | ---: | ---: | ---: | ---: |
| True | 68 | 18 | 26% | 35% | 20% |
| False | 32 | 9 | 28% | 31% | 20% |
| **all** | 100 | 27 | 27% | 34% | 20% |

### Letters

| letter | predicted | true |
| --- | ---: | ---: |
| A | 27 | 14 |
| B | 18 | 18 |
| C | 1 | 16 |
| D | 49 | 34 |
| E | 5 | 18 |
