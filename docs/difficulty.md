# Empirical difficulty per class: measurements

`python3 laptop/measure_difficulty.py --steps 60 --neighbors retrieval` on 14 Nov 2026, laptop, bank data/train.jsonl + data/val.jsonl. Estimator constants: a = 3, MIN_N = 3, 0.25 rate points per level, max shift 2 levels. See the module docstring of copilot/difficulty.py for the formula and laptop/measure_difficulty.py for the four experiments.

## 1. Label class: ten of simulate's students, true difficulty = M3Kang band

Students: threshold0,threshold1,threshold2,threshold3,threshold4,threshold5,threshold6,threshold7,random20-1,improving; 60 steps each, 3.2 s on the laptop.

- Answers: 600; problems answered: 456 of 1747 in the bank; with at least 3 answers (rated): 21.
- Answers per problem: n=1: 340, n=2: 95, n=3: 17, n=4: 2, n=5: 1, n=6: 1.
- Rated problems whose adjusted level differs from the band: 21 of 21; 1 change band once rounded, as the trainer's rule does (1 move by one level or more).
- Correlation between the M3Kang band and the observed rate of correct answers, over the 456 answered problems: Pearson 0.09, Spearman 0.10 (negative = harder bands are answered less often).

Rate per level (`by_level` of the report; `prior` is the shrunk rate the estimator uses):

| level | n | correct | p_correct | prior |
|---|---|---|---|---|
| 0 | 66 | 33 | 0.50 | 0.50 |
| 1 | 71 | 36 | 0.51 | 0.51 |
| 2 | 87 | 45 | 0.52 | 0.52 |
| 3 | 86 | 39 | 0.45 | 0.46 |
| 4 | 74 | 39 | 0.53 | 0.53 |
| 5 | 65 | 33 | 0.51 | 0.51 |
| 6 | 60 | 28 | 0.47 | 0.47 |
| 7 | 91 | 63 | 0.69 | 0.69 |

Hardest problems observed / Problemes més difícils observats (`hardest`):

| id | level | n | p_correct | p_without_hints | shrunk | adjusted_level |
|---|---|---|---|---|---|---|
| lvl-2_2020_26 | 2 | 3 | 0.00 | 0.00 | 0.26 | 3.03 |
| lvl-3_2016_23 | 3 | 3 | 0.33 | 0.33 | 0.39 | 3.24 |
| lvl-3_2022_10 | 3 | 3 | 0.33 | 0.33 | 0.39 | 3.24 |
| lvl-3_2024_20 | 3 | 3 | 0.33 | 0.33 | 0.39 | 3.24 |
| lvl-1_2016_19 | 1 | 3 | 0.33 | 0.33 | 0.42 | 1.35 |
| lvl-1_2016_8 | 1 | 3 | 0.33 | 0.33 | 0.42 | 1.35 |
| lvl-1_2017_11 | 1 | 3 | 0.33 | 0.33 | 0.42 | 1.35 |
| lvl-1_2022_14 | 1 | 3 | 0.33 | 0.33 | 0.42 | 1.35 |
| lvl-2_2016_5 | 2 | 3 | 0.33 | 0.33 | 0.42 | 2.37 |
| lvl-2_2020_16 | 2 | 3 | 0.33 | 0.33 | 0.42 | 2.37 |

Easiest problems observed / Problemes més fàcils observats (`easiest`):

