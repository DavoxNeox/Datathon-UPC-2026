# Math copilot on the Arduino UNO Q

> DRAFT of the final README (Phase 11). Replaces the organizers' setup guide at the root when
> the team agrees. Every `[[TODO ...]]` marks a figure or a fact that is not measured or decided yet.
> Figures marked *(estimate)* come from token counts on a laptop (`copilot/board_clock.py`), with
> the constants calibrated on the board on 14 Nov 2026 (11.4 tok/s reading, 5.6 tok/s writing,
> 0.12 s per embedding): the estimate was within +3.7% (mean) of the board's real time on 50
> problems. Figures marked *(board)* were measured on the board itself.

A maths copilot for Kangaroo problems that runs entirely on an Arduino UNO Q (4 GB), offline.
A student answers A to E on a web page served by the board; the board shows a tick or a cross and
the student's mastery map on its LED matrix. When the student is stuck, the copilot climbs a hint
ladder one rung at a time: an easier solved problem, a strategy card, one step of a worked
solution or a one-question nudge, and only on request the solution. The 0.8B language model never
reasons: it classifies, copies numbers and writes short sentences. The reasoning is done by our
code, by the curated content and by the student.

[[TODO photo or 20-second video of the board, the page and the LED matrix]]

Built for the Datathon FME 2026 (UPC), Qualcomm challenge "Math on the Edge", with the
[M3Kang](https://huggingface.co/datasets/qualcomm/M3Kang) dataset.

## 1. What it does

- **Teach.** An adaptive trainer picks the next problem from a map of M3Kang (embeddings, level,
  topic): a neighbour one level up after a right answer, a neighbour on the same topic one level
  down after a wrong one, with a short diagnostic at the start and spaced review of weak topics.
  Mastery per topic (0 to 5) lives in a SQLite file on the board under a pseudonym; nothing about
  the student leaves the device.
- **Hint ladder, never the answer first.** Rung 1: an easier solved neighbour (with its picture
  when the topic is visual). Rung 2: a strategy card for the topic, sometimes with an on-screen
  manipulative (rotate a shape, count paths, roll dice). Rung 3: the next step of the solver's
  trace when a solver applies, else one question written by the language model, filtered in
  code so it cannot leak the answer. Rung 4: the solution, only when asked. Answers given after
  rung 3 or 4 never raise mastery.
- **Reason, carefully.** `predict.py` answers the organizers' hidden test set. A family solver
  (ages, averages, consecutive integers, digit counts) extracts the numbers with a
  grammar-constrained JSON prompt and computes the answer in Python; the value must match
  exactly one option, so a solver never answers wrong, but it fires on about one problem in
  twenty of its family. When no solver applies, it answers the most common letter instead of
  asking the model, because we measured that the model's letter is worse than that (section 4).
- **Catalan first, English inside.** The student works in Catalan. Retrieval runs on the English
  version of the same problem, because the embedding model is English-only (section 5.4).

## 2. Architecture

```
            Arduino UNO Q (4 GB)
 ┌───────────────────────────────────────────────────────────────┐
 │ Linux (Qualcomm QRB2210, 4 x Arm)                             │
 │                                                               │
 │  llama-server :8081  Qwen3.5 0.8B Q8_0   (classify, extract,  │
 │                                           one-sentence hints) │
 │  llama-server :8082  bge-small-en-v1.5   (384-d embeddings)   │
 │                                                               │
 │  copilot/  (Python 3, standard library + sqlite3)             │
 │    pipeline.py ── solvers/ ── llm.py ── bias.py   predict.py  │
 │    trainer.py ── retrieval.py ── rag.py (data/index.db)       │
 │    hints.py ── leak_filter.py ── topics.py (data_curated/)    │
 │    webapp.py ── hal/web.py (page :7000) ── hal/led.py         │
 │                                     │ Bridge (RPC)            │
 ├─────────────────────────────────────┼─────────────────────────┤
 │ STM32 microcontroller   sketch.ino  ▼  8 x 13 LED matrix      │
 └───────────────────────────────────────────────────────────────┘
        ▲ Wi-Fi or USB (adb forward)          nothing leaves the board
   student's browser: problem, A-E, hint button, teacher view
```

[[TODO redraw as an image for the Project Hub]]

**Linux side.** Two `llama.cpp` servers (pinned commit `2cbe0ec`, see `config.env`) serve the
language model and the embedding model on `127.0.0.1`. Our Python package `copilot/` uses only
the standard library plus `sqlite3`, so nothing is installed with pip on the board. The App Lab
app (`app/`) serves the student page and the teacher view with the `web_ui` brick on port 7000
and sends LED frames over the Bridge.

**Microcontroller side.** `app/sketch/sketch.ino` receives an 8 x 13 frame and draws it on the
LED matrix: a tick or a cross after an answer, then the mastery map (one row per topic, a bar of
0 to 13 LEDs), and a path-counting animation for one of the manipulatives.

**How we use M3Kang.**

| Use | Where | What |
| --- | --- | --- |
| Problem bank | `data/train.jsonl`, `data/val.jsonl` | 1,747 problems, English and Catalan, options read from the images by OCR on the laptop (63% read) |
| Library of worked examples | `data/index.db` | every training problem embedded with bge-small; rung 1 and the trainer walk this map |
| Topic map | `data_curated/topics.json` | 8 topics for all 1,747 ids: keyword rules on the English text plus k-means on the embeddings, validated on 50 hand labels |
| Solver families | `data_curated/families.json` | 16 families of text problems with their frequency, which decided which solvers to write |
| Difficulty map | `level` 0 to 7 | the trainer's ladder; rung 1 looks one level down |
| Multilingual bridge | same `id` in `eng` and `cat` | search in English, show in Catalan |
| Benchmark | `eval.py` on `val.jsonl` | every change measured on the same problems |

The split is by problem id, so a problem and its translations never land on both sides.

## 3. How to replicate it

Start from a board set up with steps 0 to 12 of the organizers' guide (`docs/setup-guide.md`
[[TODO move the current README there]]): both services running, `data/train.jsonl`,
`data/val.jsonl` and `data/index.db` on the board.

