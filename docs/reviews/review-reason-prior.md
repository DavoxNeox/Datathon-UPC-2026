# Review of `team/reason-prior-fa7b33` (25cd70e; merged into main at 8387bcb with `OPTION_PRIOR=0`)

Reason-track protocol: reproduce the numbers on the 281 validation problems with the branch's own
commands, check that the decision was taken on train and validation was looked at once, redo
the bootstrap, confirm the 60 s limit by `board_clock`, confirm one row per id, and check the
committed table for problem data. Nothing changed by me.

**Executed**: the branch's 297 tests (OK, 1 skipped); `OPTION_PRIOR=1 python3 eval.py --limit 0
--languages eng` and the same with `OPTION_PRIOR=0`; `predict.py` on the 562 validation rows
on main and on the branch with the flag off; the policy recomputed in-process from the committed
`data_curated/option_prior.json` on validation and on the 1,466 training problems; an independent
paired bootstrap (1,000 resamples, seed 42); `laptop/learn_prior.py` with its default strata,
with the documented twelve-stratification list and with `--cv 5`; a scan of the json for ids and
text; the time of `prior.choose` over 562 problems.

## Executive summary

1. **Every figure reproduces.** Validation 80/281 = 28.5% with the prior against 77 without, by
   `eval.py` and in-process; train 425/1466 against 405; the prior fires on 35 validation problems
   (words → E on 24, 6 right against 5; level 2 → second smallest on 11, 3 right against 1), 9 right
   in all against 6 for the current policy; paired bootstrap of the gain, my own code, seed 42:
   mean +2.93, 95% [-4, +11], 27.4% of resamples at or under zero, identical to the json.
2. **Learned on train, looked at validation once.** The json says `learned_on: train.jsonl, eng,
   1466`; the twelve stratifications and the `MIN_GAIN = 10` threshold are constants of the code;
   regenerating the table with the documented strata list gives the same five chosen rules and the
   same 425, so nothing in the table depends on validation. The 5-fold cross-validation inside
   train (seeds 42, 43, 44) loses out of fold for every stratification (-0.7 to -6.0 per
   stratification, **-9.7 for the combined policy**), which is the honest reason the flag is off.
3. **Off means off.** With `OPTION_PRIOR=0` the 562 `predict.py` answers are identical to main's,
   and `eval.py` gives 77/281, the policy reviewed before. The hook sits before the middle-value
   rule and is guarded by the flag; `OPTION_PRIOR` is a key of `config.env`, so the environment
   override works.
4. **No cost, no data.** `prior.choose` takes 5 ms for 562 problems, no model, no RAM; the json
   holds counts, rule names and stratum keys (no `lvl-` id, no statement, longest strings are the
   description and keys like `level=5|picture=picture|kind=noisy_numeric`).
5. **The five "learned" rules sit exactly on the threshold.** All five pooled strata that pass do
   so with a gain of exactly +10 on train; at `--min-gain 11` nothing is learned, at 9 more noise
   would be. Together with the cross-validation, this says the result is the maximum of eleven
   rules over many small groups, as the write-up concludes. The decision to leave it off is right,
   and the write-up says so plainly.

## Findings

**N1 (MINOR). The default command does not regenerate the committed table.** `python3
laptop/learn_prior.py` (default `--strata`, the main stratification only) learns nothing and
**overwrites** `data_curated/option_prior.json` with a 5-line table; the committed file comes from
the twelve-stratification list quoted in `docs/reason-experiments.md`. Anyone who runs the
documented one-liner from the script's docstring loses the measured table. *Fix:* make the
committed list the default `--strata`, or refuse to overwrite a json whose `stratifications` differ
unless `--force`; record the exact command in the json's `description`.

**N2 (MINOR). With the flag on, a malformed `options` crashes the run.** `prior.lenient_options`
calls `options.get(letter)` and `prior.features` reads `options.values()`: a list or a string
`options` raises, as in review-main-c2de6d1-reason R1 for `ladder`. Moot while the flag is off;
the per-problem guard proposed there covers it.

**N3 (MINOR). Validation strata are tiny.** The two fired rules act on 24 and 11 validation
problems; the "+3" is one or two problems per rule. The write-up already treats it as noise;
the one-line summary in `reason-experiments.md`'s table ("+3, interval covers zero") should stay
the headline if anyone quotes it.

## Checks

| Claim | Branch | Reproduced | Status |
| --- | --- | --- | --- |
| val eng, prior on | 80/281 | 80/281 (eval and in-process) | ✓ |
| val eng, prior off | 77/281 | 77/281; predict answers identical to main on 562 | ✓ |
| train, prior on / off | 425 / 405 | 425 / 405 | ✓ |
| fires on val | 35 (24 words → E, 11 level 2 → second smallest) | 35, 9 right vs 6 | ✓ |
| paired bootstrap val | [-4, +11], 27.4% ≤ 0 | mean 2.93, [-4, 11], 0.274 | ✓ |
| paired bootstrap train | [+3, +40], 1.2% ≤ 0 | not rerun (chosen on these problems) | read |
| learned on train only | `learned_on` train 1466 eng | regeneration from train reproduces the rules and 425 | ✓ |
| 5-fold CV inside train | loss | -0.7 to -6.0 per stratification, -9.7 combined | ✓ |
| json content | counts and rule names | 0 ids, no text | ✓ |
| cost | none | 5 ms / 562 problems | ✓ |
| 60 s | unchanged | worst is still the solver extraction (41 s estimate) | ✓ |
| tests | 297 | 297 OK, 1 skipped | ✓ |

## Verdict

A clean negative result, measured the way the protocol asks, correctly left off. Fix the
regeneration footgun before someone runs the docstring's first command.
