# The demo problems: which, why, and the exact clicks

Problems are referenced by M3Kang id only (research-only data: no statement, no options, no
label, no image in git). What the speaker needs on the day (the correct values, the option
values, what each figure shows) is in `docs/demo/local/demo-notes.md`, a file that
`.gitignore` keeps out of the repository, and can be regenerated on any machine with the
data linked (`~/m3kang-data`): `python3 dev/demo_pick.py --show <id>`.

## How a problem is chosen on stage

The trainer is deterministic (`copilot/trainer.py`): the first problems of a fresh student
depend only on `SEED` (42 in `config.env`), the pseudonym and the course chosen on the start
screen. Problem 1 is at the chosen level, problem 2 two levels up, problem 3 four levels up
(the diagnostic, which needs at least three answers), each on a topic drawn from the
pseudonym, **whatever the answers are**. So the demo controls which problem appears by
typing a chosen pseudonym and course, nothing else; "Comença" resets that pseudonym first
(`start_student`), so a pseudonym used in a rehearsal gives the same chain again.

`dev/demo_pick.py` replays that choice for hundreds of pseudonyms and levels and keeps the
pairs whose first problem has a Catalan text, five clean options, a picture when the topic is
visual and a rung-1 neighbour that is really easier, of the same topic, with its own picture
when visual, and not a copy of the same problem (similarity under 0.95: Kangaroo reuses
statements across levels, and a copy is no hint). `dev/demo_pick.py --find <id>` and
`--chain <name> <level>` answer "who gets this problem" and "what does this pseudonym get".

Two conditions for the same chains to appear on the board: the same `data/train.jsonl` and
`data/val.jsonl` as on the laptop (they were pushed from the same `~/m3kang-data`, see
`docs/deploy-board.md`), and `SEED=42`. Verified on the board on 14 Nov 2026 (below); verify
again the morning of the pitch (`runbook.md`, step 6).

## The two chains (4 problems) and the reserve chain (2 problems)

| chain | pseudonym | course on the start screen | problem 1 | problem 2 |
| --- | --- | --- | --- | --- |
| **B, visual (opens the demo)** | `Mariona1` | 6è de primària (nivell 1) | `lvl-1_2024_2` | `lvl-3_2019_18` |
| **A, text** | `Guillem` | 1r d'ESO (nivell 2) | `lvl-2_2020_4` | `lvl-4_2010_12` |
| **R, reserve** | `Pau` | 2n d'ESO (nivell 3) | `lvl-3_2021_20` | `lvl-5_2022_30` |

The pseudonym must be typed exactly (`Mariona1`, capital M, no space): a different string
gives a different chain. After the two problems of a chain the diagnostic continues with a
third problem four levels above the start (Mariona1: level 5, areas), so the script never
promises what the next problem will be.

### 1. `lvl-1_2024_2`, level 1, boards (Taulers i patrons), figure

- **Why:** a count-on-a-grid problem a sixth grader can follow on a projector: short text,
  five short numeric options, the grid drawn in the picture. The rung-1 neighbour is
  `lvl-0_2024_3` (level 0, similarity 0.935, with its picture): the same idea on a smaller
  grid. It is the clearest "easier sibling" in the whole bank, and the hint gives nothing away
  because the numbers differ.
- **Rungs shown:** 1 (neighbour with image), 2 (strategy card of boards). No LLM: in Catalan
  rung 3 is also a strategy card.
- **Answer on stage:** the correct one (in the speaker notes). On the matrix: the letter for
  0.8 s, the tick, then the mastery map with the boards row growing (mastery 0 → 2). Before
  that, the four hint blocks on the bottom rows, two of them dimmed after the two hints.
- **Clicks:** `Comença` → `Pista` (action sheet at the bottom) → `Pista` → the correct value → wait for the tick (3 s) →
  `Continua` (or Enter).

### 2. `lvl-3_2019_18`, level 3, spatial (Raonament espacial), figure

- **Why:** a paper-folding problem where the picture does the explaining. The neighbour is
  `lvl-2_2019_9` (level 2, similarity 0.914, with its picture): the same action one step
  simpler. Rung 2 is the strategy card with the **"Gira i volteja" manipulative** button, the
  only rung with something that moves on screen (it opens under the hints), good on camera.