### 3.1 Get the code

```bash
cd ~
git clone https://github.com/DavoxNeox/Datathon-UPC-2026.git
cd Datathon-UPC-2026
python3 -m unittest discover tests
```

You should see `OK` (some retrieval tests skip when `data/index.db` is missing). On the board
all 125 tests pass *(board)*.

### 3.2 Data on the board

On the laptop (once, about 40 minutes, OCR included):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r laptop/requirements.txt           # needs Python 3.12 or older for the OCR package
python3 laptop/prepare_m3kang.py --languages eng,cat --save-images
python3 laptop/build_topics.py                   # keyword topics -> data_curated/topics.json
```

Copy `data/train.jsonl`, `data/val.jsonl` and `data/images/` to the board, then on the board:

```bash
python3 build_index.py --input data/train.jsonl --db data/index.db
```

You should see `2932/2932 problems embedded` and a 6.4 MB file. The index holds every training
problem in both languages, with or without options: the teaching features need the visual
problems too. [[TODO board time for build_index; laptop: a few minutes]]

### 3.3 The official run

```bash
python3 predict.py --input data/val.jsonl --output results/predictions.csv
```

One letter per problem, `status` `ok`, every `seconds` under 60.

### 3.4 Measure

```bash
python3 eval.py --limit 50 --name my-change
python3 laptop/error_analysis.py results/eval-*-my-change.csv --out docs/error-analysis.md
```

`eval.py` prints accuracy against always-D and random, latency, and accuracy by language, level
and OCR options; `laptop/error_analysis.py` adds topic, family and text_only tables.

### 3.5 The app

```bash
arduino-app-cli app start user:math-copilot       # [[TODO the app name on the board]]
```

Open `http://<board-ip>:7000` (or `adb forward tcp:7000 tcp:7000` and `http://127.0.0.1:7000`).
The teacher view is `/teacher`. On a laptop, `python3 app/python/main.py` runs the same page in
sim mode on port 7001 with the LED matrix drawn on the page.

## 4. Results

All runs are in `results/ablations.csv` with the commit that produced them. Baseline = the
organizers' one-letter prompt with the grammar `A-E`.

### 4.1 Reasoning (`predict.py`)

