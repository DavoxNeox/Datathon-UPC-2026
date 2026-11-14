# Module interfaces

This file is the contract between the four branches (`infra` A, `data` B, `trainer` C,
`hints-app` D). Each module below has an owner. In Phase 0, A wrote a **stub** for every
module that returns test data, so everyone can import and call the others' functions from
day one. Each owner replaces their stub with the real code, keeping the signatures.

Rules:

- Changing a signature or a return shape means changing this file first, and telling the
  team before merging.
- Everything under `copilot/` runs on the board: Python 3 standard library and `sqlite3`
  only. No pip packages. The App Lab app (`app/`) may use what App Lab provides
  (`arduino.app_utils`, `numpy`), nothing else.
- Student-facing strings come in Catalan with an English version: fields end in `_ca` and
  `_en`.
- Never put M3Kang problem text in a committed file. Refer to problems by `id`.

## Shared data shapes

### Problem

The M3Kang row as written by `laptop/prepare_m3kang.py`, plus the fields our code adds:

```python
{
  "id": "lvl-0_2015_13",      # same id in every language
  "language": "eng",          # "eng" | "cat" | ...
  "level": 0,                 # 0..7 (M3Kang difficulty, 0 = grade 5)
  "year": 2015,
  "text_only": True,          # from M3Kang: no figure needed
  "text": "...",
  "options": {"A": "12", "B": "15", "C": "18", "D": "20", "E": "24"},  # {} when OCR failed
  "label": "C",
  # added by us, optional until B's module fills them:
  "topic": "arithmetic",      # topic key, see below
}
```

### Topic keys

Eight topics. Code uses the English key; the student sees the Catalan name. The `visual`
flag is provisional until B measures it (Phase 3).

| key          | name_ca                   | name_en                   | visual (provisional) |
| ------------ | ------------------------- | ------------------------- | -------------------- |
| `arithmetic` | Aritmètica i problemes    | Arithmetic and word problems | no                |
| `logic`      | Lògica                    | Logic                     | no                   |
| `digits`     | Xifres i nombres          | Digits and numbers        | no                   |
| `counting`   | Comptatge i camins        | Counting and paths        | no                   |
| `areas`      | Àrees i fraccions         | Areas and fractions       | yes                  |
| `angles`     | Angles                    | Angles                    | yes                  |
| `spatial`    | Raonament espacial        | Spatial reasoning         | yes                  |
| `boards`     | Taulers i patrons         | Boards and patterns       | yes                  |

The order above is the row order on the LED matrix (row 0 = `arithmetic`).

### Mastery

Per student and topic, an integer 0..5:

| value | meaning                                              |
| ----- | ---------------------------------------------------- |
| 0     | no data                                              |
| 1     | always fails                                         |
| 2     | correct with hints                                   |
| 3     | sometimes correct without hints                      |
| 4     | consistently correct without hints                   |
| 5     | correct without hints one level above                |

`mastery_map(student_id)` returns `{topic_key: int}` with all eight keys present.

### Hint rungs

| rung | content                                                    | owner of the content |
| ---- | ---------------------------------------------------------- | -------------------- |
| 0    | no hint used                                               |                      |
| 1    | an easier solved neighbour problem (with image if visual)  | B via `retrieval`    |
| 2    | a strategy card for the topic (+ manipulative button)      | `data_curated/strategies.json` |
| 3    | a step from the solver trace, or a one-sentence LLM hint, or a second strategy | A (`solvers`), D (`hints`) |
| 4    | the solution: letter, value, full trace                    |                      |

An answer given after rung 3 or 4 never raises mastery.

### Solver trace

`solvers.solve(problem)` returns `None` or:

```python
{
  "answer": "C",              # letter that matches exactly one option
  "value": "18",              # the computed value, as a string
  "family": "ages",           # solver family key
  "trace": [                  # ordered steps; the LAST step states the answer and is never shown as a hint
    {"text_ca": "...", "text_en": "...", "value": "..."},   # value is optional
    ...
  ],
  "timings": [...],           # optional: llama-server `timings` of each LLM call, for the board clock
}
```

### Hint result

`hints.get_hint(problem_id, rung, lang)` returns:

```python
{
  "rung": 3,
  "kind": "neighbour" | "strategy" | "trace" | "llm" | "solution",
  "text_ca": "...", "text_en": "...",
  "problem": {...},           # rung 1 only: the neighbour problem (without its label)
  "manipulative": "rotate",   # rung 2 only, optional: "rotate" | "paths" | "dice"
  "estimated_board_seconds": 0.0,
}
```

### The fourth hint: a short lesson (14 Nov 2026, user request)

