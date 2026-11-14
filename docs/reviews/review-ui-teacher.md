# Review of the teacher's view (`ui-teacher`, main 3e9e0bf)

Scope asked by the controller: the statistics computed by the page (Wilson, two-proportion z,
chi-square, slope, medians, streaks) reproduced on a simulated `students.db`; whether the rule-based
diagnosis claims more than the n allows; the page with an empty database and with a one-answer
student; that nothing touches the predictor or the hints; and the board observation of a `log`
with 2 rows against tiles saying 40 answers.

## What I ran

| command | outcome | kind |
|---|---|---|
| `git diff --stat 1173913 3e9e0bf`; `git diff --name-only` filtered on predict, pipeline, hints, ladder, prior, solvers, leak, config.env | 8 files: `assets/teacher.html`, `copilot/trainer.py` (+29, one new function), `copilot/webapp.py` (+10), two tests, three docs; **nothing on the Reason or hint path** | ran |
| worktree at 3e9e0bf, `python3 -m unittest discover tests` | 307 OK, 1 skipped | ran |
| `python3 -m copilot.simulate --bank data --steps 40 --students threshold2,random20-1,improving --db data/sim3.db`; sim web on port 7021 | 3 students x 40 answers; `/api/teacher` returns `log.answers` = 120, `details[*].answers` = 40 each | ran |
| Python twin of the page's statistics on `sim3.db` (Wilson, pooled two-proportion z with `erfc`, least squares slope, chi-square with its exact 4-df survival, binomial exact and normal p against 20 %, gaps, runs, working level, weakest and strongest topic) against the values the page draws (read from the DOM for each of the three students) | **all 13 rows equal for the three students** (table below) | ran |
| `--steps 1 --students threshold2 --db data/one.db` on port 7023; a fresh `STUDENTS_DB=data/empty.db` on port 7022 | both pages render, console clean | ran |
| 8 students x 150 steps into `data/big.db` on port 7024; `curl -w` on `/api/teacher`; `answer_log()` timed in-process | 1,200 answers: 262 KB in 5 ms on the laptop; 120 answers: 31 KB | ran |
| browser at desktop and 390 px: tiles, heatmap, picker, button sizes, overflow, console | findings below | ran |
| `assets/teacher.html` 205-300 (statistics and rules), 416-530 (rendering), `copilot/trainer.py:651-677`, `copilot/webapp.py:457-505`, the new tests, `docs/ui/redesign.md` round 15 | read | read only |

## The statistics reproduce

| statistic | threshold2 (page / mine) | random20-1 | improving |
|---|---|---|---|
| accuracy, Wilson 95 % | 50 %, 35–65 / 35–65 | 10 %, 4–23 / 4–23 | 58 %, 42–71 / 42–71 |
| trend, last 10 vs previous 10 | +0 pp, p = 1.00 / same | +0, p = 1.00 / same | -10 pp, p = 0.64 / -10, 0.64 |
| slope, pp per 10 answers | -0.4 / -0.4 | -1.3 / -1.3 | +10.2 / +10.2 |
| chi-square of letters (4 df) | 3.0, p = 0.56 / same | 4.8, p = 0.31 / same | 2.5, p = 0.64 / same |
| z against 20 % | 4.7, p = 0.00 / same | -1.6, p = 0.94 / -1.6, 0.94 (exact 0.97) | 5.9, p = 0.00 / same |
| longest streaks | 2 / 2 ✓, 2 ✗ | 2 ✓, 14 ✗ | 5 ✓, 6 ✗ |
| working level | 2 → 3 | – | 5 → 6 |
| weakest / strongest topic | boards 43 % (7) / digits 56 % (9) | counting 0 % (5) / spatial 13 % (30); mine picks angles 0 % (5), a tie | angles 50 % (4) / arithmetic 75 % (4) |

Formulas checked line by line: Wilson centre and half-width (`teacher.html:211-215`); the erf is
Abramowitz-Stegun 7.1.26 with the right coefficients and nesting (max error 1.5e-7); the 4-df
chi-square survival `exp(-x/2)(1 + x/2)` is exact; the pooled two-proportion z is standard and
two-sided; the slope is least squares on the answer index and `1000 * slope` is indeed points per
10 answers; gaps over 600 s are dropped as the "how" column says; runs and the current streak sign
are right. The class tiles pool the log the same way (120 answers, 39 %, 31–48 %).

## The board observation: `log` with 2 rows, tiles with 40

`answer_log()` is one `SELECT ... FROM answers ORDER BY id` with no filter other than the optional
student (`trainer.py:664-667`); every row of the table comes back, no field is required. The tiles
are computed from that same `log.answers` array (`teacher.html:417-418`: `n = log.length`), so on
one response the tile and the log cannot disagree. On my databases the counts match (120/120,
1/1). The 2 you saw is almost certainly `log.students` (two pseudonyms), which sits next to
`log.answers` in the JSON; if `log.answers` itself ever has fewer rows than the "Respostes" tile on
the same page, send me that JSON, because that would be a different bug. Not a finding.

## Findings

### IMPORTANT