| id | level | n | p_correct | p_without_hints | shrunk | adjusted_level |
|---|---|---|---|---|---|---|
| lvl-2_2024_25 | 2 | 3 | 0.67 | 0.67 | 0.59 | 1.70 |
| lvl-2_2022_17 | 2 | 3 | 0.67 | 0.67 | 0.59 | 1.70 |
| lvl-2_2019_20 | 2 | 3 | 0.67 | 0.67 | 0.59 | 1.70 |
| lvl-2_2018_23 | 2 | 3 | 0.67 | 0.67 | 0.59 | 1.70 |
| lvl-1_2018_15 | 1 | 3 | 0.67 | 0.67 | 0.59 | 0.68 |
| lvl-1_2015_17 | 1 | 3 | 0.67 | 0.67 | 0.59 | 0.68 |
| lvl-2_2019_17 | 2 | 6 | 0.50 | 0.50 | 0.51 | 2.04 |
| lvl-1_2016_7 | 1 | 4 | 0.50 | 0.50 | 0.50 | 1.02 |
| lvl-3_2016_4 | 3 | 4 | 0.50 | 0.50 | 0.48 | 2.90 |
| lvl-2_2017_21 | 2 | 5 | 0.40 | 0.40 | 0.44 | 2.29 |

## 2. Hidden class: ten threshold students on a hidden difficulty

Thresholds (0, 1, 2, 3, 4, 5, 6, 7, 2, 5); hidden level = band + offset(id), offsets -2/-1/0/+1/+2 for 10/20/40/20/10% of the ids (1047 of 1747 bank problems are off their band); a student above their threshold guesses a letter. 60 steps each, 3.4 s on the laptop.

- Answers: 600; problems answered: 409 of 1747 in the bank; with at least 3 answers (rated): 41.
- Answers per problem: n=1: 280, n=2: 88, n=3: 25, n=4: 12, n=5: 3, n=6: 1.
- Rated problems whose adjusted level differs from the band: 37 of 41; 17 change band once rounded, as the trainer's rule does (0 move by one level or more).
- Correlation between the M3Kang band and the observed rate of correct answers, over the 409 answered problems: Pearson -0.09, Spearman -0.08 (negative = harder bands are answered less often).

Rate per level (`by_level` of the report; `prior` is the shrunk rate the estimator uses):

| level | n | correct | p_correct | prior |
|---|---|---|---|---|
| 0 | 23 | 21 | 0.91 | 0.86 |
| 1 | 54 | 43 | 0.80 | 0.78 |
| 2 | 77 | 43 | 0.56 | 0.56 |
| 3 | 89 | 56 | 0.63 | 0.62 |
| 4 | 94 | 44 | 0.47 | 0.47 |
| 5 | 80 | 47 | 0.59 | 0.58 |
| 6 | 80 | 37 | 0.46 | 0.46 |
| 7 | 103 | 65 | 0.63 | 0.63 |

- Rated problems off their band in the hidden model: 24 of 41.
- Mean absolute error against the hidden difficulty, over the 41 rated problems: band 0.71 levels, adjusted level 0.58 levels.
- Shifts of half a level or more on problems that are off their band: 11 point the right way, 1 the wrong way; 29 rated problems are on their band or barely moved.

Hardest problems observed / Problemes més difícils observats (`hardest`):

| id | level | n | p_correct | p_without_hints | shrunk | adjusted_level |
|---|---|---|---|---|---|---|
| lvl-6_2012_15 | 6 | 3 | 0.00 | 0.00 | 0.23 | 6.93 |
| lvl-6_2014_23 | 6 | 3 | 0.00 | 0.00 | 0.23 | 6.93 |
| lvl-4_2015_22 | 4 | 3 | 0.00 | 0.00 | 0.23 | 4.94 |
| lvl-4_2020_23 | 4 | 3 | 0.00 | 0.00 | 0.23 | 4.94 |
| lvl-5_2020_13 | 5 | 4 | 0.25 | 0.25 | 0.39 | 5.76 |
| lvl-6_2021_25 | 6 | 3 | 0.33 | 0.33 | 0.40 | 6.26 |
| lvl-4_2008_18 | 4 | 3 | 0.33 | 0.33 | 0.40 | 4.27 |
| lvl-7_2010_17 | 7 | 4 | 0.25 | 0.25 | 0.41 | 7.00 |
| lvl-7_2015_24 | 7 | 4 | 0.25 | 0.25 | 0.41 | 7.00 |
| lvl-4_2013_15 | 4 | 5 | 0.40 | 0.40 | 0.43 | 4.17 |

