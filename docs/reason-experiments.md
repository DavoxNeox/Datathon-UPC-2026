# Reason track: experiments against always-D

Goal: a `predict.py` policy that beats the always-D floor (65/281 = 23.1% on the English
validation set) by at least 10 problems, and also beats the most frequent letter of
whatever set it is scored on, within the rules: 60 s per problem on the UNO Q, RAM next to
the embeddings and the app, standard library, deterministic, offline. Branch
`team/reason-predict-0ff6f3`. One change is adopted (`MIDDLE_VALUE=1`, the default since the
review of 14 Nov); the others stay behind flags that are **off** (experiment 5, the learned option
prior, is on branch `reason-prior`).
the embeddings and the app, standard library, deterministic, offline. Branches
`team/reason-predict-0ff6f3` (experiments 1 to 4) and `reason-think` (5 and 6, after the
organisers made Reasoning half of the grade). One change is adopted (`MIDDLE_VALUE=1`, the
default since the review of 14 Nov); the others stay behind flags that are **off**.

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
| 6 | 0.8B writes its working, letter read from it, every level | `THINK_LEVELS=all THINK_TEXT_ONLY=0` | 281 | 76 = 27.0% | 23.1% | D 23.1% | 25.1 / 51.5 | 1.06 GB | -1 against the shipped 77 |
| 6 | same, stratified training sample | same | 297 | 82 = 27.6% | 25.6% | D 25.6% | 25.3 / 52.5 | 1.06 GB | +7 against 75, 95% [-5, +20] |
| 6 | same, the Catalan versions of the 281 | same | 281 | 66 = 23.5% | 23.1% | D 23.1% | 25.7 / 49.6 | 1.06 GB | -7 against 73 |
| 6 | levels 2 to 5 only (picked after the fact) | `THINK_LEVELS=2,3,4,5 THINK_TEXT_ONLY=0` | 281 / 297 / 281 cat | 85 / 81 / 70 | | | 13.4 / 51.5 | 1.06 GB | +8 / +6 / **-3**: not adopted |
| 6 | short instruction (`THINK_STYLE=short`), every level | `THINK_LEVELS=all THINK_TEXT_ONLY=0` | 297 / 281 / 281 cat | 84 / 79 / 80 against 75 / 77 / 73 | | | 21 / 52 | 1.06 GB | +9 / +2 / +7, pooled P = 0.063: left off |
| 7 | board, real seconds, levels 2 to 5, steps style | `THINK_LEVELS=2,3,4,5` | 50 | 16 = 32.0% | 34.0% | D 34.0% | real 10.0 / 47.9, est. 9.7 / 47.5 | 2.7 GB available | no timeout; see text |
| 8 | 0.8B writes a Python program, the board runs it, value matched to an option (practice set, 50 × eng/cat) | `PAL=1` | 100 | 22 to 24 against 25 for think alone | 20.0% (balanced letters) | 20.0% | 31 / 48 | 1.06 GB | on its rows 6/15 to 9/18 right, but abstentions starve think: off |

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
## Experiment 6: brief reasoning by the 0.8B itself (`copilot/think.py`, flag `THINK_LEVELS`)

**Hypothesis.** Every policy above asked the model for one token with the reasoning switched
off. A few lines of working before the letter might turn the 0.8B's near-chance letter into
something better on the easier problems, if they fit the board's clock: a 150-token prompt
leaves about 200 output tokens inside `EXPERIMENT_BUDGET_SECONDS=50` (13 s to read, 36 s to
write at 5.6 tokens/s).

**What the server allows (checked against the running `2cbe0ec`, not assumed).** The Qwen3.5
template honours `chat_template_kwargs: {"enable_thinking": true}` per request
(`/apply-template` ends the prompt with `<think>\n`), but the service's `--reasoning-budget 0`
closes the block at once: the completion is identical to the one without it (same text, empty
`reasoning_content`). Real thinking mode, through `/completion` with a hand-edited prompt,
spent 250 tokens on the simplest sample problem ("Thinking Process: 1. Analyze the Request...")
and had not reached an answer: 45 s of board time for nothing. With the block closed the model
still writes a short solution when asked ("Anna starts with 3 bags ... The correct answer is
C) 10", 63 tokens), so the working goes in the content, in **one** request, and the letter is
read from the text: an explicit `Answer: X` line (the prompt asks for it), else "the answer
is X", `**X)**`, a lone `X)` on the last lines, or the option whose value equals the last
number written, when the five options are distinct numbers. A working cut by `max_tokens`
only counts an explicit `Answer:` line: on the smoke run its last number or letter was the
middle of a case analysis ("If a = 7", "Comparing to the options: A) 16"). Anything else
abstains and the usual policy answers (middle value, then D). Two requests (working, then a
grammar-forced letter that sees it) were ruled out by the cache: this hybrid model restores
its state only at the start of the last user message, so the second request would re-read
problem and working, about 300 tokens, 26 s.

**Budget.** The prompt is counted with `/tokenize` (one cheap request; the 3-characters-per-
token guess is used if it fails), the system prompt is added when the cache is cold, and
`max_tokens` is what fits in the budget at the board's speeds, capped at `THINK_MAX_TOKENS=200`;
fewer than `THINK_MIN_TOKENS=80` left means no request. The guess was 2 to 6 tokens above the
server's `prompt_n` on warm runs and 30 below on the first, cold problem of a run (the system
prompt): the 10 s between the 50 s budget and the 60 s limit cover it. Measured on the laptop:
think requests cost 42.2 s of board time on average (median 46.5, worst 51.5), none over 60.

