# Board and deployment: what a fresh UNO Q, a power cut and the demo day would find

**Summary.** The board kit is sound: every script passes `bash -n`, is idempotent, pins llama.cpp
and both models by commit/revision/SHA256, the units have `Restart=on-failure`, and the relay is
one thread per connection, so a 40 s LLM request never blocks an embedding. What is weak is the
*measurement* side: `calibrate_speed.py --write` would replace `BOARD_EMBED_SECONDS=0.12` with the
per-text figure 0.05 (the committed value was typed by hand), the smoke test's "60 s" check runs on
problems that answer in 0.0 s, no script checks the demo path (relay, data, app page, RAM), the App
Lab app never health-checks the servers (it degrades silently), and the units say nothing about who
the OOM killer takes first. The reviewer's I9 (`SOLVERS=0` ignored) is a one-line `config.env` fix
in this area. No secrets or private hostnames are in git. I could not reach the board; everything
about boot, OOM and the container is reasoned from the scripts and the measurements in `docs/`.

## What I ran

| command | outcome | kind |
| --- | --- | --- |
| `bash -n board/*.sh board/common.sh dev/start_servers.sh` | all 9 files parse | VERIFIED |
| `shellcheck` | not installed on this laptop; not run | - |
| `python3 -m unittest tests.test_relay tests.test_config_hosts -v` | 7 tests, 6 OK, `test_forwards_http_to_the_target` **skipped on macOS** (same-port design needs 127.0.0.2) | VERIFIED |
| `python3 -m unittest discover tests` | 168 OK, 1 skipped, 0.97 s (baseline) | VERIFIED |
| `python3 dev/ram_budget.py` | laptop RSS 1737 + 78 MB, "OK: 525 MB headroom", text still says the App Lab reserve is "NOT measured (Phase 10)" | VERIFIED |
| `dev/start_servers.sh --status` | both shared servers up; nothing stopped or restarted | VERIFIED |
| `python3 board/calibrate_speed.py --rounds 1` (laptop, only to check the script) | runs; prints `BOARD_EMBED_SECONDS=0.003` = wall / 20 texts, i.e. **per text in a batch**, while `config.env` documents 0.12 **per request** | VERIFIED |
| key audit: every `CONFIG.get/[]` key in code vs `config.env` | read in code, absent from `config.env`: `SOLVERS`, `STUDENTS_DB`, `TRAINER_BANK`; in `config.env`, read by no Python and no shell script: `VISION_PORT`; the 17 build keys (`LLM_REPO`, `LLAMA_CPP_REF`, ...) are read by bash/ps1 only, as intended | VERIFIED |
| `python3 -c "import board.relay; relay.resolve_listen('nosuchif0')"` | raises `OSError [Errno 6]` with no message: with `docker0` missing the relay dies with a traceback and systemd restarts it every 5 s | VERIFIED |
| `git grep` for IPs, passwords, tokens, `/Users/`, `/home/` | only the organizers' example IP `192.168.1.131` and the default password `opensource` in the organizers' README; the team's clone URL; `/home/arduino/...` paths. Nothing to remove | VERIFIED |
| `git show origin/team/review-22fa88:docs/reviews/review-main-2026-11-14.md` | read I9, I11, M2, M1, M3 | READ |
| `board/*.sh`, `board/systemd/*`, `board/relay.py`, `dev/start_servers.{sh,ps1}`, `copilot/{config,client,llm,embed,board_clock,hal/web}.py`, `python/main.py`, `docs/deploy-board.md`, `docs/app-lab-app.md`, `docs/results-A.md` Phase 10, README steps 1 and 7 | read in full | READ |

Answers to the questions asked, in one line each (details in the proposals):

- **Boot order after a power cut**: `math-llm` and `math-embed` start in parallel after `local-fs.target`;
  `math-relay` after `docker.service` and both. All `Type=simple`, so there is no start timeout to hit:
  systemd considers them started at fork, and a slow 835 MB load from eMMC only delays `/health`. The
  measured cold start (`docs/deploy-board.md:127`) is 2 min to Linux, servers already up, page 20 s
  later. Fine. `Restart=on-failure` covers an OOM kill (SIGKILL) but not an exit 0; the default
  `StartLimitBurst=5/10 s` is never reached with `RestartSec=5`.
