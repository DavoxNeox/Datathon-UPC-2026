# Reason track: experiments against always-D

Goal: a `predict.py` policy that beats the always-D floor (65/281 = 23.1% on the English
validation set) by at least 10 problems, and also beats the most frequent letter of
whatever set it is scored on, within the rules: 60 s per problem on the UNO Q, RAM next to
the embeddings and the app, standard library, deterministic, offline. Branch
`team/reason-predict-0ff6f3`. One change is adopted (`MIDDLE_VALUE=1`, the default since the
review of 14 Nov); the others stay behind flags that are **off** (experiment 5, the learned option
prior, is on branch `reason-prior`).

**What the winning rule is, and is not.** The middle-value rule is a prior on how Kangaroo
distractors are built: the wrong options are made from the right value (one step too many or
too few, double, half), so the correct value usually has distractors above and below it. It
is not reasoning about the problem, it reads no text, and it says nothing about the model.
Its gain on the hidden test can be zero: the paired bootstrap below gives a 95% interval of
-2 to +26 problems on 281.

Validation = `data/val.jsonl`, English, 281 problems (167 with OCR options); the 50-problem
sample is `eval.py --limit 50` (its always-D floor is an unusual 34%). Training = 1466
English problems, used to choose rules before the single look at validation. Board seconds
are estimates from token counts with the constants calibrated on the board on 14 Nov
(`BOARD_PREFILL_TPS=11.4`, `BOARD_GEN_TPS=5.6`); for the 2B model they are scaled as
described in experiment 2. Laptop: MacBook (Apple Silicon), llama.cpp `2cbe0ec`, CPU only, 4
threads, the board's flags. Several sessions shared the 0.8B server during these runs, so
the cache artifact of `docs/results-A.md` (+33 prompt tokens, about +3 s) applies to the
model runs here.

## Summary

| # | experiment | flag | n | accuracy | always D on the set | most frequent letter | board s mean / worst | RAM | verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 0 | shipped policy: solvers, else D | | 281 | 65 = 23.1% | 23.1% | D 23.1% | 0.8 / 39.3 | 1.06 GB (0.8B) | floor |
| 1 | middle-value rule, D elsewhere | `MIDDLE_VALUE=1` | 281 | **77 = 27.4%** | 23.1% | D 23.1% | 0.7 / 38.1 | no model | **+12: adopted** |
| 1 | same, training set (rule + D alone) | `MIDDLE_VALUE=1` | 1466 | 405 = 27.6% | 25.0% | D 25.0% | 0.0 / 0.0 | no model | +38 |
| 1 | same, training set, family solvers on | `MIDDLE_VALUE=1` | 1466 | 406 = 27.7% | 25.0% | D 25.0% | 0.9 / 38.5 | 0.8B for 2 extractions | +39 |
| 1 | same, the 50-sample | `MIDDLE_VALUE=1` | 50 | 14 = 28.0% | 34.0% | D 34.0% | 1.3 / 38.1 | no model | -3 (D-heavy sample) |
| 2 | Qwen3.5 2B Q4_K_M, letter | `LLM_PORT=8091 LETTER_MODEL=1` | 50 | 13 = 26.0% | 34.0% | D 34.0% | 39 / 88, 3 over 60 s | 2.74 GB RSS on the Mac | too slow, no signal |
| 2 | Qwen3.5 2B Q4_K_M, value grammar | `LLM_PORT=8091 VALUE_MODEL=1` | 50 | 10 = 20.0% | 34.0% | D 34.0% | 38 / 88 (scaled) | same | no signal |
| 3 | 0.8B, value grammar (five option strings) | `VALUE_MODEL=1` | 50 | 15 = 30.0% | 34.0% | D 34.0% | 8.2 / 42.2 | 1.06 GB | no gain |
| 3 | same | `VALUE_MODEL=1` | 281 | 66 = 23.5% | 23.1% | D 23.1% | 6.7 / 52.6 | 1.06 GB | +1: noise |
| 4 | 0.8B, 5 cyclic shifts, strict majority | `VOTE_SHIFTS=5` | 50 | 17 = 34.0% | 34.0% | D 34.0% | 22.7 / 59.1 | 1.06 GB | 2 majorities, both wrong |
| 4 | same | `VOTE_SHIFTS=5` | 281 | 63 = 22.4% | 23.1% | D 23.1% | 20.0 / 73.7, 6 over 60 s | 1.06 GB | -2, too slow |
| 5 | learned option prior per stratum, threshold +10 on train | `OPTION_PRIOR=1` | 281 | 80 = 28.5% | 23.1% | D 23.1% | 0 / 0 | no model | +3 over the middle value, bootstrap [-4, +11]: off |
| 5 | same, training set (the rules were chosen on it) | `OPTION_PRIOR=1` | 1466 | 425 = 29.0% | 25.0% | D 25.0% | 0 / 0 | no model | +20 over the middle value, cross-validation inside train: loss |