**Protocol.** Validation: the 281 English problems. Decision set: a stratified sample of the
English training problems by level (0 to 7) x figure (`text_only`) x numeric options
(`ladder.numeric_options`), proportional with at least one per stratum, seed 42
(`dev/stratified_sample.py`, 297 ids, `eval.py --ids`). Both sets were run with the stage on
every level and both kinds of problem (`THINK_LEVELS=all THINK_TEXT_ONLY=0`) and with the
shipped policy, and compared problem by problem (paired bootstrap, 10 000 resamples, seed 42).
The stage is skipped when a problem has no five options (114 of 281, 112 of 297) or when the
budget is gone after a solver read the text (5 and 6).

**Result, everything on** (every total of this experiment carries a ±1: the server's cache
restore can change a token of the working between a cold and a warm run, and the reviewer's
reproduction landed within one problem of each figure). Validation **76/281 = 27.0%** against
77 for the shipped policy
(gain -1, 95% [-11, +9], P(gain <= 0) = 0.61). Training sample **82/297 = 27.6%** against 75
(gain +7, 95% [-5, +20], P = 0.15). The model answered 66 validation problems (18 right, the
shipped policy was right on 19 of them) and 84 training problems (28 right against 21). Of
the 162 + 179 requests, **97 + 95 hit the 200-token cap** without an `Answer:` line and
abstained: the model writes long, LaTeX-heavy working, and the board's 5.6 tokens/s is the
binding constraint, not the prompt.

By stratum, gain of the stage over the shipped policy (think's letter where it answered,
the shipped policy elsewhere):

| stratum | val gain, 95%, P(<=0) | answered (think right / shipped right) | train gain, 95%, P(<=0) | answered |
| --- | --- | --- | --- | --- |
| all | -1 [-11, +9] 0.61 | 66 (18 / 19) | +7 [-5, +20] 0.15 | 84 (28 / 21) |
| level 0 | -4 | 6 (1 / 5) | +1 | 7 (3 / 2) |
| level 1 | -2 | 5 (0 / 2) | +1 | 7 (2 / 1) |
| level 2 | +4 | 4 (4 / 0) | 0 | 5 (0 / 0) |
| level 3 | 0 | 2 (1 / 1) | +3 | 6 (4 / 1) |
| level 4 | +2 | 10 (2 / 0) | +3 | 20 (8 / 5) |
| level 5 | +2 | 17 (5 / 3) | 0 | 14 (4 / 4) |
| level 6 | -2 | 12 (3 / 5) | -3 | 13 (3 / 6) |
| level 7 | -1 | 10 (2 / 3) | +2 | 12 (4 / 2) |
| no figure (`text_only`) | -2 [-9, +5] 0.77 | 31 | +5 [-5, +16] 0.20 | 49 |
| with a figure | +1 [-7, +8] 0.45 | 35 | +2 [-5, +9] 0.34 | 35 |
| numeric options | -3 [-11, +5] 0.81 | 44 | +1 [-9, +12] 0.47 | 58 |
| non-numeric options | +2 [-4, +8] 0.32 | 22 | +6 [-1, +13] 0.045 | 26 |
| **levels 2 to 5** | **+8 [+2, +14] 0.004** | 33 (12 / 4) | **+6 [-3, +15] 0.12** | 45 (16 / 10) |
| levels 2 to 4 | +6 [+2, +11] 0.002 | 16 (7 / 1) | +6 [-2, +14] 0.08 | 31 (12 / 6) |
| levels 1 to 5 | +6 [-1, +13] 0.05 | 38 | +7 [-3, +17] 0.10 | 52 |
| levels 2 to 6 | +6 [-2, +14] 0.08 | 45 | +3 [-8, +14] 0.33 | 58 |
| levels 0 to 3 | -2 [-9, +5] 0.77 | 17 | +5 [-1, +11] 0.06 | 25 |

**Reading it.** The guess that went in (low levels without a figure) is wrong: levels 0 and 1
lose on validation (the model's working on the easiest problems replaced 7 right answers of
the prior with 1), and `text_only` is a wash. The only stratum positive on both sets with a
usable size is **levels 2 to 5**: 78 problems answered over the two sets, the model right on
28, the shipped policy on 14; validation +8 with an interval that excludes zero, training +6
with one that does not. Caveat, stated plainly: that stratum was picked after looking at
eleven candidates, so its validation interval is optimistic (the pick itself is part of the
luck). Levels 6 and 7 lose or wash on both sets, and should never run the stage: the model's
working on hard problems is wrong more often than the prior.

**A shorter instruction (`THINK_STYLE=short`, now the default).** The first prompt asked for
"at most 6 short lines" and got LaTeX and case analyses. Asking for plain text, no LaTeX and at
most 60 words cut the cap hits from 95 to 70 of 179 requests on the training sample, the cost
from 40 to 35 s per request, and raised the answered problems from 84 to 109. The same first
run of this style on each set (no further tuning):

| set | shipped | short style, every level | gain, 95%, P(<=0) | answered (think right / shipped right) | levels 2 to 5 only |
| --- | ---: | ---: | --- | --- | --- |
| training sample, 297 | 75 | **84** | +9 [-5, +23] 0.11 | 109 (37 / 28) | +8 [-2, +18] 0.07, 57 answered (22 / 14) |
| validation English, 281 | 77 | **79** | +3 [-10, +16] 0.35 | 99 (30 / 27) | +4 [-4, +12] 0.20, 50 answered (14 / 10) |
| validation Catalan, 281 | 73 | **80** | +6 [-7, +18] 0.20 | 102 (32 / 26) | +6 [-3, +15] 0.11, 59 answered (18 / 12) |
| the three pooled, 859 | 225 | 243 | +18 [-4, +41] 0.063 | 310 (99 / 81) | +18 [+3, +34] 0.013 |