- **Does the app wait for the servers?** No. `python/main.py:23-24` calls `webapp.start()` (draws the LED
  frame) and serves. No `/health`, no retry. Each hint handler catches the failure
  (`webapp.py:337`, `hints.py:395,460`) and shows "No he pogut preparar la pista", so the app does not
  crash, but a dead relay is invisible until a student asks for rung 1 or 3.
- **Relay**: not single-threaded. `serve()` accepts in one thread per port and starts one `pump`
  thread per connection (`relay.py:79`), so an embedding request proceeds while a 40 s LLM request
  runs. It forwards bytes as they arrive (streaming works). Timeouts: 10 s to connect upstream
  (`:73`), none afterwards; no `SO_KEEPALIVE`, so a container killed mid-request leaves one thread and
  two sockets until the server side closes (llama-server closes after the response, so the leak is
  bounded in practice). The `accept()` loop has no `try` (`:71`): one `EMFILE`/`ECONNABORTED` kills
  the port's thread while the process stays alive (systemd sees no failure).
- **Memory**: no `MemoryMax`, `OOMScoreAdjust` or `Nice` on any unit. With Linux's default policy the
  OOM killer takes the biggest RSS: the LLM (1059 MB measured) before the embed server (75 MB) or the
  app container (91 MB). That is the right victim, but it is luck, not policy, and the LLM comes
  back after 5 s plus the model load. The board has 1.8 GiB of swap (README step 1.1); untouched.
- **Threads**: `LLM_THREADS=4` + `EMBED_THREADS=4` on 4 cores. A rung-3 prefetch (English page,
  `areas` topic only, since the Catalan gate is closed for every topic, reviewer I13) plus a rung-1
  embedding is 8 busy threads on 4 cores; llama.cpp's spin-waiting threads degrade badly when
  oversubscribed. Unmeasured; see P5.
- **Calibration**: reproducible for prefill and generation (`cache_prompt=False`, medians, fixed
  prompts; 11.4 / 5.6 match `docs/results-A.md:80-81`). The embedding constant is **not** what the
  script writes (P1). `board_clock.py:10-11` still says the constants are "the README's measurements
  until Phase 10 calibrates them", and `results-A.md:3-4` says the same (reviewer M1).
- **One-command health check**: `05_smoke_test.sh` checks `/health` twice, one embedding, and the five
  sample problems with `assert worst < 60`. With `LETTER_MODEL=0` and `sample-1` answered by a fixture
  (reviewer I14) every row takes 0.0 s: the 60 s check is vacuous, and nothing checks the relay, the
  data, the app page or the RAM (P9).
- **Secrets/hostnames**: clean (table above).

## Proposals

### P1. `calibrate_speed.py --write` would halve `BOARD_EMBED_SECONDS`: measure one request, not one twentieth of a batch
- **Where**: `board/calibrate_speed.py:69-74,80,88`; `config.env:59`; `copilot/pipeline.py:65`
  (`clock.add_embeddings(1)` per *request*); `copilot/board_clock.py:8,10-11`; `docs/results-A.md:3-4,82`.
- **Problem / opportunity**: `secs.append((time.perf_counter() - t0) / len(TEXTS))` divides the wall
  time of a 20-text batch by 20, so the script proposes the *per-text* number (0.05 s on the board,
  0.003 s here, verified by running it). `board_clock` multiplies `BOARD_EMBED_SECONDS` by the number
  of *requests* (one query embedding per problem), and `config.env` documents 0.12 as "one embedding
  request took 0.10 to 0.15 s". The committed value was therefore chosen by hand; the next person who
  follows `docs/deploy-board.md:58-60` ("run it with `--write` to update them, and commit") writes
  0.050 and every board estimate becomes 2.4x too optimistic on embeddings. Also `board_clock.py:10-11`
  says the constants are uncalibrated, which is false since `cffe371`.
