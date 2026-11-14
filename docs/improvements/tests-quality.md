# Tests and code quality: what the 168 tests cover, what they miss, and how to run them on the board and in CI

Worktree `team/improvements-d18364` = `origin/main` 5cc2ded, 14 Nov 2026. Laptop Python 3.14.7, board Python 3.13.
Builds on the reviewer's file (`origin/team/review-22fa88:docs/reviews/review-main-2026-11-14.md`): I2 (leak filter
spellings), I7/M7 (mastery after rung 3-4), I14 (`sample-1` fixture), M1 ("125 tests"), M2 (60 s on the solver path),
M3 (prefetch join), M9 (stdlib guard reads imports only). Cited as "reviewer Xn" below; nothing there is re-reported
without new evidence.

## Summary

1. The suite is fast (0.9 s), green on 3.14 with `-W error`, order-independent (5 shuffled runs, each module alone) and
   location-independent (run from `/tmp`); a board-like checkout without `data/` gives `OK (skipped=6)`.
2. **Running the tests writes test students (`Mar`, `Pau`, `student-test`, `test-webapp`) into the live demo database
   `data/students.db`** (answers 20 -> 21 after one run): the teacher page of the demo shows them. One line fixes it.
3. Exactly one test needs the shared embedding server (`test_val_id_is_embedded_once_and_cached`); it is gated on data
   only, so on the board with data pushed and `math-embed` down it fails instead of skipping.
4. Zero tests for `copilot/pipeline.py`, `copilot/llm.py`, `predict.py`, `eval.py`, `hal/web.py`, the 60 s budget, or
   the leak filter against real option values: 35 of 339 val problems with options have a correct value (`12cm`,
   `3kg`, `2h`: digits glued to a unit) that the filter does not catch when written plainly.
5. `test_interfaces.py` checks shapes, not signatures (all 15 listed signatures match today, verified with `inspect`);
   the stdlib guard scans `board/` and `explorer/` too, but cannot see 3.14-only stdlib names or 3.14-only syntax.

## What I ran (VERIFIED BY RUNNING unless marked READ)

| Command (from the worktree root) | Outcome |
| --- | --- |
| `python3 -m unittest discover tests` twice, timed | 168 tests, `OK (skipped=1)`, 1.07 s then 0.95 s; same skip both times |
| `python3 -W error -m unittest discover tests` | `OK (skipped=1)`: no deprecation warnings on 3.14 |
| `python3 tests/test_stdlib_only.py` | 2 tests OK in 0.036 s |
| `cd /tmp && python3 -m unittest discover -s <wt>/tests -t <wt>` | `OK (skipped=1)`: no cwd assumption (paths come from `__file__`) |
| `python3 -m unittest discover tests --durations 12` | slowest 0.124 s (`test_review_rate_is_about_one_in_five`); top 5 are all `TrainerDbTest` (0.07-0.12 s); the guard 0.035 s |
| 5 shuffled orders (own runner, seeds 1-5) and each `tests.test_*` module alone | all `OK`: no order dependence between modules or tests |
| `rsync` of the tree to the scratchpad **without** `data/` symlinks (only `README.md` and `sample_problems.jsonl`), then the suite | `OK (skipped=6)`: `test_relay` (macOS) + 5 `IndexSearchTest` ("data/index.db not built"). The symlinks were never touched |
| Suite with `socket.create_connection` blocked for ports 8081/8082/8083 (own wrapper), with data | `FAILED (errors=1)`: `test_retrieval.IndexSearchTest.test_val_id_is_embedded_once_and_cached` -> `URLError ... 127.0.0.1:8082` |
| Same block on the no-data copy | `OK (skipped=6)`: without `index.db` nothing touches the network |
| `sqlite3 data/students.db` before/after one suite run | answers 20 -> 21; students `Mar`, `Pau`, `student-test`, `test-webapp` present; `data/rung0.json` mtime unchanged |
| `STUDENTS_DB=<scratch>/redirect.db python3 -m unittest tests.test_interfaces tests.test_webapp` | OK; the four test students land in `redirect.db` instead (the env var already works) |
| `python3 -X importtime -c "import copilot.webapp"` | 51 ms cumulative on the Mac (hints 35 ms, of which `urllib.request` 20 ms via `copilot.client`); wall 0.049 s. Harmless on the board |
| `dev/start_servers.sh --status` (read only) | both shared servers up (8081, 8082) |
| `predict.py` twice on `data/sample_problems.jsonl`, and twice on the first 30 English val rows | identical `(id, answer, status)` both times; **all 30 val rows answered `D` in 0.0 s**: none hit a solver family, so the LLM path was not exercised |
| Leak filter sweep over `data/val.jsonl` (cat+eng, ids only printed) | 562 rows, 339 with options and label; the plain correct value in a hint escapes `leak_reason` for **35** (all shapes `<digits><unit>` without a space: cm 30, km 3, kg 3, h 2, s 2); naming some *wrong* option plainly is rejected for 34 problems (strictness by design) |
| `ast.parse(src, feature_version=(3, 13))` over the 33 board files | all parse; the check does reject t-strings and `except A, B:` (3.14-only) |
| `python3 -c "import sys; ..."` | `annotationlib`, `compression`, `_zstd` are in 3.14's `sys.stdlib_module_names`: the guard on 3.14 would accept imports the board's 3.13 cannot do |
| `inspect.signature` of the 15 functions listed in INTERFACES.md vs the code | parameter names identical for all 15 (two regex misreads on multi-line signatures, not real differences) |
| grep of public `def`s in `copilot/`, `board/relay.py` against `tests/*.py` | 77 functions never named by a test (list in P7/P9); `pipeline`, `llm`, `embed`, `client`, `rag.build`, `hal/web` have none |
| READ: `tests/*.py` (all 13), `copilot/*.py`, `hal/*.py`, `solvers/__init__.py`, `board/relay.py`, `board/05_smoke_test.sh`, `common.sh`, `python/main.py`, `predict.py`, `INTERFACES.md`, `docs/deploy-board.md` 3, `.gitignore`, reviewer's file | no `.github/` exists (no CI). `python3 -c "import coverage"` -> not installed, so coverage is by grep |