| Approach | Problems | Accuracy | Mean time | Worst time |
| --- | --- | --- | --- | --- |
| Organizers' baseline (README, board) | 40 eng with options | 22.5% | 8.7 s | 12.7 s |
| Baseline reproduced, laptop | 281 eng val | 21.7% | 9.0 s *(estimate)* | 16.7 s *(estimate)* |
| Baseline on the board *(board)* | 50 eng val | 30.0% (15/50), 47/50 answers identical to the laptop | 10.3 s real (estimate +3.7%) | 16.0 s |
| Always D | 281 eng val | 23.1% | 0 s | 0 s |
| Baseline, same 50 ids | 50 eng / 50 cat val | 30.0% / 24.0% | 9.1 s / 10.6 s *(estimate)* | 16.7 s / 21.6 s *(estimate)* |
| Bias-corrected letter (train-400 prior, alpha 1) | 281 eng val | 17.8% | same request | same |
| Family solvers, D elsewhere | 281 eng val | 23.1% (65/281): no solver fired on validation | 0 s when no solver fires; 12.6 to 15.9 s *(estimate)* when one does | 15.9 s *(estimate)* |
| Family solvers, then the middle-value rule, then D (shipped, `MIDDLE_VALUE=1`) | 281 eng val | 27.4% (77/281) | 0 s when no solver fires | same |
| Same rule on the training set | 1466 eng train | 27.6% (405/1466) against 25.0% for always D | 0 s | 0 s |

On 400 training problems the model's own letter scored 20.8% against 27.2% for always D, and its
confidence ran the wrong way: the quartile where it was most sure was the least accurate (16.9%).
That is why `LETTER_MODEL=0`: when no solver applies, the fallback letter is the better bet.

Solver yield on the 911 English training problems with options: ages classified 17, fired 0;
average 15, 0; consecutive 11, fired 3 (2 right, 1 wrong before the classifier was tightened);
digit_count 5, fired 1, right. Kangaroo problems are not templated: the family keywords tag a
heterogeneous bag of puzzles, so parametric solvers add about one point over always D at most.
**The middle-value rule** (`copilot/ladder.py`, `docs/reason-experiments.md`) is a prior on how
Kangaroo distractors are built, not reasoning: the wrong options are made from the right value
(one step too many or too few, double, half), so when the five options are distinct numbers the
correct one usually has distractors above and below it and is rarely an extreme. The rule answers
the middle value and abstains on everything else (no options, words, OCR noise, repeated values),
which then gets D as before. Chosen on the training set, checked once on validation: +12 problems
on 281 (27.4% against 23.1%), +38 on the 1466 training problems. A paired bootstrap on the 281
puts the gain between -2 and +26 problems (95%), with 6% of resamples at or under zero: the sign
is well supported, the size is not, and a hidden test can return the gain to zero. Nothing else
measured beat always D: a bigger model (Qwen3.5 2B, too slow for 60 s on the board), asking for
the option's value instead of its letter (66/281), or voting over five shifts of the options
(63/281). The rest of the Reason track stays at the always-D floor; the value of the project is
the Teach track. [[TODO official run on the board with MIDDLE_VALUE=1, 562 problems]]

### 4.2 Teaching

| What | Measured | Result |
| --- | --- | --- |
| Rung 1 neighbour, train id | time per query, n=30 | 0.6 ms on the laptop, no embedding (stored vector reused) |
| Rung 1 neighbour, unseen id | time per query, n=30 | one embedding (0.12 s on the board) + 14 ms Python on the laptop |
| Rung 1 neighbour, hand check | 20 validation problems, `level_delta=-1` | easier 20/20, same real topic 15/20 |
| Hint leak filter | 66 LLM hints | 3 rejected, 1 after the retry |
| Rung 3 LLM hint | median on the board *(estimate)*, with prefetch | 12.6 s |
| Trainer convergence | simulated students on the real bank | settles in 3 to 4 steps, about 0.24 s per step *(estimate, old constants)* |
| App on the board *(board)* | end to end | page served on port 7000, real Catalan problem without its label, answer corrected in both languages, mastery updated, cross frame drawn on the matrix over the Bridge |
| RAM on the board *(board)* | both servers + relay + app container | 2,609 MB available; the LLM server takes 1,059 MB, the embedding server 75 MB, the container 91 MB |
| Catalan hints | human judgement [[TODO n]] | poor quality: rung 3 is kept for topics whose judged quality reaches `HINT_QUALITY_MIN` |

[[TODO board times for rung 3 and the trainer step, with the calibrated constants]]

### 4.3 Topics and the Catalan bridge

| What | Measured | Result |
| --- | --- | --- |
| Topic assignment, keywords only | agreement with 50 hand labels | 36/50 (72%) |
| Topic assignment, keywords + k-means (k=8), shipped | same 50 | 38/50 (76%) |
| Visual flag per topic | share of problems with `text_only = false`, final table | areas 86% (n=309), boards 83% (76), spatial 81% (352), angles 73% (75) → visual; counting 50% (60), arithmetic 29% (451), digits 26% (378), logic 15% (46) → text |
| Catalan vs English query | 60 val ids, k=5 | 17% of the neighbours in common; neighbours on the problem's own topic 72% (English query) vs 43% (Catalan query) |