Easiest problems observed / Problemes més fàcils observats (`easiest`):

| id | level | n | p_correct | p_without_hints | shrunk | adjusted_level |
|---|---|---|---|---|---|---|
| lvl-1_2017_11 | 1 | 4 | 1.00 | 1.00 | 0.91 | 0.50 |
| lvl-7_2015_25 | 7 | 4 | 1.00 | 1.00 | 0.84 | 6.15 |
| lvl-3_2021_24 | 3 | 4 | 1.00 | 1.00 | 0.84 | 2.14 |
| lvl-7_2019_5 | 7 | 3 | 1.00 | 1.00 | 0.81 | 6.25 |
| lvl-3_2017_27 | 3 | 3 | 1.00 | 1.00 | 0.81 | 2.25 |
| lvl-3_2017_23 | 3 | 3 | 1.00 | 1.00 | 0.81 | 2.25 |
| lvl-1_2016_8 | 1 | 5 | 0.80 | 0.80 | 0.79 | 0.95 |
| lvl-5_2007_6 | 5 | 3 | 1.00 | 1.00 | 0.79 | 4.17 |
| lvl-2_2019_17 | 2 | 3 | 1.00 | 1.00 | 0.78 | 1.11 |
| lvl-3_2016_23 | 3 | 4 | 0.75 | 0.75 | 0.70 | 2.71 |

## 3. Probes: a new student on the hidden class's history, flag off and on

Three hidden-difficulty students (thresholds (1, 3, 5)) run 60 steps each on a copy of the hidden class's database, once with DIFFICULTY_ADJUST=0 and once with 1 (same seeds). The settled band is simulate's (last 10 non-review problems, M3Kang levels); the hidden column is the hidden levels of the last 10 problems served, which is what the student actually faced.

| probe | DIFFICULTY_ADJUST | n | wrong answers | mean hidden level - threshold | steps on a rated problem | settled band (M3Kang) | hidden levels, last 10 | steps to settle | repeats | laptop ms/step |
|---|---|---|---|---|---|---|---|---|---|---|
| hidden threshold 1 | off | 60 | 29 | 1.52 | 7 | 1-3 (unsettled) | 0-4 | - | 0 | 4.9 |
| hidden threshold 1 | on | 60 | 28 | 1.65 | 4 | 2-5 (unsettled) | 0-7 | - | 0 | 6.6 |
| hidden threshold 3 | off | 60 | 29 | 1.25 | 2 | 2-4 (unsettled) | 1-6 | - | 0 | 7.4 |
| hidden threshold 3 | on | 60 | 27 | 1.40 | 1 | 4-6 (unsettled) | 3-6 | - | 0 | 10.4 |
| hidden threshold 5 | off | 60 | 26 | 1.25 | 3 | 4-7 (unsettled) | 3-7 | - | 0 | 4.2 |
| hidden threshold 5 | on | 60 | 27 | 1.30 | 2 | 5-7 (unsettled) | 3-7 | - | 0 | 5.2 |

## 4. Long history: the hidden class after 300 steps per student

Same ten students and offsets as experiment 2, 300 steps each (11.8 s on the laptop): what the estimate and the probes look like once the class has a term's worth of answers.

- Answers: 3000; problems answered: 1278 of 1747 in the bank; with at least 3 answers (rated): 490.
- Answers per problem: n=1: 452, n=2: 336, n=3: 223, n=4: 168, n=5: 66, n=6: 27, n=7: 5, n=8: 1.
- Rated problems whose adjusted level differs from the band: 431 of 490; 214 change band once rounded, as the trainer's rule does (70 move by one level or more).
- Correlation between the M3Kang band and the observed rate of correct answers, over the 1278 answered problems: Pearson 0.03, Spearman 0.05 (negative = harder bands are answered less often).