- **Proposal**: in `main()` measure `embed([TEXTS[0]])` `rounds` times and take that median as
  `BOARD_EMBED_SECONDS` (keep the batch figure as an informational line "per text in a batch of 20");
  make `--write` also refresh the comment block's date line (`re.subn` on `# Board speed, measured on
  ... on <date>`); add `tests/test_calibrate_speed.py` that monkeypatches `embed` and `post` with fixed
  timings and asserts the three proposed values and that `--write` on a temp copy of `config.env`
  changes exactly the three keys. Fix the two stale paragraphs (`board_clock.py:10-11`,
  `results-A.md:3-4`) in the same commit.
- **Impact (jury or student)**: medium. The board estimate is the number every laptop result quotes;
  a silent 2x error on one term undermines "we measured" in front of the jury.
- **Effort**: S.
- **Risk**: none to the demo; no INTERFACES change. Safe before the demo.
- **How to measure**: `python3 board/calibrate_speed.py --rounds 1` on the laptop prints
  `BOARD_EMBED_SECONDS` near the single-request wall time (about 0.03 to 0.06 s here), and on the board
  near 0.12; the new test passes.
- **Verified**: ran (the script and its output); the fix is read-only reasoning.

### P2. Harden `relay.py`: survive `accept()` errors, keepalive, a clear message when `docker0` is missing
- **Where**: `board/relay.py:63-79` (`serve`), `:41-60` (`pump`), `:26-38` (`interface_address`,
  `resolve_listen`); `board/systemd/math-relay.service:3-4,10-11`.
- **Problem / opportunity**: (a) `client, _ = server.accept()` at `:71` is outside any `try`: one
  `OSError` (`EMFILE` after a burst of page polls, `ECONNABORTED`) ends that port's thread; the
  process keeps running on the other port, so `Restart=on-failure` never fires and the LLM (or the
  embeddings) is unreachable from the container until someone restarts the unit by hand. (b) No
  `SO_KEEPALIVE` on either socket and no timeout after connect: if the container is stopped during a
  60 s hint, the upstream side closes after the response and the pump ends, so the leak is bounded,
  but a client that vanishes before llama-server answers while the server waits on a slot (queued
  behind another request, `results-A.md:99-102`) is held until the server times out. (c) When
  `docker0` does not exist yet (fresh board, docker not started), `interface_address` raises
  `OSError [Errno 6]` with no explanation (verified), the unit restarts every 5 s and the journal fills
  with tracebacks.
- **Proposal**: wrap the accept loop body in `try/except OSError as error:` that logs and `continue`s
  (sleep 0.1 s on `EMFILE`); set `SO_KEEPALIVE` on `client` and `upstream` (plus `TCP_KEEPIDLE=30`,
  `TCP_KEEPINTVL=10`, `TCP_KEEPCNT=3` when the platform has them) so a dead peer is detected within a
  minute; in `pump` use `sel.select(timeout=300)` and close both sides after 5 idle minutes; in
  `resolve_listen`, on `OSError` print `interface docker0 not found: is docker running?` and retry
  every 5 s for up to 2 minutes before exiting 1. Tests: `test_serve_survives_accept_error` (mock
  `socket.accept` to raise once, then serve a request), `test_pump_closes_idle` with a tiny timeout.
- **Impact (jury or student)**: medium. The relay is the single point between the app and both
  models; a dead port on demo day means "no hints" with no error anywhere visible.
- **Effort**: M.
- **Risk**: low; the pump logic is small and covered by `test_pump_copies_both_ways`. Deploy with
  `sudo systemctl restart math-relay` and the `06` health lines. Safe before the demo if P3 lands
  first so the forwarding test runs on the laptop.
- **How to measure**: `tests/test_relay.py` green on macOS and Linux; on the board
  `journalctl -u math-relay` shows one line, not a traceback, when docker is stopped and started.
- **Verified**: read only (the `OSError` on a missing interface was run).

### P3. Let `serve()` map the port so the forwarding test runs on every laptop
- **Where**: `board/relay.py:63-79` (signature `serve(listen_host, port, target_host, ready=None)`),
  `tests/test_relay.py:30-33`.
- **Problem / opportunity**: the relay listens and forwards on the *same* port, so the test needs a
  second loopback address and is skipped on macOS, i.e. on the three team laptops. The only test of
  the relay's main path has never run in the team's own `unittest` loop (1 skipped in every baseline).
- **Proposal**: `serve(listen_host, port, target_host, ready=None, target_port=None)` with
  `target_port = target_port or port`; `main()` keeps the same-port behaviour. The test binds
  `("127.0.0.1", 0)` for the listener (via `ready(port)`) and forwards to the upstream's port; drop
  the `skipTest`. Add `test_upstream_down_closes_client`: target a closed port, assert the client gets
  `ConnectionResetError`/empty read within 1 s and a second request still works.
- **Impact (jury or student)**: low for the jury, high for the team: the relay becomes testable
  where the team develops.
- **Effort**: S.
- **Risk**: none to the board (default path unchanged). Safe before the demo.
- **How to measure**: `python3 -m unittest tests.test_relay -v` shows 0 skipped on macOS.
- **Verified**: read only.

### P4. Write the OOM and restart policy into the units instead of trusting the defaults
- **Where**: `board/systemd/math-llm.service:3,9-10`, `math-embed.service:3,9-10`,
  `math-relay.service:3-4,10-11`; `board/04_install_services.sh:20-29` (render), `README.md:585-620`
  (the organizers' step 7 copies of the same units).
- **Problem / opportunity**: the units carry only `Restart=on-failure` and `RestartSec=5`. Who dies
  first under memory pressure is left to the kernel's RSS heuristic (today: the LLM, which is the
  best victim, but a bigger hint prompt or a second App Lab brick changes the ranking). `on-failure`
  does not restart a clean exit; a hint prefetch thread (`hints.py:407-418`) competes at equal
  priority with the page's `/api/state` polls, so the page stutters during the only 28 s the jury
  waits. The three units cannot be told apart in `systemd-analyze blame`.
- **Proposal**: in `math-llm.service` add `OOMScoreAdjust=500` (the designated victim; the app and the
  embed server survive), `Nice=5` (the web page and the Bridge stay responsive while the model
  works), `Restart=always`, `StartLimitIntervalSec=0`, `TimeoutStopSec=15`; in `math-embed.service`
  `OOMScoreAdjust=200`, `Restart=always`; in `math-relay.service` `OOMScoreAdjust=-200` (tiny, must
  stay), `Restart=always`, and `After=network.target` next to `docker.service`. Do **not** set
  `MemoryMax`: with `--cache-ram 0` the LLM's RSS is flat at 1059 MB and a cgroup limit would turn a
  rare spike into a certain kill. Re-run `./board/04_install_services.sh` and `06`; document in
  `docs/deploy-board.md` §5 one line: "under memory pressure the LLM is killed first and comes back
  in about 20 s; hints degrade to strategy cards meanwhile".
- **Impact (jury or student)**: medium. A demo that survives an OOM with a card instead of a frozen
  page is the difference between a story and an apology.
- **Effort**: S.
- **Risk**: low; `Nice=5` slows the LLM by a few percent only when something else wants the CPU.
  Needs one restart of the three units on the board and a rerun of `calibrate_speed.py` to confirm
  the rates. Safe before the demo if done on the rehearsal day, not the morning of.
- **How to measure**: `systemctl show -p OOMScoreAdjust -p Nice math-llm`; `choom -p $(pidof
  llama-server)`; `calibrate_speed.py` within 5% of 11.4 / 5.6.
- **Verified**: read only (cannot reach the board).

### P5. Measure thread oversubscription (4 + 4 threads on 4 cores) before choosing `EMBED_THREADS`
- **Where**: `config.env:26,38` (`LLM_THREADS=4`, `EMBED_THREADS=4`); `board/systemd/*.service:8`;
  `copilot/hints.py:407-418` (prefetch thread), `copilot/retrieval.py:122` (`embed` for rung 1);
  `board/calibrate_speed.py`.
- **Problem / opportunity**: both servers are told to use all four cores. The only moment they run
  together is a rung-3 prefetch (English page, `areas`) overlapping a rung-1 embedding or an
  `eval.py --rag` query. llama.cpp threads busy-wait; eight of them on four Cortex-A53 cores can cut
  the prefill rate by much more than half, and the prefill is 80% of every hint's 28 s. Nobody has
  measured it; `calibrate_speed.py` runs "with nothing else using the servers" by design.
- **Proposal**: add `--contend` to `calibrate_speed.py`: a background thread that calls
  `embed(TEXTS)` in a loop during the prefill rounds, and print the two medians side by side (alone /
  under contention). Run it on the board once with `EMBED_THREADS=4` and once with 2 (edit the unit,
  `daemon-reload`, restart `math-embed` only). If the loss is above 20%, set `EMBED_THREADS=2` in
  `config.env` (0.12 s becomes about 0.2 s, invisible to the student) and add the measured table to
  `docs/results-A.md` Phase 10.
- **Impact (jury or student)**: low to medium: it only bites with the LLM gate open, but then it
  doubles the one wait the jury sees. The measurement itself is a good "we measured the board" slide.
- **Effort**: S for the flag and the run; the config change is one line.
- **Risk**: none on the laptop; one embed-server restart on the board. Safe before the demo.
- **How to measure**: the printed "alone / contended" prefill tok/s; target: contended within 20% of
  11.4 tok/s.
- **Verified**: read only.

### P6. `04`/`06` must not trust `$USER` and `$HOME`: `adb shell` has an Android-shaped environment
- **Where**: `board/04_install_services.sh:21` (`s|@USER@|$USER|g`), `board/06_install_relay.sh:11`,
  `board/common.sh:7-8` (`${LLAMA_CPP_DIR/#\~/$HOME}`), `docs/deploy-board.md:103-107` (the
  `TMPDIR=/data/local/tmp` finding).
- **Problem / opportunity**: the deploy guide already proves that `adb shell` does not give a normal
  login environment (`TMPDIR=/data/local/tmp`). Under `set -u` (`common.sh:2`) an unset `USER` kills
  the script with "unbound variable" (acceptable), but a `USER` set to something other than `arduino`,
  or a script run as `sudo ./board/04_install_services.sh` (`USER=root`, `HOME=/root`), renders
  `User=root` and `/root/llama.cpp/...` into the unit, which then fails at boot with no model found.
  Nothing guards against it.
- **Proposal**: in `common.sh` set `RUN_USER="$(id -un)"`, `RUN_HOME="$(getent passwd "$RUN_USER" |
  cut -d: -f6)"` and use them for `~` expansion and the `@USER@` placeholder; add
  `[ "$(id -u)" -ne 0 ] || die "run this script as arduino, not with sudo: it calls sudo itself"` to
  `01`, `04` and `06`. One shell test (`tests/test_board_scripts.sh` or a Python test that runs
  `bash -c 'source board/common.sh; echo $RUN_USER'` with `USER=bogus`) asserts the real user wins.
- **Impact (jury or student)**: low for the jury, medium for the team: a unit rendered for the wrong
  user is exactly the kind of boot failure that appears the morning of the demo after a reinstall.
- **Effort**: S.
- **Risk**: none; the rendered units for user `arduino` are byte-identical. Safe before the demo.
- **How to measure**: `USER=bogus bash board/04_install_services.sh` on a Linux box renders
  `User=<real user>`; `grep User= /etc/systemd/system/math-llm.service` on the board says `arduino`.
- **Verified**: read only.

### P7. `config.env` hygiene: add `SOLVERS=1` (reviewer I9), document `STUDENTS_DB`/`TRAINER_BANK`, drop `VISION_PORT`, fix the RAM constants, guard it with a test
- **Where**: `copilot/config.py:19-21` (environment wins *only for keys present in the file*);
  `copilot/pipeline.py:21`; `copilot/trainer.py:174,265`; `config.env:28,63-64`;
  `dev/ram_budget.py:9-12,22-23,60,65`; `docs/results-A.md:72,104,125`.
- **Problem / opportunity**: verified by the key audit: `SOLVERS` is read at `pipeline.py:21` but
  absent from `config.env`, so `SOLVERS=0 eval.py` silently runs with solvers on (reviewer I9: the
  documented board baseline was measured that way). `STUDENTS_DB` and `TRAINER_BANK` work only
  because `trainer.py` reads `os.environ` directly, bypassing the documented "config.env, environment
  wins" contract. `VISION_PORT=8083` is read by nothing. `BOARD_RAM_AVAILABLE_MB=3100` and
  `BOARD_APP_LAB_RESERVE_MB=500` are "placeholder until Phase 10", but Phase 10 measured 2.9 GB
  after boot, 2609 MB with servers, relay and app, and a 91 MB container; `ram_budget.py` still prints
  "NOT measured".
- **Proposal**: add to `config.env`: `SOLVERS=1` (with the I9 comment), `STUDENTS_DB=` and
  `TRAINER_BANK=` (empty = defaults) under a "Trainer" heading; remove `VISION_PORT` or wire it into
  the README's explorer section; set `BOARD_RAM_AVAILABLE_MB=2900`, `BOARD_APP_LAB_RESERVE_MB=300`
  (container 91 MB + docker daemon + relay, rounded up) and rewrite the two stale strings in
  `ram_budget.py`. Add `tests/test_config_keys.py`: parse `config.env`, grep every
  `CONFIG.get("X"` / `CONFIG["X"]` under `copilot/`, `board/`, `dev/`, `eval.py`, `predict.py`, and
  assert the sets match (allow-list for keys read only by bash). Then rerun the 50-problem board
  baseline with `SOLVERS=0` really off, as the reviewer asks.
- **Impact (jury or student)**: medium: it makes the documented baseline command true and closes a
  class of "the switch did nothing" errors for every future key.
- **Effort**: S for the keys and the test; the baseline rerun is 10 min on the board.
- **Risk**: none; defaults unchanged. Does not touch INTERFACES. Safe before the demo.
- **How to measure**: `SOLVERS=0 python3 -c "import copilot.pipeline as p; print(p.USE_SOLVERS)"`
  prints `False`; the new test is green; `ram_budget.py` prints the measured reserve.
- **Verified**: ran the key audit; the fix is read only.

### P8. Resolve the App Lab host without trusting the `msgpack-rpc-router` alias, and say at startup whether the servers answer
- **Where**: `copilot/config.py:27-42` (`APP_LAB_HOST_ALIAS`, `resolve_host`); `python/main.py:23-24`;
  `copilot/webapp.py:452-456` (`start()`); `copilot/client.py:13-15` (`get`); `tests/test_config_hosts.py`.
- **Problem / opportunity**: inside the container `auto` becomes the literal name
  `msgpack-rpc-router`, an App Lab implementation detail found by reading its compose file. If an App
  Lab update renames it, both URLs fail with `URLError: Name or service not known` on every hint, and
  nothing tells the team: the app starts fine, the page works, rungs 1 and 3 say "No he pogut preparar
  la pista". There is no health check at startup, no log line with the resolved host, no retry.
- **Proposal**: in `resolve_host("auto")` inside the container try `socket.gethostbyname(ALIAS)`; on
  `OSError` fall back to the default gateway read from `/proc/net/route` (stdlib: the line with
  destination `00000000`, gateway hex little-endian), which is `docker0`'s address, where the relay
  listens anyway. In `webapp.start()` (or `python/main.py`) add a non-blocking `threading.Thread`
  that polls `GET /health` on both servers every 5 s for up to 2 min, logs one line
  `servers: llm <host>:8081 ok after 3 s, embed ... ok` or `... unreachable: <error>`, and stores the
  result in `Session` so `/api/state` can carry `"servers": {"llm": true, "embed": false}` and the
  page can show a small grey dot (teacher view only). Tests: mock `gethostbyname` to raise and a fake
  `/proc/net/route` text; assert `172.17.0.1`.
- **Impact (jury or student)**: medium. It turns a silent failure mode of the demo into a one-line
  diagnosis in `arduino-app-cli app logs`.
- **Effort**: M.
- **Risk**: adds one optional key to `/api/state` (INTERFACES.md lists its fields: add it there
  first). The fallback only runs when the alias fails, so the verified path is unchanged. Safe before
  the demo.
- **How to measure**: `arduino-app-cli app logs ... --all | grep servers:` shows both `ok` after
  boot; `tests/test_config_hosts.py` gains two green tests.
- **Verified**: read only.

### P9. One command for demo day: a health check that tests the real path, including the 60 s budget
- **Where**: `board/05_smoke_test.sh:7-11,24-37`; `board/00_check_board.sh:53-60` (checks only two
  units); `data/sample_problems.jsonl`; `copilot/solvers/__init__.py:49-50` (the `sample-1`
  fixture, reviewer I14); `docs/deploy-board.md` §3, §5.
- **Problem / opportunity**: `05` asserts `worst < 60` on five problems that the pipeline answers in
  0.0 s (`LETTER_MODEL=0`, one fixture, the rest `D`), so the budget check proves nothing about the
  model; it never touches the relay, the data, the app page, the LED Bridge, the RAM or the disk.
  `00` does not know `math-relay` exists. On demo morning the team has no single command that says
  "everything the jury will see is up".
- **Proposal**: new `board/07_demo_check.sh` (sourcing `common.sh`, read-only, exit 1 on any FAIL):
  (1) `systemctl is-active math-llm math-embed math-relay`; (2) `/health` on `127.0.0.1` and on the
  `docker0` address for both ports; (3) data: `wc -l data/train.jsonl data/val.jsonl` (expect 2932
  and 562 lines), `data/index.db` present and `sqlite3 ... "select count(*) from problems"`,
  `ls data/images | wc -l` (3494), `data_curated/*.json` parse; (4) `data/students.db` writable by
  the current user and by the container's uid (`stat -c %U`); (5) one real chat completion (the
  hello world of `dev/start_servers.sh:128-137`) timed, and `python3 -c` with
  `board_clock.estimate_tokens(300, 40)` printed against `TIME_LIMIT_SECONDS`: FAIL if a 300-token
  prompt plus 40 tokens would exceed 60 s at the measured rates; (6) `arduino-app-cli app list` shows
  `math-copilot` running, `curl -sf http://127.0.0.1:7000/api/state` returns JSON without `label`;
  (7) `free -m` available ≥ 2000 MB, `df` ≥ 1 GB; (8) `nmcli radio wifi` printed (the demo runs with
  Wi-Fi off). Mention it in `docs/deploy-board.md` §5 as the last line before the pitch. Keep `05` as
  the install-time test but make its budget line honest: run `LETTER_MODEL=1 SOLVERS=0 predict.py` on
  the samples so one real letter request is timed.
- **Impact (jury or student)**: high. Every item is a failure the reviewer or the team already met
  once (relay, images, `TMPDIR`, label leak, foreign requests queued on the server).
- **Effort**: M.
- **Risk**: none; read-only script. Safe before the demo; it is *for* the demo.
- **How to measure**: `./board/07_demo_check.sh` prints only `OK` lines on the rehearsal board and
  fails loudly when `sudo systemctl stop math-relay` is run first.
- **Verified**: read only.

### P10. `docs/deploy-board.md` for a fresh board: the twelve gaps a stranger hits
- **Where**: `docs/deploy-board.md:3,16-17,31-42,81,89-96,99`; `docs/README-final-draft.md:97,111`;
  `docs/results-A.md:74`; `docs/app-lab-app.md:21-26`.
- **Problem / opportunity**: walking the guide on a fresh clone: (1) `:16` clones over HTTPS from
  GitHub; while the repository is private (until step 15) the board needs a token or an SSH key,
  neither is mentioned; the offline alternative (`git bundle create` on the laptop, `adb push`, clone
  from the bundle) is not either. (2) `chmod +x board/*.sh` is a no-op (mode 755 in git), harmless.
  (3) `:3` says "steps 0 to 7 of the README" but the README-final-draft `:97` says "steps 0 to 12";
  pick one. (4) The build time is given once as 30 and once as 35 minutes (`:11`, `results-A.md:73`);
  fine, but say that the build needs no internet after the fetch and survives an SSH drop only inside
  `tmux` (README step 3 says it). (5) `:31-42`: `index.db` "was built on the laptop" but the draft
  README builds it on the board; `build_index.py` needs `math-embed` up, which neither says; the
  images are 144 MB here and "71 MB for English" in the README. (6) `data/students.db` and
  `data/rung0.json` are created by the first answer, from inside the container: nothing says which
  uid owns them afterwards or that host-side `eval.py`/tests must still be able to write `data/`.
  (7) `:81` `ln -s` assumes `~/ArduinoApps` exists (App Lab's first setup creates it) and that App
  Lab follows symlinks (verified on our board, say so with the App Lab version). (8) `:89` "start
  the app once first" contradicts the order of the next two blocks; `docker0` exists as soon as the
  docker daemon runs, so the sentence should read "docker must be running". (9) After `git pull`:
  `app restart` is given (`:99`); re-running `04` when `config.env` changes and `06` when the repo
  moves is in the scripts' headers but not in the guide. (10) Wi-Fi off for the demo: no command
  (`nmcli radio wifi off`, and how to turn it back on blind: `adb shell nmcli radio wifi on`). (11)
  The board's Python is 3.13 and the laptop's 3.14: say which one the tests were run on. (12) "125
  tests pass on the board" (`results-A.md:74`, draft `:111`) against 168 today (reviewer M1).
- **Proposal**: one editing pass adding a "Before you start" box (internet, sudo password, token or
  bundle, App Lab done once), a "Who writes what" table (file, created by, owner, needed by), and a
  "After a change" table (`git pull` → `app restart`; `config.env` → `04` + `06`; move repo → `06`).
  Fix the five inconsistencies above in the three docs.
- **Impact (jury or student)**: medium: "how to replicate it, step by step, from a fresh board" is an
  explicit deliverable (README step 15.1).
- **Effort**: M.
- **Risk**: none. Safe before the demo.
- **How to measure**: a teammate who has never touched the board follows the guide on the second
  board (or a reflash) without asking a question; count the questions.
- **Verified**: read only (walked through, no board).

### P11. Idempotence and failure modes of `02`/`03`/`04` that bite on a reinstall
- **Where**: `board/02_build_llama_cpp.sh:7-10,19-21`; `board/03_download_models.sh:16-24`;
  `board/04_install_services.sh:10-17,35-41`.
- **Problem / opportunity**: the scripts are idempotent (verified by reading: version grep, SHA
  check, `systemctl restart`), with three sharp edges. (a) `02`: when `build/` exists from an
  interrupted run, cmake continues, good; but when the checkout moved to a *different* commit (someone
  tried a newer llama.cpp) the `--version` grep fails and the script fetches and rebuilds for 35 min
  without saying why; print the found version first. (b) `03`: `wget --continue -O target.part`
  resumes, good; but a `.part` whose SHA fails is deleted and the script dies with "run it again",
  i.e. two full 835 MB downloads to recover; try once more inside the script before dying. (c) `04`:
  `pgrep -f "llama-server.*--port $port"` matches the *service's own* process on a rerun and the
  guard compares against `MainPID` of both units correctly, but `systemctl show -p MainPID --value
  math-llm math-embed` prints `0` for a stopped unit and the `[[ ... != *$'\n'"$pid"$'\n'* ]]` test
  then fails to exclude a PID of `0`: harmless today, but the check is hard to read and untested;
  (d) `04` always `restart`s both servers even when the rendered units are byte-identical, dropping
  the prompt cache in the middle of someone's eval; compare the rendered text with `cmp -s` and skip
  the restart when nothing changed.
- **Proposal**: the four small edits above; a `tests/test_board_scripts.py` that renders the units
  through `04`'s `render()` (extract it to `common.sh`) with a fake `config.env` and asserts the
  `ExecStart` line equals `dev/start_servers.sh:118-121`'s flags (today the two are kept equal by
  hand; the ps1 has a third copy at `:116-121`).
- **Impact (jury or student)**: low to medium; it is the second reinstall that pays.
- **Effort**: S.
- **Risk**: none. Safe before the demo.
- **How to measure**: run `04` twice: the second run prints "units unchanged, not restarting";
  the flag test fails when one of the three copies of the `ExecStart` flags drifts.
- **Verified**: read only.

## Discarded

- **Bind the two llama-servers on `docker0` as well and remove the relay.** It would save a process
  and a hop, but "the servers listen on 127.0.0.1 only" is an invariant repeated in the README (step
  5), the units, the skills and the deploy guide, and the relay is the only place that *measurably*
  works end to end today (`results-A.md:117-121`). Not worth the risk a day before the demo.
- **`MemoryMax` on `math-llm`.** With `--cache-ram 0` the RSS is flat; a cgroup limit turns a spike
  into a kill. Folded into P4 as "do not".
- **Swap/zram tuning or `vm.swappiness`.** System settings on a board I cannot reach, with 1.8 GiB of
  swap already present and 2.6 GB available with everything running. No evidence it is needed.
- **A health-check `ExecStartPre` in `math-relay.service` waiting for both servers.** The relay
  connects per request and the app degrades per request; the ordering buys nothing and could delay
  the unit past the app's own start. P8 does the waiting where the symptom is seen.
- **`host.docker.internal`-style alias or `network_mode: host` for the container.** The compose file
  is App Lab's, not ours.

## Table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | `calibrate_speed.py --write` writes the per-text embed figure, not per request | medium | S | yes |
| P2 | Harden `relay.py`: accept-loop errors, keepalive, missing `docker0` message | medium | M | yes (after P3) |
| P3 | `serve(..., target_port)` so the relay forwarding test runs on macOS | low (team: high) | S | yes |
| P4 | OOM, nice and restart policy written into the three units | medium | S | yes (rehearsal day) |
| P5 | Measure 4+4 threads on 4 cores; pick `EMBED_THREADS` from data | low-medium | S | yes |
| P6 | `04`/`06`: real user via `id -un`, refuse `sudo ./script`, `adb shell` env | low-medium | S | yes |
| P7 | `config.env`: `SOLVERS=1` (I9), trainer keys, drop `VISION_PORT`, RAM constants, key test | medium | S | yes |
| P8 | Host fallback to the default gateway + startup health log and `servers` in `/api/state` | medium | M | yes (INTERFACES first) |
| P9 | `board/07_demo_check.sh`: relay, data, app page, RAM and a real 60 s budget check | high | M | yes |
| P10 | `deploy-board.md` for a fresh board: twelve gaps and three doc inconsistencies | medium | M | yes |
| P11 | Idempotence edges of `02`/`03`/`04` and a test that the three `ExecStart` copies agree | low-medium | S | yes |
