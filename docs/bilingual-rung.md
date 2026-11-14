# Rung 0: reading the problem in the other language

M3Kang ships the same problem, with the same `id` and the same answer, in 108 languages. We
keep Catalan and English. Before any mathematical hint the student can read the statement in
the other language ("Llegeix-lo en anglès" / "Read it in Catalan"). The point is diagnostic: it
separates *I don't understand the statement* from *I can't solve it*, which the hint ladder
(rungs 1 to 4) cannot tell apart.

Rules, all tested (`tests/test_hints.py` `Rung0Test`, `tests/test_webapp.py` `Rung0Test`):

- The other version is found by `id` (`hints.translation(problem_id, lang)`), text and options
  only. Its label is never in the result nor in `/api/state`.
- It costs no model time: a dictionary lookup, `estimated_board_seconds` 0.0, 1 ms on the laptop.
- It is **not a hint for mastery**: the session's `rung` is untouched, so `trainer.record_answer`
  receives `hint_rung_used = 0` when the student used nothing else. `trainer.py` is unchanged.
- Each use is a `timeline` row (`rung0:translation`) and is counted per session and per student:
  uses, problems, answers and correct answers after using it against without it
  (`data/rung0.json`, git-ignored, pseudonyms and counts only). `/api/teacher` reports it as
  `rung0` and `assets/teacher.html` shows it with Catalan and English labels.

How to try it in sim mode: `python3 python/main.py`, open http://127.0.0.1:7001, start a student,
press the pill under the problem's meta line (or the key `T`). The other language appears beside
the statement on a laptop and under it on a phone; press again to hide it. The teacher view is
at /teacher.html, section "Esglaó 0".

## The pairs in the validation split

Measured on 14 Nov 2026 with `python3 laptop/measure_bilingual.py --input data/val.jsonl
--out results/bilingual-val.csv` (ids and counts only), tokens from the running llama-server's
`/tokenize` (Qwen3.5 0.8B, the board's tokenizer) on the problem block the prompts use (text,
then one `A) option` line per option read by OCR), seconds from
`copilot.board_clock.estimate_tokens` with `BOARD_PREFILL_TPS=11.4` (config.env, calibrated on
the board).

Pairs: **281/281** validation ids have both languages, with the **same label in 281/281**;
options were read by OCR in both languages for 158/281.

| measure (problem block: text + options) | Catalan | English | Catalan / English |
|---|---|---|---|
| mean tokens | 91.1 | 74.8 | 1.218 |
| median tokens | 90 | 76 | |
| max tokens | 205 | 149 | |
| mean characters | 245 | 241 | 1.020 |
| mean board prefill seconds (`estimate_tokens`) | 7.99 | 6.56 | 1.218 |
| mean difference, tokens (Catalan minus English) | +16.3 | | |
| pairs where Catalan is longer | 269/281 | | |

| level | n | mean tokens cat | mean tokens eng | ratio |
|---|---|---|---|---|
| 0 | 20 | 86.5 | 68.8 | 1.256 |
| 1 | 17 | 82.2 | 70.4 | 1.169 |
| 2 | 29 | 81.1 | 62.9 | 1.289 |
| 3 | 12 | 84.8 | 71.4 | 1.188 |
| 4 | 62 | 98.9 | 79.7 | 1.242 |
| 5 | 53 | 92.2 | 76.2 | 1.210 |
| 6 | 49 | 91.5 | 78.1 | 1.171 |
| 7 | 39 | 92.3 | 75.8 | 1.217 |

Reading: the two versions have the same length in characters (2 % apart), but the Qwen
tokenizer spends **22 % more tokens on the Catalan text** (n = 281 pairs, 269 of them longer in
Catalan), which is 1.4 s more prefill per problem on the board at 11.4 tok/s. B's figure of
15 % more prefill is the same effect measured on a whole prompt: a fixed English prefix (system
prompt, instructions, examples) dilutes the ratio, and with the numbers above a prefix of about
34 tokens brings 21.8 % down to 15 %. On the problem text alone the correction is 22 %, not 15 %.

Consequences for the design, which already hold in the code: the hint prompt and retrieval use
the English version of the `id` (`hints._problem_block`, `retrieval.neighbors`), so the Catalan
page pays the Catalan cost only where the student reads; and rung 0 itself costs nothing, since
both versions are already in memory.

## What is not measured yet

Whether rung 0 reduces wrong answers caused by reading rather than by maths. That needs people:
see the 10-minute protocol in `docs/teach-measurement.md`. The teacher view's "correct after
rung 0 / without" columns are observational (students choose when to use it), so the two rates are
not comparable without that protocol.
