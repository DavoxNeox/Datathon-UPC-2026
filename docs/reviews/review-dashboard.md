# Review of the decision dashboard (`assets/dashboard.html`, main 33601f8)

Scope asked by the controller: every figure checked against its source document, no problem text or
ids on the page, representation fit for each figure, rendering at 1280x800 and 390x844 in light and
dark, and the headline's dependence on the Reason outcome.

## What I ran

| command | outcome | kind |
|---|---|---|
| `git worktree add` at 33601f8, `python3 -m unittest discover tests` | 304 tests OK, 1 skipped | ran |
| `SIM_WEB_PORT=7019 STUDENTS_DB=data/rev14.db python3 python/main.py`; `GET /dashboard.html` | 200; page loads only `theme.css` and `style.css`, no other request | ran |
| `grep` for `lvl-`, `http`, `<script src`, `@import`, `url(` in the page | only the SVG namespace string; no problem id, no statement, no external load | ran |
| `python3 -m copilot.simulate --bank data --neighbors retrieval --steps 60` and `--neighbors index` (default 8 students, then 5 random students) | tables below; 0.9 s per run | ran |
| OCR coverage from `data/train.jsonl` + `data/val.jsonl`: rows with a non-empty option | 2202 of 3494 | ran |
| Browser at 1280x800 and 390x844, light and dark, CA and EN, Tab/Enter on the three controls; contrast ratios and overflow measured with page scripts | findings below | ran |
| `docs/results-A.md`, `docs/error-analysis.md`, `docs/README-final-draft.md`, `docs/deploy-board.md`, `docs/improvements/trainer.md`, `docs/improvements/retrieval-topics.md`, `data_curated/hint_quality.json`, `copilot/hints.py:428`, `config.env` | sources for the cross-check | read only |

## Figure by figure

| panel | figure on the page | source | verdict |
|---|---|---|---|
| tiles, policies | 21.7 (61/281), 23.1 (65/281), 20.0 random, 17.8 bias-corrected, 23.1 solvers-else-D, 27.4 middle value, board 23.1 and 26.7 on 562 | results-A.md:14-30, 64, 113, 123 | match |
| confidence | 25.7 / 21.4 / 22.9 / 16.9 | results-A.md:33-34 | match |
| topics | n, model % and always-D % for the eight topics | error-analysis.md:13-20 | match (all 24 cells) |
| topics source | "76% agreement with 50 hand labels" | README-final-draft.md:224 (38/50 shipped; 72% keywords only); the same file calls 76% optimistic | match, optimistic |
| solvers | ages 17/0/0/0, average 15/0/0/0, consecutive 11/3/2/1, digit_count 5/1/1/0; 911 train | results-A.md:53-61 | match |
| decisions "4 fired / 911 train, 0 / 281 val", "Visual topics 21% (n=150)" | sums of the two tables (3+1 fired; 63+6+61+20 = 150, 32/150 = 21.3%) | derived correctly |
| latency 0.12, 10.3 real mean, 38.7 worst, +3.7% | results-A.md:82, 95-96, 115 | match |
| latency 12.6 with prefetch | README-final-draft.md:211, marked *(estimate)* there | match, label missing |
| latency 31.0 no prefetch, "265 -> 50 tokens", "n=24" | nowhere in `docs/`, `config.env`, `copilot/` or the commit history of main | **unsourced** |
| latency "Solver JSON extraction 13.6" | results-A.md:60-61 gives 15.1 mean / 15.9 max (consecutive) and 12.6 (digit_count); README-final-draft.md:177 "12.6 to 15.9 s (estimate)" | **13.6 appears in no source** |
| hints 5/10, 0/10 | hints.py:428 "measured on the samples (laptop, n=10)" | match, but the page says "on val" |
| hints 3/66, 1/66 | README-final-draft.md:197 | match |
| hints 0/3 Catalan, 2/3 English, "judged by a team member" | hint_quality.json: n=3 in total (2 arithmetic + 1 areas), `judge: "D draft (Claude, 2026-11-14) - the team must redo it"` | numbers match, **attribution wrong** |
| RAM 1059 / 75 / 91, total 3669 | deploy-board.md:116-117 (steady state, 2609 MB available) | match |
| RAM "2796 available with everything running" (tile, panel, decision log) | deploy-board.md:129 "after boot"; results-A.md:137 gives 2609 with the app in use, 2758 during the evaluation | match, the best of three |
| trainer rows | `copilot.simulate` (see below) | **4 of 6 rows do not reproduce** |
| retrieval 20/20, 15/20, 43/60, 26/60, 10/60, 2202/3494 | README-final-draft.md:209, 226; OCR count reproduced | match |
| retry budget 30 s, limit 60 s | config.env:43, 102 | match |

