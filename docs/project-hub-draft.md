# Arduino Project Hub: Math copilot on the UNO Q (draft)

> DRAFT for the Project Hub write-up (Phase 11). Sections follow the Hub format. `[[TODO ...]]`
> marks a missing figure, photo or decision. Figures marked *(estimate)* come from token counts on
> a laptop and must be replaced by the board's own measurements.

**Title:** A Kangaroo maths copilot that teaches, not solves, on the Arduino UNO Q

**One line:** A student answers Kangaroo problems in Catalan on a page served by the board; the
LED matrix shows a tick, a cross and the mastery map; hints come one rung at a time, and nothing
leaves the device.

## 1. Introduction

[[TODO photo of the board with the LED matrix lit and the page on a phone]]

Mathematics results in Catalonia are falling: in PISA 2022 Catalonia scored 469 points in
mathematics, 21 points below 2018 (OECD, PISA 2022; we do not use PISA 2025, whose Catalan sample
was invalidated). Teachers are stretched and generative AI, used naively, makes it worse (see
"Why this design"). We built a copilot for a classroom that has one Arduino UNO Q, no internet
and students who should keep thinking for themselves.

The copilot uses [M3Kang](https://huggingface.co/datasets/qualcomm/M3Kang), 1,747 Kangaroo
competition problems in 108 languages, as a problem bank, a library of worked examples, a topic
and difficulty map, a multilingual bridge and a benchmark.

## 2. Components and apps

- Arduino UNO Q (4 GB), its 8 x 13 LED matrix, a USB-C power supply. No other hardware.
- Arduino App Lab (the `web_ui` brick serves the page; the Bridge talks to the microcontroller).
- llama.cpp at commit `2cbe0ec`, built on the board.
- Qwen3.5 0.8B Q8_0 (835 MB): classification, number extraction, one-sentence hints.
- bge-small-en-v1.5 Q8_0 (37 MB): 384-dimension embeddings for retrieval.
- Python 3 standard library only on the board; a laptop with Python for the one-off data
  preparation (OCR of the options).

## 3. Why this design

Every choice below comes from a measurement of our own or from published evidence.

**The model never gives the answer, and the ladder starts far from it.** Bastani et al. (PNAS,
2025) ran a field experiment in high-school maths: students with unrestricted GPT-4 access did
better on practice and 17% worse on the exam taken without AI; a version that knew the solution
and gave graduated hints instead of answers removed the harm. Our hint ladder is that second
version: rung 1 is an easier solved neighbour, rung 2 a strategy card, rung 3 one step or one
question, rung 4 the solution only on request, and answers after rung 3 or 4 never raise
mastery. The language model that writes rung 3 is given the correct answer and a prompt that
forbids it; a filter in code (`copilot/leak_filter.py`) rejects any hint that contains the answer's
value, with a retry under a strict grammar. We measured [[TODO D: 3 of 66 hints rejected, 1 after
the retry]].

**Short steps, fast feedback, a teacher view.** Oreopoulos and Low (NBER WP 35620, 2026) found
that Khanmigo, a capable tutor, added no learning in their trial because students barely used
it. A hint that takes a minute to arrive is a hint nobody asks for. On our board a one-letter
answer already costs about 9 s and a line of reasoning 26 s, so rungs 1, 2 and 4 use no model and
answer in well under a second, and rung 3 is prefetched while the student reads (median
12.6 s *(estimate)*). Roschelle et al. (2016) showed with ASSISTments that immediate feedback on
homework plus reports to the teacher raised maths achievement; the LED matrix gives the tick or
cross at once and `/teacher` shows each pseudonym's mastery per topic.

**Teach at the student's real level.** Muralidharan, Singh and Ganimian (AER, 2019) measured large
gains from Mindspark, software that adapts to the level the student actually has, not the grade
they are in; Henkel et al. (2024) found the same with Rori in Ghana. Our trainer starts with a
short diagnostic, then moves one level up after a right answer and one level down, on the same
topic, after a wrong one, over M3Kang's eight levels and eight topics; mastery rises only with two
independent correct answers, at least one without hints.

**A domain map, two independent checks, spaced review.** From the `socratic-tutor` skill in
[janestreet/agent_skills](https://github.com/janestreet/agent_skills) (MIT) we took three habits:
a map of the domain (our eight topics and sixteen families), the rule that an answer counts only
after two independent checks (mastery 3 needs two distinct problems right), and spaced review
(about one problem in five revisits the topic answered longest ago).

**The small model is not allowed to reason.** We measured it: on 400 training problems the
model's letter scored 20.8% against 27.2% for always D, and its confidence was anti-correlated
with being right. So the model classifies the family, copies the numbers into a
grammar-constrained JSON object and writes one short sentence; Python computes, curated cards
explain, the student reasons.

**Catalan outside, English inside.** The embedding model is English-only. Searching with the
Catalan text finds neighbours on the right topic 43% of the time; with the English text of the
same problem id, 72%. The student never sees the English.

## 4. Architecture

[[TODO the diagram from the README as an image]]

Linux runs the two model servers and the Python copilot; the App Lab app serves the page and
talks to the microcontroller over the Bridge; the microcontroller draws on the LED matrix. The
page is the only input; the matrix and the page are the outputs. Everything runs with Wi-Fi off.

## 5. Step by step

Each step says what to run and what you should see. The full commands are in the repository
README ([[TODO link]]).

1. **Set up the board** with the organizers' guide, steps 0 to 12: build tools, llama.cpp at
   `2cbe0ec`, the two models with their SHA256, both servers as systemd services, the datathon
   code. Check: `curl http://127.0.0.1:8081/health` and `:8082/health` answer `{"status":"ok"}`.
2. **Prepare M3Kang on the laptop**: `laptop/prepare_m3kang.py --languages eng,cat --save-images`
   downloads the dataset, reads the options from the images with OCR (63% read) and splits by
   problem id. Copy `train.jsonl`, `val.jsonl` and `images/` to the board.
3. **Build the retrieval index on the board**: `build_index.py` embeds the 2,932 training rows
   (English and Catalan) into `data/index.db` (6.4 MB).
4. **Topics and families** are already in the repository (`data_curated/`): ids only. Rebuild with
   `laptop/build_topics.py`, `laptop/cluster_topics.py` and `laptop/build_families.py` if you
   change the rules.
5. **Run the tests**: `python3 -m unittest discover tests` prints `OK`.
6. **The official run**: `python3 predict.py --input data/val.jsonl --output results/predictions.csv`.
7. **Start the app** from App Lab and open `http://<board-ip>:7000`. Choose a pseudonym, answer,
   ask for a hint, watch the matrix. The teacher view is `/teacher`.
8. **Measure your change**: `eval.py --limit 50 --name <change>`, then
   `laptop/error_analysis.py` for the tables by topic, family, language, level and text_only.

[[TODO one screenshot per step 6 to 8]]

## 6. Results and error analysis

Reasoning, on the validation set (281 English problems unless stated):

| Approach | Accuracy | Time per problem |
| --- | --- | --- |
| Organizers' baseline (board, 40 problems) | 22.5% | 8.7 s |
| Baseline reproduced | 21.7% | 9.0 s *(estimate)* |
| Always D | 23.1% | 0 s |
| Bias-corrected letter | 17.8% | same |
| Family solvers, D elsewhere | [[TODO]] | [[TODO]] |

Teaching: rung 1 costs 0.6 ms for a bank problem and one embedding for a new one; the trainer
settles in 3 to 4 steps on simulated students; the leak filter rejected 3 of 66 hints, 1 after the
retry; the LLM rung takes 12.6 s median with prefetch *(estimate)*. [[TODO board figures]]

Error analysis [[TODO final run]]: on the visual topics (areas, angles, spatial, boards; 54 of the
100 sample problems) the baseline scored 30% against 37% for always D: the model reads a text
that describes a picture it cannot see, so it is at chance level there. The text topics are where
the solvers act; the most frequent families in the training set are digits of a number (97
problems), speed and time (44), sharing (38), money (29), ages (27), divisibility (25) and
percentages (25). Catalan and English score within noise of each other on the same 50 problems
(24% vs 30%, always D 34%), but Catalan costs about 15% more reading time.

## 7. What we learned, and what's next

- A 0.8B model on this board is a good clerk and a bad solver: let it copy numbers and write one
  sentence, and let code and content do the rest.
- Measure the floors. Always-D beats the model; a feature that does not beat always-D on the same
  problems is not a feature.
- Retrieval, embeddings and SQLite are free on this board; generation is what costs. Design the
  interaction around what is free.
- Next: more solver families from the frequency table, a vision model for the visual topics
  measured against the 60 s limit, calibration of the board clock, and a classroom trial of the
  ladder with a teacher.

## References

- Bastani, H. et al. (2025). Generative AI without guardrails can harm learning. *PNAS*.
- Oreopoulos, P. and Low, A. (2026). *NBER Working Paper 35620* (Khanmigo field trial).
- Muralidharan, K., Singh, A. and Ganimian, A. J. (2019). Disrupting education? Experimental
  evidence on technology-aided instruction in India (Mindspark). *American Economic Review*.
- Henkel, O. et al. (2024). Effective and scalable math support: evidence on the impact of an
  AI-tutor (Rori) on math achievement in Ghana.
- Roschelle, J. et al. (2016). Online mathematics homework increases student achievement
  (ASSISTments). *AERA Open*.
- Jane Street, `socratic-tutor` skill, [janestreet/agent_skills](https://github.com/janestreet/agent_skills), MIT.
- OECD (2023). PISA 2022 results; Catalonia: 469 points in mathematics.
- Torres-Camps et al. (2026). M3Kang. [arXiv:2601.16218](https://arxiv.org/abs/2601.16218).
  Research use only; no problem data is published here.

[[TODO check every reference's exact title, venue and year before publishing]]
