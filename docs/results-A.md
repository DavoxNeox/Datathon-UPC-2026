# Measurements, branch infra (A)

All "board" seconds below are **estimates** from token counts (`copilot/board_clock.py`,
11 tok/s prefill, 5.5 tok/s generation, 0.25 s per embedding) until Phase 10 calibrates
them on the real board. Laptop: MacBook (Apple Silicon), llama.cpp `2cbe0ec` CPU only,
4 threads, the board's server flags. Validation = `data/val.jsonl`, English, from
`laptop/prepare_m3kang.py --languages eng,cat` (281 problems; options read by OCR for 167).

## Phase 1: the laptop reproduces the README

| what | README (board) | laptop (estimate) |
| --- | --- | --- |
| Hello world, 27 prompt tokens, 10 written | about 4 s | 4.3 s, same answer, same token counts |
| Baseline, one letter, grammar A-E | 22.5% (9/40), 8.7 s mean | 21.7% (61/281), 9.0 s mean, 16.7 s worst |
| Always D | 25% (train) | 23.1% on these 281 |
| Letters chosen (predicted/true) | D 21, A 14 of 40 | A 92/55, B 51/62, C 1/52, D 135/65, E 2/47 |

## Phase 2: the model's letter carries no information

Calibration on 400 English **training** problems (`calibrate_bias.py --limit 400 --dry-run`):
raw model 20.8%, always D 27.2%. Model prior over letters: A 32%, B 22%, C 3%, D 38%, E 6%.
The best grid setting (alpha 0.5, margin 1.0) scores 27.0% by answering D 364 times out of 400.

Scored offline on the 281 validation problems from the stored log probabilities:

| policy | accuracy |
| --- | --- |
| always D | 23.1% |
| raw model letter | 21.7% |
| bias-corrected, train-400 prior, alpha 1.0 | 17.8% |
| bias-corrected, alpha 0.5, margin 1.0 (almost always D) | 23.5% |

Raw accuracy by confidence quartile (margin between the two best letters): 25.7%, 21.4%,
22.9%, **16.9%** for the most confident quartile. Confidence is anti-correlated with being right.

Decision: `LETTER_MODEL=0` in `config.env`. When no family solver applies, `predict.py` answers
`FALLBACK_ANSWER` (D) without calling the model. The letter model stays available
(`LETTER_MODEL=1`) for measurements; `eval.py` then stores the five logprobs per problem.
The 100-problem calibration that was tried first (alpha 1.0, margin 0.1) scored 20.0% on 50
validation problems against 30.0% raw and 34.0% always D on the same 50; it was not shipped.

## Phase 5: solvers (in progress)

- Grammar-constrained JSON extraction: correct on two made-up problems, 74 to 87 prompt
  tokens, 16 to 24 written, about 11 s estimated on the board.
- Family `consecutive`: made-up problem answered correctly, 132 prompt tokens, 17.3 s estimated.
- Coverage and accuracy on validation: pending B's family frequency table.

## Known measurement artifact

Several sessions share one `llama-server` with `--parallel 1 --cache-ram 0`: the system prompt
is evicted from the slot between requests and re-read (about 33 tokens, 3 s of estimate per
problem). Runs made while others used the server show +3 s. On the board, `predict.py` runs
alone and the prefix stays cached. Raw letters were identical across runs (50/50).