### Trainer rows against the simulator

Page: threshold 2 → mastered 2; threshold 5 → 7; improving → same topic 94%, mastered 4;
random 20% "5 runs" → band 0-5, same topic 85%, mastered 1.

| student | page | `--neighbors retrieval` (shipped path) | `--neighbors index` (trainer.md:62) |
|---|---|---|---|
| threshold2 | 2-3, 3 steps, 100%, mastered 2 | 2-3, 3, 100%, **3** | 2-3, 3, 100%, **1** |
| threshold5 | 5-6, 3, 100%, mastered 7 | 5-6, 3, 100%, **3** | 5-6, 3, 100%, **4** |
| always | 7-7, 4, mastered 8 | same | same |
| improving | 6-7, 32, **94%**, mastered 4 | 6-7, 32, **89%**, **5** | 6-7, 32, **89%**, **6** |
| hints_only | 7-7, 4, mastered 0 | same | same |
| random, 5 runs | 0-5, **85%**, mastered 1 | bands 0-1 / 0-0 / 0-0 / 0-1 / 0-1; same 91-95%; mastered 0 in all five | bands 0-1 / 0-1 / 0-6 unsettled / 0-2 unsettled / 0-0; same 89-97%; mastered 0, 0, 1, 0, 1 |

The band, steps and "100%" cells reproduce; the "topics mastered" column and the two percentages
for improving and random match neither run. The conclusions written on the page (settle in 3 steps,
a random student masters at most one topic) hold in every run.

## Findings

### IMPORTANT

**D1. Four latency figures cannot be traced to any document** (`assets/dashboard.html:91-94`,
`:124-130` decision log row "Prefetch the problem into the cache?"). "31.0 s median without
prefetch", "265 -> 50 tokens", "n=24" and "Solver JSON extraction 13.6 s" are in no file of main;
the documented solver extraction times are 12.6 to 15.9 s per family, with 15.1 s mean and 15.9 s
worst for the family that fired. The lede promises "every figure was measured by our team". Why it
matters: a jury member who follows the "Source" line finds nothing, and the rule says an unmeasured
number must not look measured. Fix: either commit the measurement (a short table in
`docs/results-A.md` or the hints report: n, medians, token counts, command) or replace the rows
with the documented ones: "12.6 to 15.9 s (estimate)" for the solver, and drop 31.0 or mark it as
the hints branch's estimate with the command that produced it. Mark 12.6 as *(estimate)* as the
README draft does; the page marks only 10.3 and 38.7 as "real", which is right.

**D2. The trainer table does not reproduce** (`assets/dashboard.html:107-114`). See the table
above: mastered 2 / 7 / 4, improving "94%", random "85%, band 0-5" match neither neighbour mode of
`copilot.simulate`, and the page says nothing about which mode or seed it used. Fix: regenerate the
six rows from `python3 -m copilot.simulate --bank data --neighbors retrieval --steps 60` (the
shipped retrieval), put the command in `src`, and for the random student show the five runs' ranges
as the simulator prints them (bands 0-1, same topic 91-95%, mastered 0) rather than one invented
summary. The conclusion text can stay.

**D3. The hint-quality judgement is attributed to a team member** (`assets/dashboard.html:96`
src, `:127`, `:148` d4, `:173`). `data_curated/hint_quality.json` says the verdicts are a draft
produced by a tool on 14 November and that the team must redo them; n is 3 hints in total, not 3
per language. Why it matters: the Teach half of the grade is judged on honesty of this kind, and the
same file names the tool, which the team rule keeps out of the repository. Fix: until a person
redoes the judgement, label the two rows "draft, to be redone (n=3)" or remove them and keep the
two leak rows; after the redo, quote the person's n per topic. Also rename the `judge` field.