The hint button works `HINT_MAX_USES` times per problem (now 4). Uses 1 to 3 climb the ladder
as before. The **fourth** use returns a short theory lesson that helps the student think about
this kind of problem, never a formula that produces the answer and never the solution:

```python
# data_curated/lessons.json  (owner: content)
{"lessons": [
  {"key": "counting", "family": null,          # topic key; family optional (families.json keys)
   "title_ca": "...", "title_en": "...",
   "text_ca": "60-110 words: the idea, why it works, one tiny example with numbers that are NOT
               the problem's, one question to ask yourself", "text_en": "...",
   "strategy_ref": 2}                           # optional: the strategy card it builds on
]}
# copilot/hints.py (owner: D)
get_lesson(problem_id, lang="cat") -> dict | None
    # the lesson of the problem's family when one exists, else of its topic, else None;
    # {"rung": "lesson", "kind": "lesson", "title_ca", "title_en", "text_ca", "text_en",
    #  "estimated_board_seconds": 0.0}; passed through the leak filter against this problem.
```

Web (D + UI): the fourth press calls the lesson; it is shown as a card of its own, counts as
`hint_rung_used = 3` for mastery (an answer after it does not raise mastery), and the fourth
dot is drawn differently (a small book) so the student knows it is a lesson, not a hint.

## Functions by module and owner

### `copilot/topics.py` (B)

```python
TOPICS: list[dict]                          # the eight rows of the table above, in LED order
get_topic(problem_id: str) -> str           # topic key; "arithmetic" when unknown
is_visual(topic: str) -> bool
```

### `copilot/retrieval.py` (B)

```python
neighbors(problem_id: str, level_delta: int = 0, same_topic: bool = True,
          lang: str = "cat", k: int = 1) -> list[dict]
```

Returns up to `k` problems (Problem dicts in `lang`), most similar first, whose `level`
is `problem.level + level_delta` (or the nearest level that has candidates), never the
problem itself in any language. Search runs on the English text of the same `id`
(bge-small is an English model); the returned dicts are in `lang`.

### `copilot/trainer.py` (C)

```python
next_problem(student_id: str) -> dict                       # a Problem dict in Catalan
record_answer(student_id: str, problem_id: str, letter: str,
              hint_rung_used: int) -> dict
    # -> {"correct": bool, "label": "C", "topic": "arithmetic",
    #     "mastery_before": int, "mastery_after": int, "review": bool}
mastery_map(student_id: str) -> dict[str, int]              # all eight topic keys
```

`student_id` is a pseudonym chosen by the student or teacher; no personal data is stored.

Added for the demo (14 Nov 2026, controller):

```python
start_student(student_id: str, level: int | None = None) -> dict
    # Creates or resets the student. With level (0..7, the Kangaroo band the teacher picks)
    # the diagnostic starts there and every topic's base level is set from it; with None
    # the diagnostic runs from level 0 as before. Returns mastery_map(student_id).
reset_student(student_id: str) -> None     # forgets every answer and mastery of that pseudonym
```

Web (D): a start screen with the pseudonym, an optional level selector (0..7, shown with the
school-year labels in Catalan) and a "Reinicia" button that calls `reset_student`.

### `copilot/solvers/__init__.py` (A)

```python
solve(problem: dict) -> dict | None     # Solver trace shape above, or None when no family applies
```

`solve` is also what `predict.py` calls first. It must finish well inside the time limit:
the extraction prompt is short and its output is forced by a GBNF grammar.

### `copilot/hints.py` (D)

```python
prefetch(problem_id: str, lang: str = "cat") -> None        # warm the LLM prompt cache in a thread
get_hint(problem_id: str, rung: int, lang: str = "cat") -> dict   # Hint result shape above
```

### `copilot/hal/led.py` (A)

```python
show_result(ok: bool) -> None                 # tick or cross
show_mastery(mastery: dict[str, int]) -> None # 8 rows, bar of 0..13 LEDs each
show_path(grid: list[list[int]]) -> None      # animate the path counter (manipulative b)
```

Backend is chosen by `RUNTIME` in `config.env` / environment: `sim` prints the frame as
ASCII and keeps the last frame for the web page; `board` sends it over the App Lab Bridge.
Callers never know which one runs.

### `copilot/difficulty.py` (A, innovation "empirical difficulty")

```python
estimate(db_path: str | None = None) -> dict[str, dict]
    # {problem_id: {"n": int, "p_correct": float, "p_without_hints": float, "shrunk": float,
    #               "level": int, "prior": float}}  read-only over the trainer's `answers` table
adjusted_level(problem: dict, estimates: dict) -> float   # M3Kang level +- up to 2, 0..7
report(db_path: str | None = None) -> dict                 # JSON-serialisable, labels in ca/en
```

