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
- Yield on real data (B's `families.json`, 21 English problems tagged `consecutive`, train+val):
  6 pass the keyword classifier, **1 fires and is right** (13.5 s estimated), 0 wrong. The other
  20 use the word "consecutive" in puzzles that follow no template (jumps, dates, calendars,
  squares of consecutive integers...). B's table: `digit_sum` 112, `speed_time` 48, `sharing` 43,
  `money` 33, `ages` 31 problems, but a sample of each shows the same heterogeneity (the
  `speed_time` tag includes an ant on a cube and seats in a car).
- Four families on the 911 English training problems with options (`ages`, `average`,
  `consecutive`, `digit_count`, each with sub-templates the model picks as a letter):

  | family | classified | fired | right | wrong | board s (mean / max) |
  | --- | --- | --- | --- | --- | --- |
  | ages | 17 | 0 | 0 | 0 | - |
  | average | 15 | 0 | 0 | 0 | - |
  | consecutive | 11 | 3 | 2 | 1 (false positive, classifier since tightened) | 15.1 / 15.9 |
  | digit_count | 5 | 1 | 1 | 0 | 12.6 |

  Net gain over always D: about 0.3 points on train. On the 281 English validation problems the
  shipped policy (solvers, else D) scores **65/281 = 23.1%**, exactly always D: no family fired.
- Conclusion: Kangaroo problems are not templated. Parametric family solvers never answer wrong
  (exactly-one-option check) but fire on about 1 problem in 20 of their own family, so on the
  hidden test they add at most about one point over always-D. The Reason track stays near the
  always-D floor; the project's value is the Teach track.

## Phase 10: the real board (Arduino UNO Q 4 GB, 14 Nov 2026)

Debian 13, 4 cores, 3.6 GB RAM (2.9 GB available after boot, 2.8 GB with both servers up),
llama.cpp `2cbe0ec` built on the board in about 35 minutes, both models verified, services active.
Our 125 tests pass on the board; `predict.py` on the sample problems answers at once.

`board/calibrate_speed.py`, 2 rounds, nothing else using the servers:

| what | README | measured | config.env now |
| --- | --- | --- | --- |
| reading (prefill), 119 to 269-token prompts | about 11 tok/s | 11.3 to 11.6 tok/s | `BOARD_PREFILL_TPS=11.4` |
| writing, 52 tokens | about 6 tok/s | 5.6 to 5.7 tok/s | `BOARD_GEN_TPS=5.6` |
| one embedding request | a fraction of a second | 0.10 to 0.15 s (0.05 s per text in a batch of 20) | `BOARD_EMBED_SECONDS=0.12` |
| hello world, 27 tokens read, 10 written | about 4 s | 10.7 and 5.7 tok/s | |

So every "board estimate" printed on the laptop before this date (constants 11 / 5.5 / 0.25) was
within about 4% on the model work and twice too pessimistic on embeddings.

Baseline on the board (`LETTER_MODEL=1 SOLVERS=0 eval.py --limit 50 --languages eng`, the same 50
problems as the laptop run):

| | laptop (estimate) | board (real) |
| --- | --- | --- |
| accuracy | 15/50 = 30.0% | 15/50 = 30.0% |
| answers identical | | 47/50 (3 near-ties flip with the platform's float arithmetic) |
| mean per problem | 9.1 s | 10.3 s real, 10.7 s estimated with the old constants |
| estimate error | | mean +3.7%, worst +5.7%, 50/50 within 15% |
| worst problem | 16.7 s | 16.0 s from the pipeline itself |

Two problems took 54 s and 41 s of wall time: the service log shows two foreign requests (348
prompt tokens, 60 generated, 41 s each) sent to the board's server at that moment, and the
evaluation's requests queued behind them (`--parallel 1`). The pipeline never generated more
than one token. In the jury's run the server is alone.

RAM with both servers and the evaluation running: 2758 MB available; `llama-server` 1059 MB
(LLM) and 75 MB (embeddings).

### The App Lab app on the board (same day)

Verified end to end: the repository root is the app, linked into `~/ArduinoApps/math-copilot`;
the sketch compiles and flashes; the Python container imports `copilot`, reaches both servers
through the `math-relay` service on `docker0` (`/health` ok from inside the container), and the
`web_ui` brick serves the student page on port 7000 (HTTP 200 from the laptop over
`adb forward`). `/api/state` returns a real Catalan problem with its topic and no label.
Answering a problem returns the correction in Catalan and English, updates mastery, and sends
a cross frame (22 LEDs) to the matrix over the Bridge, with no errors in the app log.

RAM with both servers, the relay and the app container: 2609 MB available; the container uses
91 MB. Nothing listens on the Wi-Fi interface except App Lab's own port 7000 for the page.

Cold start (`sudo reboot`): about two minutes to the Linux prompt; the two model services and
the relay answer as soon as `adb` reconnects, the app page 20 s later, with the app set as App
Lab's default. 2796 MB available after boot with everything running.

Pitfalls met on the way, all in `docs/deploy-board.md`: the container sees only the app folder;
`127.0.0.1` inside it is the container; `adb shell` sets a `TMPDIR` that breaks the sketch build;
`/proc/device-tree` is absent in the container; `app start` does not restart a running app.

## Known measurement artifact

Several sessions share one `llama-server` with `--parallel 1 --cache-ram 0`: the system prompt
is evicted from the slot between requests and re-read (about 33 tokens, 3 s of estimate per
problem). Runs made while others used the server show +3 s. On the board, `predict.py` runs
alone and the prefix stays cached. Raw letters were identical across runs (50/50).
