# Review of reason-think (main 2d083df, `copilot/think.py`, Experiments 6 and 7)

Protocol for a Reason branch: reproduce the figures on the 281 validation problems with the
branch's own commands; check that the decision was taken on train and validation looked at once;
check the bootstrap; no problem over 60 s on the board by `board_clock`; `predict.py` one row per
id on odd inputs (R1) and the solver skipped with a telling status on long statements (R2); and,
since the stage ships off, the 562 answers with `THINK_LEVELS` empty identical to the ones before.

## What I ran

| command | outcome | kind |
|---|---|---|
| `git diff --stat 3e9e0bf 2d083df`, `git diff -- config.env copilot/pipeline.py copilot/solvers/__init__.py copilot/board_clock.py eval.py` | 24 files; the Reason path gains `think.py` (196 lines), `pipeline.normalise_problem`, `solvers.solve_within` with `SOLVER_BUDGET_SECONDS=42`, `eval.py --ids`; the Teach modules are untouched by the think commits | read + ran |
| worktrees at 2d083df and 3e9e0bf, `python3 -m unittest discover tests` | 332 OK, 1 skipped at 2d083df | ran |
| `python3 predict.py --input data/val.jsonl` (562 rows) at both commits, `THINK_LEVELS` empty | 562 letters identical; 2 statuses and the wall-clock seconds differ (below) | ran |
| `predict.py` on a 16-line file of odd rows (options as list, as one string, nested, numeric, lower-case keys, empty, missing; text null; level as string and null; no id; a JSON array line; a non-JSON line; an unterminated line; a bare string; a 1,300-character statement with the words of the `ages` family), with the server up, with `THINK_LEVELS=all`, and with `LLM_PORT=1` | 16 rows each time, one letter each, exit 0 | ran |
| `dev/stratified_sample.py` (297 ids), then `eval.py --limit 0` seven times: the shipped policy on eng 281, cat 281 and the 297; `THINK_LEVELS=all THINK_TEXT_ONLY=0` with the default `THINK_STYLE=short` on the three sets; `THINK_STYLE=steps` on eng 281; paired bootstrap of my own (10 000 resamples, seed 42) on the per-problem CSVs | table below; 69 minutes of laptop time against the shared server | ran |
| one think request timed on the laptop, with `/tokenize` and the board estimate | 0.78 s on the laptop, 137 prompt + 74 output tokens, 25.2 s on the board by the clock | ran |
| `docs/reason-experiments.md` Experiments 5 to 7 and Decision, `copilot/think.py`, `copilot/pipeline.py:108-146, 160-216`, `copilot/solvers/__init__.py`, `tests/test_think.py`, `tests/test_pipeline_inputs.py`, `predict.py` | read | read only |

## Reproduction

| run (`THINK_LEVELS=all THINK_TEXT_ONLY=0`) | branch report | my run | paired gain, 95 %, P(gain <= 0) | think answered (right / shipped right) | cap hits / requests | board s mean / worst |
|---|---|---|---|---|---|---|
| shipped policy, eng 281 | 77 | 77 | | | | 0.4 / 28.9 |
| shipped policy, cat 281 | 73 | 73 | | | | 0.0 / 0.0 |
| shipped policy, train sample 297 | 75 | 75 | | | | 0.3 / 26.8 |
| short, eng 281 | 79 | **79** | +2 [-11, +15] 0.41 (report +3, 0.35) | 97 (30 / 28) | 67 / 164 | 20.6 / 47.5 |
| short, cat 281 | 80 | **79** | +6 [-6, +18] 0.19 (report +6, 0.20) | 97 (30 / 24) | 74 / 172 | 21.7 / 44.6 |
| short, train 297 | 84 | **85** | +10 [-4, +24] 0.09 (report +9, 0.11) | 107 (37 / 27) | 75 / 182 | 21.3 / 47.6 |
| short, the three pooled, 859 | +18 [-4, +41] 0.063 | **+18 [-4, +40] 0.058** | 74 wins, 56 losses on the 301 answered | | | 21.2 / 47.6 |
| short, levels 2 to 5 pooled, 463 | +18 [+3, +34] 0.013 | +19 [+4, +34] 0.007 | 40 wins, 21 losses | | | |
| steps, eng 281 | 76 | **76** | -1 [-11, +9] 0.62 (report the same) | 63 (18 / 19) | 102 / 164 | 23.9 / 47.6 |
| steps, eng 281, levels 2 to 5 | +8 [+2, +14] 0.004 | +8 [+2, +14] 0.004 | | | | |