The 36 vs 38 difference is inside the noise of 50 labels; the rules were adjusted once after
reading the disagreements, so 76% is an optimistic figure.

## 5. Error analysis

`laptop/error_analysis.py` joins the eval CSV with `val.jsonl`, `topics.json` and
`families.json` and prints these tables with the n next to every percentage.
[[TODO replace the sample below with the final run on all 281 validation problems:
`python3 laptop/error_analysis.py results/eval-<final>.csv --out docs/error-analysis.md`]]

### 5.1 By topic

Sample: baseline letter, 50 English + 50 Catalan validation problems (same ids), laptop.

| Topic | n | accuracy | always D |
| --- | ---: | ---: | ---: |
| arithmetic (text) | [[TODO]] | | |
| ... | | | |

See `docs/error-analysis-sample.md` for the full sample tables. What they already show:

- **Visual topics are at chance.** On the 54 problems of visual topics (areas, angles, spatial,
  boards) the baseline scored 30% against 37% for always D: the model reads a text that describes
  a picture it cannot see. [[TODO confirm on the final run]]
- **Text topics are where the solvers can win.** The families with the most problems in the
  training set are digits of a number (97), speed and time (44), sharing and ratios (38), money
  (29), ages (27), divisibility (25) and percentages (25); together [[TODO %]] of the text-only
  problems.

### 5.2 By language

Same 50 ids: 30.0% in English, 24.0% in Catalan, within noise of each other (always D: 34% on that
sample). Catalan costs about 15% more prompt tokens (10.6 s vs 9.1 s mean *(estimate)*, worst
21.6 s vs 16.7 s).

### 5.3 By level

[[TODO table from the final run; the sample shows no usable trend with 1 to 12 problems per level]]

### 5.4 Ten wrong answers, one by one

[[TODO: ids and one line each, from the explorer, no problem text]]

## 6. What didn't work, and what's next

- **Asking the model for a letter.** Below always-D on 281 problems, and more confident when
  wrong. Correcting the bias with its own log probabilities did not help (17.8%). Asking for the
  option's value with a grammar (23.5%), voting over five shifts of the options (22.4%, and 6
  problems over 60 s without a time guard), and a 2B model (26% on 50, about 2.6 tokens/s on
  the board) did not help either: `docs/reason-experiments.md`.
- **Searching with the Catalan text.** bge-small is English-only: the Catalan query finds
  neighbours on the right topic 43% of the time, the English query 72%. The bridge by `id` fixes
  it at no cost.
- **k-means on its own.** The clusters mostly follow the keyword topics; combined they add two
  labels out of 50, which is noise.
- **Catalan hints from a 0.8B model.** [[TODO D's figures]]. The ladder prefers curated content
  (strategy cards, solver traces) and keeps the LLM for topics where its hints were judged good.
- **Family solvers as a scoring strategy.** Never wrong, rarely applicable: 0 of 281 validation
  problems fired. They stay for the hint ladder, where a solver trace is the best rung 3.
- **OCR.** 37% of the problems have no readable options, mostly pictures as options; a solver
  cannot check its value there.
- Next: [[TODO: a vision model for the visual topics measured against the 60 s limit; a
  classroom trial of the ladder with a teacher; solver traces for more families as hints, not as
  answers]]

## 7. The team

[[TODO names and roles: A infrastructure and solvers, B data, topics and retrieval, C trainer,
D hint ladder and app]]

## Credits and licenses

- M3Kang: Torres-Camps et al., 2026, [arXiv:2601.16218](https://arxiv.org/abs/2601.16218),
  Qualcomm. Research use only: no problem text, image or index is in this repository; only
  problem ids and our labels (`data_curated/`).
- llama.cpp (MIT), Qwen3.5 0.8B (Qwen team, GGUF by bartowski), bge-small-en-v1.5 (BAAI, GGUF by
  CompendiumLabs), RapidOCR (Apache 2.0). See the model cards for their licenses.
- The hint ladder's design borrows from the `socratic-tutor` skill in
  [janestreet/agent_skills](https://github.com/janestreet/agent_skills) (MIT): a domain map, the
  rule of two independent checks before accepting an answer, and spaced review.
- Our code: MIT [[TODO add LICENSE]].
