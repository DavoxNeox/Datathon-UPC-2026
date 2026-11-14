# Review of `innov-bilingual`, already on `origin/main` (2dbfbf5..5cc2ded, 14 Nov 2026)

Scope: rung 0 (`hints.translation`, `/api/translate/{show|hide}`, the page's "Llegeix-lo en
anglès" pill, `Rung0Stats` in `copilot/webapp.py`, the teacher section), `docs/bilingual-rung.md`,
`laptop/measure_bilingual.py`, the 10-minute protocol added to `docs/teach-measurement.md`. Nothing
changed by me.

**Executed**: the suite on `origin/main` (OK); `laptop/measure_bilingual.py` (every figure of the
token table regenerated); the M3Kang dataset card for the "108 languages" claim (confirmed).
**Only read**: the page's JavaScript and CSS, the teacher section.

## Executive summary

1. The brief promised rung 0 (the statement in the other language, by id, never the label) with a
   measurement. Delivered: a dictionary lookup (0 model time), the label never in the result or in
   `/api/state` (tested), `hint_rung_used` stays 0, and the measurement is what the doc says:
   281/281 pairs, same label 281/281, Catalan 22% more Qwen tokens than English (1.218, 269 of 281
   longer), 1.4 s more prefill per problem on the board.
2. Two decisions are defensible but should be visible to the jury: reading the other language is
   "not a hint" for mastery, and the teacher page shows accuracy "after rung 0" against "without"
   from observational counts, which the doc itself says are not comparable.
3. Small inconsistency with the start-screen wipe: `start()` resets the trainer but keeps the
   rung-0 counters of the pseudonym.

## Findings

**B1 (IMPORTANT). The teacher page shows two rates that must not be compared, side by side.**
`copilot/webapp.py:Rung0Stats.report` and `assets/teacher.html` "Esglaó 0" list `with` and `without`
correct/answers; students choose when to open rung 0 (harder statements), so the comparison is
biased by construction. `docs/bilingual-rung.md` says this in its last paragraph. *Fix:* a one-line
caption on the page ("observational: not a comparison") until the 10-minute protocol has run.

**B2 (MINOR). `start()` wipes the trainer but not the rung-0 counters.** `Session.start`
(`webapp.py`) calls `trainer.start_student` (which resets the pseudonym, see review-main I4) and
does not call `self.rung0.forget`; only `reset()` does. After a re-start the teacher page shows a
pseudonym with rung-0 answers and zero trainer answers. *Fix:* forget on start, or (better) stop
wiping on start.

**B3 (MINOR). Rung 0 adds another GET with side effects** (`/api/translate/show` increments
counters and writes `data/rung0.json`). Consistent with the rest of the API; same remedy as the
main review (POST).

**B4 (MINOR). The protocol is well designed and not run.** Crossed conditions, a `reading / maths /
time` tag per failure, n = 16 per condition, authors fluent in both languages. Until it runs, the
Teach claim for rung 0 is "possible", not measured; keep the README sentence conditional.

**B5 (MINOR). Payload.** While shown, the translation text and options travel in every 500 ms poll
of `/api/state`. Small (a few hundred bytes), noted for completeness.

**Verified claims**: "108 languages", 1,747 problems, 2007-2024, 8 levels, research-only license,
from the dataset card.

## Figures checked

| Claim | Recomputed | Status |
| --- | --- | --- |
| 281/281 pairs, same label 281/281, options in both 158/281 | identical | ✓ |
| tokens cat/eng 91.1/74.8 = 1.218, median 90/76, max 205/149, +16.3, 269/281 longer | identical | ✓ |
| per-level ratios 1.169 to 1.289 | identical | ✓ |
| board prefill 7.99 vs 6.56 s | identical (estimate from calibrated constants) | ✓ |
| reconciliation with B's 15% (34-token prefix) | arithmetic checks | ✓ |

## Verdict

Cheap, honest and well tested; label the teacher's two rates as observational and fix the counter
wipe. The Catalan of the pill and the kind line is correct ("Llegeix-lo en anglès", "Esglaó 0 · en
anglès · no compta com a pista").
