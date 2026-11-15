# Math on the Edge · Teach track · one page for the jury

**A maths copilot that never gives the answer, running entirely on an Arduino UNO Q (4 GB),
offline, with M3Kang as the teacher.** Graded in two halves: a Reasoning exam corrected from
`predict.py`'s answers, and this Teaching demo judged in three minutes.

## Reasoning half: deterministic, measured, honest

`predict.py` never calls the language model for a letter (its letter was measured at chance:
21.7% vs 23.1% always D on 281 problems, and its confidence anti-correlated with being right).
It answers with deterministic family solvers (grammar-constrained extraction, exactly-one-option
check) and, otherwise, the **middle-value rule**: when the five options are numeric, the middle
one, else D. Measured: **77/281 = 27.4%** on validation (always D 65/281), **150/562 = 26.7%**
on the board over both languages, mean 0.38 s, worst 38.7 s, none over 60 s. The gain is a
prior about how Kangaroo distractors are built, not reasoning; the bootstrap of the gain over
always D is -2 to +26 problems, so a hidden exam may hand part of it back. The rule never enters
the hints. *[Brief-reasoning experiment: result pending; reported only once measured.]*

The 0.8B language model cannot solve Kangaroo problems (we measured it: chance level). So it
never reasons. The copilot corrects with the M3Kang labels, picks the next problem at the
student's level, and offers a ladder of hints built from the dataset itself: an easier
neighbour problem found by embeddings, a strategy card, and the solution only on request.
The LED matrix shows a tick or a cross and the mastery map; the teacher view shows every
student by topic and level.

## Teaching half: five numbers (all measured, `docs/results-A.md`, `docs/error-analysis.md`)

| | number | n |
| --- | --- | --- |
| Model's letter, English validation | **21.7%** (61 right) vs **23.1%** always D | 281 problems |
| Most confident quarter of the model | **16.9%** right: confidence anti-correlated with truth | 70 of 281 |
| Official run on the board, both languages | **150/562 = 26.7%** vs 23.1% always D (eng 77/281, cat 73/281); mean 0.38 s, worst 38.7 s, none over 60 s | 562 problems |
| Template solvers, 4 families | fired on **4** of 911 training problems (3 right, 1 wrong): about +0.3 points | 911 problems |
| The board, everything running | **2.6 GB free**, cold start **2 min**, embedding **0.12 s**, reading 11.4 tok/s, writing 5.6 tok/s | measured 14 Nov 2026 |

Hints cost no model time: every step of the live demo ran in under 0.2 s in rehearsal, with
a board estimate of 0.0 s. The "before and after" with people follows the protocol in
`docs/teach-measurement.md` (n = 15 answers per condition) and is reported as such.

## What the jury should notice

1. The model never reasons, and on this board that is a virtue: nothing waits for it, nothing it says can be wrong.
2. The student reasons: three hints and a lesson, climbed on demand; no answer before the student commits.
3. M3Kang is the teacher: neighbour hint, correction and level come from the dataset's labels and structure.
4. Everything is offline on the board, one USB cable; the page's timing table shows real seconds per step.
5. The Reasoning half is deterministic and stated honestly, numbers and limits included.

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
  correction made it worse (17.8%). Shipped policy: the middle value when the five options are
  numeric, else D. That rule is a prior about how Kangaroo distractors are built (the correct
  value usually sits between distractors above and below), not reasoning; it never enters the
  hints, and a hidden test may hand part of the gain back (bootstrap on val: -2 to +26 problems).
- Kangaroo problems are not templated: parametric solvers fire on about 1 problem in 20 of
  their own family. The Reason track stays at the always-D floor.
- The model's one-sentence hint is off in Catalan until its judged quality passes 70%.

## Next

Measure with real students before and after; turn the model hint on per topic as quality
is judged; add the error-signature, lineage and bilingual rungs now in branches.

Repository: `github.com/DavoxNeox/Datathon-UPC-2026` · M3Kang is research-only: ids, never
statements, in git.