Rate per level (`by_level` of the report; `prior` is the shrunk rate the estimator uses):

| level | n | correct | p_correct | prior |
|---|---|---|---|---|
| 0 | 124 | 100 | 0.81 | 0.80 |
| 1 | 221 | 144 | 0.65 | 0.65 |
| 2 | 338 | 198 | 0.59 | 0.58 |
| 3 | 422 | 216 | 0.51 | 0.51 |
| 4 | 415 | 205 | 0.49 | 0.49 |
| 5 | 428 | 231 | 0.54 | 0.54 |
| 6 | 450 | 219 | 0.49 | 0.49 |
| 7 | 602 | 383 | 0.64 | 0.64 |

- Rated problems off their band in the hidden model: 275 of 490.
- Mean absolute error against the hidden difficulty, over the 490 rated problems: band 0.72 levels, adjusted level 0.52 levels.
- Shifts of half a level or more on problems that are off their band: 169 point the right way, 1 the wrong way; 320 rated problems are on their band or barely moved.

Hardest problems observed / Problemes més difícils observats (`hardest`):

| id | level | n | p_correct | p_without_hints | shrunk | adjusted_level |
|---|---|---|---|---|---|---|
| lvl-5_2011_2 | 5 | 6 | 0.00 | 0.00 | 0.18 | 6.44 |
| lvl-5_2016_8 | 5 | 6 | 0.00 | 0.00 | 0.18 | 6.44 |
| lvl-6_2012_15 | 6 | 5 | 0.00 | 0.00 | 0.18 | 7.00 |
| lvl-4_2020_23 | 4 | 5 | 0.00 | 0.00 | 0.18 | 5.24 |
| lvl-3_2024_20 | 3 | 5 | 0.00 | 0.00 | 0.19 | 4.28 |
| lvl-6_2013_9 | 6 | 4 | 0.00 | 0.00 | 0.21 | 7.00 |
| lvl-6_2014_23 | 6 | 4 | 0.00 | 0.00 | 0.21 | 7.00 |
| lvl-6_2015_15 | 6 | 4 | 0.00 | 0.00 | 0.21 | 7.00 |
| lvl-4_2010_16 | 4 | 4 | 0.00 | 0.00 | 0.21 | 5.13 |
| lvl-4_2018_20 | 4 | 4 | 0.00 | 0.00 | 0.21 | 5.13 |

Easiest problems observed / Problemes més fàcils observats (`easiest`):

| id | level | n | p_correct | p_without_hints | shrunk | adjusted_level |
|---|---|---|---|---|---|---|
| lvl-0_2017_9 | 0 | 4 | 1.00 | 1.00 | 0.91 | 0.00 |
| lvl-0_2016_19 | 0 | 3 | 1.00 | 1.00 | 0.90 | 0.00 |
| lvl-1_2017_11 | 1 | 5 | 1.00 | 1.00 | 0.87 | 0.12 |
| lvl-2_2024_7 | 2 | 6 | 1.00 | 1.00 | 0.86 | 0.89 |
| lvl-1_2021_22 | 1 | 4 | 1.00 | 1.00 | 0.85 | 0.20 |
| lvl-1_2018_15 | 1 | 4 | 1.00 | 1.00 | 0.85 | 0.20 |
| lvl-1_2017_3 | 1 | 4 | 1.00 | 1.00 | 0.85 | 0.20 |
| lvl-7_2023_9 | 7 | 4 | 1.00 | 1.00 | 0.84 | 6.17 |
| lvl-7_2015_25 | 7 | 4 | 1.00 | 1.00 | 0.84 | 6.17 |
| lvl-7_2013_12 | 7 | 4 | 1.00 | 1.00 | 0.84 | 6.17 |

Probes (60 steps each) on this history:

| probe | DIFFICULTY_ADJUST | n | wrong answers | mean hidden level - threshold | steps on a rated problem | settled band (M3Kang) | hidden levels, last 10 | steps to settle | repeats | laptop ms/step |
|---|---|---|---|---|---|---|---|---|---|---|
| hidden threshold 1 | off | 60 | 29 | 1.52 | 22 | 1-3 (unsettled) | 0-4 | - | 0 | 3.0 |
| hidden threshold 1 | on | 60 | 26 | 1.40 | 18 | 1-5 (unsettled) | 0-5 | - | 0 | 10.1 |
| hidden threshold 3 | off | 60 | 29 | 1.25 | 21 | 2-4 (unsettled) | 1-6 | - | 0 | 3.8 |
| hidden threshold 3 | on | 60 | 29 | 1.55 | 12 | 4-7 (unsettled) | 2-7 | - | 0 | 10.1 |
| hidden threshold 5 | off | 60 | 26 | 1.25 | 16 | 4-7 (unsettled) | 3-7 | - | 0 | 3.9 |
| hidden threshold 5 | on | 60 | 27 | 1.15 | 19 | 5-7 (unsettled) | 4-6 | - | 0 | 10.4 |
## Reading the figures

Written by hand after the run above (14 Nov 2026, `--neighbors retrieval`, the embedding
server for the validation ids); the same script with `--neighbors index` gave the same
picture (results/difficulty-index.md, not committed). Everything below the first heading
and above this one is regenerated by the script; this section is kept.

**The estimator recovers a class's difficulty.** On the hidden class the mean error against
the hidden difficulty falls from 0.71 to 0.58 levels after 600 answers (41 rated problems)
and from 0.72 to 0.52 after 3000 answers (490 rated problems). Of the shifts of half a level
or more on problems that are off their band, 11 of 12 point the right way after 600 answers
and 169 of 170 after 3000. On the label class, where the band is the truth, the noise is
small: 1 of 21 rated problems changes band after rounding at 600 answers (the shrinkage
keeps a problem seen three times within a third of a level of its band).

**Coverage is the limit for a class of ten.** 600 answers touch 400 to 450 of the 1747
problems, but only 21 to 65 of them three times or more, because the adaptive rule sends
each student along their own path. The teacher's report is informative from the first
week; the adjusted level is informative for a problem only after the class has met it
three times, which for most problems takes a term (490 rated problems after 3000 answers).

**The correlation between band and rate is near zero by design.** Pearson 0.03 to 0.11 in
every class. This is not a flaw of the bands: the trainer keeps each student at the edge of
what they can do, so every band is answered about half the time by the students who reach
it. The rate per level says how the class is matched to the problems, not how hard the
bands are; the per-problem shrinkage against the level's own rate is what measures
difficulty.

**The trainer hook does not help a simulated student, so it stays off.** With
`DIFFICULTY_ADJUST=1` the three probes made 28, 27 and 27 wrong answers against 29, 29 and
26 with it off (600-answer history) and 26, 29, 27 against 29, 29, 26 (3000-answer
history): within noise, and the mean distance between the hidden level served and the
student's threshold is slightly larger with the flag on in 4 of 6 pairs. The cause shows in
the paths: a lucky guess on a problem the class rates two levels harder sends the student
two levels up instead of one, so the adjustment amplifies the guessing noise of a
multiple-choice answer as much as it corrects mislabelled problems. A variant that steps
from the M3Kang level and uses the adjusted level only to filter neighbours was no better
(results/difficulty-variant-filter.md, not committed). The step cost also grows from 3 to
10 ms on the laptop with a 3000-answer history, since `estimate` re-reads the table on
every step (the cache proposed in INTERFACES.md would remove that).

What the module is for, then, is the teacher: `report()` lists the problems this class
finds hardest and easiest with their counts, and the rate per level, from the board's own
data. A real class may differ from the hidden model (the offsets here are an assumption:
40% of the problems off their band by one or two levels); the first real figure comes from
`python3 -m copilot.difficulty --db data/students.db` on the board after a few sessions.