Every figure reproduces to within one problem; the two that differ by one (Catalan 79 against
80, train 85 against 84) are the non-determinism the module's docstring admits: the server's
cache restore can change a token of the working between a cold and a warm run, and one letter
with it. The bootstrap is a paired bootstrap of per-problem differences, which is the right
one; P is the bootstrap tail P(gain <= 0), not a test p-value, and the document says so in its
column heads. No problem passed 60 s by the board clock in any run: worst 47.6 s, mean 21 s per
problem with the stage on every level, 10.7 s per problem projected for levels 2 to 5 on the
English set (50 minutes for 281 against 96 on every level and 2 on the shipped policy).

**Was the decision taken on train?** Partly, and the document says which part was not. The
stratum "levels 2 to 5" was picked after looking at eleven strata on the English validation run
with the steps style (Experiment 6, "Caveat, stated plainly"); its validation interval is
therefore optimistic, and the Catalan run with the same style then lost 3 on that stratum. The
short style was designed from the cap-hit counts of the training sample and run once per set;
that part is clean. The pooled 859 leans on the English and Catalan validation sets, which are
the same 281 problems twice, so its effective n is nearer 578 than 859. What ships is
`THINK_LEVELS` empty, so none of this reaches the exam unless the controller turns it on.

## R1: odd inputs

16 rows in, 16 rows out, exit 0, in the three configurations. A list of five options is read as
A to E, lower-case keys are upper-cased, numeric option values become strings, nested values drop
their key, a null text becomes "", a missing id becomes `line-6`, the JSON array and the bare
string get `error:not-an-object`, the broken lines `error:json:JSONDecodeError`, all with the
fallback letter. The 1,300-character `ages` statement gets `ok (solver skipped: budget)` without a
request, in 0.0 s, and the middle value answers. With the server unreachable every row still has
a letter.

## R2: the solver budget and the two budgets on the board

`solve_within` guesses the extraction's cost from the text length at 3.0 characters per token
before any request. On the three validation problems it now skips, the guess is 30 % above the
server's count (398 against 304 tokens, 378 against 289, 444 against 324), so the guessed 46 to
52 board seconds correspond to 38 to 41 s by the token count; since the one extraction measured on
the board ran at 1.33 times its estimate (Experiment 7), the real cost of those three would have
been 51 to 55 s, and skipping them is the right call. The test
`test_the_guess_errs_on_the_long_side` pins the direction. The chain on one problem is bounded:
solver 42 s estimated (about 56 real), think budget `45 - clock.board_seconds()` so it is skipped
after a long extraction, HTTP timeout `57 - elapsed` on both, fallback inside the handler: the
worst real time the branch measured is 47.9 s, with one 57.1 s timeout before the budgets existed.

## The 562 answers with `THINK_LEVELS` empty

All 562 letters are identical between 3e9e0bf and 2d083df. The CSV is not byte-identical: the
`seconds` column is wall time, and two rows (`lvl-1_2020_23`, `lvl-5_2019_29`, both `ages`
candidates of 1,100 to 1,200 characters) now read `ok (solver skipped: budget)` where before
the extraction was sent (0.8 s on the laptop, about 50 s real on the board) and abstained. The
answers do not change because no family solver fires on validation; on the hidden test a long
problem whose solver would have fired now gets the middle value instead, which costs at most the
solvers' 0.3 points on train and saves 50 s each time.

## Findings

### IMPORTANT

**K1. `predict.py` cannot resume, and the stage multiplies the exposure to the board's resets.**
Experiment 7 records two hard resets of the board inside one 8-minute run (18:39 and 18:41 UTC,
"crash" in `last -x`) and a third at a boot earlier that day; it then says "a restart can resume
from the last row written". `predict.py` has no such code: it opens the output with `"w"` and
starts from line 1 (`predict.py:35, 90-100`). With the shipped policy the 281 take 2 minutes;
with `THINK_LEVELS=all` 96 minutes on the board clock, with levels 2 to 5 about 50. A reset
twenty minutes into the exam leaves a partial CSV unless someone is watching. Fix before anyone
turns the stage on: when `--output` exists, read the ids already written and append the rest
(`"a"`), and say so in the runbook; it is a 10-line change and a test.

