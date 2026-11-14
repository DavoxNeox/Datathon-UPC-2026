# Reason track: experiments against always-D

Goal: a `predict.py` policy that beats the always-D floor (65/281 = 23.1% on the English
validation set) by at least 10 problems, and also beats the most frequent letter of
whatever set it is scored on, within the rules: 60 s per problem on the UNO Q, RAM next to
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
| 5 | 0.8B writes its working, letter read from it, every level | `THINK_LEVELS=all THINK_TEXT_ONLY=0` | 281 | 76 = 27.0% | 23.1% | D 23.1% | 25.1 / 51.5 | 1.06 GB | -1 against the shipped 77 |
| 5 | same, stratified training sample | same | 297 | 82 = 27.6% | 25.6% | D 25.6% | 25.3 / 52.5 | 1.06 GB | +7 against 75, 95% [-5, +20] |
| 5 | same, the Catalan versions of the 281 | same | 281 | 66 = 23.5% | 23.1% | D 23.1% | 25.7 / 49.6 | 1.06 GB | -7 against 73 |
| 5 | levels 2 to 5 only (picked after the fact) | `THINK_LEVELS=2,3,4,5 THINK_TEXT_ONLY=0` | 281 / 297 / 281 cat | 85 / 81 / 70 | | | 13.4 / 51.5 | 1.06 GB | +8 / +6 / **-3**: not adopted |
| 5 | short instruction (`THINK_STYLE=short`), every level | `THINK_LEVELS=all THINK_TEXT_ONLY=0` | 297 / 281 / 281 cat | 84 / 79 / 80 against 75 / 77 / 73 | | | 21 / 52 | 1.06 GB | +9 / +2 / +7, pooled P = 0.063: left off |
| 6 | board, real seconds, levels 2 to 5, steps style | `THINK_LEVELS=2,3,4,5` | 50 | 16 = 32.0% | 34.0% | D 34.0% | real 10.0 / 47.9, est. 9.7 / 47.5 | 2.7 GB available | no timeout; see text |

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

## Experiment 5: brief reasoning by the 0.8B itself (`copilot/think.py`, flag `THINK_LEVELS`)

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

**Result, everything on.** Validation **76/281 = 27.0%** against 77 for the shipped policy
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
board run (Experiment 6) gives the real seconds behind these estimates.

## Experiment 6: the board, 50 problems (`eval.py --limit 50`, real seconds)

Run on the UNO Q from a copy of this branch in `~/reason-think` (next to the controller's
checkout, never inside it), against the shared servers, with `THINK_LEVELS=2,3,4,5
THINK_TEXT_ONLY=0`, the steps instruction and `THINK_BUDGET_SECONDS=45`: the 50-problem sample
of `eval.py --limit 50 --languages eng` (its always-D floor is 17/50 = 34%).

**Accuracy: 16/50 = 32.0%**, the same 16 as the laptop with the same policy on the same 50;
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

## Reproduce

```bash
MIDDLE_VALUE=1 python3 eval.py --limit 0 --languages eng --name R-middle-eng281
MIDDLE_VALUE=1 python3 eval.py --input data/train.jsonl --limit 0 --languages eng --name R-middle-train-eng1466
VALUE_MODEL=1 python3 eval.py --limit 0 --languages eng --name R-value08-eng281
VOTE_SHIFTS=5 python3 eval.py --limit 0 --languages eng --name R-vote5-08-eng281
LLM_PORT=8091 LETTER_MODEL=1 SOLVERS=0 python3 eval.py --limit 50 --languages eng --name R-2bq4-letter-eng50
# Experiment 5: the stratified training sample, then the stage on every level and the shipped policy, per set
python3 dev/stratified_sample.py > results/train-strat300.ids
THINK_LEVELS=all THINK_TEXT_ONLY=0 python3 eval.py --limit 0 --languages eng --name T-think-all-eng281
THINK_LEVELS=all THINK_TEXT_ONLY=0 python3 eval.py --input data/train.jsonl --ids results/train-strat300.ids --limit 0 --languages eng --name T-think-all-train297
THINK_LEVELS=all THINK_TEXT_ONLY=0 python3 eval.py --limit 0 --languages cat --name T-think-all-cat281
python3 eval.py --limit 0 --languages eng --name T-base-eng281   # and --ids / --languages cat likewise
# Experiment 6, on the board, from a copy of the branch next to the controller's checkout
THINK_LEVELS=2,3,4,5 THINK_TEXT_ONLY=0 python3 eval.py --limit 50 --languages eng --name B-final-l25-eng50
```

Each run adds a line to `results/ablations.csv` with its commit and writes the per-problem
CSV (`rule` and `extra` columns carry the rule that answered and the vote tallies or value).