M3Kang's `level` is the Kangaroo band a problem was set for; `estimate` measures how hard
it is for THIS class from the answers stored on the board (nothing leaves the device):
`shrunk = (correct + a * prior_L) / (n + a)` with `a = 3` and `prior_L` the class's own
rate on level L (0.5 without data). `adjusted_level` shifts the level by
`(prior_L - shrunk) / 0.25` levels, clipped to +-2, and only after 3 answers on the
problem; with fewer, or no data, it returns the M3Kang level. `report` lists the 10
hardest and 10 easiest problems with enough answers (ids, n, p) and the rate per level,
with a `labels` dict of Catalan and English strings for every column. Ids only, never text.
Formula, constants and the mapping are documented at the top of the module. The report
carries a `note` (ca/en): the method was validated on a SIMULATED class only
(docs/difficulty.md), nothing is measured with real students yet. Recommended use: the
teacher's `report()`; the trainer hook below is measured as neutral and stays off.

## Empirical difficulty

How the trainer uses `adjusted_level`, behind `DIFFICULTY_ADJUST=0|1` in config.env
(default 0: the trainer behaves exactly as above):

- `trainer._level_of(problem_id, level)` returns the M3Kang level when the flag is off and
  `difficulty.adjusted_level(...)` over `difficulty.estimate(trainer.db_path())` when on.
- The adaptive rule (`_choose_adaptive`) uses it in two places: the wanted level after the
  last answer is `round(adjusted level of the last problem) +- 1` instead of `level +- 1`,
  and a neighbour is accepted or skipped by ITS adjusted level, so a problem the class
  finds much harder than its band is treated as a problem of that harder band. With the
  flag on, retrieval is asked for `level_delta = wanted - M3Kang level` so the neighbours
  come from the wanted band.
- The diagnostic, the review problems and the bank fallback keep M3Kang levels: they
  pick problems by band from the bank, where the empirical level is unknown for most ids.

- `estimate` is read once per `next_problem` (`trainer._estimates()`), never when the
  flag is off; `tests/test_difficulty.py` checks the count.

Proposed, not implemented: a `level_fn` argument to `trainer.configure(...)` (default
`None` = the rule above) would let the simulator and the tests inject any level function
without touching the flag. Measured on a simulated class only (docs/difficulty.md): the
hook did not reduce a simulated student's wrong answers, so the recommended use of the
module is the teacher's report, not the choice of problems.

### `copilot/lineage.py` (innovation: the lineage of a problem)

An exploration, not a hint: "look how this idea grows across the levels". The rungs are
further problems, shown unsolved and without their answers; nothing in the chain helps to
answer the current problem, so it never counts as a hint rung.

```python
lineage(problem_id: str, lang: str = "cat", min_similarity: float = 0.75,
        max_links: int = 5) -> list[dict]
    # At every level other than the problem's own, the most similar training problem of the
    # SAME topic (embedding index, English vectors), kept when similarity >= min_similarity,
    # at most max_links (the most similar stay), ordered easiest level first. Each link:
    # {"id", "level", "year", "topic", "similarity", "text" (in lang), "language",
    #  "options", "text_only"}  -- never the label, never problem_id itself.
    # Empty list without an index or for an unknown id.
led_frame(chain: list[dict], current_level: int) -> list[list[int]]
    # 8x13 frame for hal.led (brightness 0..7): row = level 0..7; a link is a bar from the
    # left at brightness 3 whose length is its similarity (0.5 -> 0 LEDs, 1.0 -> 13);
    # the current level is a full row at 7. Returns the frame; the caller draws it.
embeddings_needed(problem_id: str) -> int   # 0 for a training id (stored vector), 1 otherwise
DEFAULT_MIN_SIMILARITY = 0.75               # the default above; calibration in docs/lineage.md
```

Cost on the board: one embedding at most (0.12 s) for a validation id, none for a training
id, plus about 12 ms of Python on the laptop (one dot product per same-topic row).

Calibration (docs/lineage.md): on a clean second sample of 15 validation chains at 0.75,
14/65 links (21.5%) are the same mathematical idea; links at 0.85 or above are 18/20 over
both samples. The web should show the similarity of every rung (the bar of `led_frame`)
and may mark rungs at 0.85 or above as strong.

Web proposal (not implemented, `webapp.py` untouched): an "Explora el llinatge" button,
apart from the hint ladder, draws a staircase of up to five thumbnails, one step per level
from easiest (bottom left) to hardest (top right), each with its level, year, similarity bar
and the `data/images/<id>_<lang>.png` miniature when the topic is visual, the current
problem's step highlighted; clicking a step opens that problem read-only (no label), and
the LED shows `led_frame(chain, level)`.

