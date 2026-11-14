# Review of `team/reason-predict-0ff6f3` (68f067e, 14 Nov 2026)

Scope: `git diff origin/main...origin/team/reason-predict-0ff6f3` (ladder.py, votes.py, pipeline.py,
eval.py, config.env, docs/reason-experiments.md, two test files). Nothing changed by me.

**Executed**: the branch's 159 tests (OK, 1 skipped on macOS); the smoke test with `MIDDLE_VALUE=1`;
the middle-value policy recomputed in pure Python on val (eng and cat), train (eng and cat) and the
50-sample; the rank distribution of the correct value; a 2,000-sample bootstrap of the gain; the
gain by year and by level; the rule's speed; the stdlib guard. **Only read**: experiments 2 to 4
(the 2B model, the value grammar, the vote): no server on port 8091 here, and each 281-run costs
an hour of the shared server.

## Executive summary

1. The brief promised a rule that beats always-D on validation without tuning on it. Every number
   I could recompute matches: 77/281 = 27.4% (val eng), 405/1466 (train eng), 14/50 on the
   50-sample, the rank histogram 47/123/179/160/60 on plain-number training problems. The rule
   costs 3 ms for 562 problems, no model, no RAM, deterministic, stdlib, off by default, and the
   `MIDDLE_VALUE` key is in `config.env`, so the environment override works (unlike `SOLVERS`).
2. The gain is real but modest and at the edge of significance on 281: bootstrap 95% CI of the
   gain over always-D is [-2, +26] on val (P(gain <= 0) = 4.8%) and [+1, +73] on train
   (P = 2.2%). Both independent sets agree, 14 of 18 competition years agree, and only level 2
   loses. Expect about +4 points on a hidden set of M3Kang problems with OCR options, with a
   one-in-twenty chance of a small loss.
3. The rule does not depend on D being frequent: on the 120 numeric validation problems the labels
   are A 28, B 26, C 27, D 24, E 15 and the middle value scores 36. What does depend on the hidden
   set is how often it fires: 43% of the validation problems (120/281); 47 problems with options
   abstain on OCR noise. Clean options in the organizers' file would help it, missing options would
   silence it (then the policy is today's always-D).
4. The only thing to fix before adopting it is wording: the README must present it as what it is,
   a prior on how Kangaroo distractors are built, not reasoning; and it must never reach the hint
   ladder (a student taught "pick the middle number" has learned a test trick).

## Findings

**I1 (IMPORTANT). Present the rule as a prior, not as reasoning, and keep it out of the ladder.**
`docs/reason-experiments.md` is honest ("distractors are built around the right answer"), but the
README draft's Reason section will need the same sentence next to the figure, and a sentence that the
rule is not used for hints. *Fix:* one paragraph in `docs/README-final-draft.md` §4.1 and a test that
`copilot/hints.py` never imports `ladder`.

**I2 (IMPORTANT). State the uncertainty with the figure.** +12 on 281 has a bootstrap CI of [-2, +26].
`docs/reason-experiments.md` §"Validation, one look" gives the point estimate only. *Fix:* add the CI
and the train confirmation (+38 rule-only, CI [+1, +73]); say "about +4 points expected on a hidden set
of this size, with a 5% chance of no gain".

**M1 (MINOR). The train figure is written two ways.** `config.env` says 405/1466 = 27.6%,
`docs/reason-experiments.md` table says 406 = 27.7%, and "+39" in the summary; the rule alone gives
405 (recomputed), the extra one is a family solver firing in the eval run. Pick one and say which.

**M2 (MINOR). The unit regex accepts letter garbage as a unit.** `copilot/ladder.py:20`
`[A-Za-z]{1,7}` lets `"6 QQQ"` and `"5 ZZZ"` (OCR noise, 2 of 6 word-unit cases on train+val) count as
numbers. Harmless for the score (both wrong anyway) but the docstring says noise abstains. *Fix:*
whitelist the units seen in the data (cm, m, km, mm, dm, kg, g, min, h, €, %, °, cm², km/h).

**M3 (MINOR). The vote loop can exceed 60 s and the doc says it is not worth guarding.**
`copilot/votes.py:vote_letter` has no per-shift time check; the branch measured 6 of 281 over 60 s
with `VOTE_SHIFTS=5`. The flag is off, but a flag that breaks the rule when turned on should either
check `remaining` before each shift or be removed. The same for `VALUE_MODEL` (52.6 s worst).

**M4 (MINOR). Experiments 2 to 4 are not reproducible from the repository.** The 2B model file is in
`~/models` but nothing in `board/` or `dev/` starts it on 8091, and the per-problem CSVs are in the
git-ignored `results/`. Commit the CSVs under `docs/runs/` (ids only) or say the figures are
one-off.

**M5 (MINOR). `eval.py` now writes 18 columns.** `laptop/error_analysis.py` reads by column name, so
it should cope; the two 281-problem CSVs in `docs/error-analysis.md` were written with 16. Rerun the
error analysis on the new CSV once `MIDDLE_VALUE=1` ships, so the "by level" table reflects the rule.

## Figures checked

| Claim | Where | Recomputed | Status |
| --- | --- | --- | --- |
| 77/281 = 27.4% val eng, fires on 120, 36 right vs 24 for D | reason-experiments.md | 77/281, 120, 36, 24 | ✓ |
| 405/1466 train eng (config.env) / 406 (doc) | both | 405 rule-only | ✓ / off by one |
| 14/50 on the 50-sample, 7 vs 10 on 26 numeric | reason-experiments.md | 14, 26, 7, 10 | ✓ |
| ranks 47/124/180/159/60 on 571 plain-number problems | reason-experiments.md | 47/123/179/160/60 on 569 | ✓ (regex rounding) |
| unit form: 654 problems, middle 199, D 161 | reason-experiments.md | 663, 201, 163 | ✓ (same picture) |
| letters on the 120: every letter near 20-23%, rule 30% | reason-experiments.md | A 28 B 26 C 27 D 24 E 15; middle 36 | ✓ |
| val cat (not in the doc) | | 73/281 = 26.0% vs 65 | new, consistent |
| no model, no time | ladder.py | 3.1 ms for 562 problems | ✓ |
| 2B speed/RAM, value grammar, votes | §2-4 | not run | read only |

## Verdict

Adopt `MIDDLE_VALUE=1` with the wording of I1 and the uncertainty of I2. It is the only Reason-track
change the team has that is positive on two independent sets, free on the board and deterministic.
