# The demo problems: which, why, and the exact clicks

Problems are referenced by M3Kang id only (research-only data: no statement, no image in
git). To read one, on a machine with the data linked: `python3 dev/demo_pick.py --show <id>`.

## How a problem is chosen on stage

The trainer is deterministic (`copilot/trainer.py`): the first problems of a fresh student
depend only on `SEED` (42 in `config.env`), the pseudonym and the course chosen on the start
screen. Problem 1 is at the chosen level, problem 2 two levels up, problem 3 four levels up
(the diagnostic), each on a topic drawn from the pseudonym, **whatever the answers are**. So
the demo controls which problem appears by typing a chosen pseudonym and course, nothing
else; "Comença" resets that pseudonym first (`start_student`), so a pseudonym used in a
rehearsal gives the same chain again.

`dev/demo_pick.py` replays that choice for hundreds of pseudonyms and levels and keeps the
pairs whose first problem has a Catalan text, five clean options, a picture when the topic is
visual and a rung-1 neighbour that is really easier, of the same topic, with its own picture
when visual, and not a copy of the same problem (similarity under 0.95: Kangaroo reuses
statements across levels, and a copy is no hint). `dev/demo_pick.py --find <id>` and
`--chain <name> <level>` answer "who gets this problem" and "what does this pseudonym get".

Two conditions for the same chains to appear on the board: the same `data/train.jsonl` and
`data/val.jsonl` as on the laptop (they were pushed from the same `~/m3kang-data`, see
`docs/deploy-board.md`), and `SEED=42`. **Verify on the board the morning of the pitch**
(`runbook.md`, step 6): the ids must match this table.

## The two chains (4 problems) and the reserve chain (2 problems)

| chain | pseudonym | course on the start screen | problem 1 | problem 2 |
| --- | --- | --- | --- | --- |
| **B, visual (opens the demo)** | `Mariona1` | 6è de primària (nivell 1) | `lvl-1_2024_2` | `lvl-3_2019_18` |
| **A, text** | `Guillem` | 1r d'ESO (nivell 2) | `lvl-2_2020_4` | `lvl-4_2010_12` |
| **R, reserve** | `Pau` | 2n d'ESO (nivell 3) | `lvl-3_2021_20` | `lvl-5_2022_30` |

Checked with the real data on 14 Nov 2026 (`retrieval.neighbors` through `hints.get_hint`,
images in `data/images`, rehearsal in sim with `dev/demo_rehearse.py`):

### 1. `lvl-1_2024_2`, level 1, boards (Taulers i patrons), figure

- **Why:** a counting-on-a-grid problem a sixth grader can follow on a projector: short text
  (106 characters), options 10 / 12 / 15 / 18 / 21, the grid drawn in the picture. The
  rung-1 neighbour is `lvl-0_2024_3` (level 0, similarity 0.935, with its picture): the same
  idea with a smaller grid and one column fewer. It is the clearest "easier sibling" in the
  whole bank, and the hint gives nothing away because the numbers differ.
- **Rungs shown:** 1 (neighbour with image), 2 (strategy card of boards: look for the pattern
  that repeats). No LLM: in Catalan rung 3 is also a strategy card.
- **Correct answer:** C. The narration says the reasoning in one sentence (rows plus columns
  minus their overlap).
- **Clicks:** `Comença` → `Pista` → `Pista` → `C` → wait for the tick (3 s) → `Següent problema`.

### 2. `lvl-3_2019_18`, level 3, spatial (Raonament espacial), figure

- **Why:** a sheet folded twice and cut twice; the picture does the explaining. Options
  15 / 12 / 16 / 8 / 9. The neighbour is `lvl-2_2019_9` (level 2, similarity 0.914, with its
  picture): the same sheet folded twice and cut once. Rung 2 is the strategy card with the
  **"Gira i volteja" manipulative** button: the only rung that opens a dialog, good on camera.
- **Rungs shown:** 1 (neighbour with image), 2 (strategy with manipulative; open it only if
  the demo is ahead of time).
- **Answer on stage:** A, wrong on purpose (the label is E). This shows the cross on the LED,
  the "La resposta era E" message, mastery of spatial at 1, and lets V2 say that the next
  problem of this topic comes one level down.
- **Clicks:** `Pista` → `Pista` → (`Gira i volteja` → `Tanca`, optional) → `A` → wait 3 s →
  `Vista del professor` in the second tab.

### 3. `lvl-2_2020_4`, level 2, arithmetic (Aritmètica i problemes), text

- **Why:** a word problem about buying boxes of eggs for a recipe: everyday numbers, options
  2 / 8 / 4 / 1 / 3, no figure needed (`text_only`). The neighbour `lvl-1_2021_21` (level 1,
  similarity 0.827) is also a sharing-into-boxes problem: the same "divide, then round up"
  move. Shows that rung 1 works on pure text too.
- **Rungs shown:** 1 (neighbour, text only), 2 (strategy card of arithmetic: write the data
  and circle what is asked).