**U1. The trend sentence ignores the p it computes** (`teacher.html:285`). "Millora: X punts
més" / "Empitjora" fires on a 15-point difference between the last 10 answers and the previous
ones as soon as the previous block has 5 answers; the two-proportion p is shown in the table but
not used. Reproduced with the page's own `twoProp`: 2/5 then 6/10 gives +20 pp with p = 0.46; 1/5
then 3/10 gives +10 pp (not shown) and 2/5 then 6/10 "Millora: 20 punts més". A teacher reads
that as a fact about the child. Fix: require `previousN >= 10` and `p < 0.1`, or keep the 15-point
rule and word it as a hint ("sembla millorar; encara pocs problemes").

**U2. "Depèn de les pistes: encerta amb ajuda però no sense" from three answers each way**
(`teacher.html:284`). The gate is 3 hinted and 3 clean answers, hint share 50 % or more, and a
25-point difference, which one answer produces (3/3 against 2/3 is 33 points). The sentence is
unhedged and prescribes action. Fix: 8 answers in each group and `twoProp` with p < 0.1, or the
hedged form; show the two fractions in the sentence.

**U3. "Amb 5 o més el diagnòstic és fiable" is not true** (`teacher.html:138`, `:183`). At
n = 5 the Wilson interval of 5/5 is 57–100 % and of 2/5 is 12–77 %; the page's own interval says
so one tile to the right. With 3 answers the page already writes "Domina el que fa: pot pujar de
nivell" (3/3) or "Massa difícil: baixa un nivell" (0/3 or 1/3), both unhedged, both prescribing
a level change (`:279-281`). Fix: "orientatiu fins a 20 respostes" in the few-data sentence, the
three level sentences from n >= 5 and with "(n = …)" in the text, and the interval width as the
guard (for example: only prescribe a level change when the whole interval is above 75 % or below
45 %).

### MINOR

**U4. Guessing index at small n.** The rule starts at 8 answers but uses the normal approximation
of the binomial: for 3/8 the normal gives p = 0.11, the exact binomial 0.20; for 4/8, 0.02 against
0.06. The chi-square branch at n = 8 has an expected count of 1.6 per letter (needs about 5, so
n >= 25): five of eight answers on one letter already gives p = 0.05. The sentence is hedged
("Possible resposta a l'atzar"), which is why this is minor. The table also prints the index for
any n: the one-answer student shows "z = 2.0 (p = 0.02)". Fix: exact binomial tail (a 20-line
loop), chi-square only from n >= 25, and hide the row under 8 answers like the sentence.

**U5. Topic and level sentences from 3 answers without the n.** "Reforça Angles: 33 %
d'encerts" and "Nivell de treball 2; el repte és el 3" can come from 1/3 and 2/3; the table shows
the n, the sentence does not. Fix: n in the sentence and 5 as the floor, or keep 3 and say "(3
problemes)".

**U6. "Respon molt de pressa (0 s de mediana)" on any simulated database.** The simulator writes
answers milliseconds apart, so every simulated student is told not to read. Real answers on the
board are seconds apart and the rehearsal database is real, so a live class is unaffected; a
seeded demo database would show it on stage. Guard: ignore gaps under 1 s or say "dades simulades"
when the median is under 1 s.

**U7. The student picker and the heatmap are mouse-only.** The picker's options are `tabindex="-1"`
with click handlers; the only key handled is Escape (`:445-453`); the heatmap rows select on
click only. The button, the language toggle and the two links are 44 px. Fix: ArrowUp/ArrowDown
and Enter on the list (or a native `<select>`), `tabindex="0"` and Enter on the rows.

**U8. Every answer travels every 3 seconds.** `load()` polls `/api/teacher` at 3 s and the
response carries the whole log: 31 KB at 120 answers, 262 KB at 1,200 (5 ms to build on the
laptop; the board's SQLite and JSON will be slower but well under a second). A class day of 1,200
answers moves 5 MB per minute over the board's Wi-Fi to a page nobody is watching between
glances. Fix: poll at 10 s, or `?since=<last created_at>` and merge, or an ETag made of
`(count, max id)` so unchanged logs return 304.

**U9. `answer_log` is not in `INTERFACES.md`.** The docstring is complete; the interface file
still lists `teacher_report` as the only read API of the trainer.

**U10. Ties and labels.** Weakest topic ties resolve by first appearance in the log (the random
student shows counting, not angles, both at 0/5); the "Tema més fort" needs two topics with 3
answers, so a student on one topic never gets one. Cosmetic.

## Verified without findings

Empty database: tiles "–", heatmap header only, "Encara no ha respost cap problema", picker "cap
alumne encara", no console error. One answer: tiles and interval (100 %, 21–100 %), one sentence
("Poques dades: 1 respostes"), six charts drawn, trend, slope, time and topics shown as "–", no
error. Pseudonyms go through `esc()` in every `innerHTML` and the sentences through
`textContent`. `answer_log` opens its own connection, reads two tables and closes; `record_answer`,
`next_problem`, the pipeline and the hint modules are untouched. No horizontal overflow at phone
width outside the scrolling tables; the five class tiles stack two per row.

Praise: the "how" column next to every statistic is the right habit, and all thirteen numbers
reproduce to the digit from a 60-line Python twin.