### `copilot/signatures.py` (innovation: error signatures)

**POST-ANSWER EXPLANATION ONLY, NEVER A HINT.** A signature states the relation between
the chosen value and the correct one (double, one too many, "the 12 of the statement was
not added"): with the options still in front of them a student inverts it and finds the
correct option in one step, and the leak filter cannot see it because no text writes the
value (every signature except `statement_number` pins the correct option this way: 85%
of the signed distractors, 1176/1381). So the
web calls `diagnose()` only once the problem is closed, the answer recorded and "La
resposta era C" shown, and displays the text as the explanation of the error next to the
solution. Never while the options are enabled, never as a hint rung.

```python
diagnose(problem: dict, chosen_letter: str) -> dict | None
    # -> {"signature": "plus_one",                     # one of SIGNATURE_KEYS below
    #     "confidence": "high" | "low",                # low: correct value < 10, or two signatures fit, or "none"
    #     "text_ca": "...", "text_en": "...",          # explanation for the student, never the value or the letter
    #     "evidence": {"chosen_letter": "D", "chosen_value": "19", "correct_value": "18", "difference": "1",
    #                  "ratio": "19/18", "statement_numbers": ["1", "3", "10"],
    #                  "candidates": ["plus_one"], "dropped_by_leak_filter": [], ...}}
SIGNATURE_KEYS = ["sum_vs_product", "product_vs_sum", "statement_number", "digits_swapped", "sign",
                  "times_10", "div_10", "double", "half", "plus_one", "minus_one",
                  "missing_add", "missing_subtract", "none"]
```

`None` when there is nothing to diagnose: the answer is right, the letter is not an
option, or the chosen or the correct option is not a single number (pictures, sets,
ratios, OCR noise). `"none"` when both are numbers but no signature fits. Pure stdlib;
every text passes `copilot/leak_filter.py` (a matching signature whose text would name
the correct value is dropped and the next one is tried). The web shows the text only when
`confidence` is `"high"`; the teacher page may list every row. `evidence` holds the
correct value and the difference for logs and the teacher page.

Measured (val + train, 938 problems with a numeric correct option): 39% of the numeric
distractors get a signature, 16% with high confidence; a null model with the design
removed estimates that about three in four signatures below 10 and one in two above 10
(high confidence included) would also fire on a random option of the same size. Details,
order of the signatures and the manual judgement in `docs/error-signatures.md`.

Web wiring (controller): after `record_answer` returns `correct: False` and the solution
panel is drawn, `d = signatures.diagnose(problem, letter)`; if `d` and
`d["confidence"] == "high"`, show `d["text_ca"]` as a "Per què m'he equivocat?" line under
"La resposta era C". Nothing changes in the hint ladder or in mastery.

## Phase 0 stubs

Every module above exists as a stub that returns fixed test data and raises nothing.
`tests/test_interfaces.py` checks that the stubs (and later the real code) keep these shapes.
Run `python3 -m unittest discover tests` before every commit.

## Rung 0: the problem in the other language (14 Nov 2026, branch `innov-bilingual`)

M3Kang aligns Catalan and English by `id`, so before any mathematical hint the student can
read the same statement in the other language. Rung 0 separates "I don't understand the
statement" from "I can't solve it" and is **not a hint for mastery**: the web app keeps
`hint_rung_used` at 0 when only rung 0 was used, and `record_answer` is unchanged.

```python
hints.translation(problem_id: str, lang: str = "cat") -> dict   # lang = what the student reads now
hints.get_hint(problem_id, 0, lang)                              # the same; rungs are now clamped to 0..4
```

```python
{
  "rung": 0, "kind": "translation",
  "language": "eng",            # the other language: eng for a Catalan reader, cat for an English one
  "available": True,            # False when the data has no version in that language (then text "" and options {})
  "text": "...", "options": {"A": "12", ...},   # text and options of that version; NEVER its label
  "text_ca": "El mateix problema, en anglès.", "text_en": "The same problem, in English.",
  "estimated_board_seconds": 0.0,   # a dictionary lookup, no model
}
```

Web (`copilot/webapp.py`): `GET /api/translate/{show|hide}`. `/api/state` carries
`translation` (the result above while shown, else `null`), `translation_available`,
`other_language` and `rung0` (uses on this problem). Each `show` is a `timeline` row
`rung0:translation` and is counted per session and per student (uses, problems, answers
and correct answers after using it, against answers and correct answers without it).
`/api/teacher` adds `rung0`: `{"students_using", "students_total", "uses", "with": {"answers", "correct"},
"without": {"answers", "correct"}, "by_student": {name: {...}}}`.