**D4. Editing one number blanks the page** (`assets/dashboard.html:250`). The worst-latency tile
is looked up with `DATA.latency.rows.find(r => r.s === 38.7).s`. Reproduced: setting that row to
40.1 and calling `render()` throws `Cannot read properties of undefined` before any tile or panel
is built, so a fresh load shows an empty page. The controller intends to update the figures if
reason-think wins, and the first edit anyone makes to the latency row will hit this. Fix: give the
row a key (`worst: true`, like `free: true` in the RAM rows) and look it up by key; wrap `render()`
in a try/catch that leaves a visible message.

### MINOR

**D5. Headline tied to the Reason outcome.** The lede (CA `:138`, EN `:163`), decision d1
(`:142`, `:167`), decision-log row 2 (`:124`), tile 3 (`:139`, `:164`) and the policies rows all
say the middle-value prior is the one Reason gain and 26.7% the shipped figure. If reason-think (or
a later branch) wins, all six places change together; keep a note in the file header listing them.
The statement is accurate today: the learned prior is off (review-reason-prior.md) and
`predict.py` ships the middle-value rule.

**D6. "On val" and "after a cold boot" labels stretch the sources.** The two leak counts were
measured on the sample problems on the laptop (hints.py:428), not on val (`:96`). The RAM panel's
source (`:104`) presents the RSS figures and the 2796 MB as one cold-boot measurement; the RSS
numbers come from the steady-state measurement where 2609 MB were available. Quote both: "2609 MB
available with the app in use, 2796 MB right after boot".

**D7. Labels collide or spill at 390 px** (measured, light and dark). Policies chart: the two
reference labels "random 20%" and "always D" overprint each other under the bars. Topics chart: the
legend is cut at the right edge ("always D" truncated). Latency chart: the two longest labels are
cut at the left edge ("model hint, no prefetch", "model, one problem"). RAM chart: the white label
of the LLM segment is longer than the segment (also at 1280 px: "1059 MB" is white on the card and
invisible); the 75 MB and 91 MB segments have no label at all, only a mouse tooltip
(`attachTip`, mousemove only, nothing for keyboard or touch). Fix: shorter labels under 640 px,
stagger the two reference labels, print the three RSS values in the source line.

**D8. Low-contrast graphics and small text.** The "floor" bars use `var(--line)`: 1.3:1 on the
light card, 1.6:1 on the dark card, under the 3:1 of WCAG 1.4.11 (the value is printed next to
them, so nothing is lost). The "open" status pill is 11 px `#c98a00` on the light card at 2.7:1
(text needs 4.5:1); the same pill reads 6.1:1 in dark. The three controls are 27 px (back link) and
36-37 px tall (CA/EN), under the 44 px the team set for the app. Focus rings are visible (3 px,
`--focus`) and Enter on EN switches language, so keyboard use works.

**D9. SVGs carry `role="img"` with no accessible name** (`:228` and the bar helpers). Add
`aria-label` with the panel question, or a `<title>` child; the text nodes inside are read in
order today, which is tolerable but unlabeled.

**D10. Mixed denominators in one bar chart.** The retrieval panel puts n=20, n=60 and n=3494 in
the same bars, the hints panel n=10, n=66 and n=3. The fractions are printed in each label, so a
careful reader is not misled; a table would have carried the n better than bar length, as the
solvers and trainer panels already do.

## Representations

Numbers that stand alone are tiles; comparisons of a policy against floors are bars with the two
floors drawn as reference lines; per-topic model-vs-floor is paired bars; counts with four columns
are tables; the RAM budget is a two-row bar against the 3669 MB axis with the non-additivity written
under it; the decision log is a table with a status pill. Each fits, with the two mixed-n charts of
D10 as the only arguable choice. Nothing is drawn where a number suffices and nothing is a number
where a comparison was needed.

## Verified without findings

No problem text, no M3Kang id, no image, no external request. CA and EN switch completely
(no Catalan left in EN and no `{a}` placeholder after render), the choice persists in
`localStorage`. No horizontal scroll at 390 px; tables wrap inside their container; tiles stack;
dark theme follows `prefers-color-scheme` through the shared `theme.css` and every text colour
measured stays above 7:1 in dark and 5:1 in light except the pill of D8. Teacher view links to it
(`assets/teacher.html:29`) and the back link returns.

Praise: the decision log with evidence, decision and status per question is the clearest page in
the app for a jury, and 20 of the 25 figures I could trace reproduce to the digit.