- **Rungs shown:** 1 (neighbour with image), 2 (strategy with manipulative; open it only if
  the demo is ahead of time).
- **Answer on stage:** a wrong value on purpose (in the speaker notes). This shows the cross
  on the LED, the correction message, mastery of spatial at 1.
- **Clicks:** `Pista` → `Pista` → (`Gira i volteja`, opens under the hints, optional) → the wrong value →
  wait 3 s → `Vista del professor` in the second tab.

### 3. `lvl-2_2020_4`, level 2, arithmetic (Aritmètica i problemes), text

- **Why:** an everyday word problem about buying in boxes, no figure needed (`text_only`),
  five short numeric options. The neighbour `lvl-1_2021_21` (level 1, similarity 0.827) is
  also a sharing-into-groups problem: the same "divide, then round" move. Shows that rung 1
  works on pure text too.
- **Rungs shown:** 1 (neighbour, text only), 2 (strategy card of arithmetic).
- **Answer on stage:** the correct one. Tick, mastery of arithmetic 0 → 2.
- **Clicks:** `Comença` (Guillem, 1r d'ESO) → `Pista` → `Pista` → the correct value →
  wait 3 s → `Continua` (or Enter).

### 4. `lvl-4_2010_12`, level 4, digits (Xifres i nombres), text

- **Why:** a think-of-a-number chain solved by working backwards; the neighbour
  `lvl-3_2016_29` (level 3, similarity 0.810) is another chain of the same kind, and the
  arithmetic strategy card about checking with the opposite operation is exactly the method.
- **Rungs shown:** 1, then a wrong answer for the cross; or 1 then `Solució` (rung 4) if the
  team wants to show the solution rung once: the page scrolls to the solution card and leaves
  only `Continua` (the answer afterwards does not raise mastery).
- **Clicks:** `Pista` → the wrong value → wait 3 s → `Vista del professor`.

### Reserve 5. `lvl-3_2021_20`, level 3, areas (Àrees i fraccions), figure

- **Why:** a grey-area-inside-a-square problem whose neighbour `lvl-2_2022_15` (level 2,
  similarity 0.859, with picture) is the same kind of figure: the same "cut into known
  pieces" strategy. Reserve only because the OCR text of its options is garbled on the page;
  the picture shows them correctly.
- **Clicks:** `Comença` (Pau, 2n d'ESO) → `Pista` → `Pista` → the correct value.

### Reserve 6. `lvl-5_2022_30`, level 5, counting (Comptatge i camins), figure

- **Why:** second problem of the `Pau` chain, an orderings problem with a small figure.
  Neighbour `lvl-4_2016_11` (similarity 0.729, no picture): weaker as a hint, acceptable as a
  filler.
- **Clicks:** `Pista` → the correct value.

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
| Continua (next problem) | 0.00 | 0.0 |
| Vista del professor | 0.00 | – |
| reset (`/api/reset`, the page's menu → `Canvia d'alumne`) | 0.00 | – |

No step uses the LLM in Catalan (the model hint is gated by judged quality, under 70% for
every topic), so the board estimate is 0.0 s everywhere: the only model work is one
embedding (0.12 s on the board) when a validation problem is the query. Nothing was over
10 s. Both chains produced the ids above, the neighbours above, "easier=True", the pictures,
the tick (mastery 0→2) and the cross (mastery 0→1), the teacher view with hits by level, and
the reset back to the start screen.

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
- The first `Pista` of a session loads the retrieval index (0.2 s on the laptop, more on the
  board): the runbook warms it up before the jury arrives.
- The teacher view is empty after a reset (the student is forgotten): open it **before**
  resetting, as in the click script.
- In the pitch nothing shows the LLM working. If the jury asks, the honest answer is in the
  lessons block: the model's hint (rung 3) is off until its judged quality passes 70%; the
  model's letter was measured and discarded.
- `dev/demo_pick.py --chain <name> <level>` tells what any pseudonym would get, in case
  someone wants a real name on the day.