- **Correct answer:** A.
- **Clicks:** `Comença` (Guillem, 1r d'ESO) → `Pista` → `Pista` → `A` → wait 3 s →
  `Següent problema`.

### 4. `lvl-4_2010_12`, level 4, digits (Xifres i nombres), text

- **Why:** "think of a number, divide, add, multiply, the result is 777": a working-backwards
  problem, options 7 / 111 / 722 / 567 / 728. The neighbour `lvl-3_2016_29` (level 3,
  similarity 0.810) is another think-of-a-number chain. Rung 1 is useful (same inverse
  operations strategy) and the arithmetic strategy card "check by going backwards with the
  opposite operation" is exactly the method.
- **Rungs shown:** 1, then answer wrong (B) for the cross, or 1 then `Solució` (rung 4) if
  the team wants to show the solution rung once: it prints the letter and value and the
  answer afterwards does not raise mastery.
- **Correct answer:** E.
- **Clicks:** `Pista` → `B` (wrong) → wait 3 s → `Vista del professor`.

### Reserve 5. `lvl-3_2021_20`, level 3, areas (Àrees i fraccions), figure

- **Why:** grey area inside a 16 cm² square; the neighbour `lvl-2_2022_15` (level 2,
  similarity 0.859, with picture) is a grey area inside a 100 cm² square: the same "cut the
  figure into known pieces" strategy. Reserve only because the OCR of its options is noisy
  on the page (`3cm2`, `2 11 cm2`, `4cm²2`); the picture shows them correctly. Label E.
- **Clicks:** `Comença` (Pau, 2n d'ESO) → `Pista` → `Pista` → `E`.

### Reserve 6. `lvl-5_2022_30`, level 5, counting (Comptatge i camins), figure

- **Why:** second problem of the `Pau` chain: five rings taken off one by one, how many
  orders. Options 16 / 20 / 24 / 30 / 45, label B. Neighbour `lvl-4_2016_11` (paths in a park,
  similarity 0.729, no picture): weaker as a hint, acceptable as a filler.
- **Clicks:** `Pista` → `B`.

## Rehearsal in sim (14 Nov 2026, MacBook, servers up, `SIM_WEB_PORT=7006`)

`python3 dev/demo_rehearse.py --base http://127.0.0.1:7006 Mariona1 1 C A --hints 2 --hints2 2`
and `... Guillem 2 A B --hints 2 --hints2 1`, then the same clicks by hand in the browser.

| step | real s (laptop) | board estimate (`/api/state` timeline) |
| --- | ---: | ---: |
| page load, `/api/state` | 0.01 | – |
| Comença (start + first problem) | 0.03 | 0.0 |
| Pista 1 (neighbour, first call loads the index) | 0.20 | 0.0 |
| Pista 1 (later calls) | 0.00 | 0.0 |
| Pista 2 (strategy) | 0.00 | 0.0 |
| Resposta (correction, LED frame) | 0.00 | 0.0 |
| Següent problema | 0.00 | 0.0 |
| Vista del professor | 0.00 | – |
| Reinicia | 0.00 | – |

No step uses the LLM in Catalan (the model hint is gated by judged quality, under 70% for
every topic), so the board estimate is 0.0 s everywhere: the only model work is one
embedding (0.12 s on the board) when a validation problem is the query. Nothing was over
10 s. Both chains produced the ids above, the neighbours above, "easier=True", the pictures,
the tick (mastery 0→2) and the cross (mastery 0→1), the teacher view with hits by level, and
the reset back to the start screen. On the board, measured earlier the same day
(`docs/results-A.md` §10), the same flow with the pseudonym `prova` ran without errors.

## Verified on the board (14 Nov 2026, main 8501c23, over `adb forward` from the laptop)

`dev/demo_rehearse.py --base http://127.0.0.1:7002 Mariona1 1 C A --hints 2 --hints2 2` and
`... Guillem 2 A B --hints 2 --hints2 1` against the board gave exactly the chains above:
`lvl-1_2024_2` (neighbour `lvl-0_2024_3`, 0.935, with picture, tick, mastery 0 to 2),
`lvl-3_2019_18` (neighbour `lvl-2_2019_9`, 0.914, strategy with the rotate manipulative, cross,
mastery 0 to 1), `lvl-2_2020_4` (neighbour `lvl-1_2021_21`, 0.827, tick) and `lvl-4_2010_12`
(neighbour `lvl-3_2016_29`, 0.810, cross). Every step under 0.5 s real on the board, no LLM
call, teacher view and reset working. The pseudonyms were reset afterwards.

## Things seen in the rehearsal that the team should know

- The problem's picture (the statement as Kangaroo printed it) is shown **small** above the
  text, and the neighbour's picture smaller still inside the hint card. On a projector set
  the browser zoom to 150% (`Cmd` + `+` twice) before the pitch; the page still fits.
- The teacher view is empty after `Reinicia` (the student is forgotten): open it **before**
  resetting, as in the click script.
- In the pitch nothing shows the LLM working. If the jury asks, the honest answer is in the
  lessons block: the model's hint (rung 3) is off until its judged quality passes 70%; the
  model's letter was measured and discarded.
- The pseudonym must be typed exactly (`Mariona1`, capital M, no space); a different string
  gives a different chain. `dev/demo_pick.py --chain <name> <level>` tells what any
  pseudonym would get, in case someone wants a real name on the day.
