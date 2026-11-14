# Review of `team/innov-difficulty-8199cc` (8484c17, 14 Nov 2026)

Scope: `copilot/difficulty.py`, `laptop/measure_difficulty.py`, `tests/test_difficulty.py`,
`docs/difficulty.md`, the `DIFFICULTY_ADJUST` hook in `copilot/trainer.py`, INTERFACES and config.env.
Nothing changed by me.

**Executed**: the branch's tests (OK); `laptop/measure_difficulty.py` with the defaults (16 s on the
laptop; `docs/difficulty.md` regenerated with the same headline figures); `python3 -m
copilot.difficulty --db` on a real trainer database from my web probes (works, Catalan and English
labels); the flag-off path of `trainer._level_of`. **Only read**: the four experiments' design.

## Executive summary

1. The brief promised an empirical difficulty per class from the trainer's SQLite with a measured
   error, and a hook. Delivered, read-only, stdlib, milliseconds, honest about the result: the hook
   does not reduce wrong answers in simulation and ships off; the module's value is the teacher's
   report.
2. The headline "error 0.72 → 0.52 levels" is measured against a hidden difficulty that the script
   itself plants (offsets of one or two levels on 60% of the ids, threshold students): it shows the
   estimator recovers planted offsets, not that real problems are mislabelled. The doc says so in
   its last paragraph; the controller's one-line summary did not. Any README line must say
   "simulated class".
3. Coverage is the real limit and the doc states it: after 600 answers only 21 to 41 of 1,747
   problems have the three answers the estimate needs; after 3,000, 490.

## Findings

**D1 (IMPORTANT). Say "simulated" wherever the error figure appears.** `docs/difficulty.md` headline
sections 2 and 4 and the branch summary quote 0.71 → 0.58 and 0.72 → 0.52 as if measured; the ground
truth is `measure_difficulty.py`'s own offsets. *Fix:* "on a simulated class whose true difficulty
was planted" in the first sentence of "Reading the figures" and in any summary table; the first
real figure is the report on the board after the demo day.

**D2 (IMPORTANT). With the flag on, the trainer re-reads the whole `answers` table once per
neighbour.** `trainer._level_of` calls `difficulty.estimate(db_path())` for the last problem and
again for each of up to 8 neighbours (`trainer.py:_choose_adaptive`), nine full scans per step; the
doc measured 3 → 10 ms on the laptop with 3,000 answers, more on the board's CPU and with a term of
data. The flag is off and must stay off until `estimate` is cached per step (the INTERFACES proposal).

**D3 (IMPORTANT). The hook amplifies guessing noise, as the doc found.** A lucky guess on a problem
the class rates two levels harder moves the student two levels up. Nothing to fix now; the honest
conclusion ("the module is for the teacher") should be the one in the README, not the hook.

**M1 (MINOR). The per-level rate table is not a difficulty table.** The doc explains that the
trainer keeps every student near 50% at every level, so the `by_level` rates say how the class is
matched, not how hard the bands are. The report's label "Taxa d'encert per nivell" invites the
wrong reading on the teacher page; add a sentence to `LABELS` or the page.

**M2 (MINOR). `estimate` ignores who answered.** Three misses by one student on a problem the
trainer repeated (`_least_recent`) count like three students' misses. Count distinct students in
`n`, or require answers from 2+ pseudonyms before rating.

**M3 (MINOR). Teacher page not wired.** The report exists as JSON and a CLI; `assets/teacher.html`
does not show it. For the demo it can be printed from the board.

## Figures checked

| Claim | Recomputed | Status |
| --- | --- | --- |
| hidden class, 600 answers: error 0.71 → 0.58, 41 rated, 11 of 12 shifts right way | identical | ✓ (simulation) |
| 3,000 answers: 0.72 → 0.52, 490 rated, 169 of 170 | identical | ✓ (simulation) |
| probes: 28/27/27 vs 29/29/26 wrong (600); 26/29/27 vs 29/29/26 (3,000) | identical | ✓ |
| label class: 1 of 21 changes band | identical | ✓ |
| flag off = unchanged trainer | `_level_of` returns the level; `level_delta=delta` | ✓ |
| report on a real database | runs, labels in ca/en | ✓ |

## Verdict

Keep as a teacher report; keep the hook off; write "simulated" next to every error figure.
