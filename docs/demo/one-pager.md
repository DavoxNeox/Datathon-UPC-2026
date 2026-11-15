# Math on the Edge · Teach track · one page for the jury

**A maths copilot that never gives the answer, running entirely on an Arduino UNO Q (4 GB),
offline, with M3Kang as the teacher.** Graded in two halves: a Reasoning exam corrected from
`predict.py`'s answers, and this Teaching demo judged in three minutes.

## Reasoning half: deterministic, measured, honest

The small model does not reason in text: its letter was measured at chance (21.7% on 281 M3Kang
validation problems), and its confidence anti-correlated with being right. What works is making it
write a short Python program that the board runs. The **exam policy** (15 Nov 2026): the model
translates the statement into English, writes a program, the board runs it in a restricted
interpreter and the value has to equal one of the five options (exact when it is right); brief
reasoning is the backup when the program gives no letter, then the middle value, else D.
Measured on the organisers' practice set (50 problems in two languages, 100 rows, 20 rows per
correct letter), one run per setting:
- any fixed letter: **20/100**;
- the M3Kang policy (middle value, else D): **16/100** (every numeric option set is printed in order, so the middle value is C);
- brief reasoning of the model alone, on the board: **27/100**, 33 s per problem;
- exam policy, on the laptop: **38/100** (the program decides 30 rows, 20 right);
- exam policy, on the board with real seconds, 20 rows: **8/20** against 5/20 for brief reasoning on the same rows; mean 29 s, worst 49 s, about 10 minutes for the 20 exam problems.

Twenty rows is a small sample, and the exam is 20 problems: the expectation is a few points above
a fixed letter, not a promise. For history, the M3Kang policy (the middle value, a prior about how
Kangaroo distractors are built, not reasoning) scored 70/281 = 24.9% on validation and 140/562 on
the board with the v2 options. The program stage never enters the hints.

The 0.8B language model cannot solve Kangaroo problems in text (we measured it: chance level). So on
stage it never reasons. The copilot corrects with the M3Kang labels, picks the next problem at the
student's level, and offers a ladder of hints built from the dataset itself: an easier
neighbour problem found by embeddings, a strategy card, and the solution only on request.
The LED matrix shows a tick or a cross and the mastery map; the teacher view shows every
student by topic and level.

## Teaching half: five numbers (all measured, `docs/results-A.md`, `docs/error-analysis.md`)

| | number | n |
| --- | --- | --- |
| Model's letter, M3Kang English validation | **21.7%** (61 right): chance level | 281 problems |
| Most confident quarter of the model | **16.9%** right: confidence anti-correlated with truth | 70 of 281 |
| Practice set, any fixed letter / M3Kang policy / exam policy (laptop) | **20** / **16** / **38** right of 100; on the board, 20 rows: **8** vs 5 for brief reasoning, mean 29 s, worst 49 s | 100 rows, 20 on the board |
| Template solvers, 4 families | fired on **4** of 911 training problems (3 right, 1 wrong): about +0.3 points | 911 problems |
| The board, everything running | **2.6 GB free**, cold start **2 min**, embedding **0.12 s**, reading 11.4 tok/s, writing 5.6 tok/s | measured 14 Nov 2026 |

Hints cost no model time: every step of the live demo ran in under 0.2 s in rehearsal, with
a board estimate of 0.0 s. The "before and after" with people follows the protocol in
`docs/teach-measurement.md` (n = 15 answers per condition) and is reported as such.

## What the jury should notice

1. The small model does not reason in text, and that is a virtue on stage: nothing waits for it, nothing it says can be wrong. What works is a short program it writes and the board runs.
2. The student reasons: three hints and a lesson, climbed on demand; no answer before the student commits.
3. M3Kang is the teacher: neighbour hint, correction and level come from the dataset's labels and structure.
4. Everything is offline on the board, one USB cable; the page's timing table shows real seconds per step.
5. The Reasoning half is measured and stated honestly: a program the board executes, numbers and limits included.

## Architecture (text diagram)

```
                 Arduino UNO Q, 4 GB, Debian 13, Wi-Fi off
 ┌───────────────────────────────────────────────────────────────────────┐
 │  systemd services (start at boot)                                    │
 │   math-llm    llama-server  Qwen3.5-0.8B Q8_0   :8081   1059 MB      │
 │   math-embed  llama-server  bge-small-en  Q8_0   :8082     75 MB      │
 │   math-relay  forwards both ports to the app's Docker network         │
 │                                                                       │
 │  App Lab app  user:math-copilot  (container, 91 MB)                   │
 │   python/main.py ─ copilot/webapp.py ─ hal/web.py  → page on :7000    │
 │      │ trainer.py   next problem, mastery 0..5, SQLite students.db    │
 │      │ hints.py     rung 1 neighbour (retrieval.py, index.db 1747 ids)│
 │      │              rung 2 strategy card + manipulative               │
 │      │              rung 3 solver trace / LLM sentence (quality-gated)│
 │      │              rung 4 solution (label from M3Kang)               │
 │      └ hal/led.py   tick / cross / mastery map ─ Bridge ─ sketch.ino  │
 │                                                        8x13 LED matrix│
 │  data/ (never in git): train.jsonl, val.jsonl, index.db, images/     │
 └──────────────────────────────┬────────────────────────────────────────┘
                                │ USB only: adb forward tcp:7002 tcp:7000
                        laptop browser  http://127.0.0.1:7002  (/teacher)
```

## What did not work, and we say so

- The model's letter carries no information (prefers D 38%, C 3% of the time); bias
  correction made it worse (17.8%). The middle-value rule that served M3Kang is a prior about
  how Kangaroo distractors are built, not reasoning, and on the practice set (letters balanced,
  options printed in order) it falls to 16/100, below any fixed letter. The exam policy is the
  program stage with brief reasoning behind it; 8/20 against 5/20 on the board is a small sample.
- Kangaroo problems are not templated: parametric solvers fire on about 1 problem in 20 of
  their own family; the program stage is what lifted the practice set.
- The model's one-sentence hint is off in Catalan until its judged quality passes 70%.

## Next

Measure with real students before and after; turn the model hint on per topic as quality
is judged; add the error-signature, lineage and bilingual rungs now in branches.

Repository: `github.com/DavoxNeox/Datathon-UPC-2026` · M3Kang is research-only: ids, never
statements, in git.