Every total above is ±1 (cache non-determinism, see the first result); the reviewer's rerun
reproduced each of them within one problem.

(Gains are "think's letter where it answered, the shipped policy elsewhere", paired per
problem; the run's own totals differ by one where a solver skip changed the fallback.) The
sign is the same on all three sets, the size is 1 to 3 points, no single set reaches P < 0.05,
and the pooled interval leans on two sets that are translations of each other. The levels 2 to
5 pooled interval excludes zero, but that stratum was picked on the steps-style English data;
its only clean confirmation is the Catalan set (+6, P = 0.11). Cost: 36 s per request, about
21 s per problem on every level and 13 s on levels 2 to 5.

**Catalan, the same 281 problems.** `data/val.jsonl` carries each validation problem in
Catalan too (same ids, OCR options of their own: the shipped policy is 73/281 there, the
middle value fires on 123). The stage, with the same English instruction, writes English
working on 142 of 172 requests (the rest mix the two languages), the prompts are longer
(mean 150 tokens, max 255) and 87 of 172 hit the cap. Result: **66/281 against 73**, gain -7
[-17, +3], P = 0.93; **levels 2 to 5: -3** [-9, +3] (47 answered, think right on 8, the shipped
policy on 11); non-numeric 0; levels 6 and 7 -1. The stratum that gained +8 on the English
versions of these very problems loses 3 on their Catalan versions: the English gain was
noise plus selection, not a property of the levels.
**Time.** The stage costs about 42 s of board time per request, whatever the result (a
cut-off working costs the same as a parsed one). With `THINK_LEVELS=2,3,4,5` on the 281
validation problems, 84 requests: board estimate mean 13.4 s per problem, median 0, worst
51.5 s, 63 minutes for the set; the shipped policy takes 4 minutes, the stage on every level
118. For the exam, per problem, from the validation runs: shipped policy
(`THINK_LEVELS` empty) mean 0.8 s, worst 38 s (a family solver's extraction); with
`THINK_LEVELS=2,3,4,5` mean 13.4 s (English) / 13.5 s (Catalan), worst 52 s, that is 4 minutes
against 63 minutes per 281 problems. A 300-problem exam: about 4 minutes with the shipped
policy, about 67 minutes with the stage on levels 2 to 5, about 2 hours on every level. The
board run (Experiment 7) gives the real seconds behind these estimates.

## Experiment 7: the board, 50 problems (`eval.py --limit 50`, real seconds)

Run on the UNO Q from a copy of this branch in `~/reason-think` (next to the controller's
checkout, never inside it), against the shared servers, with `THINK_LEVELS=2,3,4,5
THINK_TEXT_ONLY=0`, the steps instruction and `THINK_BUDGET_SECONDS=45`: the 50-problem sample
of `eval.py --limit 50 --languages eng` (its always-D floor is 17/50 = 34%).

**Accuracy: 16/50 = 32.0%** (±1, as everywhere a working is involved), the same 16 as the laptop with the same policy on the same 50;
48 of 50 answers identical (the two differences are workings that changed a token between
machines: the model's working is deterministic on one server, not bit-stable across two). 12
think requests, 5 answered (3 right), 6 cut at the cap (fell to the middle value or D), 1
skipped by the budget after a solver's extraction had read the text. No solver fired, every
status `ok`.

**Time, real seconds on the board:** mean 10.0 s, median 0, **worst 47.9 s**, 8.3 minutes for
the 50, none over 60 s; the token estimate said mean 9.7, worst 47.5. On the 13 model requests
real time was 0.99 to 1.10 of the estimate (mean 1.04) for the working, and **1.33** for the one
solver extraction (estimated 28.8 s, real 38.2 s: a grammar-constrained JSON on a cold cache).
Hence two budgets, both in `config.env`: `THINK_BUDGET_SECONDS=45` (real worst case about 50 s;
in a first run without it a request estimated at 49.5 s hit the 57 s HTTP timeout, answered
by the middle value at 57.1 s) and `SOLVER_BUDGET_SECONDS=42` (real worst case about 56 s). The
HTTP timeout, the seconds really left minus the 3 s margin, is the backstop behind both, and
every skip or timeout falls to the usual policy, so a row never lacks a letter.

**Exam time with the shipped policy** (`THINK_LEVELS` empty): on these 50 the shipped policy
spends 38 s on one problem (the extraction) and 0 on the rest, 0.8 s per problem on average on
the 281; a 300-problem exam is about 4 minutes, worst problem under 60 s. With
`THINK_LEVELS=2,3,4,5`: 10 s per problem here, 13 s on the 281 (the sample has fewer
five-option problems on those levels), about 50 to 65 minutes per 300 problems, worst problem
about 50 s.

**The board itself.** During the first run the board hard-reset twice (18:39 and 18:41 UTC,
`last -x` shows "crash", the journal ends mid-request with no shutdown messages, no OOM; the
boot of 15:37 had also ended in a crash, before any of this ran). Memory was 2.7 GB available
and the CPU at 35 C each time. The final run then completed 50 problems in 8 minutes without
incident. Whoever runs the exam should know the board can reset on its own and `predict.py`
writes each row as it goes (`out.flush()`), so a restart can resume from the last row written.

## Data v2 (15 Nov 2026): the OCR v2 options, every figure measured again

`laptop/prepare_m3kang.py` v2 reads the options of 88.1% of the training versions and 89.0% of
the validation versions (v1: 63.5% and 60.3%); `~/m3kang-data/train.jsonl` and `val.jsonl` are
the v2 files, v1 is in `~/m3kang-data/backup-v1-20261114/`. The 281 English validation problems
go from 167 with five options to 250 (83 recovered, none edited); the Catalan versions from 172
to 250 (78 recovered, 37 edited: the v2 options are language-neutral, so a Catalan version now
carries the same numbers as its English one). Train English: 911 to 1291 (380 recovered). Two
recovered option sets checked against their images (`lvl-0_2022_2`, five five-digit numbers;
`lvl-1_2016_11`, five areas in cm²) are read correctly. Every figure below is v2 unless
marked v1; the v1 figures of 14 Nov stay in the sections above. Same protocol: one run per
policy and set, paired bootstrap (10 000, seed 42) against the shipped policy; the training
sample is `dev/stratified_sample.py` on the v2 file (301 ids, strata by level, figure and
numeric options, so it differs from the 297 of Experiment 6).

| policy | flags | val eng 281 (v1 → v2) | val cat 281 (v1 → v2) | train sample (v1 297 → v2 301) |
| --- | --- | --- | --- | --- |
| always D | `SOLVERS=0 MIDDLE_VALUE=0` | 65 → 64 | 65 → 65 | 68 (v2) |
| middle value, else D | `SOLVERS=0 MIDDLE_VALUE=1` | 77 → **70** | 73 → **70** | 80 (v2) |
| shipped: solvers, middle value, D | defaults | 77 → **70** (no solver fired) | 73 → 70 | 75 → 80 |
| learned option prior (learned on **v1** train) | `OPTION_PRIOR=1` | 76 | 76 | 90 |
| brief reasoning, short style, every level (`THINK_STYLE=short`) | `THINK_LEVELS=all THINK_TEXT_ONLY=0` | 79 → **77** (+7 over shipped v2, 95% [-9, +23], P 0.21) | 80 → **73** (+3, [-11, +17], 0.36) | 84 → 85 (+5, [-10, +20], 0.28) |
| same, levels 2 to 5 only (derived per problem from that run) | `THINK_LEVELS=2,3,4,5 THINK_TEXT_ONLY=0` | 78 (+8, [-3, +19], 0.09) | 76 (+6, [-4, +16], 0.14) | 82 (+2, [-8, +12], 0.38) |

Brief reasoning on v2: the stage now runs on 246 to 267 problems per set (more have five
options), 101 to 118 workings hit the cap, 35 s of board time per request, 31 s per problem
on average on every level (12 s on levels 2 to 5). Pooled over the three sets (863 problems):
every level +15 [-11, +41], P(<=0) 0.14; levels 2 to 5 +16 [-2, +34], P 0.048, the same
picture as on v1 (+18 and +18): a small gain in the same direction on every set, never clear
on any one of them, and the stratum was chosen on the v1 data. `THINK_LEVELS` stays empty.

**Why the middle value falls from 77 to 70 (and 73 to 70).** The rule now fires on 167
English validation problems instead of 120: 44 right (26.3%) against 36 of 120 before. On the
83 recovered problems it fires on 48 and is right on 8 (16.7%), while D is right on 15 of those
48: -7, the whole drop. On the 380 recovered training problems it fires on 223, right on 61, and
D is right on 61 of them: zero gain, no loss. So the recovered problems do not break the rule;
they just carry no gain, and on validation the 48 of them happen to be D-heavy (15 of 48 = 31%).
Neither fractions nor an inferred option explain it: the v2 file does not mark inferred
options, fraction and decimal sets are 10 of 168 (the rule is right on 5), and the two
recovered sets checked against their images are correct.

What does separate the rule's hits from its misses is whether the five values are **printed in
order**. When they are ascending (or descending) the middle value is option C, a position; when
they are not, it is a value. Data v2, the rule where it fires:

| stratum | train 1466: n, middle right, D right | val eng 281: n, middle right, D right | val cat: n, middle, D |
| --- | --- | --- | --- |
| values in ascending order | 465, 133 (28.6%), 132 | 82, 18 (22%), 27 | 82, 18, 27 |
| not ascending | 421, 129 (30.6%), 92 | 86, 26 (30%), 12 | 86, 26, 12 |
| of the ascending, recovered in v2 | 111, 34, 32 | 24, 2, 11 | 21, 4, 8 |
| of the not ascending, recovered in v2 | 112, 27, 29 | 24, 6, 4 | 22, 5, 4 |
| fraction or decimal values | 25, 13, 2 | 10, 5, 2 | 10, 5, 2 |

(The Catalan numeric strata equal the English ones because the v2 options are shared across
languages.) Unordered option sets are real Kangaroo layouts, not OCR noise (five lengths, five distances or
five small integers printed in a shuffled order, each in several training problems). The prior holds there
(train 129 against 92); on ordered sets it is "always C" and has nothing over always D (133
against 132).

**An extra condition, chosen on train, looked at once on validation.** Candidates on the 1466
training problems, gain over the current rule (paired bootstrap):

| condition on the rule | train gain, 95%, P(<=0) | val eng, one look | val cat |
| --- | --- | --- | --- |
| abstain when the values are ascending | -1 [-33, +30] 0.54 | +9 [-4, +22] 0.10 | +9 |
| abstain when ascending **or descending** | **+11 [-23, +44] 0.28** | **+10 [-3, +23] 0.08** | +10 |
| only integer values | -11 [-19, -4] 1.00 | -3 | -3 |
| only problems without a figure | -15 [-40, +10] 0.89 | -3 | -3 |
| only problems with a figure | -23 [-57, +11] 0.91 | -2 | -2 |

Train prefers "abstain when the values are printed in order" by 11 problems, inside a wide
interval; validation agrees in sign (+10 on 281, 80 instead of 70, in both languages). It is
in the code as `MIDDLE_VALUE_SKIP_ORDERED=1` (`ladder.middle_letter(problem, skip_ordered=True)`,
`ladder.is_ordered`), **off by default**: a +11 of 1466 with P = 0.28 on the set that chose it
is not a gain the hidden test is owed, and the validation look is one look. On the v1 files
it changes nothing in English (77 either way) and gains 5 in Catalan (73 to 78). It is the
controller's call; the measured expectation is +1 to +3 points on 281 with no time cost.

**The learned option prior** was learned on the v1 training file (`data_curated/option_prior.json`,
`learned_on`); its 76 / 76 / 90 here are on v2 problems it never saw in this form and should be
re-learned on v2 by its owner before being compared.

## The practice set (15 Nov 2026): the exam's format, 100 rows, `data/demo/train.jsonl`

The organisers' practice set: 50 problems written for the datathon (not M3Kang), in English and
Catalan (100 rows), 80 rows of text and 20 with a figure, levels 0 to 7, five options on every
row, **20 rows per correct letter**. The final exam is 20 other problems, one language each, 4
with a figure, run by the organisers with our `predict.py` on the board (60 s per problem, no
network, nobody watching). Everything below is measured on these 100 rows only, on the laptop
(board seconds from token counts), one run per setting; the controller measures real seconds on
the board. With balanced letters, always D is 20 and 90 of the 90 numeric option sets are
printed in ascending order, so the middle value is option C on all of them: the shipped policy
answers C 90 times and D 10, and scores **16/100**.

| setting (`THINK_LEVELS=all THINK_TEXT_ONLY=0` unless stated) | right / 100 | think answered (right) | fell through (right, by the middle value) | board s mean / max |
| --- | ---: | --- | --- | --- |
| shipped policy (middle value, else D) | 16 | | | 0 / 0 |
| always D | 20 | | | 0 / 0 |
| `THINK_STYLE=short`, cap 200, budget 45 | **25** | 57 (15 = 26%) | 43 (10) | 33.7 / 44.6 |
| short, cap 200, budget 57 (the most the limit allows) | 25 | 61 (15) | 39 (10) | 34.7 / 49.1 |
| `THINK_STYLE=match` ("the letter whose value equals your result"), cap 200, budget 45 | 20 | 55 (9) | 45 (11) | 35.7 / 44.6 |
| short, cap 300, budget 90 (not feasible on the board) | 22 | 67 (16) | 33 (6) | 42.0 / **69.9** |
| short, cap 400, budget 120 (not feasible) | 22 | 67 (16) | 33 (6) | 49.7 / **87.8** |

Paired bootstrap on the 100 rows: short cap 200 against the shipped policy +9 [+1, +17],
P(<= 0) 0.021; against always D +5 [-7, +17], P 0.23. The match instruction is worse than short
(+4 against shipped, 0 against D): told to compare its result with the options, the model
names C more often (55 answers of C) and is right on 9 of 55. Cap 300 and 400 answer 10 more
rows, 1 of them right, and lose 4 that the middle value had got by falling through; the 33 rows
still cut at 400 tokens are the same 33 cut at 300, workings that re-read the options and start
again ("Let me re-read the options..."), so no cap finishes them. On the board a 300-token
working takes 54 s to write before the prompt is read: the cap stays at 200, and budget 57
buys 4 more answered rows and no more right ones for 5 more seconds of worst case.

**Figure rows (text_only false, 20 rows, labels D 10, E 4, A 4, C 2).** The model, which
cannot see the figure, answered 18 of them and got 6 (30%); the shipped policy got 2; a fixed
letter would get 4 on average and 10 only with D on this particular set, which is 20 rows of
10 problems. No fixed letter is justified by that: the stage stays on for figure rows
(`THINK_TEXT_ONLY=0`). Their prompts are shorter (22 s per row against 37).

**When the working gives no letter (43 rows at cap 200).** Falling to the middle value gets 10,
to D 8, to C 12 (the middle value is C on 40 of the 43), to A 7, to E 8: the differences are two
or three rows out of 43, noise. The fallback stays the middle value, then D.

**By language and level.** Catalan 12/50 and English 13/50 (8 and 7 right among the answered
rows); the per-level counts (10 to 16 rows each) run from 1 to 4 right and show no stratum to
switch off; levels 0 and 1, which lost on M3Kang validation, get 4 and 3 here.

**On the board (15 Nov 2026, `eval.py --limit 0` on the 100 practice rows, real seconds, main 7ddc174 flags):** **27/100** (15 Catalan, 12 English; by level 3/16, 3/16, 2/14, 2/12, 5/12, 6/10, 4/10, 2/10), mean 33.0 s per problem, worst 45.2 s, none over 60 s, 55 minutes for the 100 rows (so about 11 minutes for the 20-problem exam). Letters answered A 11, B 11, C 44, D 16, E 18: the C surplus is the middle-value fall-through. `results/ablations.csv` on the board, run `practica-board-think-short-all`.

**Recommendation for the 20-problem exam, under 60 s each:** `THINK_LEVELS=all`,
`THINK_TEXT_ONLY=0`, `THINK_STYLE=short`, `THINK_MAX_TOKENS=200`, `THINK_BUDGET_SECONDS=45`, the
rest as shipped. Measured here 25/100 against 16 for the shipped policy and 20 for always D,
with an estimated 34 s per problem on average and 45 s at most (real board time ran at 0.99 to
1.10 of the estimate in Experiment 7, so about 50 s worst case; 20 problems, about 12 minutes).
Nothing measured beats 25/100 clearly: the gain over always D is +5 with an interval of [-7,
+17], and the only clear gain is over the shipped policy, whose middle value is "always C" on
this format. The flags are left as shipped in `config.env`; this is the controller's switch.
## Experiment 8: program-aided reasoning on the practice set (`copilot/pal.py`, flag `PAL`)

**Hypothesis.** The 0.8B gets arithmetic wrong in prose but writes a short calculation in Python
acceptably; if the board runs the program and its value has to equal one of the five options,
the letter is right more often than with the brief text reasoning of Experiment 6.

**What runs.** One chat request: the stable block (a system instruction and two worked examples
invented for the module, both explicit brute force: a count over 1 to 50 and a search over pairs,
each a few lines ending in `answer = ...`) in earlier messages, so the server's checkpoint at the
start of the last user message keeps it cached between problems; the statement and the five
options in the last user message. Temperature 0, seed 42, `max_tokens` from the board clock so
that prompt, output and the program's 2 s fit `PAL_BUDGET_SECONDS=45` minus what the problem
already cost. The first fenced block is parsed (`ast`), checked and run with `exec` in a thread:
imports only of `math`, `itertools` (without its infinite iterators; `permutations`,
`combinations`, `product` refuse more than 2 million tuples) and `fractions`, no attribute that
starts with `_` or names a frame, no dunder name, no `try`/`with`/`class`/`global`, a short list
of pure builtins, a tracer that stops the program after 2 s or 1 million lines or when a variable
holds more than 2 million items, and size checks on `range`, `**`, `*`, `<<`, `+` and
`math.factorial/comb/perm/prod` (a single long C call is the one thing a tracer cannot stop).
Every exception is caught. The value of `answer` (or of the last single-value `print` when there
is no `answer`; a list or set counts as its length only when the question says "how many" or
"quants"/"quantes") is matched against the options that are one clean number (short unit, `3/4`,
`25%` also as `0.25`): equal within 1e-6, else the nearest option within 1% if it is the only one;
otherwise the stage abstains and the usual order answers (think with what is left of its 45 s,
then the middle value, then D). With `PAL_TEXT_ONLY=1` (the default) problems with a figure skip
the stage. `pipeline.solve` calls it just before think and returns `rule="pal"` when it decides.

**Protocol.** `data/demo/train.jsonl`, the organisers' practice set: 50 problems × eng/cat = 100
rows, 80 without a figure, correct letters balanced (20 per letter). Laptop, a private llama-server
on port 8095 with the board's flags (`--parallel 1 --cache-ram 0 --ctx-checkpoints 2`), so no
other session touched the cache. The shipped exam setting otherwise (`THINK_LEVELS=all
THINK_TEXT_ONLY=0 THINK_STYLE=short`, middle value, D). Paired bootstrap over the 50 problem ids
(both rows of an id resampled together), 10 000 draws, seed 42, against think alone. Board seconds
are token estimates. Four runs, one change each:

- **A**: the module as first written (one direct and one brute-force example, imports of `math`
  only, PAL on figures too), and a pessimistic cache rule (the stable block counted as cached only
  after a request of this stage on a problem it answered).
- **A2**: A plus the recommendations of the controller after reading the 50 statements (most are
  enumerations over a small space): both examples brute force, `itertools` and `fractions`, last
  `print`, list length for "how many", no PAL on figure problems. Same cache rule as A.
- **A3**: A2 with exact cache tracking: `copilot/client.py` records the leading messages of the last
  completed chat request per server, and the block is counted as read again unless they are this
  stage's. This is the code on the branch.
- **B**: A3 with the statement of every Catalan row replaced, for PAL only, by the English text of
  the same id (`PAL_TEXT_FIELD=text_eng` on a copy of the file; think still reads the Catalan).
  Not available in the exam, where each problem comes in one language; it measures what the
  Catalan costs.

| run | correct / 100 | PAL decides (right) | PAL eng / cat rows | think after PAL abstains (right) | middle value (right) | think alone on PAL's rows | paired vs think alone, 95% | board s mean / max |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- |
| think alone (exam setting, rerun) | **25** | | | 57 (15) | 40 (10) | | | 34.0 / 44.6 |
| A | 20 | 15 (5) | 4/8, 1/7 | 8 (0) | 71 (15) | 3 | -5, [-14, +4], P(≤0) 0.89 | 27.9 / 47.6 |
| A2 | 24 | 18 (9) | 7/11, 2/7 | 25 (6) | 54 (9) | 5 | -1, [-8, +6], 0.67 | 30.8 / 47.6 |
| A3 (branch) | 22 | 15 (6) | 5/9, 1/6 | 26 (6) | 56 (10) | 5 | -3, [-10, +4], 0.84 | 31.1 / 47.6 |
| B (English text for PAL) | 31 | 21 (13) | 5/9, 8/12 | 26 (6) | 51 (12) | 6 | +6, [-2, +15], 0.10 | 31.6 / 47.6 |

Think alone reproduces the 25/100 of the exam-setting note in `config.env` exactly (57 decided, 15
right). The worst row of every run, 47.6 s, is a problem PAL does not apply to (non-numeric
options): think alone, over its 45 s by its own estimate, as before. No row passes 60 s; PAL's
own rows have a worst case of 43.4 s, and the program ran at most 0.15 s on the laptop.

**What the table says.**

- **Where PAL answers, it is right more often than think.** A2: 9 of 18 against 5 for think alone on
  the same rows; A3: 6 of 15 against 5; B: 13 of 21 against 6. In A, with figures, the 7 figure
  rows PAL answered were all wrong (8 text rows: 5 right), hence `PAL_TEXT_ONLY=1`.
- **Where it abstains, it costs think.** On the rows PAL leaves, think receives what is left of its
  45 s after PAL's request (29 to 32 s spent on average), and on 42 to 47 of them it no longer fits its 80
  tokens: they fall to the middle value. Those rows score 15 to 16 against 20 for think alone
  in A2/A3. The gain on PAL's rows (+1 to +4) does not pay for this loss (-4 to -5).
- **Catalan costs PAL most of its gain.** Same problems, same options: with the Catalan text PAL
  decides 6 Catalan rows and gets 1 right (A3); with the English text it decides 12 and gets 8
  (B). The English rows do not change between A3 and B (5/9), as they should. With English
  statements throughout (B), PAL is right on 13 of its 21 decisions.
- **The cache rule matters for the 60 s, not for accuracy.** With A2's rule two requests
  were sized as cached while the server read the 264-token block again (+23 s unplanned: in
  both, the row before was one PAL does not apply to, where think ran). With A3's tracking the prompt
  estimate equals the server's `prompt_n` on all 15 answered rows. A3's lower score than A2 (22
  against 24) comes from different `max_tokens` and cache states, i.e. different workings; on
  100 rows it is noise.
- **Why it abstains.** A3, 76 rows where the stage applies: 4 skipped by the budget, 16 programs
  cut at `max_tokens` (cold cache plus a long statement), 4 errors or no `answer`, and 52 programs
  that ran (6 of them through the last `print`): 35 values matched no option, 2 were not a
  number, 15 matched. The model writes runnable code readily; it writes
  the right computation for one problem in five.

**Conclusion.** PAL does not beat brief reasoning on the practice set as the exam will see it:
22 to 24 against 25, the interval includes zero on both sides, so `PAL=0` stays the default.
The hypothesis is half confirmed: on the problems where the program's value lands on an option,
the letter is right 40 to 62% of the time against about 30% for think on the same rows, and
much more often with English statements (8/12 against 1/6 on the Catalan rows). Two things stand
between that and a gain, and they are the next experiments, not settings to switch on now: (1)
an abstention must not starve think, which needs a smaller PAL budget or a cheaper first step;
(2) Catalan statements, which on the exam have no English twin. B's +6 ([-2, +15], P 0.10) is
not available on the exam and is not significant on 50 problems either.

### Experiment 8, appendix: translating first (variant C) and PAL on English problems only

**Variant C** (`PAL_TRANSLATE=1`, branch `reason-pal-2`): a problem whose `language` is not English
is first translated by the model, in a request on the same stable block (one more invented pair
at its end: a worked Catalan-to-English translation under the instruction "keep every number,
unit, name and the sentence structure; output only the translation"), so that the program
request after it reads only its own last message. `max_tokens` is 1.4 × the statement's tokens,
cut further so that the program can still follow; the two requests share
`PAL_TRANSLATE_BUDGET_SECONDS=50` (board estimate). The translation is discarded, and the row goes
to think if think still fits, when it is cut, empty, loses a number of the statement (the
problem's own leading number excepted), or has more Catalan/Spanish function words than English
ones. **PAL on English only** (`PAL_LANGUAGES=eng`): the A3 stage on English rows, think on the
others. Same protocol as above (private server on port 8095, `--parallel 1`, the board's flags).

| policy on the 100 rows | correct | PAL decides (right) | eng / cat rows | paired vs think alone, 95% | board s mean / max |
| --- | ---: | ---: | --- | --- | --- |
| think alone (exam setting) | 25 | | 13 / 12 | | 34.0 / 44.6 |
| PAL B, English text for PAL (not possible in the exam) | 31 | 21 (13) | 11 / 20 | +6, [-2, +15], P(≤0) 0.10 | 31.6 / 47.6 |
| C, real translation, `--parallel 1` server | 25 | **0** | 13 / 12 | 0 (the same 100 answers) | 34.0 / 44.6 |
| PAL on English rows only | 23 | 9 (5) | 11 / 12 | -2, [-8, +3], P(≤0) 0.81 | 35.0 / 47.6 |

**C never ran PAL.** With the translation pair the stable block is 300-odd tokens, about 27 s on
the board when it is not cached. On a `--parallel 1` server think replaces the cached prompt every
time it runs, so the block was never cached: 38 Catalan rows skipped the translation on budget,
38 English rows skipped the program on budget, every one of them fell to think, and think
answered exactly as it does alone. The 25 is think alone, not a measurement of the translation.
For C to run at all the block has to stay cached. The branch has the pieces for that, measured on
a few rows only, not on the 100, and off by default: `PAL_SLOT=1 LLM_DEFAULT_SLOT=0` on a
server started with `--parallel 2` pins PAL to its own slot (every other request goes to slot 0),
and `pal.warm_up` reads the block once into that slot (about 28 to 32 s on the board, charged to
the first problem where the stage runs; that problem gets no PAL and no think). The board's
server runs `--parallel 1`, so this would also mean changing `math-llm.service`.

**What the translations looked like** (smoke runs on 8 Catalan rows without a figure, on the
two-slot server; no problem text is reproduced here). With the instruction alone, before the
worked example was added, the 0.8B answered one row in Spanish and on another echoed the Catalan
statement under the instruction. With the worked example, inside the stage (budget 50 s): 2 of
the 8 were skipped on budget (the first paid the warm-up; the other is the longest statement, 93
tokens), 6 were translated, all within the token cap, and 1 of the 6 was judged not English.
Translated without a budget, 7 of the 8 dropped the problem's own leading number ("8.", which is
not data; the check now ignores it), and one also dropped a time range that the question needs. How
much that costs PAL on the 50 Catalan rows was not measured: the runs were stopped at the
controller's decision before the last call.

**PAL on English rows only** loses 2 against think alone (11 against 13 on the English rows, the
Catalan rows unchanged at 12): PAL answers 9 English rows and gets 5 right, but its abstentions
again leave think too little of the 45 s.

**Recommendation for the exam** (20 problems, one language each, 4 with a figure, 60 s each):
`PAL=0`, brief reasoning alone on every level, as shipped. No PAL variant measured here beats it on
the practice set; C cannot run on the board's single-slot server; and the one variant with a gain,
B, needs an English text that a Catalan exam problem does not have.

## The exam setting on the board (15 Nov 2026, 10:00): program stage with a dedicated slot

`math-llm.service` restarted with `--parallel 2 --ctx-size 8192` (board/systemd); `PAL=1 PAL_TRANSLATE=1 PAL_SLOT=1
LLM_DEFAULT_SLOT=0`, think on what the program leaves. Laptop, two-slot server, the 100 practice rows: **38/100**
(the program decides 30 rows, 20 right: English 12/18, translated Catalan 8/12; think 7 of 26; middle value 11 of 42),
against 25 for think alone on the same server. Board, real seconds, 20 rows (10 English problems and 10 other
Catalan ones, 6 with a figure, `/tmp/exam20.jsonl`): **8/20** against 5/20 for think alone on the same rows
(from the 100-row board run), mean 29.1 s, worst 49.4 s, none over 60 s, 9.7 minutes in all; the board estimate was
within 2 s of the real time on every row. Memory after the restart: 2664 MB available. Letters answered A 4, B 1,
C 10, D 3, E 2 against truths 4/5/3/6/2. This is the configuration shipped for the exam.

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

**Brief reasoning (Experiments 5 and 6), after the grade became 50% Reasoning.** `THINK_LEVELS`
stays **empty** (off) in `config.env`. The stage works as built: one request sized by the board
clock, real time within 0.99 to 1.10 of the estimate on the board, a 57 s HTTP timeout and the
usual policy behind every skip, so `predict.py` never passes 60 s and never lacks a letter. What
it does not do is win clearly. With the short instruction it gains 1 to 3 points on each of the
three sets (training sample +9, English validation +2, Catalan +7; pooled +18 of 859, P = 0.063),
and on levels 2 to 5 the pooled interval excludes zero (+18, [+3, +34]), but that stratum was
chosen after looking, no single set reaches P < 0.05, and the first instruction lost 7 on the
Catalan set. The price is 13 s per problem on levels 2 to 5 (36 s per request), 65 minutes per
300 problems against 4. If the controller wants the expected +1 to +2 points and the exam has
no total-time cap, `THINK_LEVELS=2,3,4,5 THINK_TEXT_ONLY=0` (`THINK_STYLE=short`,
`THINK_BUDGET_SECONDS=45`) is the setting measured here; levels 0, 1, 6 and 7 should never run
it (they lose on validation). Levels 2 to 5 with the figure problems included: `THINK_TEXT_ONLY=0`,
because the figure problems did not lose (+1, +2) and the text-only ones did not win.

**Program-aided reasoning (Experiment 8).** `PAL=0` stays. On the organisers' practice set it scores
22 to 24 of 100 against 25 for brief reasoning alone: right on 40 to 62% of the rows it answers,
but its abstentions leave think too little of the 45 s, and Catalan statements cut its decisions
and its accuracy. The module, its sandbox and the exact cache tracking in `copilot/client.py`
stay on the branch for the next attempt (a smaller PAL budget, or English statements). Variant C (translate first) and
PAL on English rows only did not change that (25, with PAL never reached on a single-slot server,
and 23; appendix to Experiment 8).

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
# Experiment 6: the stratified training sample, then the stage on every level and the shipped policy, per set
python3 dev/stratified_sample.py > results/train-strat300.ids
THINK_LEVELS=all THINK_TEXT_ONLY=0 python3 eval.py --limit 0 --languages eng --name T-think-all-eng281
THINK_LEVELS=all THINK_TEXT_ONLY=0 python3 eval.py --input data/train.jsonl --ids results/train-strat300.ids --limit 0 --languages eng --name T-think-all-train297
THINK_LEVELS=all THINK_TEXT_ONLY=0 python3 eval.py --limit 0 --languages cat --name T-think-all-cat281
python3 eval.py --limit 0 --languages eng --name T-base-eng281   # and --ids / --languages cat likewise
# Experiment 8, laptop, private server on 8095 with the board's flags (run B reads a copy of the file with text_eng added)
LLM_PORT=8095 PAL=0 python3 eval.py --input data/demo/train.jsonl --limit 0 --name pal-baseline-think
LLM_PORT=8095 PAL=1 python3 eval.py --input data/demo/train.jsonl --limit 0 --name pal-A3
LLM_PORT=8095 PAL=1 PAL_TEXT_FIELD=text_eng python3 eval.py --input <copy with text_eng> --limit 0 --name pal-B-eng-text
LLM_PORT=8095 PAL=1 PAL_TRANSLATE=1 python3 eval.py --input data/demo/train.jsonl --limit 0 --name pal-C-translate
LLM_PORT=8095 PAL=1 PAL_LANGUAGES=eng python3 eval.py --input data/demo/train.jsonl --limit 0 --name pal-eng-only
# Experiment 7, on the board, from a copy of the branch next to the controller's checkout
THINK_LEVELS=2,3,4,5 THINK_TEXT_ONLY=0 python3 eval.py --limit 50 --languages eng --name B-final-l25-eng50
```

Each run adds a line to `results/ablations.csv` with its commit and writes the per-problem
CSV (`rule` and `extra` columns carry the rule that answered and the vote tallies or value).
