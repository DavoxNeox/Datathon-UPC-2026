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
Formula, constants and the mapping are documented at the top of the module.

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

Proposed, not implemented: a `level_fn` argument to `trainer.configure(...)` (default
`None` = the rule above) would let the simulator and the tests inject any level function
without touching the flag. Cost on the board: `estimate` re-reads the `answers` table on
every trainer step (one SQL query, milliseconds for a class's history); a cache keyed by
the number of answers would remove even that if the table grows large.

## Phase 0 stubs

Every module above exists as a stub that returns fixed test data and raises nothing.
`tests/test_interfaces.py` checks that the stubs (and later the real code) keep these shapes.
Run `python3 -m unittest discover tests` before every commit.