Fragility catalogue (answers to the brief's checklist):

- **Network / shared servers**: 1 test (`test_val_id_is_embedded_once_and_cached`, `tests/test_retrieval.py:73-84`), gated on `HAS_INDEX and HAS_VAL`, not on the server. Everything else mocks `_call`/`neighbors` or uses the sample fallback.
- **Data symlinks**: 5 tests gated with `skipUnless(HAS_INDEX)` (clean skips); `test_interfaces.TrainerTest`, `LedTest` and `test_webapp.StartResetTest` run against whichever bank exists (train+val when linked, samples otherwise) and against the **default DB** (finding 2).
- **Wall-clock**: `test_relay` uses `ready.wait(2)` and `timeout=3`; `test_webapp` arms a 3 s `threading.Timer` and cancels it in `tearDown`/inline (`tests/test_webapp.py:81,109-112`). No `time.sleep`, no `time.time` asserts.
- **Dict order / locale / hard-coded ports**: none found (ports are 0; files opened with `encoding="utf-8"` in tests; `shuffle` runs green).
- **3.14 vs 3.13**: tests use nothing 3.14-only; `--durations` (used above) exists since 3.12. The *guard* is the 3.14/3.13 risk (P5).
- **macOS vs Linux**: the single skip is `test_relay.test_forwards_http_to_the_target` (`tests/test_relay.py:31-33`): it needs a second loopback address (`127.0.0.2`) to relay the same port, which Linux has and macOS does not. On the board it runs.
- **Global module state**: `hints._problems`/`_state`, `trainer._settings`, `retrieval._QUERY_CACHE` are module globals mutated by tests (`register_problem("bi-1")`, `configure()`); shuffled runs stayed green, so the resets in `setUp`/`tearDown` are sufficient today.

## Proposals

### P1. Sandbox the student database when the tests run
- **Where**: `tests/__init__.py` (empty today); `copilot/trainer.py:173-174` (`db_path()` reads `STUDENTS_DB` at call time); callers `tests/test_interfaces.py:33-47,81`, `tests/test_webapp.py:27-80`.
- **Problem / opportunity**: `trainer.next_problem("student-test")`, `record_answer(...)` and `webapp.Session().start("Mar", "2")` hit the real trainer with the default `data/students.db`. Verified: one suite run adds an answer row (20 -> 21) and the students `Mar`, `Pau`, `student-test`, `test-webapp` are in the demo DB. `docs/deploy-board.md:47` tells the team to run the suite on the board right before the demo, so the teacher page (`/teacher`) will list four fake pupils, and `test_interfaces` itself is not reproducible (the same `student-test` accumulates history run after run; `test_record_answer_shape` only passes because the sample bank stays gradable).
- **Proposal**: in `tests/__init__.py` (imported by `discover` before any test module): `os.environ.setdefault("STUDENTS_DB", os.path.join(tempfile.mkdtemp(prefix="m3kang-tests-"), "students.db"))`. Optionally also `webapp.RUNG0_FILE`-style redirect (not needed today: `Session()` in tests has no stats path; `data/rung0.json` mtime unchanged). Add an assertion test: `tests/test_env.py::test_tests_never_touch_the_demo_db` comparing `trainer.db_path()` with `trainer.DEFAULT_DB`.
- **Impact (jury or student)**: high: a clean teacher view in the 3-minute demo, and reproducible contract tests.
- **Effort**: S.
- **Risk**: none; no INTERFACES change; safe before the demo (verified with the env var: both modules pass and write to the redirected file). Also delete the four test pupils from the board's DB once (`trainer.reset_student`) or recreate it.
- **How to measure**: `sqlite3 data/students.db "select count(*) from answers"` identical before and after `python3 -m unittest discover tests`.
- **Verified**: ran.

### P2. Gate the one network test on the server, or mock the embedding
- **Where**: `tests/test_retrieval.py:73-84`; `copilot/retrieval.py:111-124` (`query_vector` calls `embed`).
- **Problem / opportunity**: with data linked and port 8082 blocked the suite fails with `URLError` (verified). On the board, `deploy-board.md:31` pushes `val.jsonl` and `index.db`, so this test runs there and fails whenever `math-embed` is restarting, which is exactly when someone runs the tests to see what is wrong. The reviewer's figure "149 run, 1 skipped" and the brief's "168 OK" both had the servers up.
- **Proposal**: the test checks caching, not vectors. Patch `retrieval.embed` with `mock.patch.object(retrieval, "embed", return_value=[[1.0] + [0.0] * 383])` and keep the assertions (`_QUERY_CACHE[...][2] == 1`, never itself). Keep one *optional* real-server variant behind `@unittest.skipUnless(tests._env.server_up(EMBED_PORT), "embedding server down")` with a 0.3 s `socket.create_connection` probe in a new `tests/_env.py` (also exporting `HAS_DATA`).
- **Impact**: medium: the suite becomes a reliable board health check.
- **Effort**: S.
- **Risk**: none; safe before the demo.
- **How to measure**: the blocked-socket run (`scratchpad/netblock.py` pattern) gives `OK` with data linked.
- **Verified**: ran (the failure); the mock variant is read only.

### P3. `board/07_run_tests.sh` and honest numbers in the docs (no `--board` flag needed)
- **Where**: new `board/07_run_tests.sh`; `docs/deploy-board.md:45-48`; `docs/results-A.md:74` and `docs/README-final-draft.md:111` ("all 125 tests pass", reviewer M1); `docs/project-hub-draft.md:112`.
- **Problem / opportunity**: the board run today is one bare command whose output nobody records. The brief asked for a `--board` marker or `BOARD_TESTS=1`; after P1 and P2 it is unnecessary: the suite already self-gates on data (`skipUnless(HAS_INDEX)`) and would self-gate on servers, and the board-like no-data run is `OK (skipped=6)`, with data and servers `OK (skipped=0)` (Linux runs `test_relay`). Note the expected skip counts: Mac with data 1, Linux with data and servers 0, no data 5 (+1 on macOS).
- **Proposal**: `board/07_run_tests.sh` = `source common.sh; cd "$REPO_DIR"; step "Unit tests"; python3 -m unittest discover tests -v 2> >(tee results/tests-$(date +%F).log >&2) | tail -3; grep -c skipped results/tests-*.log` and `ok`/`die` on the exit code, then `python3 -W error -m unittest discover tests` once (3.13 deprecations differ from 3.14). Document in `deploy-board.md` 3: "expect `Ran 168`, `OK`, skipped 0 (data + servers) or 5 (no data)". Replace the "125 tests" sentences with the real count and the date, and say that the count is the suite's, not the board's (the board skips when data is absent).
- **Impact**: medium: jury reads the README; "125 tests pass on the board" is wrong today (168) and will be wrong again tomorrow, so write "`python3 -m unittest discover tests` prints OK (168 tests on 14 Nov)".
- **Effort**: S.
- **Risk**: none; safe before the demo.
- **How to measure**: the log file in `results/` from the board with `Ran 168` and `OK`.
- **Verified**: the skip behaviour ran (no-data copy, from `/tmp`); the script is a proposal.

### P4. Minimal CI: GitHub Actions on Ubuntu, Python 3.13 and 3.14, no data, no servers
- **Where**: new `.github/workflows/tests.yml` (no `.github/` exists; verified).
- **Problem / opportunity**: the repository will be public with "tests pass" in the README and no badge or run behind it (reviewer I11 is about evidence; this is the cheapest evidence). Nothing in the suite needs data or servers to be green: the no-data copy gave `OK (skipped=6)` (5 data skips; `test_relay` runs on Linux). The board's Python is 3.13, the laptops run 3.14: CI on both catches 3.14-only stdlib names and syntax that the guard cannot (P5).
- **Proposal**: exact file:

  ```yaml
  name: tests
  on: [push, pull_request]
  jobs:
    unit:
      runs-on: ubuntu-latest
      strategy:
        fail-fast: false
        matrix:
          python: ["3.13", "3.14"]
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: ${{ matrix.python }}
        - name: Stdlib guard (the board has no pip)
          run: python -m unittest tests.test_stdlib_only -v
        - name: Unit tests, warnings are errors, no data and no model servers
          run: python -W error -m unittest discover tests -v 2>&1 | tee tests.log
        - name: Expect exactly the data skips (5), no network, no demo database
          run: |
            test "$(grep -c 'skipped' tests.log)" -eq 5
            test ! -e data/students.db
  ```

  With P1 the last line holds (the DB goes to a temp dir); without P1 drop it. With P2 the count stays 5 when the index is absent. Add the badge line to `docs/README-final-draft.md` next to the test command.
- **Impact**: medium: public proof the suite is green on the board's Python version, for free.
- **Effort**: S.
- **Risk**: none to the board or demo; the workflow only runs on GitHub.
- **How to measure**: a green run on both matrix entries after the first push; `Ran 168`, `skipped=5` on each.
- **Verified**: the no-data behaviour and the `-W error` run ran locally (3.14); 3.13 was not available on this Mac (`uv python list` shows only 3.14.7), which is the point of the matrix.

### P5. Close the stdlib guard's gaps: dynamic imports, 3.14-only stdlib names, 3.14-only syntax
- **Where**: `tests/test_stdlib_only.py:29-37` (`imported_modules`), `:41-53`; `copilot/hal/web.py:36-37` (the only `importlib.import_module`, inside the listed exception).
- **Problem / opportunity**: answers to the brief's questions, verified by reading `board_files()` and running probes: (a) it **does** scan `board/relay.py`, `explorer/server.py`, `build_index.py`, `calibrate_bias.py` (everything outside `laptop/ dev/ tests/`), `python/main.py` with `arduino` + `numpy` allowed; (b) `ast.walk` sees imports inside functions and inside `try/except ImportError` (`hal/led.py:46` is caught and whitelisted); (c) it does **not** see `importlib.import_module("...")` or `__import__` (reviewer M9; today only `hal/web.py`, which is listed anyway); (d) `allowed = set(sys.stdlib_module_names)` is the **running** interpreter's list: on 3.14 it contains `annotationlib`, `compression`, `_zstd` (verified), none of which exist on the board's 3.13, so a future `import annotationlib` would pass the guard on every laptop and crash on the board; (e) 3.14-only syntax (t-strings, `except A, B:` without parentheses) is invisible to an import scan. The 33 board files are clean today under `ast.parse(..., feature_version=(3, 13))`.
- **Proposal**: three additions to the same test file: (1) in `imported_modules`, also yield the first string argument of `ast.Call` nodes whose func is `importlib.import_module` or `__import__`; (2) `NOT_ON_THE_BOARD = {"annotationlib", "compression", "_zstd", "string.templatelib"}` subtracted from `allowed` with a comment "Python 3.13 on the UNO Q"; (3) a new test `test_board_code_parses_with_the_board_grammar` that runs `ast.parse(src, path, feature_version=(3, 13))` over `board_files()` and lists offenders. Optional (4): flag text-mode `open()` without `encoding=` in board files (`copilot/config.py:10`, `predict.py:37`, `eval.py:53`, `build_index.py:27`, `explorer/server.py:85`); Linux coerces the C locale to UTF-8 so it works today, but `val.jsonl` is Catalan and one `LC_ALL=C PYTHONUTF8=0` would break the official run; cheaper to add `encoding="utf-8"` to those five lines than to test for it.
- **Impact**: medium: the stdlib rule is a hard constraint and the guard is its only enforcement.
- **Effort**: S (1-3), M with (4).
- **Risk**: none; no INTERFACES change; safe before the demo (pure test additions; the five `encoding=` edits are mechanical).
- **How to measure**: `python3 tests/test_stdlib_only.py` -> 4 tests OK; temporarily add `import annotationlib` to a copy and watch it fail.
- **Verified**: ran (the probes); the test code is a proposal.

### P6. Make `test_interfaces.py` check the signatures written in INTERFACES.md, not only that functions exist
- **Where**: `tests/test_interfaces.py` (90 lines, 9 tests); `INTERFACES.md:119-191,207-208`.
- **Problem / opportunity**: the file checks return shapes (`set(r) == {...}`, 8 topics, 8x13 frame) and calls each function once; it never compares parameter names, defaults or counts with the contract. `neighbors` happens to be called with keywords (so a rename would fail), `record_answer` positionally (a rename would pass). Verified with `inspect.signature`: all 15 listed functions match today, so this is drift insurance, not a bug report. The Hint result shape per rung (`INTERFACES.md:106-115`) is only asserted for rung 1's `problem` and the `kind` set.
- **Proposal**: add `SignatureTest` that parses the ```python blocks of `INTERFACES.md` with a small regex (`^(\w+)\((.*?)\)\s*->`, joining continuation lines ending in a comma), maps the name to the module by the preceding `### \`copilot/...\`` heading, and asserts `list(inspect.signature(fn).parameters) == doc_params` and the defaults (`lang="cat"`, `k=1`, `level=None`). Add `test_hint_result_keys_per_rung` asserting the exact key sets for rungs 0-4 from the contract (rung 1 adds `problem`, `easier`; 2 adds `manipulative`; 4 adds `label`, `value`, `trace`; 3 `llm` adds `llm_lang`), so an accidental new key (for example `error` from `webapp._compute_hint`) is noticed.
- **Impact**: medium: four branches merge into `copilot/`; a silent signature change is what breaks the demo page at the worst time.
- **Effort**: M.
- **Risk**: none; it only reads INTERFACES.md (and makes the file executable documentation). Safe before the demo.
- **How to measure**: rename a parameter locally and watch one test fail with the contract line quoted.
- **Verified**: the `inspect` comparison ran; the test is a proposal.

### P7. Tests for the 60 s budget and for `pipeline.solve` (none exist)
- **Where**: new `tests/test_pipeline.py`; `copilot/pipeline.py:29-100` (untested module), `:74-78` (`remaining` only on the letter path, reviewer M2), `copilot/solvers/consecutive.py:26-27` (`extract_json` with the default `timeout=60`), `copilot/hints.py:421-426` (`_prefetched` joins up to `LLM_TIMEOUT` = 60 s, reviewer M3), `copilot/board_clock.py:103` (`sleep_to_board_time`, untested).
- **Problem / opportunity**: `grep -l pipeline tests/` finds nothing: the function the official run calls has zero tests, and the 60 s rule (jury criterion) is asserted nowhere; `board/05_smoke_test.sh:33` checks `worst < 60` only on the five samples, which answer in 0.0 s. The `except (socket.timeout, TimeoutError)` and `URLError` branches (`pipeline.py:91-97`) are unexecuted code paths before the official run.
- **Proposal** (all with `mock.patch.object`, no network): (a) `letter_scores` raising `socket.timeout` with `USE_LETTER_MODEL` patched True -> `status == "timeout"`, `answer == FALLBACK`, `seconds` present; (b) `letter_scores` raising `URLError(ConnectionRefusedError())` -> `status.startswith("error:")`; (c) `solvers.solve_with_timings` returning `(None, [{"prompt_n": 700, "predicted_n": 0}])` -> `board_seconds > 60` and the test *documents* that `status` is still `"ok"` (M2) so the fix flips the assertion; (d) assert `extract_json` receives `timeout <= TIME_LIMIT - MARGIN` once M2 is implemented (the test is the spec); (e) `hints._prefetched` with a `threading.Thread` target that sleeps 2 s and `timeout=0.1` returns `None` in under 0.5 s, and `get_hint` then falls back to a strategy card: this needs the small change from M3 (`_prefetched(state, timeout=remaining)`), so write the test red first; (f) `Clock` already tested; add `sleep_to_board_time` with a patched `time.sleep`.
- **Impact**: high: "60 s per step" is a listed criterion, and the fallback path is the one that runs when the board is slow.
- **Effort**: M.
- **Risk**: tests only touch mocks; the M2/M3 fixes they drive change `pipeline.py` and `hints.py`, not INTERFACES. Write the tests before the demo; land the `hints.py` change only with a full ladder rehearsal (prefetch is on in the demo).
- **How to measure**: `python3 -m unittest tests.test_pipeline -v` 6 tests; the `-X importtime` cost of importing `pipeline` in tests is 20 ms (`urllib.request`), fine.
- **Verified**: read only (the gap was verified by grep and by reading `pipeline.py`).

### P8. A data-gated leak-filter sweep over every real option value, and the `12cm` fix it finds
- **Where**: `copilot/leak_filter.py:122-129` (`_core` strips units from the *option*; `_contains_token` requires a non-word character after the number, so `12cm` in the hint never matches `12`), `:104-108`; new `tests/test_leak_filter_val.py`; `tests/test_leak_filter.py` (14 tests, hand-written only).
- **Problem / opportunity**: the reviewer (I2) found missing *word* spellings with 34 hand-written hints; nobody has run the filter against the real option values. I did: of 339 val problems (cat+eng) with options and a label, the plain correct value written in a hint ("Pensa en <value> i continua.") escapes `leak_reason` for **35 (10.3%)**, all of one shape: digits glued to a unit (`cm` 30, `km` 3, `kg` 3, `h` 2, `s` 2; e.g. ids `lvl-1_2023_16`, `lvl-2_2016_22`, `lvl-4_2007_10`). Minimal repro: `leak_reason("Pensa en 12cm i continua.", "C", {"C": "12cm"})` -> `None`, while `"12 cm"` -> `value:12 cm`. The LLM grammar forbids digits, but the filter also guards the solver traces (`hints.py:273`), where digits with units do appear. Also measured: for 34 problems a hint naming some *wrong* option plainly is rejected (shapes like `9 9`, `9-9-9-9-9`, `9:9`: the correct value shares a digit token), the documented strictness; each costs one retry inside `HINT_RETRY_BUDGET`.
- **Proposal**: (1) in `leak_reason`, normalise the hint as the option is normalised: `folded = re.sub(rf"(?<=\d)({_UNITS})\b", r" \1", folded)` before the token checks (or strip the units from the hint with `_core`); (2) add the six shapes as cases in `tests/test_leak_filter.py` (`12cm`, `3kg`, `2h`, `1,5km`, `12cm 3mm`-like, `12cm.`); (3) new `tests/test_leak_filter_val.py` with `@unittest.skipUnless(HAS_DATA)`: for every val+train row with options, assert the plain correct value in a Catalan and an English carrier sentence is caught, printing **ids only** on failure; record the false-rejection count as a number in the message, not as an assertion. Builds on reviewer I2 (different class: units, not words).
- **Impact**: high: "guide without revealing" is the chosen track; this is the only quantitative check of the filter on the real data, and it found a 10% hole in two minutes.
- **Effort**: M.
- **Risk**: the fix only adds rejections (safer), no INTERFACES change; run the 14 existing tests plus the sweep before merging. Safe before the demo if the demo set's rung-3 traces are rehearsed once after it (a trace step with "12 cm" that was shown before might now be skipped).
- **How to measure**: the sweep's miss count 35 -> 0 on val and on train; `python3 -m unittest tests.test_leak_filter tests.test_leak_filter_val`.
- **Verified**: ran (the sweep and the minimal repro); the fix is read only.

### P9. Error paths of the web app and the sim HTTP server have no tests
- **Where**: `copilot/webapp.py:257-282` (`answer_letter` errors), `:310-330` (`hint`/`solution` while busy), `:332-353` (`_compute_hint` exception fallback), `:355-394` (`image`, `led_path`, `led_frame`, `teacher` without `teacher_report`, `estimate`), `:432-449` (`routes`); `copilot/hal/web.py:44-100` (`_compile`, `route` 500 handler, `static` traversal guard).
- **Problem / opportunity**: grep of `tests/test_webapp.py`: `solution`, `image`, `led_path`, `led_frame`, `estimate`, `routes` are never called; `hint()` once (through `self.s.rung = 2`, not the thread); nothing asserts `{"error": "choose A to E"}`, `"already answered"`, `"busy"`, or the `_compute_hint` fallback (`"No he pogut preparar la pista."`). `hal/web.py` has zero tests: the reviewer checked `/../config.env -> 404` by hand with `curl`; `led_path("x")` raises `ValueError` and the page would see a 500 JSON only because `route()` catches it, also untested. The handler class is created inside `_serve_sim`, so it cannot be instantiated by a test.
- **Proposal**: (1) `tests/test_webapp.py`: `ErrorPathTest` with the mocked trainer from `Rung0Test.setUp`: `answer_letter("Z")`, `answer_letter("C")` twice, `hint()` with `busy=True`, `solution()` then `hint()` -> `"busy"`, `_compute_hint(3)` with `hints.get_hint` patched to raise -> one hint appended with `error` and `busy False`, `led_path("1,1;1,2")` -> frame rows, `estimate("100", "10")` -> `board_seconds > 0`, `teacher()` with `del trainer.teacher_report` -> `source == "mastery_map"`. (2) `hal/web.py`: lift the `Handler` into `make_handler(routes, assets_dir)` (10-line move; `_serve_sim` calls it) and add `tests/test_hal_web.py` that starts `ThreadingHTTPServer(("127.0.0.1", 0), make_handler(webapp.routes(session), ASSETS))` in a thread and GETs `/api/state` (200 JSON), `/api/answer/Z` (200 with `error`), `/api/led/path/x` (500 JSON), `/../config.env` and `/%2e%2e/config.env` (404), `/teacher` (200 `text/html; charset=utf-8`), then `shutdown()`. Port 0, loopback, no fixed port.
- **Impact**: medium: these are the paths a presenter hits when a click lands twice during the live demo.
- **Effort**: M.
- **Risk**: (1) none; (2) a mechanical refactor of `hal/web.py` (not in INTERFACES); do it with the test in the same commit and run `RUNTIME=sim python3 python/main.py` once. Safe before the demo.
- **How to measure**: `python3 -m unittest tests.test_webapp tests.test_hal_web -v`: about 15 new tests, suite still under 2 s.
- **Verified**: read only (gaps verified by grep).

### P10. A determinism test for `predict.py` and a note on what it can and cannot prove
- **Where**: new `tests/test_predict.py`; `predict.py:22-50`; `copilot/pipeline.py:19-26` (`BIAS`, `USE_SOLVERS`, `USE_LETTER_MODEL` read at import).
- **Problem / opportunity**: "deterministic" is a rule (`predict.py:11`) with no test. The trainer has two determinism tests (`tests/test_trainer.py:191-199,266-271`); the pipeline has none. Verified by hand: two `predict.py` runs on the samples and on the first 30 English val rows are identical in `(id, answer, status)`, but every val row came back `D` at 0.0 s (none of the 30 is in a solver family), so the LLM path's determinism rests on `temperature 0, seed 42` and the reviewer's note of 3/50 near-ties flipping *between platforms* (`results-A.md:94`), not on a test.
- **Proposal**: `tests/test_predict.py`: run `predict.main()` twice via `subprocess.run([sys.executable, "predict.py", "--input", "data/sample_problems.jsonl", "--output", tmp])` (the sample file is committed, so this runs in CI and on the board without the servers because `LETTER_MODEL=0` and no sample is classified), assert the header, 5 rows, `answer in "ABCDE"`, `status == "ok"`, `float(seconds) < 60`, and byte-identical `(id, answer, status)` columns. Add a second, mocked test of `pipeline.solve` with `letter_scores` patched to return the same `scores` twice and `BIAS` patched -> same letter and `margin` (the bias tie-break is already asserted deterministic in `tests/test_bias.py:50`). State in `docs/results-A.md` that LLM-path determinism is by server settings and was measured, not unit-tested.
- **Impact**: medium: a rule of the official run, cheap to pin.
- **Effort**: S.
- **Risk**: none; safe before the demo.
- **How to measure**: `python3 -m unittest tests.test_predict` (about 0.3 s: two interpreter starts).
- **Verified**: the two-run comparison ran; the test is a proposal.

### P11. Tests that cement behaviour the team has decided to change
- **Where**: `tests/test_solvers.py:68-70` (`test_solve_keeps_the_sample_fixture`), `tests/test_interfaces.py:51-60` (`SolversTest` on `sample-1`), `tests/test_hints.py:79-88,113-121` (rung 3/4 on `sample-1`), all resting on `copilot/solvers/__init__.py:49-50,70-80` (`_SAMPLE_1`, reviewer I14); `tests/test_trainer.py:137-143` (`test_answer_after_rung_three_or_four_never_raises`) asserting `mastery_after <= max(mastery_before, 1)`, i.e. a pupil who answers correctly after seeing the solution ends at mastery 1 = "always fails" (reviewer I7/M7 on the wording).
- **Problem / opportunity**: no test asserts a leak (I checked every `assertIn`/`assertNotIn` on `label`, `value`, option text: rung 4 and the wrong-answer message are the only places the letter appears, both by design, and `test_rung3_walks_the_trace_but_never_its_last_step` asserts the answer value is absent). But four tests pin the `sample-1` back door into board code, so the day I14 is fixed, they go red together with the demo trace. The trainer test pins a semantics the team is still discussing.
- **Proposal**: move the fixture out of board code as a *test family*: in `tests/_fixtures.py` define a module with `KEY = "sample_fixture"`, `matches(text)` true only for the sample-1 text marker, `extract` returning the parameters with empty timings and `compute` returning `(10, trace)`; register it in `setUpModule` of `test_hints.py`, `test_solvers.py`, `test_interfaces.py` via `solvers.register(...)` and unregister in `tearDownModule` (`FAMILIES.pop`). For the demo, add the trace to `data_curated/` as the reviewer suggests, so `sample-1` keeps its trace on the board without the `if problem.get("id") == "sample-1"` line. For the trainer test, rename it to say what it asserts (`..._caps_mastery_at_one`) and add the INTERFACES line number in the docstring, so the decision (I7) is explicit.
- **Impact**: low for the jury, medium for the team: removes a reviewer's "back door" without losing the ladder tests.
- **Effort**: M.
- **Risk**: touches `solvers/__init__.py` (a listed INTERFACES module, signature unchanged) and the demo's `sample-1` trace: do it after the demo, or with a full rehearsal of rung 3 and 4 on `sample-1`.
- **How to measure**: `grep -n sample-1 copilot/` returns only `topics.py`; the 168 tests stay green.
- **Verified**: read only.

## Coverage gaps by module (grep of public `def`s against `tests/`, coverage.py not installed)

- **No test at all**: `copilot/pipeline.py` (`solve`), `copilot/llm.py` (`format_problem`, `build_messages`, `letter_scores`, `extract_json`, `json_grammar`), `copilot/embed.py`, `copilot/client.py`, `copilot/rag.py` (`build`, `Index.search`), `copilot/hal/web.py` (all), `predict.py`, `eval.py`, `build_index.py`, `calibrate_bias.py`, `board/calibrate_speed.py`, `python/main.py`, `explorer/server.py`.
- **Partly**: `retrieval` (`neighbors_for_vector`, `_english_text` only via the one network test), `hints` (`warm`, `_prefetch_full`, `_prefetched`, `_image_path` only through `sample-3`), `webapp` (P9 list), `hal/led._draw_board`, `board_clock.on_board`/`sleep_to_board_time`, `bias.corrected_scores`, `simulate` (only `synthetic_problems`/`make_synthetic_neighbors` as fixtures; `metrics`, `run_student`, `setup_bank`, `make_index_neighbors` untested, reviewer I10 says the simulator is circular anyway), `relay.interface_address` (Linux `ioctl`, cannot run on macOS; runs on the board via P3).
- Branch-level gaps verified by reading: `pipeline.py:91-97` (timeout/URLError), `webapp.py:209-211,229-230` (older-trainer fallbacks), `hints.py:454-456` is tested (`test_server_down_is_not_ok_and_does_not_raise`), `hints.py:276` (a trace step that leaks is skipped) untested, `trainer._connect` migration tested (`test_old_database_without_start_level_is_migrated`).

## Summary table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | Sandbox the student database when the tests run | high | S | yes |
| P2 | Gate the one network test on the server, or mock the embedding | medium | S | yes |
| P3 | `board/07_run_tests.sh` and honest test numbers in the docs | medium | S | yes |
| P4 | Minimal CI on Ubuntu, Python 3.13 and 3.14, no data | medium | S | yes |
| P5 | Close the stdlib guard's gaps (dynamic imports, 3.14 names, 3.14 syntax) | medium | S | yes |
| P6 | `test_interfaces.py` checks the INTERFACES.md signatures | medium | M | yes |
| P7 | Tests for the 60 s budget and `pipeline.solve` | high | M | tests yes; the M3 fix with a rehearsal |
| P8 | Leak-filter sweep over real option values; the `12cm` fix | high | M | yes, with one rung-3 rehearsal |
| P9 | Error paths of the web app and the sim HTTP server | medium | M | yes |
| P10 | Determinism test for `predict.py` | medium | S | yes |
| P11 | Un-cement the `sample-1` fixture and the mastery-1 assertion | low/medium | M | no (after the demo) |

## Discarded

- **A `--board` flag or `BOARD_TESTS=1` to skip data/server tests**: unnecessary. The data tests already skip on `HAS_INDEX`; the only server dependency is one test (P2). Verified: a board-like checkout without data is `OK (skipped=6)` with no flag. A flag would hide failures the board should show.
- **Installing `coverage` (or `pytest`) on the board or in the repo**: the board has no pip (hard constraint) and the tests must stay `unittest`-only so `python3 -m unittest discover tests` is the one command everywhere; coverage can run in CI later with `pip install coverage` in the workflow, not in the tree.
- **A test that runs `predict.py` on `data/val.jsonl` twice to prove LLM-path determinism**: the 57 classified problems cost up to 42 s each on the board (reviewer M2) and need the shared servers; two passes are 80 minutes of model time. Keep it as a measured number in `results-A.md` (P10 says so), not a test.
- **Hiding the `data/` symlinks in the worktree to test the no-data path**: not needed; a copy of the tree without `data/` in the scratchpad reproduces the board exactly and cannot disturb the other sessions working in this worktree.
