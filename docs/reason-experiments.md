# Reason track: experiments against always-D

Goal: a `predict.py` policy that beats the always-D floor (65/281 = 23.1% on the English
validation set) by at least 10 problems, and also beats the most frequent letter of
whatever set it is scored on, within the rules: 60 s per problem on the UNO Q, RAM next to
the embeddings and the app, standard library, deterministic, offline. Branch
`team/reason-predict-0ff6f3`. One change is adopted (`MIDDLE_VALUE=1`, the default since the
review of 14 Nov); the others stay behind flags that are **off**.

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
and the 2B is too slow for the board and no better. `tests/test_reason_policy.py` checks
that the Teach modules import none of this and that `predict.py` answers a letter in every
case (no options, words, noise, duplicates, server down).

## Reproduce

```bash
MIDDLE_VALUE=1 python3 eval.py --limit 0 --languages eng --name R-middle-eng281
MIDDLE_VALUE=1 python3 eval.py --input data/train.jsonl --limit 0 --languages eng --name R-middle-train-eng1466
VALUE_MODEL=1 python3 eval.py --limit 0 --languages eng --name R-value08-eng281
VOTE_SHIFTS=5 python3 eval.py --limit 0 --languages eng --name R-vote5-08-eng281
LLM_PORT=8091 LETTER_MODEL=1 SOLVERS=0 python3 eval.py --limit 50 --languages eng --name R-2bq4-letter-eng50
```

Each run adds a line to `results/ablations.csv` with its commit and writes the per-problem
CSV (`rule` and `extra` columns carry the rule that answered and the vote tallies or value).