The letter model restricted to the middle three values (offline, from the baseline's stored
log probabilities, 99 strictly numeric problems): 24 right, against 29 for the middle value
alone and 22 for the raw letter. The model does not help choose among the middle values.

## Experiment 1: the middle-value rule (`copilot/ladder.py`)

**Hypothesis.** Kangaroo distractors are built around the right answer (one step too many or
too few, double, half), so when the options are numbers the correct one is rarely an extreme.
Cost: none (Python only).

**Where it comes from.** On the 571 English training problems whose five options are plain
numbers, the rank of the correct value when the five are sorted is: smallest 47, second 124,
middle 180, fourth 159, largest 60. The middle value is right 31.5% of the time; the always-D
floor on those problems is 24.6%, the most frequent letter (C) 24.7%. Allowing a short unit
after the number ("48 cm", "4 kg", "165 cm²", "25%") covers 654 training problems (middle
199 = 30.4%, D 161 = 24.6%); taking the first number of any option string covers 797 but the
OCR noise ("1 10", "88 616") drops the gain (28.4% against 24.6%). The unit form was chosen
on training and is what `ladder.numeric_options` accepts: one number, an optional unit of up
to seven letters (or %, €, $, °, cm², km/h), five distinct values. Anything else abstains.

**Validation, one look.** `MIDDLE_VALUE=1 python3 eval.py --limit 0 --languages eng`:
77/281 = 27.4%, +12 problems over always D (4.3 points). **Uncertainty:** a paired bootstrap
of the 281 problems (10 000 resamples, seed 42, the rule's hits minus D's hits on the same
resample) gives a 95% interval of **[-2, +26] problems ([-0.7, +9.3] points)**; the gain is
zero or negative in 6.0% of the resamples (negative in 4.3%). On the 1466 training problems
the same bootstrap gives [+2, +75], with 2.1% of resamples at or under zero. So the sign is
well supported by both sets, the size is not: a hidden test of 281 problems can return a
gain anywhere in that interval, including none. The rule fires on 120 problems: 36 right (30.0%)
against 24 for D (20.0%) and 28 for the most frequent letter there (A, 23.3%). On the other
161 problems the answer stays D (41 right, 25.5%, D is their most frequent letter). By level
on the 120: it wins at levels 0, 1, 3, 5, 6, 7 and loses at levels 2 (1 against 3) and 4
(6 against 8).

**Against the most frequent letter.** The rule's gain does not depend on D being the most
frequent letter: on the 120 numeric problems every letter is near 20 to 23%, and the rule
scores 30%. On a hidden set with another letter distribution the rule keeps its edge on the
numeric problems, and `FALLBACK_ANSWER` decides the rest, as today.

**The 50-sample.** 14/50 against 17 for always D: the sample has 17 D labels (34%), and on
its 26 numeric problems the rule gets 7 against 10 for D. This is why the decision uses the
281 and the training set, not the 50.

**Training count, 405 or 406.** The rule with D elsewhere scores 405/1466 (201 of the 662
numeric problems plus 204 D elsewhere). The `eval.py` run in the table (406) also had the
family solvers on, as `predict.py` does: two fired (`lvl-6_2018_11`, `digit_count`;
`lvl-6_2020_6`, `consecutive`), both right, one on a problem the rule would have missed, so
the shipped policy (solvers, then the rule, then D) scores 406 and the rule alone 405.
`config.env` and `copilot/ladder.py` quote 405.

**Cost.** None: no model call, no embedding. The worst board estimate (38 s) is the existing
family solver's extraction on one problem, unchanged.

## Experiment 2: a bigger model, Qwen3.5 2B Q4_K_M