### MINOR

**K2. The stage answers from an empty statement** (`think.applies`, `think.py:85-100`). A row
with `text: null` and five numeric options (my `r3`) still sends a request; the model wrote a
working on nothing and answered A where the middle value gives C. Cost on the board: a full
think request. Fix: `applies` returns False when the normalised text has fewer than, say, 20
characters.

**K3. The skip status is lost on the fallback path** (`pipeline.py:187`). `result["status"] =
"ok"` on the no-letter-model path overwrites `ok (solver skipped: budget)` set at line 122:
`lvl-4_2008_22` (an `ages` candidate without OCR options) is skipped by the budget but its row
says plain `ok`, 0.0 s. The controller asked for a status that says it; only the rows that end in
the middle value keep it. Fix: drop line 187 (the status is already "ok" by default).

**K4. With the server down, a classified problem gets D instead of the middle value**
(`pipeline.py:206-214`, pre-existing: the same at 3e9e0bf). The solver's extraction raises
`URLError` out of the whole `try`, so the Python stages after it never run: my `r11` (`average`
family) answers D with `error: Connection refused` while the middle value would have given C. The
think stage catches its own errors and falls through; the solver stage should do the same (wrap
`solve_within` like `think_letter`, or move the middle-value rule into the handler). About 5 % of
problems are classified, so this is worth one letter in twenty if the server dies mid-exam.

**K5. Two documentation details.** `config.env:97` still says the output is capped to fit
`EXPERIMENT_BUDGET_SECONDS` where the code uses `THINK_BUDGET_SECONDS` (`think.py:60`,
`pipeline.py:134`). Experiment 6 reports the Catalan short run as 80 and the train sample as 84;
a second run gives 79 and 85, which the module's docstring predicts: say "±1 between runs" next
to those totals so the jury does not read a stable number.

## Opinion: turn `THINK_STYLE=short` on for the exam?

What the numbers support. The expected gain is about +2 points (18 of 859, the same sign on the
three sets: +0.7, +2.1, +3.4 points), the pooled interval [-4, +40] has a 6 % tail below zero,
and the downside is bounded: the stage only ever replaces the shipped letter on the 35 % of
problems where it answers, and there it won 74 and lost 56. On levels 2 to 5 the ratio is 40
wins to 21 losses for half the cost, but that stratum was chosen on validation and its clean
confirmations are the Catalan and train sets only. On accuracy alone, switching it on is a
small positive bet, not a win the jury will see: +2 points on a hidden test of 300 problems is 6
problems, inside the noise of the always-D floor itself.

What decides it is the run, not the statistics. The board hard-reset three times on 14
November, `predict.py` cannot resume (K1), and the stage turns a 2-minute run into 50 or 96
minutes on the board clock (real time 1.0 to 1.1 of that, 1.33 on solver rows). Turned on, the
risk is not "minus two points" but "a partial CSV", and the rules score a missing row as wrong.
The module itself is sound: budgets measured, timeouts bounded at 57 s, fallbacks everywhere, no
problem over 48 s in 1,400 runs.

Recommendation: leave `THINK_LEVELS` empty unless three things are true on exam day: (1)
`predict.py` resumes from its own output; (2) a soak run of the length the exam will take has
completed on the board without a reset; (3) someone can watch the run and restart it. If the
three hold and the organisers' procedure has no total-time cap, use `THINK_LEVELS=2,3,4,5
THINK_TEXT_ONLY=0` (10.7 s per problem, 40 wins to 21 losses pooled) rather than every level
(21 s, 74 to 56): the same expected gain for half the exposure. If the exam is run by the
organisers unattended, off.

Praise: the branch measured its own failure (the first style lost 7 on Catalan), wrote the
caveat about picking a stratum after looking, and every number I re-ran came back within one
problem, including the time per problem.