There is no Qwen3.5 1.7B; the sizes are 0.8B, 2B, 4B, 9B. `bartowski/Qwen_Qwen3.5-2B-GGUF`
(Apache 2.0), file `Qwen_Qwen3.5-2B-Q4_K_M.gguf`, 1.40 GB, SHA256
`57a1085840f497d764a7fc5d346922dbde961efb54cc792ea81d694fd846a1d8`, revision
`7d26695454df6de5fbcce2e58681e62dae06ce43`, downloaded to `~/models`. Started on port 8091
with `math-llm.service`'s flags (4 threads, ctx 4096, `--parallel 1 --cache-ram 0
--ctx-checkpoints 2 --jinja --reasoning off --reasoning-budget 0`).

**Speed, measured on the Mac with the same 129-token prompt and 50 generated tokens, both
servers idle:**

| model | read tok/s | write tok/s |
| --- | ---: | ---: |
| 0.8B Q8_0 (port 8081) | 574, 576 | 96.8, 93.9 |
| 2B Q4_K_M (port 8091) | 132.2, 133.2 | 34.0, 33.5 |

Ratios 0.231 (read) and 0.354 (write), so on the board: about **2.6 tok/s read, 2.0 tok/s
write** (from 11.4 and 5.6). Applied to the 281 validation prompts of the baseline (mean 98
tokens, max 182): mean 37.6 s, worst 69.7 s, 5 problems over 60 s; a prompt fits in 60 s
only up to 156 tokens. **RAM:** 2.74 GB RSS on the Mac for the 2B against 1.80 GB for the
0.8B on the same Mac (1.06 GB on the board), so about 1.6 GB expected on the board, which
would fit next to the embeddings (75 MB) and the app (91 MB) only if it replaced the 0.8B.

**Accuracy, 50 problems, letter:** 13/50 = 26.0% against 30.0% for the 0.8B and 34.0% for
always D on the same 50; letters chosen A 28, D 14, B 5, E 3, C 0. The bigger model is as
positional as the small one. With the value grammar (`VALUE_MODEL=1`): 10/50 = 20.0%, 6/34 right on the problems with options against 13/34 for D; letters A 12, D 20, C 7, B 6, E 5.

**Verdict.** Too slow for the 60-second rule on 2% of the problems and 4 times slower on
average, and no accuracy signal on 50. Not pursued to 281. A Q8_0 of the 2B (2.08 GB) would
be slower still on reading and tighter in RAM.

## Experiment 3: ask for the value, not the letter (`copilot/votes.py: value_letter`)

**Hypothesis.** The letter bias (A and D) cannot act if the model never writes a letter: the
grammar allows only the five option strings, and the value maps back to its letter.
Estimated cost before running: the baseline prompt plus 1 to 4 written tokens, about 9 s mean
and 17 s worst on the board.

**Result, 50:** the rule answered 35 problems (the ones with options): 11/35 right (31.4%)
against 13/35 for D on those; whole sample 15/50 = 30.0% against 34.0% for D. Letters
chosen A 12, D 19, B 8, E 7, C 4. Board estimate mean 8.2 s, worst 42.2 s (that worst is
the family solver's extraction).

**Result, 281:** 66/281 = 23.5%, one problem over always D. The value model answered the
167 problems with options: 35 right (21.0%) against 34 for D on them; letters chosen A 44,
B 25, C 33, D 136 (the 114 fallbacks included), E 43. Board estimate mean 6.7 s, worst 52.6 s
(a family-solver extraction followed by the value call). On the 120 problems where the
middle-value rule applies, the value model is right on 25 against 36 for the rule, and it
picks one of the three middle values 61 times out of 120 (random: 72 of 120, 60%): it does not even
learn that the extremes are rare. No gain, more cost.

## Experiment 4: vote over cyclic shifts of the options (`copilot/votes.py: vote_letter`)

**Hypothesis.** Asking once per cyclic shift (ABCDE, BCDEA, CDEAB, DEABC, EABCD) puts every
option in every position once, so a purely positional model gives each option one vote and
a tie, while any content preference breaks the tie. The problem text goes in its own message
and the options in the last one, because this hybrid model's cache is restored only at the
start of the last user message: measured on one problem, the first shift reads 110 tokens
and each further shift 44 (`cache_n` 99). Estimated cost before running: text once plus
4 × 44 tokens plus 5 letters, about 26 s for a typical problem and 47 s for the longest.

**Result, 50:** 35 problems voted. Vote shapes: 17 five-way ties (1 vote each: the model
followed position only), 12 pluralities of 2 votes, 4 two-way ties at 2, 2 strict majorities
of 3 (both wrong). Plurality rule (unique top, any count): 14 problems, 2 right, D right on 4
of them. Whole sample with the strict majority 17/50 = 34.0% = always D (48 answers were D).
Board estimate mean 22.7 s, median 28.3 s, worst 59.1 s: at the limit.

**Result, 281:** 63/281 = 22.4%, two problems under always D. 167 problems voted: 91 five-way
ties, 44 pluralities of 2, 25 two-way ties at 2, 7 strict majorities of 3, **all 7 wrong**.
The plurality rule (unique top, any count) would answer 51 problems with 8 right against 12
for D on them. Board estimate mean 20.0 s, median 27.6 s, worst 73.7 s, **6 problems over
60 s** in this run, which had no time guard. Five looks at the same problem give the model
five positional answers, not one considered answer.

**Time guard, added after the review.** Both experiments now take a budget in board seconds,
`EXPERIMENT_BUDGET_SECONDS=50` minus what the problem has already cost: `value_letter` skips
a problem whose prompt (guessed at 3 characters per token) would pass it, and `vote_letter`
skips the first shift on the same guess, then stops before any further shift whose cost (the
previous request's prompt tokens, read again, plus one letter) would pass it; an interrupted
vote never elects. Whoever turns these flags on gets a policy that respects the 60-second
rule, and nothing else: they still do not beat always D.

## Experiment 5: a learned option prior (`copilot/prior.py`, `laptop/learn_prior.py`)

**Hypothesis.** The middle-value rule is one prior on the options; maybe other strata of problems
have a better one. A level-2 problem with a picture, a problem whose options are words, one whose
options are listed out of order, one whose OCR'd options carry a stray digit: each could have its own
best rule (another rank of the values, a fixed letter, the option that says "none"). The prior reads
the five option strings, the level and whether there is a picture, never the problem text, so like
experiment 1 it costs nothing on the board. Flag `OPTION_PRIOR` (default 0), hook in
`copilot/pipeline.py` right before the middle-value rule, so the order is solvers, prior, middle
value, D.

**Candidate rules** (`prior.apply_rule`): a fixed letter A to E (the most frequent letter of the
stratum is one of them); a rank of the numeric values, `min`, `second_smallest`, `middle`,
`second_largest`, `max`; `none_option`, the single option whose text says none, impossible, cannot
(English or Catalan). Numeric values come from `ladder.numeric_options` (strict, five distinct
numbers with a unit at most) or, where that fails, from a lenient parser that drops a stray leading
digit that repeats the number's first digit ("1 10", "4 40cm", "6 600 g") and ignores junk after the
number and its unit ("88 616", "300 g 400g 100g 2"): 102 training problems become "noisy numeric"
this way, on top of the 663 strict ones. A rule that does not apply to a problem falls back to the
current policy, so every rule is scored on the whole stratum and compared with the current policy
(middle value where the options are five distinct numbers, else D) on the same problems.

**Strata.** The main stratification is level 0-7 × picture/text × kind of options (numeric, noisy
numeric, words, no options): 62 strata on the 1466 English training problems. The task's other
strata are measured as pooled stratifications: level alone, kind alone, picture alone, language,
and the option patterns (ascending or unsorted values, fractions, π or roots, "none" text, number of
distinct options), each crossed with the kind. A stratum keeps its best rule only when the rule
beats the current policy by **at least 10 problems** in that stratum (`--min-gain 10`); otherwise
the stratum keeps the current policy. The table is `data_curated/option_prior.json` (counts and rule
names only), written by `laptop/learn_prior.py`, which also prints everything below.

### Training, main stratification (level / picture / options), 1466 English problems

No stratum reaches +10: the largest gains are +8 (level 2 with picture, numeric: D 9 against the
middle value 1 on 16 problems; level 2 with picture, noisy numeric; level 3 text numeric) and +7
(level 7 text words: E). With the main stratification alone **nothing is learned** and the policy
is the current one, 405/1466.

| level | picture | options | n | labels A B C D E | current policy | best rule | hits | gain |
| ---: | --- | --- | ---: | --- | ---: | --- | ---: | ---: |
| 0 | picture | no options | 49 | 2 10 10 14 13 | 14 | `D` | 14 | +0 |
| 0 | picture | noisy numeric | 10 | 0 1 2 4 3 | 4 | `second_largest` | 5 | +1 |
| 0 | picture | numeric | 33 | 3 8 7 10 5 | 8 | `D` | 10 | +2 |
| 0 | picture | words | 5 | 0 0 0 3 2 | 3 | `D` | 3 | +0 |
| 0 | text | no options | 4 | 2 1 0 1 0 | 1 | `A` | 2 | +1 |
| 0 | text | noisy numeric | 1 | 0 0 0 1 0 | 1 | `D` | 1 | +0 |
| 0 | text | numeric | 17 | 1 6 6 4 0 | 6 | `second_largest` | 7 | +1 |
| 0 | text | words | 3 | 0 1 0 1 1 | 1 | `B` | 1 | +0 |
| 1 | picture | no options | 36 | 3 2 8 12 11 | 12 | `D` | 12 | +0 |
| 1 | picture | noisy numeric | 10 | 0 0 0 7 3 | 7 | `D` | 7 | +0 |
| 1 | picture | numeric | 17 | 0 4 5 4 4 | 7 | `middle` | 7 | +0 |
| 1 | picture | words | 3 | 0 1 1 1 0 | 1 | `B` | 1 | +0 |
| 1 | text | no options | 5 | 0 1 3 1 0 | 1 | `C` | 3 | +2 |
| 1 | text | noisy numeric | 2 | 1 0 0 0 1 | 0 | `A` | 1 | +1 |
| 1 | text | numeric | 16 | 2 4 1 7 2 | 3 | `D` | 7 | +4 |
| 2 | picture | no options | 45 | 9 10 8 11 7 | 11 | `D` | 11 | +0 |
| 2 | picture | noisy numeric | 13 | 0 6 4 0 3 | 0 | `B` | 6 | +6 |
| 2 | picture | numeric | 16 | 0 3 1 9 3 | 1 | `D` | 9 | +8 |
| 2 | picture | words | 3 | 2 1 0 0 0 | 0 | `A` | 2 | +2 |
| 2 | text | no options | 12 | 2 2 5 2 1 | 2 | `C` | 5 | +3 |
| 2 | text | noisy numeric | 2 | 1 1 0 0 0 | 0 | `A` | 1 | +1 |
| 2 | text | numeric | 25 | 5 4 5 7 4 | 6 | `second_smallest` | 8 | +2 |
| 2 | text | words | 1 | 0 0 1 0 0 | 0 | `C` | 1 | +1 |
| 3 | picture | no options | 30 | 3 4 12 8 3 | 8 | `C` | 12 | +4 |
| 3 | picture | noisy numeric | 12 | 1 3 1 4 3 | 4 | `second_largest` | 6 | +2 |
| 3 | picture | numeric | 9 | 3 4 0 1 1 | 3 | `B` | 4 | +1 |
| 3 | picture | words | 6 | 1 1 2 1 1 | 1 | `C` | 2 | +1 |
| 3 | text | no options | 19 | 4 4 4 6 1 | 6 | `D` | 6 | +0 |
| 3 | text | noisy numeric | 1 | 1 0 0 0 0 | 0 | `A` | 1 | +1 |
| 3 | text | numeric | 33 | 4 3 10 7 9 | 8 | `second_smallest` | 14 | +6 |
| 3 | text | words | 1 | 0 0 0 1 0 | 1 | `D` | 1 | +0 |
| 4 | picture | no options | 71 | 14 14 17 16 10 | 16 | `C` | 17 | +1 |
| 4 | picture | noisy numeric | 11 | 0 2 5 2 2 | 2 | `C` | 5 | +3 |
| 4 | picture | numeric | 54 | 8 9 13 15 9 | 15 | `second_largest` | 19 | +4 |
| 4 | picture | words | 13 | 3 1 4 1 4 | 1 | `C` | 4 | +3 |
| 4 | text | no options | 30 | 3 6 7 11 3 | 11 | `D` | 11 | +0 |
| 4 | text | numeric | 89 | 12 22 21 19 15 | 28 | `middle` | 28 | +0 |
| 4 | text | words | 9 | 4 2 2 0 1 | 0 | `A` | 4 | +4 |
| 5 | picture | no options | 42 | 7 4 5 14 12 | 14 | `D` | 14 | +0 |
| 5 | picture | noisy numeric | 12 | 5 0 3 3 1 | 3 | `A` | 5 | +2 |
| 5 | picture | numeric | 36 | 6 9 5 6 10 | 9 | `E` | 10 | +1 |
| 5 | picture | words | 13 | 2 5 1 3 2 | 3 | `B` | 5 | +2 |
| 5 | text | no options | 30 | 8 3 5 9 5 | 9 | `D` | 9 | +0 |
| 5 | text | noisy numeric | 3 | 1 1 0 1 0 | 1 | `second_largest` | 2 | +1 |
| 5 | text | numeric | 94 | 12 22 25 19 16 | 35 | `middle` | 35 | +0 |
| 5 | text | words | 13 | 1 2 5 2 3 | 2 | `C` | 5 | +3 |
| 6 | picture | no options | 55 | 16 9 12 10 8 | 10 | `A` | 16 | +6 |
| 6 | picture | noisy numeric | 10 | 4 2 0 2 2 | 2 | `A` | 4 | +2 |
| 6 | picture | numeric | 30 | 4 9 8 5 4 | 8 | `second_smallest` | 11 | +3 |
| 6 | picture | words | 27 | 6 6 3 6 6 | 6 | `A` | 6 | +0 |
| 6 | text | no options | 38 | 4 4 11 12 7 | 12 | `D` | 12 | +0 |
| 6 | text | noisy numeric | 1 | 0 0 0 0 1 | 0 | `E` | 1 | +1 |
| 6 | text | numeric | 87 | 14 18 23 22 10 | 30 | `middle` | 30 | +0 |
| 6 | text | words | 8 | 1 2 2 1 2 | 1 | `B` | 2 | +1 |
| 7 | picture | no options | 53 | 11 14 8 13 7 | 13 | `B` | 14 | +1 |
| 7 | picture | noisy numeric | 10 | 1 1 4 1 3 | 1 | `C` | 4 | +3 |
| 7 | picture | numeric | 24 | 4 6 7 4 3 | 8 | `middle` | 8 | +0 |
| 7 | picture | words | 20 | 4 1 6 4 5 | 4 | `C` | 6 | +2 |
| 7 | text | no options | 36 | 4 6 8 12 6 | 12 | `D` | 12 | +0 |
| 7 | text | noisy numeric | 4 | 2 1 0 1 0 | 1 | `A` | 2 | +1 |
| 7 | text | numeric | 83 | 10 14 22 24 13 | 26 | `middle` | 26 | +0 |
| 7 | text | words | 21 | 4 5 1 2 9 | 2 | `E` | 9 | +7 |

### Training, pooled stratifications

Five pooled strata reach exactly +10, all of them two findings seen several times: level 2 →
`second_smallest` (30 against 20 on 117 problems) and words → `E` (36 against 26 on 146 problems,
also seen as words without fractions, words without "none" text, English words). With all the
stratifications together, finest first, the learned policy scores 425/1466 = 29.0% on training
(+20; paired bootstrap of the gain, 1000 resamples, seed 42: 95% [+3, +40]), which is the usual
optimism of a rule chosen on the same data.

| stratification | stratum | n | current policy | best rule | hits | gain | chosen |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| level/kind | level=0, kind=no_options | 53 | 15 | `D` | 15 | +0 |  |
| level/kind | level=0, kind=noisy_numeric | 11 | 5 | `second_largest` | 6 | +1 |  |
| level/kind | level=0, kind=numeric | 50 | 14 | `second_largest` | 16 | +2 |  |
| level/kind | level=0, kind=words | 8 | 4 | `D` | 4 | +0 |  |
| level/kind | level=1, kind=no_options | 41 | 13 | `D` | 13 | +0 |  |
| level/kind | level=1, kind=noisy_numeric | 12 | 7 | `D` | 7 | +0 |  |
| level/kind | level=1, kind=numeric | 33 | 10 | `D` | 11 | +1 |  |
| level/kind | level=1, kind=words | 3 | 1 | `B` | 1 | +0 |  |
| level/kind | level=2, kind=no_options | 57 | 13 | `C` | 13 | +0 |  |
| level/kind | level=2, kind=noisy_numeric | 15 | 0 | `B` | 7 | +7 |  |
| level/kind | level=2, kind=numeric | 41 | 7 | `D` | 16 | +9 |  |
| level/kind | level=2, kind=words | 4 | 0 | `A` | 2 | +2 |  |
| level/kind | level=3, kind=no_options | 49 | 14 | `C` | 16 | +2 |  |
| level/kind | level=3, kind=noisy_numeric | 13 | 4 | `second_largest` | 7 | +3 |  |
| level/kind | level=3, kind=numeric | 42 | 11 | `second_smallest` | 18 | +7 |  |
| level/kind | level=3, kind=words | 7 | 2 | `C` | 2 | +0 |  |
| level/kind | level=4, kind=no_options | 101 | 27 | `D` | 27 | +0 |  |
| level/kind | level=4, kind=noisy_numeric | 11 | 2 | `C` | 5 | +3 |  |
| level/kind | level=4, kind=numeric | 143 | 43 | `second_largest` | 44 | +1 |  |
| level/kind | level=4, kind=words | 22 | 1 | `A` | 7 | +6 |  |
| level/kind | level=5, kind=no_options | 72 | 23 | `D` | 23 | +0 |  |
| level/kind | level=5, kind=noisy_numeric | 15 | 4 | `A` | 6 | +2 |  |
| level/kind | level=5, kind=numeric | 130 | 44 | `middle` | 44 | +0 |  |
| level/kind | level=5, kind=words | 26 | 5 | `B` | 7 | +2 |  |
| level/kind | level=6, kind=no_options | 93 | 22 | `C` | 23 | +1 |  |
| level/kind | level=6, kind=noisy_numeric | 11 | 2 | `A` | 4 | +2 |  |
| level/kind | level=6, kind=numeric | 117 | 38 | `middle` | 38 | +0 |  |
| level/kind | level=6, kind=words | 35 | 7 | `B` | 8 | +1 |  |
| level/kind | level=7, kind=no_options | 89 | 25 | `D` | 25 | +0 |  |
| level/kind | level=7, kind=noisy_numeric | 14 | 2 | `min` | 6 | +4 |  |
| level/kind | level=7, kind=numeric | 107 | 34 | `middle` | 34 | +0 |  |
| level/kind | level=7, kind=words | 41 | 6 | `E` | 14 | +8 |  |
| picture/kind | picture=picture, kind=no_options | 381 | 98 | `D` | 98 | +0 |  |
| picture/kind | picture=picture, kind=noisy_numeric | 88 | 23 | `second_largest` | 26 | +3 |  |
| picture/kind | picture=picture, kind=numeric | 219 | 59 | `second_smallest` | 59 | +0 |  |
| picture/kind | picture=picture, kind=words | 90 | 19 | `E` | 20 | +1 |  |
| picture/kind | picture=text, kind=no_options | 174 | 54 | `D` | 54 | +0 |  |
| picture/kind | picture=text, kind=noisy_numeric | 14 | 3 | `A` | 6 | +3 |  |
| picture/kind | picture=text, kind=numeric | 444 | 142 | `middle` | 142 | +0 |  |
| picture/kind | picture=text, kind=words | 56 | 7 | `E` | 16 | +9 |  |
| level | level=0 | 122 | 38 | `second_largest` | 41 | +3 |  |
| level | level=1 | 89 | 31 | `D` | 32 | +1 |  |
| level | level=2 | 117 | 20 | `second_smallest` | 30 | +10 | yes |
| level | level=3 | 111 | 31 | `second_smallest` | 36 | +5 |  |
| level | level=4 | 277 | 73 | `middle` | 75 | +2 |  |
| level | level=5 | 243 | 76 | `none_option` | 76 | +0 |  |
| level | level=6 | 256 | 69 | `middle` | 70 | +1 |  |
| level | level=7 | 251 | 67 | `middle` | 67 | +0 |  |
| kind | kind=no_options | 555 | 152 | `D` | 152 | +0 |  |
| kind | kind=noisy_numeric | 102 | 26 | `second_largest` | 30 | +4 |  |
| kind | kind=numeric | 663 | 201 | `middle` | 201 | +0 |  |
| kind | kind=words | 146 | 26 | `E` | 36 | +10 | yes |
| picture | picture=picture | 778 | 199 | `none_option` | 198 | -1 |  |
| picture | picture=text | 688 | 206 | `none_option` | 206 | +0 |  |
| kind/order | kind=noisy_numeric, order=ascending | 49 | 18 | `D` | 18 | +0 |  |
| kind/order | kind=noisy_numeric, order=unsorted | 53 | 8 | `second_smallest` | 13 | +5 |  |
| kind/order | kind=numeric, order=ascending | 354 | 99 | `D` | 100 | +1 |  |
| kind/order | kind=numeric, order=unsorted | 309 | 102 | `middle` | 102 | +0 |  |
| kind/fraction | kind=no_options, fraction=False | 555 | 152 | `D` | 152 | +0 |  |
| kind/fraction | kind=noisy_numeric, fraction=False | 97 | 25 | `second_largest` | 29 | +4 |  |
| kind/fraction | kind=noisy_numeric, fraction=True | 5 | 1 | `A` | 3 | +2 |  |
| kind/fraction | kind=numeric, fraction=False | 646 | 193 | `middle` | 193 | +0 |  |
| kind/fraction | kind=numeric, fraction=True | 17 | 8 | `C` | 8 | +0 |  |
| kind/fraction | kind=words, fraction=False | 146 | 26 | `E` | 36 | +10 | yes |
| kind/pi_root | kind=no_options, pi_root=False | 555 | 152 | `D` | 152 | +0 |  |
| kind/pi_root | kind=noisy_numeric, pi_root=False | 102 | 26 | `second_largest` | 30 | +4 |  |
| kind/pi_root | kind=numeric, pi_root=False | 663 | 201 | `middle` | 201 | +0 |  |
| kind/pi_root | kind=words, pi_root=False | 115 | 20 | `E` | 29 | +9 |  |
| kind/pi_root | kind=words, pi_root=True | 31 | 6 | `A` | 7 | +1 |  |
| kind/none_text | kind=no_options, none_text=False | 555 | 152 | `D` | 152 | +0 |  |
| kind/none_text | kind=noisy_numeric, none_text=False | 102 | 26 | `second_largest` | 30 | +4 |  |
| kind/none_text | kind=numeric, none_text=False | 663 | 201 | `middle` | 201 | +0 |  |
| kind/none_text | kind=words, none_text=False | 145 | 25 | `E` | 36 | +11 | yes |
| kind/none_text | kind=words, none_text=True | 1 | 1 | `D` | 1 | +0 |  |
| kind/distinct | kind=no_options, distinct=0 | 555 | 152 | `D` | 152 | +0 |  |
| kind/distinct | kind=noisy_numeric, distinct=5 | 102 | 26 | `second_largest` | 30 | +4 |  |
| kind/distinct | kind=numeric, distinct=5 | 663 | 201 | `middle` | 201 | +0 |  |
| kind/distinct | kind=words, distinct=3 | 2 | 0 | `C` | 2 | +2 |  |
| kind/distinct | kind=words, distinct=4 | 3 | 0 | `A` | 1 | +1 |  |
| kind/distinct | kind=words, distinct=5 | 141 | 26 | `E` | 35 | +9 |  |
| language/kind | language=eng, kind=no_options | 555 | 152 | `D` | 152 | +0 |  |
| language/kind | language=eng, kind=noisy_numeric | 102 | 26 | `second_largest` | 30 | +4 |  |
| language/kind | language=eng, kind=numeric | 663 | 201 | `middle` | 201 | +0 |  |
| language/kind | language=eng, kind=words | 146 | 26 | `E` | 36 | +10 | yes |

### Cross-validation inside training (before the look at validation)

Five folds, three shuffles (seeds 42, 43, 44): the rules are learned on four fifths with the same
+10 threshold and scored on the fifth; the table gives the out-of-fold gain over the current policy
summed over the five folds. Nothing generalises: at the threshold of 10 every stratification is at
zero or negative, and the full hierarchy loses about 10 problems. (At a threshold of 5, outside the
protocol, level × kind shows +15 / +17 / +5 and everything else loses; not pursued.)

| stratification | strata | chosen rules | out-of-fold gain, seeds 42 / 43 / 44 | mean |
| --- | ---: | ---: | --- | ---: |
| level, picture, kind | 62 | 0 | +0 / +0 / +0 | +0.0 |
| level, kind | 32 | 0 | -3 / +0 / -1 | -1.3 |
| picture, kind | 8 | 0 | -1 / -1 / +0 | -0.7 |
| level | 8 | 1 | +0 / -3 / -2 | -1.7 |
| kind | 4 | 1 | -2 / -2 / +0 | -1.3 |
| picture | 2 | 0 | +0 / +0 / +0 | +0.0 |
| kind, order | 4 | 0 | -9 / -9 / +0 | -6.0 |
| kind, fraction | 6 | 1 | -2 / -2 / +0 | -1.3 |
| kind, π or root | 5 | 0 | -4 / -4 / -1 | -3.0 |
| kind, none text | 5 | 1 | -1 / -1 / +0 | -0.7 |
| kind, distinct options | 6 | 0 | -3 / -2 / -1 | -2.0 |
| language, kind | 4 | 1 | -2 / -2 / +0 | -1.3 |
| all of the above, finest first | 146 | 5 | -13 / -15 / -1 | -9.7 |

### Validation, one look

The policy of the full protocol (all the stratifications, finest first, threshold 10, the five
rules above) on the 281 English validation problems, `python3 laptop/learn_prior.py --strata
"level,picture,kind;level,kind;picture,kind;level;kind;picture;kind,order;kind,fraction;kind,pi_root;kind,none_text;kind,distinct;language,kind"
--validate`:

| set | n | learned prior | current policy (middle value, else D) | gain | paired bootstrap of the gain, 1000 resamples, seed 42 |
| --- | ---: | ---: | ---: | ---: | --- |
| validation | 281 | **80 = 28.5%** | 77 = 27.4% | +3 | 95% [-4, +11], **27.4% of resamples at or under zero** |
| training | 1466 | 425 = 29.0% | 405 = 27.6% | +20 | 95% [+3, +40], 1.2% at or under zero (chosen on these problems) |

Where the learned rules fired on validation: words → E on 24 problems, 6 right against 5 for D;
level 2 → second smallest on 11 problems, 3 right against 1 for the current policy. The real
pipeline agrees: `OPTION_PRIOR=1 python3 eval.py --limit 0 --languages eng` gives 80/281 = 28.5%
with the family solvers on (35 answers by the prior, 112 by the middle value, board estimate mean
0.8 s, worst 41.2 s, the solver extraction as before). Three problems
of gain with an interval that covers zero comfortably, after a cross-validation that predicted a
loss: not a result to ship.

**Verdict.** `OPTION_PRIOR=0`. The prior stays in the repository as a negative result: with
honest thresholds, the strata of M3Kang do not have option priors that beat the middle value, and
the gains that look real on training (+8 here, +10 there) are the maximum of eleven rules over small
groups. The one direction with some support is the lenient parser (102 noisy numeric problems where
the current policy answers D), but no rank rule beat D on them by 10, and out of fold the kind
stratification lost. Everything is reproducible with the script; a bigger training set (the
Catalan copies of the same problems are not new problems) could change the picture.

## Decision

`MIDDLE_VALUE=1` is the default in `config.env` (review of 14 Nov): it is the only change
that meets the criterion (+12 problems on the 281, +38 on the 1466 training problems with
the rule alone, nothing to run on the board), it answers in Python with no model call, and
it abstains on anything that is not five distinct numbers, so the rest of the policy (family
solvers first, then `FALLBACK_ANSWER` D) is unchanged; a problem without options, with
non-numeric options, with OCR noise or with repeated values still gets D. It is a prior on
the distractors, not reasoning, and the bootstrap says the hidden-test gain can be anything
from -2 to +26 problems. `LETTER_MODEL=0`, `VALUE_MODEL=0` and `VOTE_SHIFTS=0` stay: the
0.8B's choice carries no information whether it writes a letter, a value, or five letters,
and the 2B is too slow for the board and no better. `OPTION_PRIOR=0` stays too: no stratum has
a better option prior than the middle value by a margin that survives cross-validation
(experiment 5). `tests/test_reason_policy.py` checks
that the Teach modules import none of this and that `predict.py` answers a letter in every
case (no options, words, noise, duplicates, server down).

## Reproduce

```bash
MIDDLE_VALUE=1 python3 eval.py --limit 0 --languages eng --name R-middle-eng281
MIDDLE_VALUE=1 python3 eval.py --input data/train.jsonl --limit 0 --languages eng --name R-middle-train-eng1466
VALUE_MODEL=1 python3 eval.py --limit 0 --languages eng --name R-value08-eng281
VOTE_SHIFTS=5 python3 eval.py --limit 0 --languages eng --name R-vote5-08-eng281
LLM_PORT=8091 LETTER_MODEL=1 SOLVERS=0 python3 eval.py --limit 50 --languages eng --name R-2bq4-letter-eng50
python3 laptop/learn_prior.py --cv 5                                   # experiment 5: tables and cross-validation on train
python3 laptop/learn_prior.py --strata "level,picture,kind;level,kind;picture,kind;level;kind;picture;kind,order;kind,fraction;kind,pi_root;kind,none_text;kind,distinct;language,kind" --validate
OPTION_PRIOR=1 python3 eval.py --limit 0 --languages eng --name R-prior-eng281
```

Each run adds a line to `results/ablations.csv` with its commit and writes the per-problem
CSV (`rule` and `extra` columns carry the rule that answered and the vote tallies or value).
