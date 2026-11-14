# Cross-cutting: the 3-minute demo must not freeze, lie or die, and the 60 s rule holds by construction

Second-round integration of one theme across eight area reports (`docs/improvements/*.md`, written at
`5cc2ded`) re-checked against `origin/main 7a67b77` (the worktree; 181 tests OK, 1 skipped). Builds on
the reviewer's M2, M3, I4, I9, C2, C3 and "What can fail live" (`origin/team/review-22fa88`). Problems
are named by id only.

**Summary (5 lines).**
1. The demo chains are safer than the reports suggest: all four chain problems and their four rung-1
   neighbours are **training ids** (vectors in `index.db`), so no step of the rehearsed Catalan demo
   calls the LLM or the embedding server; the failures below reach the stage only off-script (a jury
   member types a validation problem, switches the page to English on an `areas` topic, or a service dies).
2. Reproduced today on `7a67b77`: a hung LLM keeps the page `busy` for 1x (prefetch off) or 2x (prefetch
   `full`, the default) `TIME_LIMIT_SECONDS` with a card that carries no error (3.0 s and 6.1 s with the
   limit at 3 s = 60 to 120 s live); a blank pseudonym wipes `demo` (answers 1 -> 0); `predict.py` dies on a
   row without `id`; a missing index shows the made-up `sample-4` as "un problema semblant"; the embedding
   server down makes `get_hint` raise on a validation id; a double click returns `{"error"}` that the page
   cannot render.
3. One object fixes the time side everywhere: `board_clock.Deadline` (a `Clock` with a budget), created
   per student step (`HINT_BUDGET_SECONDS`) and per `predict.py` problem (`TIME_LIMIT_SECONDS` minus
   `TIME_MARGIN_SECONDS`), passed down to `llm.post`, `extract_json`, `letter_scores`, `embed`,
   `hints.llm_hint`/`_prefetched`, and consulted before every model call (`fits()`): no call starts that
   cannot finish, every socket timeout is "what is left", and a prefetch still running is never doubled.
4. The other side is "degrade, never invent": `neighbors()` never raises and never returns a sample
   problem for a real id, `Bridge.call` is guarded, the page renders `{"error"}` as a status line and shows a
   banner after three failed polls, `predict.py` writes a letter for every row whatever happens.
5. Demo day becomes one board-side script (`board/07_demo_check.sh`: services, relay from `docker0`, data
   counts, index, app page without `label`, RAM, Wi-Fi, one timed letter call against the 60 s rule) plus
   the runbook's laptop steps, with the tests sandboxed (`STUDENTS_DB` redirected) and a strict list of
   what is done the night before, the morning of, and never on demo day (trainer P1/P3, retrieval P1/P5,
   POST, hints P2, `calibrate_speed.py --write`, `git pull`).

## What I ran

All from the worktree at `7a67b77`, Python 3.14, the shared servers up (`dev/start_servers.sh --status`:
both OK before and after; never stopped). `STUDENTS_DB` pointed at the scratchpad for everything that
touches the trainer. LLM calls made: **1** (the timed letter call); the hung-LLM test uses a socket that never
answers, the other probes `LLM_PORT=1`/`EMBED_PORT=1`.

| what | command | outcome | kind |
| --- | --- | --- | --- |
| Suite on main | `STUDENTS_DB=<scratch>/x.db python3 -m unittest discover tests` | `Ran 181 tests in 7.1 s, OK (skipped=1)` | VERIFIED |
| Hung LLM, prefetch off | `PF=off python3 <scratch>/hang_llm.py` (a socket on `LLM_PORT` that accepts and never answers; `TIME_LIMIT_SECONDS=3`, `llm_allowed` patched True, `Session.rung=2`, `/api/hint`) | `busy for 3.0 s; kind=strategy; error key present=False`; timeline `hint3:strategy` | VERIFIED |
| Hung LLM, prefetch full (the default) | `PF=full python3 <scratch>/hang_llm.py` | `busy for 6.1 s` (prefetch join 3 s + own call 3 s), same silent card | VERIFIED |
| `predict.py`, row without `id` | `LETTER_MODEL=0 python3 predict.py --input <scratch>/noid.jsonl` | `KeyError: 'id'` traceback, CSV has the header only | VERIFIED |
| `predict.py`, 6 edge rows (no options, Catalan, no text, duplicate id, options as a list, `text: null`; made up) | same on `<scratch>/edge.jsonl` | 6 rows, all `D ok`, exit 0 | VERIFIED |
| Embedding server down, rung 1 on a validation id | `EMBED_PORT=1 HINT_PREFETCH=off python3 -c "hints.get_hint('lvl-2_2016_22', 1, 'cat')"` | **`URLError` propagates out of `get_hint`** ("never raises for a known problem" is false); `webapp._compute_hint` would show "Ara no puc preparar cap pista." | VERIFIED |
| Embedding server down, trainer step | `EMBED_PORT=1` `start_student(x, 2)`, `next_problem`, wrong answer, `next_problem` | no error (the served ids were training ids); `trainer._neighbors` has no `try`, so a validation id in the adaptive step would raise out of `/api/next` | VERIFIED (run) / READ (the gap) |
| Index missing, rung 1 | `INDEX_DB=/nonexistent python3 -c "hints.get_hint('lvl-2_2016_22', 1, 'cat')"` | `neighbour sample-4 easier=True "Un problema semblant i més fàcil (nivell 1)"` | VERIFIED |
| Blank pseudonym against a sim app | `SIM_WEB_PORT=7031 STUDENTS_DB=<scratch>/sim.db python3 python/main.py` (own process, killed afterwards by pid); `/api/start/demo/1`, `/api/answer/A`, `/api/teacher`, `/api/start/%20/auto`, `/api/teacher` | `demo` had `answers 1, base_level 1`; after the blank start `student='demo'`, `answers 0, base_level 0`: **wiped** | VERIFIED |
| Double click and bad input, same app | `/api/answer/B` twice, `/api/hint`, `/api/next` twice, `/api/led/path/abc` | `{"error": "already answered"}` x2 (the page's `render()` throws on it: web report), `/api/next` fine, `/api/led/path/abc` -> `{"error": "ValueError: invalid literal for int()..."}` | VERIFIED |
| Where the demo ids live | `grep -c` of the 4 chain ids and 4 neighbours in `data/val.jsonl` / `data/train.jsonl` | **all 8 in train (0 in val)**: vectors stored, 0 embeddings per step | VERIFIED |
| One real letter call, timed | `llm.letter_scores(sample-1)` | laptop 0.19 s, `prompt_n 103`, `predicted_n 1`, **board estimate 9.2 s**; `estimate_tokens(300, 40) = 33.5 s`; `(488, 61) = 53.7 s` | VERIFIED (1 LLM call) |
| `data_curated/demo_set.json` vs `docs/demo/demo-problems.md` | ids | the 13 demo-set ids (`lvl-0_2016_8`, ...) contain **none** of the 4 chain ids (`lvl-1_2024_2`, `lvl-3_2019_18`, `lvl-2_2020_4`, `lvl-4_2010_12`) | VERIFIED |
| Read | `copilot/{board_clock,llm,embed,client,pipeline,hints,webapp,retrieval,trainer,config}.py`, `copilot/hal/{led,web}.py`, `copilot/solvers/__init__.py`, `predict.py`, `assets/app.js`, `board/{05_smoke_test,00_check_board,common}.sh`, `dev/demo_rehearse.py`, `tests/{__init__,test_webapp,test_hints,test_board_clock,test_solvers}.py`, `INTERFACES.md`, `docs/demo/*.md`, `docs/deploy-board.md` 3 and 5, the reviewer's M2/M3 and "What can fail live" | | READ |

Not run: anything on the board (not reachable from this session); Bridge, OOM and relay rows below are reasoned
from the scripts and the board report.

## 1. One time budget: `board_clock.Deadline`

Merges reason P2 (per-problem deadline, skip what cannot fit, `SOLVERS=0`), web P1 (`HINT_BUDGET_SECONDS`,
`finally: busy = False`, `fallback_reason`), hints P8 (one LLM call in the shown language; keep the gate),
tests P7 (the tests that drive it), reviewer M2 (solver path has no budget) and M3 (prefetch join then a
second call). Design rule: **one object per step, created where the step starts, passed down, consulted
before every model call, never created inside a model module.**

```python
# copilot/board_clock.py (additive)
TIME_LIMIT = float(CONFIG.get("TIME_LIMIT_SECONDS", 60))
MARGIN = float(CONFIG.get("TIME_MARGIN_SECONDS", 3))      # was pipeline.MARGIN = 3.0, hard-coded
CHARS_PER_TOKEN = 3.8                                     # prompt size guess before a call (reason report, tokenized)


class OutOfTime(Exception):
    """Raised by a model call that was not started because it could not finish in time."""


class Deadline(Clock):
    """A Clock with a budget. One per student step (webapp) and one per predict.py problem.

    spent() is the larger of the wall time and the board estimate of the tokens spent: on the
    board both agree, in sim the estimate is what the 60 s rule is checked against and the wall
    time is what a hung socket costs. remaining() therefore shrinks in both runtimes.
    """
    def __init__(self, budget=TIME_LIMIT, margin=MARGIN):
        super().__init__()
        self.budget, self.margin = float(budget), float(margin)

    def spent(self):
        return max(self.real_seconds(), self.board_seconds())

    def remaining(self):
        return max(0.0, self.budget - self.margin - self.spent())

    def expired(self):
        return self.remaining() <= 0.0

    def timeout(self, floor=1.0):
        """What to pass as the HTTP timeout: what is left, never under `floor` (urllib needs > 0)."""
        return max(floor, self.remaining())

    def fits(self, prompt_tokens, output_tokens=0, embeddings=0):
        """Consult BEFORE a model call: can a request of this size finish inside what is left?"""
        return estimate_tokens(prompt_tokens, output_tokens, embeddings) <= self.remaining()

    def check(self, prompt_tokens, output_tokens=0, embeddings=0):
        if not self.fits(prompt_tokens, output_tokens, embeddings):
            raise OutOfTime(f"{self.remaining():.1f} s left, request needs "
                            f"{estimate_tokens(prompt_tokens, output_tokens, embeddings):.1f} s")


def prompt_tokens_of(text):
    return len(text) / CHARS_PER_TOKEN
```

Signatures (all additive; `INTERFACES.md` gets a new "Time budget" block listing them, and one line on
`solve_with_timings`, `get_hint`, the Hint result keys, `neighbors` and `/api/state`):

| module | today | after |
| --- | --- | --- |
| `copilot/llm.py` | `letter_scores(problem, examples=(), timeout=60, url=URL, top=20)` | `letter_scores(..., deadline=None)`: when given, `deadline.check(prompt_tokens_of(prompt text), 1)` then `timeout=deadline.timeout()`; `deadline.add_llm(timings)` on return |
| | `extract_json(problem_text, grammar, fields_hint, timeout=60, max_tokens=60, url=URL)` | `extract_json(..., deadline=None)`: same pattern with `max_tokens` as the output guess |
| | `answer_letter(..., timeout=60, image_b64=None, url=URL)` | `+ deadline=None` |
| `copilot/embed.py` | `embed(texts, query=False, timeout=60)` | `embed(texts, query=False, timeout=60, deadline=None)`: `deadline.check(0, 0, embeddings=1)`, `timeout=deadline.timeout()`, `add_embeddings(1)` |
| `copilot/solvers/__init__.py` | `solve_with_timings(problem)`; each family `extract(problem)` | `solve_with_timings(problem, deadline=None)` -> `module.extract(problem, deadline=None)` -> `llm.extract_json(..., deadline=deadline)`. `solve(problem)` unchanged (INTERFACES) |
| `copilot/hints.py` | `get_hint(problem_id, rung, lang="cat")`; `llm_hint(problem, lang="cat", strict_first=False)`; `_prefetched(state, timeout=LLM_TIMEOUT)`; `_call(messages, max_tokens, grammar=None, timeout=LLM_TIMEOUT)` | `get_hint(..., deadline=None)` (None = `Deadline(HINT_BUDGET)`); `llm_hint(..., deadline=None)` (None = `Deadline(TIME_LIMIT)`, used by the prefetch thread); `_prefetched(state, deadline)` joins `deadline.timeout()` and, **if the thread is still alive after the join, returns a sentinel that makes `_rung3` fall back at once** (never a second call on the single server slot); `_call(..., deadline)`: `deadline.check(prompt_tokens_of(text), max_tokens)` then `timeout=deadline.timeout()`. Before the strict retry: `deadline.fits(same size)` else `rejected.append("no-time")` (replaces the `RETRY_BUDGET` comparison; keep the key as its default) |
| `copilot/webapp.py` | `hint()`/`solution()` start `_compute_hint(rung)` | `_compute_hint(rung, deadline=Deadline(HINT_BUDGET))`; `problem_id` read under the lock; `try/finally: busy = False`; `result["fallback_reason"]` copied from `rejected` when a card replaced an LLM hint; `_record` with `deadline.board_seconds()` |
| `copilot/pipeline.py` | `clock = Clock()`, `remaining = time_limit - elapsed - MARGIN` on the letter path only | `deadline = Deadline(time_limit)`; `solvers.solve_with_timings(problem, deadline)`; `letter_scores(..., deadline=deadline)`; `except OutOfTime: status = "skipped: budget"`; `result["prompt_tokens"] +=` (reason P2 d) |

Config keys in `config.env` (all read through `CONFIG`, so the env override works, which today it does
not for `SOLVERS`, board P7):

```
TIME_LIMIT_SECONDS=60        # exists: the official rule, one problem of predict.py
TIME_MARGIN_SECONDS=3        # new: kept free for Python and the CSV write (was MARGIN = 3.0 in pipeline.py)
HINT_BUDGET_SECONDS=30       # new: one hint step of the web page. 28 s is the measured cost of a live
                             # English `areas` hint on the board (hints report), so 30 keeps it; set 15 in
                             # the demo environment (contingency row 4 goes to the video at 15 s anyway)
SOLVERS=1                    # new (reviewer I9): 0 = never run a family solver
```

Tests (no network; all with `mock.patch.object`):

- `tests/test_board_clock.py::DeadlineTest`: `remaining()` shrinks with a patched `time.perf_counter`;
  `add_llm({"prompt_n": 1100})` in sim expires it; `fits(300, 40)` is True at 60 and False at 30;
  `timeout()` never under 1.0; `check` raises `OutOfTime`.
- `tests/test_pipeline.py` (new, tests P7 a-d): `letter_scores` raising `socket.timeout` -> `status
  "timeout"`, answer `D`; `URLError(ConnectionRefusedError())` -> `status.startswith("error:")`;
  `solve_with_timings` returning `(None, [{"prompt_n": 700}])` in sim then `LETTER_MODEL=1` -> the letter call
  is **not made** and `status == "skipped: budget"` (today it would be made with `timeout=60`, M2); the
  `timeout` reaching `llm.post` equals `deadline.timeout()` at that moment.
- `tests/test_hints.py`: `_prefetched` with a thread that sleeps 2 s and `Deadline(0.3, 0)` returns the
  sentinel in under 0.5 s and `get_hint(..., 3)` is a strategy card with `fallback_reason ==
  ["prefetch-running"]`; `llm_hint` whose `_call` raises `OutOfTime` -> `ok False`, `rejected == ["no-time"]`;
  `test_prefetch_warms_in_a_thread_for_validated_topics` patches `hints.PREFETCH` instead of reading
  `config.env` (hints P8: today it fails under `HINT_PREFETCH=off`).
- `tests/test_webapp.py`: `hint()` with `hints.get_hint` patched to a function that records its `deadline`
  -> `isinstance(Deadline)` and `budget == HINT_BUDGET`; `_read_image` patched to raise -> `busy` is False
  afterwards (the `finally`); the card appended carries `fallback_reason` when `get_hint` returns one.

## 2. Degradation table

"Today" is what the student or jury sees on `7a67b77`; **V** = verified by running here or in the cited
area report (in a real browser for the page rows), **R** = read from the code or the scripts (board not reachable).

| failure | today | after the plan | delivered by |
| --- | --- | --- | --- |
| LLM hung (gate open: English page, `areas`) | page `busy` 60 s (prefetch off) or **120 s** (prefetch `full`, the default); the five letters, Pista, Solució, Següent and Reinicia disabled; then a strategy card with no error and no log line. **V** (3.0 s / 6.1 s at `TIME_LIMIT_SECONDS=3`) | `busy` at most `HINT_BUDGET_SECONDS` (15 in the demo env) whether or not a prefetch is running; the answer letters stay enabled while a hint is pending; the card says why in `fallback_reason` and one stderr line; `thinking` chaser on the LED (web P7) optional | P1, P3 |
| LLM down (connection refused) | instant strategy card (16 ms), silent. **V** (web report) | same card with `fallback_reason: ["error:... refused"]`; the teacher page shows a red `llm` dot from `/api/state.servers`; `07_demo_check` fails before the pitch | P1, P4, P6 |
| Embedding server down | rung 1 on a **validation** id: `URLError` escapes `get_hint`, the page shows "Ara no puc preparar cap pista."; `trainer._neighbors` unguarded, so `/api/next` after an adaptive step on a validation id answers 500 and the page shows "…". Training ids (the four demo chains) unaffected. **V** (hint) / **R** (trainer) | `neighbors()` returns `[]` and logs once; rung 1 says "No tinc cap problema semblant més fàcil" (text exists); the trainer falls to `bank().candidates(...)` as it does when `hits` is empty; red `embed` dot | P4 |
| `index.db` missing (push failed) | rung 1 shows the made-up `sample-4` as "Un problema semblant i més fàcil (nivell 1)" with `easier=True`. **V** | rung 1 "No tinc cap problema semblant"; startup line `retrieval: no index, rung 1 disabled`; `07_demo_check` FAIL on `data/index.db` | P4, P6 |
| Relay dead (`math-relay` stopped or `docker0` missing) | from the container both servers are unreachable: the two rows above at once, nothing says so; `00_check_board.sh` does not know the unit exists. **R** | `07_demo_check`: `systemctl is-active math-relay` and `/health` on the `docker0` address for both ports; app startup health thread logs `servers: llm ... unreachable` | P4, P6 |
| Wi-Fi / adb drop (page cannot reach the board) | status "…", every button enabled, each click an unhandled rejection, `setInterval` keeps stacking fetches, burst on recovery. **V** (web report, browser) | after 3 failed polls: banner "La placa no respon. Espera un moment." and buttons disabled; polls back off to 1.5 s and never overlap; banner clears on the first success. Runbook row 3 (`adb forward` again) unchanged | P3 |
| Bridge failure (sketch not flashed, router restart) | `Bridge.call` unguarded: `answer_letter` raises after `record_answer` (DB written, no message, no timer), `_load_next` fails on every Següent, page stuck. **R** | one stderr line, `_last_frame` kept so the page canvas still shows the frame; contingency row 5 stays true ("the page shows the same frame") | P4 |
| OOM kill | kernel takes the biggest RSS (the LLM, 1059 MB): right victim by luck; `Restart=on-failure` brings it back in about 20 s; meanwhile hints behave as "LLM down" (silent). **R** | `OOMScoreAdjust=500` on `math-llm`, `200` on `math-embed`, `-200` on `math-relay`, `Restart=always`: the victim is policy, the app and the relay survive; the card says `fallback_reason` meanwhile | P7, P1 |
| Blank pseudonym ("Comença" with an empty box, or `/api/start/%20/auto`) | `demo` is started **and wiped** (answers 1 -> 0, `base_level` 1 -> 0). **V** | server `{"error": "name?"}`, page keeps the start screen and focuses the box; a known pseudonym with the course left on "auto" continues instead of resetting | P5 |
| Double click (a letter twice, Pista during a hint) | `{"error": "already answered"}` / `{"error": "busy"}` -> `render()` throws `TypeError`, `<html lang>` flips to `en` until the next poll. **V** (reply) / **V** (crash, web report) | `api()` turns `data.error` into a status line ("Ja has respost", "Un moment…") and returns null; nothing re-renders | P3 |
| Second tab (teacher's laptop, a jury phone) | one `Session`: both see the same student; the second tab's click gets `already answered` and its page crashes for 500 ms. **V** (web report) | same shared state (by design), the message instead of the crash; version-based polling (web P10) after the demo | P3 |
| Power cut | the board is on the laptop's battery: nothing stops (contingency row 7). If the board itself reboots: 2 min to Linux, units start at boot, page 20 s later; `Restart=on-failure` does not restart a clean exit; `students.db` is safe (SQLite journal). **R** | `Restart=always`; `07_demo_check` after any reboot; nothing else | P7, P6 |

## 3. Demo day as code

### `board/07_demo_check.sh` (board P9 merged with runbook steps 2-5; read-only; exit 1 on any FAIL)

Runs **on the board** (`adb shell 'cd ~/Datathon-UPC-2026 && TMPDIR=/tmp ./board/07_demo_check.sh'` or over
SSH). Makes exactly one LLM request (the timed letter call) and one embedding request.

```bash
#!/usr/bin/env bash
# Everything the jury will see, checked in one command. Read-only. Run it the night before and the
# morning of the pitch; it fails loudly, so a green run means "go".
source "$(dirname "$0")/common.sh"
set +e +o pipefail
cd "$REPO_DIR" || exit 1
fails=0
check() { if "$@" >/dev/null 2>&1; then ok "$*"; else fail "$*"; fails=$((fails+1)); fi; }
expect() { local what="$1" got="$2" want="$3"; if [ "$got" = "$want" ]; then ok "$what: $got"; else fail "$what: $got (expected $want)"; fails=$((fails+1)); fi; }

step "Services (units)"
for u in math-llm math-embed math-relay; do check systemctl is-active --quiet "$u"; done

step "Servers from the host and from the container's side (the relay on docker0)"
gw="$(ip -4 -o addr show docker0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)"
[ -n "$gw" ] && ok "docker0 is $gw" || { fail "docker0 has no address: is docker running?"; fails=$((fails+1)); }
for p in "$LLM_PORT" "$EMBED_PORT"; do
  check curl -sf --max-time 5 "http://127.0.0.1:$p/health"
  [ -n "$gw" ] && check curl -sf --max-time 5 "http://$gw:$p/health"
done

step "Data on the board (research-only files, never in git)"
expect "data/train.jsonl lines" "$(wc -l < data/train.jsonl 2>/dev/null)" 2932
expect "data/val.jsonl lines"   "$(wc -l < data/val.jsonl 2>/dev/null)" 562
expect "data/images files"      "$(ls data/images 2>/dev/null | wc -l | tr -d ' ')" 3494
expect "index.db rows"          "$(sqlite3 data/index.db 'select count(*) from problems' 2>/dev/null)" 2932
check python3 -c 'import json,glob; [json.load(open(f)) for f in glob.glob("data_curated/*.json")]'

step "Student database: writable by me and by the app container"
[ -e data/students.db ] || ok "data/students.db does not exist yet (the first answer creates it)"
[ -e data/students.db ] && { check test -w data/students.db; echo "  owner $(stat -c %U data/students.db) (the container writes as this user)"; }
check python3 -c 'from copilot import trainer; trainer.mastery_map("07-check")'

step "The 60 s rule, with the real model"
python3 - <<'PY' || fails=$((fails+1))
import json, time, sys
from copilot import llm, board_clock
limit = board_clock.TIME_LIMIT if hasattr(board_clock, "TIME_LIMIT") else 60.0
est = board_clock.estimate_tokens(300, 40)
print(f"  300-token prompt + 40 tokens at the calibrated rates: {est:.1f} s (limit {limit:.0f})")
assert est < limit - 3, "the calibrated rates cannot answer a 300-token problem in time"
p = [json.loads(l) for l in open("data/sample_problems.jsonl") if l.strip()][0]
t = time.perf_counter(); letter, _s, tm = llm.letter_scores(p, timeout=limit); wall = time.perf_counter() - t
print(f"  one real letter call on {p['id']}: {wall:.1f} s wall, prompt_n {tm.get('prompt_n')}, est {board_clock.estimate(tm):.1f} s")
assert letter in "ABCDE" and wall < limit, "the letter call is too slow"
PY

step "App Lab app and the page (port 7000, no label in the state)"
TMPDIR=/tmp arduino-app-cli app ps 2>/dev/null | grep -q "math-copilot" && ok "user:math-copilot is running" || { fail "app not running: TMPDIR=/tmp arduino-app-cli app start user:math-copilot"; fails=$((fails+1)); }
state="$(curl -sf --max-time 5 http://127.0.0.1:7000/api/state)"
[ -n "$state" ] && ok "/api/state answers (${#state} bytes)" || { fail "/api/state does not answer"; fails=$((fails+1)); }
echo "$state" | grep -q '"label"' && { fail "the state carries a label"; fails=$((fails+1)); } || ok "no label in /api/state"
echo "$state" | grep -q '"started": false' && ok "start screen is up" || warn "a student is started: press Reinicia or curl /api/reset before the pitch"

step "Memory, disk, radio"
avail=$(awk '/MemAvailable/ {printf "%d", $2/1024}' /proc/meminfo); [ "$avail" -ge 2000 ] && ok "RAM available ${avail} MB" || { fail "RAM available ${avail} MB (< 2000)"; fails=$((fails+1)); }
gb=$(free_gb "$HOME"); awk "BEGIN {exit !($gb >= 1)}" && ok "${gb} GB free" || { fail "only ${gb} GB free"; fails=$((fails+1)); }
echo "  wifi: $(nmcli radio wifi 2>/dev/null || echo unknown) (the demo runs with Wi-Fi off: nmcli radio wifi off)"

echo
if [ "$fails" -eq 0 ]; then echo "${GREEN}${BOLD}GO: everything the jury will see is up.${RESET}"
else echo "${RED}${BOLD}$fails check(s) failed. See docs/demo/contingency.md.${RESET}"; exit 1; fi
```

The laptop side stays in `docs/demo/runbook.md` (steps 1, 4, 6-8): `adb devices`, `adb forward tcp:7002
tcp:7000`, `dev/demo_rehearse.py --base http://127.0.0.1:7002 Mariona1 1 C A --hints 2 --hints2 2` (ids must
be `lvl-1_2024_2` / `lvl-3_2019_18`, neighbours `lvl-0_2024_3` / `lvl-2_2019_9`), the tabs, the zoom.
`demo_rehearse.py` gains two asserts: `hint["kind"] != "neighbour" or hint["problem"]["id"] != "sample-4"`
(an invented neighbour) and `"fallback_reason" not in hint` (a card that replaced a model hint): the
rehearsal then fails on exactly the two lies the table above lists.

### Pseudonym seeding and determinism (trainer P3, web P6, demo-problems.md)

The chains depend on `start_student` resetting the pseudonym (`demo-problems.md`: "Comença resets that
pseudonym first, so a pseudonym used in a rehearsal gives the same chain again"). Web P6 ("do not reset a
known pseudonym") must not break that. Resolution (P5 below): **`start()` resets when the course selector
was used (`chosen is not None`) or the pseudonym is unknown; "auto" on a known pseudonym continues.** Every
chain in `demo-problems.md` uses an explicit course (Mariona1 / 6è, Guillem / 1r d'ESO, Pau / 2n d'ESO), so
"Comença" on stage is a reset and the chain is deterministic; the jury's "any pseudonym and course" after
the pitch is a fresh start too; a teacher who comes back with "auto" keeps the LED map (the reviewer's demo
risk 1 and I4). The runbook's steps 5 and 10 keep `/api/reset` from the terminal for rehearsal residue.
Trainer P3 (diagnostic `(L, L+1, L-1)` instead of `(L, L+2, L+4, ...)`) changes problem 2 of every chain
(`lvl-3_2019_18` is the "two levels up" problem the pitch narrates at 55 s): **not before the demo**.

### Tests with the database redirected (tests P1)

`tests/__init__.py`: `os.environ.setdefault("STUDENTS_DB", os.path.join(tempfile.mkdtemp(prefix="m3kang-tests-"),
"students.db"))`, plus `tests/test_env.py::test_tests_never_touch_the_demo_db` (`trainer.db_path() !=
trainer.DEFAULT_DB`). Until that lands, every run on the board is
`STUDENTS_DB=/tmp/tests.db python3 -m unittest discover tests` (verified here: the four test pupils land in
the redirected file). `docs/deploy-board.md:47` gets the same line.

### Order

| when | do | never |
| --- | --- | --- |
| **Night before** (rehearsal day) | `git log -1` equals the demo commit; `./board/07_demo_check.sh`; `STUDENTS_DB=/tmp/tests.db python3 -m unittest discover tests` (expect `Ran 181`, OK); P7's units (`04_install_services.sh` re-run, `calibrate_speed.py` within 5% of 11.4 / 5.6, then `07` again); one `demo_rehearse.py` per chain over `adb forward`; delete the rehearsal pupils (`/api/reset` or `trainer.reset_student`); charge everything; record the backup video after the rehearsal (contingency §9) | `calibrate_speed.py --write`; `config.env` edits other than `HINT_BUDGET_SECONDS=15` |
| **Morning of** (t = 0 to 12 min, runbook §1-6) | power on, `adb devices`, `./board/07_demo_check.sh` (replaces runbook §2-3's hand checks), `adb forward`, one `demo_rehearse.py Mariona1 1 C A`, `/api/reset`, type `Mariona1` + 6è, CA, tabs, zoom | tests, `git pull`, `app stop/start` unless `07` fails, any script of `board/01-06` |
| **Never on demo day** | | trainer P1/P3/P7 (chains change), retrieval P1/P5/P6 (neighbour pool or index change), hints P2 (the demo set does not contain the chain ids), web P3 (POST, untested brick), web P4 (the pitch's 70 s line "la pàgina li diu quina era" and the video storyboard assume the letter is shown), web P10 version polling, tests P11, board P1/P11, index rebuild, `Nice=` on any unit |

## 4. Conflicts resolved

- **Web P6 (no reset of a known pseudonym) vs demo determinism.** Reset iff the level selector was used
  or the pseudonym is new; "auto" continues. The chains use explicit levels, so they stay deterministic;
  the blank name becomes an error instead of `demo`. Test: start `Mar` level 2 twice -> `start_student`
  called twice; start `Mar` auto after an answer -> not called, the answer survives in `/api/teacher`.
- **Web P3 (POST) vs the untested brick.** `expose_api(method, ...)` takes the method but POST was never
  exercised on the board; the sim's POST path has zero tests. Not before the demo. The demo-relevant harm of
  GET side effects (the accidental wipe) is removed by P5 without touching methods. After the demo: switch
  the ten routes with one `adb forward` test and `tests/test_hal_web.py` (tests P9).
- **Web P10 (polling) vs web P2 (error path).** Same function in `app.js`. Before the demo only P2's
  scheduler: a self-rescheduling `setTimeout` (500 ms after the previous poll finished, 1,500 ms after a
  failure), `AbortSignal.timeout(4000)`, no overlapping requests; the rate stays 2/s idle so the rehearsed
  feel does not change. P10's `version` short-circuit and image-by-id are an `/api/state` shape change
  (INTERFACES) and go after the demo.
- **Board P4 `Nice=5` vs calibration.** `Nice` only matters when something else wants the CPU; in the
  Catalan demo the LLM is idle and the page poll costs 0.7 ms. Any unit change needs a `calibrate_speed.py`
  re-run to confirm 11.4 / 5.6 within 5%, which is a rehearsal-day job; `OOMScoreAdjust` and
  `Restart=always` are worth that re-run (they decide who survives an OOM), `Nice` is not. Drop `Nice`
  from the demo build; measure it with board P5's `--contend` after the hackathon.
- **Hints P8 (`warm` instead of `full`) vs web P1 (bounded `full`).** With `Deadline`, `full` is harmless:
  the join is bounded and a running prefetch is never doubled. Keep `full` so a rehearsed English hint
  still arrives early; take from P8 the one-call-in-the-shown-language rule (two calls double the exposure
  to the budget) and the gate `n >= 10`. Both are config/one function and safe.
- **Retrieval P1 (0.75 gate) vs the chains.** The four demo neighbours score 0.935, 0.914, 0.827, 0.810,
  so the gate would not change them, but P1 also reorders the fallback chain and adds a `skip` kind the
  page does not render. After the demo, or before only with the two chains re-run.
- **Reason P2's `remaining` in sim.** `Clock.seconds()` is the estimate in sim and real time on the board;
  a hung socket adds no tokens, so an estimate-only deadline would not shrink in sim (that is why the 6.1 s
  reproduction exists even with a 3 s limit). `Deadline.spent()` takes the larger of the two, which is
  conservative in both runtimes and leaves `eval.py --simulate-latency` untouched.

## Proposals

### P1. `board_clock.Deadline`: one budget per step and per problem, consulted before every model call
- **Where**: `copilot/board_clock.py:84-125` (`Clock`, `estimate_tokens`), `copilot/pipeline.py:15-17,53-56,74-88,91-97`
  (`MARGIN` constant, solver call without budget, `remaining` on the letter path only, the `except` list),
  `copilot/llm.py:46-54,75-85,110-120` (`timeout=60` defaults), `copilot/embed.py:12-17`, `copilot/solvers/__init__.py:45-66`
  and `ages.py:38-39` (+3 twins), `copilot/hints.py:49,375-381,421-426,429-468` (`LLM_TIMEOUT`, `_call`, `_prefetched`,
  `llm_hint`), `copilot/webapp.py:341-391` (`hint`, `solution`, `_compute_hint`), `config.env:44-47`, `INTERFACES.md`.
- **Problem / opportunity**: the 60 s rule is a per-socket HTTP timeout, not a per-step budget. Verified: a hung
  server holds the page `busy` for 1x or **2x** the limit (prefetch join, then a fresh call: 6.1 s at a 3 s limit); the
  solver path passes no budget at all (M2: a 344-token extraction then a 144-token letter call is 53.7 s estimated,
  no margin for a queued server); `SOLVERS=0` is ignored because the key is not in `config.env` (I9). Nothing
  checks before a call whether it can finish.
- **Proposal**: the class, signatures, keys and tests of section 1. Order inside: `board_clock` + its test; `llm`/`embed`
  accept `deadline`; `solvers.solve_with_timings(problem, deadline=None)` threads it; `pipeline.solve` creates it and
  catches `OutOfTime`; `hints` (`_call`, `_prefetched` with the running-prefetch sentinel, `llm_hint` retry check,
  `get_hint(..., deadline=None)`, `fallback_reason`); `webapp._compute_hint(rung, deadline)` with `finally`. INTERFACES:
  a "Time budget" block, `deadline=None` on `solve_with_timings` and `get_hint`, optional `fallback_reason`/`error` on the
  Hint result.
- **Impact (jury or student)**: high. It is the only path that can freeze the live page, and "60 s per step" becomes a
  property of the code rather than of a measurement run.
- **Effort**: M (2 h with the tests).
- **Risk**: additive signatures only; `solve(problem)`, `prefetch`, `neighbors` unchanged. The `hints.py` part is the
  one to rehearse (prefetch is on in the demo; the Catalan gate is closed so the demo never enters the LLM branch).
  Safe before the demo with the suite green and one `demo_rehearse.py` run.
- **How to measure**: section 5 (hang test 3.0 / 6.1 s -> about 1.0 / 1.0 s; `tests/test_pipeline.py` green).
- **Verified**: ran (the freeze, the token estimates); the design is read-only reasoning.

### P2. `predict.py` writes a letter for every row, whatever happens; `SOLVERS=0` honoured
- **Where**: `predict.py:38-45` (`problem["id"]`), `copilot/pipeline.py:91-97` (only `socket.timeout`, `TimeoutError`,
  `URLError` caught), `copilot/llm.py:14` (`problem["text"].strip()`), `config.env` (no `SOLVERS` line), `copilot/pipeline.py:21`.
- **Problem / opportunity**: verified: a row without `id` kills the official run with `KeyError` and the CSV has the header
  only (rows after it are never written: each unanswered problem scores 0 where `D` scores 23%). The reason report also
  verified `RuntimeError`, `ConnectionResetError`, `KeyError('choices')`, `ValueError` escaping `pipeline.solve` from a
  solver. The six made-up edge rows pass today only because `LETTER_MODEL=0` short-circuits before `problem["text"]`.
- **Proposal**: reason P1 verbatim: `except Exception as error: status = f"error: {type(error).__name__}"` at the end of
  `solve()` (answer stays `FALLBACK`); `predict.py` reads `problem.get("id", f"row-{n}")`, `setdefault("text", "")`,
  `setdefault("options", {})`, and wraps `solve()` in a last-resort `try` that writes `D, 0.0, "error: ..."`; `llm.format_problem`
  uses `(problem.get("text") or "")`. Add `SOLVERS=1` to `config.env` (board P7). Tests: `tests/test_pipeline.py` (shares P1's
  file) with `ages.extract` raising `RuntimeError` -> `D`, `status` starts with `error`; `tests/fixtures/edge_rows.jsonl` with
  the seven made-up rows of the scratchpad (no id, no text, `text: null`, options as a list, duplicate id, blank line, no
  options; none is an M3Kang problem) run through `subprocess` -> one output row per input row, a letter in A-E each, exit 0;
  `SOLVERS=0 python3 -c "from copilot import pipeline; print(pipeline.USE_SOLVERS)"` -> `False`.
- **Impact (jury)**: high; it is the only way the hidden-set score falls below the always-D floor.
- **Effort**: S.
- **Risk**: none for the demo (the app does not call `predict.py`); no INTERFACES change. Safe before the demo.
- **How to measure**: `python3 predict.py --input tests/fixtures/edge_rows.jsonl --output /tmp/e.csv` -> 7 rows, exit 0.
- **Verified**: ran (the `KeyError`, the edge rows, `SOLVERS` ignored per the reason report).

### P3. The page's error path: no crash on `{"error"}`, a board-unreachable banner, no overlapping polls, letters usable while a hint is pending
- **Where**: `assets/app.js:51-57` (`api()` ignores `r.ok` and `data.error`), `:140-146` (`b.disabled = !!a || s.busy`),
  `:201-215` (`render`, `poll`), `:217-226` (every handler does `render(await api(...))`), `:247` (`setInterval(poll, 500)`),
  `copilot/hal/web.py:72-76` (500 body is the Python exception text).
- **Problem / opportunity**: `{"error": "already answered"}` after a double click is verified today; the web report verified
  in a real browser that `render()` then throws `TypeError` and flips `<html lang>`, that a fetch failure shows only "…" with
  every button enabled, and that `setInterval` stacks requests with no timeout. On a hung hint the letters are disabled
  (`b.disabled = !!a || s.busy`), so the student cannot even answer while the board thinks. `/api/led/path/abc` returns the
  exception text to the page (verified).
- **Proposal**: web P2 plus one line of web P1: `api(path)` = `fetch(path, {cache: "no-store", signal: AbortSignal.timeout(4000)})`;
  when `!r.ok || data.error`, write the translated error (`busy` -> `thinking`, `already answered` -> `answered`, `no hints left`
  -> `no_hints`, else the raw text) into `#status` and return `null`; every handler `const s = await api(...); if (s) render(s);`.
  Replace `setInterval` with a self-rescheduling `setTimeout` (500 ms after the previous poll finished, 1,500 ms after a failure);
  after 3 consecutive failures show a fixed banner `#offline` ("La placa no respon. Espera un moment." / "The board is not
  answering.") and disable the buttons; clear on success. Letters: `b.disabled = !!a` (a pending hint no longer blocks the
  answer; the server already serialises on `Session.lock`). `hal/web.py` 500 body: `{"error": "internal", "type":
  type(error).__name__}` and the traceback to stderr. Tests: `tests/test_assets.py` greps `app.js` for no bare `render(await api(`
  and for `AbortSignal.timeout`, `index.html` for `id="offline"`; `tests/test_webapp.py::ErrorPathTest` (tests P9: `answer_letter`
  twice, `hint()` while busy, `led_path("abc")` -> `{"error"}` without raising).
- **Impact (jury or student)**: high; a 10-year-old double-clicks, and the USB/adb link is the least reliable part of the stack.
- **Effort**: M.
- **Risk**: pure page change plus one `hal/web.py` line; no INTERFACES change. Safe before the demo with one browser rehearsal
  (`fetch` patched to reject for 5 s in the console -> banner; `render({error: "busy"})` -> no throw).
- **How to measure**: in the browser console the two checks above; `performance.getEntriesByType("resource")` shows no two
  `/api/state` requests in flight at once.
- **Verified**: ran (the replies); the browser crash and the Wi-Fi behaviour are the web report's browser runs.

### P4. Degrade, never invent: `neighbors()` never raises, no sample neighbour for a real id, Bridge guarded, a startup health line
- **Where**: `copilot/retrieval.py:127-151` (`neighbors`), `:111-124` (`query_vector` -> `embed`), `:164-168` (`_fallback` for any
  unknown id), `copilot/trainer.py:301-304` (`_neighbors`, no `try`), `copilot/hints.py:213` (`_rung1` call), `copilot/hal/led.py:44-50`
  (`Bridge.call` unguarded), `copilot/webapp.py:194-210` (`state()`), `:490-494` (`start()`), `python/main.py:23-24`, `copilot/config.py:27-42`.
- **Problem / opportunity**: three verified lies or crashes: `INDEX_DB` missing -> `sample-4` shown as a real easier neighbour;
  `EMBED_PORT=1` -> `URLError` out of `get_hint` on a validation id (the docstring promises "never raises"), and the trainer's
  `_neighbors` would raise out of `/api/next` on the same condition (read); `Bridge.call` has no `try` (read: a failure leaves
  `answer_letter` half done after `record_answer`). Nothing at startup says whether the two servers and the index are there
  (board P8), so a dead relay is invisible until a hint.
- **Proposal**: (1) `retrieval.neighbors`: wrap `query_vector` in `try/except (OSError, ValueError, KeyError)` -> log once per
  process (`retrieval: embedding server unreachable: <error>`) and return `[]`; `_fallback` only when
  `problem_id.startswith("sample-")`, else `[]` (retrieval P4 without the metadata table); INTERFACES: "never raises; `[]` when
  the index or the embedding server is unavailable". `_rung1` already renders `[]` ("No tinc cap problema semblant més fàcil");
  `_choose_adaptive` already falls to `bank().candidates` on empty `hits`. (2) `hal/led._draw_board`: `try: Bridge.call(...)
  except Exception as error: sys.stderr.write(f"led: Bridge.call failed: {error}\n")` (web P7 part 3; `_last_frame` is already
  set before the call). (3) `webapp.start()`: a daemon thread that polls `GET /health` on both hosts every 5 s for up to 2 min,
  logs `servers: llm <host>:<port> ok after N s | unreachable: <error>`, same for `embed`, and stores `Session.servers =
  {"llm": bool|None, "embed": bool|None, "index": os.path.exists(retrieval.INDEX_DB)}`; `/api/state` carries `servers`
  (INTERFACES: one optional key); `teacher.html` shows three grey/green/red dots. Tests: `FallbackTest.test_real_id_without_index_returns_nothing`
  (`retrieval._INDEX=None, INDEX_DB="/nonexistent"`); `test_embed_down_returns_empty` (`embed` patched to raise `URLError`);
  `LedTest` with a fake `Bridge` whose `call` raises -> `show_result(True)` returns and `last_frame()` is the tick; `state()`
  has `servers` with the three keys.
- **Impact (jury or student)**: medium-high: an invented problem in front of the jury is worse than "no hint", and the health
  line turns the silent relay failure into one grep in `arduino-app-cli app logs`.
- **Effort**: M (S without the health thread).
- **Risk**: `neighbors` keeps its signature; `/api/state` gains one optional key (INTERFACES first). The health thread is
  non-blocking and only logs. Safe before the demo; the four chain neighbours are training ids and unaffected by (1).
- **How to measure**: the three reproduction commands of "What I ran" return `problem: None` / no exception / the tick;
  `arduino-app-cli app logs ... | grep servers:` shows two `ok` lines after boot.
- **Verified**: ran (index missing, embed down on `get_hint`); trainer and Bridge gaps read.

### P5. `start()`: reset only on an explicit course or a new pseudonym; a blank name is an error; an exhausted bank does not loop on one problem
- **Where**: `copilot/webapp.py:215-237` (`start`: `student.strip()[:32] or "demo"`, unconditional `start_student`), `:212-213`
  (`set_student` = `start(student, "auto")`), `assets/app.js:223` (`|| "demo"`), `copilot/trainer.py:427-431` (`_least_recent`
  `ORDER BY id LIMIT 1`), `tests/test_trainer.py:183-189`, `docs/demo/demo-problems.md:8-14`.
- **Problem / opportunity**: verified: `/api/start/%20/auto` starts **and wipes** `demo` (answers 1 -> 0, `base_level` 1 -> 0);
  the page sends `"demo"` for an empty box, so one stray "Comença" on the start screen in front of the jury erases the
  pseudonym a curious jury member is most likely to use. Reviewer I4: every "Comença" is a reset, so "mastery lives on the
  board" is only true until the next start. And the chains need the reset (section 3). Trainer P5: with every problem
  seen, `_least_recent` serves the student's **first** problem forever (reproduced in the trainer report on a 12-problem
  bank), which the stub bank and a long jury Q&A on a thin topic cell can reach.
- **Proposal**: in `start()`: `student = student.strip()[:32]; if not student: return {"error": "name?"}`; `known = student in
  {r["student_id"] for r in (trainer.teacher_report() or {}).get("students", [])}`; call `start_student(student, chosen)` when
  `chosen is not None or not known`, else only set `self.student` and `_load_next()` (web P6, narrowed so the chains stay
  deterministic). Page: an empty box keeps the start screen and focuses `#student`; drop `|| "demo"`. `_least_recent`:
  `SELECT problem_id FROM answers WHERE student_id=? GROUP BY problem_id ORDER BY MAX(id) LIMIT 1`. Tests: start `Mar` level 2
  twice -> `start_student` called twice with 2; start `Mar` auto after one (mocked) answer -> not called and the answer survives;
  `start(" ", "auto")` -> `{"error": "name?"}` and `started` stays False; extend `test_repeats_only_when_the_bank_is_exhausted`
  so `ids[12:20]` are 8 distinct ids. `demo-problems.md:13` reworded: "Comença with a course chosen resets that pseudonym".
- **Impact (jury or student)**: high; it removes the reviewer's demo risk 1 and the only accidental data loss in the app.
- **Effort**: S.
- **Risk**: none to INTERFACES (`teacher_report` exists on main); the chains are unchanged because every demo start names a
  course. Safe before the demo; re-run `demo_rehearse.py` once (it always passes a level).
- **How to measure**: the curl sequence of "What I ran" leaves `demo` with `answers 1` and returns `{"error": "name?"}`.
- **Verified**: ran (the wipe); the fixes are read-only reasoning (trainer P5 reproduced in its report).

### P6. Demo day as one command: `board/07_demo_check.sh`, sandboxed tests, an honest smoke test, two asserts in the rehearsal script
- **Where**: new `board/07_demo_check.sh` (section 3), `board/05_smoke_test.sh:24-37` (worst latency of problems that answer
  in 0.0 s), `tests/__init__.py` (empty), `dev/demo_rehearse.py:62-75`, `docs/demo/runbook.md` §2-3, §10, `docs/deploy-board.md:47`.
- **Problem / opportunity**: the runbook checks services and `/health` by hand and nothing else; `05`'s `assert worst < 60` runs
  on five problems that take 0.0 s (`LETTER_MODEL=0`, verified by the smoke CSV); nothing checks the relay from the container's
  side, the data counts, the index, the page, the RAM; the suite writes `Mar`, `Pau`, `student-test`, `test-webapp` into the live
  `data/students.db` (tests P1, verified there; the redirect works: verified here) and `deploy-board.md` tells the team to run
  it before the demo; the rehearsal script would happily print `sample-4` as a neighbour.
- **Proposal**: the script of section 3 (one LLM request, one embedding, exit 1 on FAIL); `tests/__init__.py` redirect +
  `tests/test_env.py`; `05`: replace the vacuous block by `LETTER_MODEL=1 SOLVERS=0 python3 predict.py --input data/sample_problems.jsonl`
  and assert `seconds < 60` on the real letter calls (the five samples are short: `sample-1` is 103 prompt tokens, 9.2 s
  estimated); `demo_rehearse.py`: fail on an invented neighbour (`id == "sample-4"` or any `sample-*` for a non-sample problem)
  and on `fallback_reason`; runbook §2-3 become "run `07`", §0 gains the tests line with `STUDENTS_DB`. Tests: `bash -n` of the new
  script in `tests/test_board_scripts.py` (or by hand), the `test_env` test.
- **Impact (jury or student)**: high; every item is a failure already met once (relay, images, `TMPDIR`, label leak, test pupils
  on the teacher page).
- **Effort**: M (the script 1 h, the rest S).
- **Risk**: none: read-only script, test plumbing. Safe before the demo; it is for the demo.
- **How to measure**: `./board/07_demo_check.sh` prints only OK lines on the rehearsal board and fails after `sudo systemctl
  stop math-relay`; `sqlite3 data/students.db "select count(*) from answers"` identical before and after the suite.
- **Verified**: ran (the redirect, the vacuous smoke line via the reason report's `smoke5.csv`, the one real letter call);
  the script is a proposal (board not reachable).

### P7. Units: the OOM victim is policy, `Restart=always`; no `Nice` before the demo
- **Where**: `board/systemd/math-llm.service`, `math-embed.service`, `math-relay.service` (`Restart=on-failure`, `RestartSec=5`,
  nothing else), `board/04_install_services.sh:20-29`, `docs/deploy-board.md` §5.
- **Problem / opportunity**: board P4, read: under memory pressure the kernel takes the biggest RSS (the LLM, 1059 MB), which is
  the right victim by luck; a bigger hint prompt or a second brick changes the ranking and the app container (91 MB) or the relay
  could go instead, which is the one failure the table above cannot degrade gracefully. `on-failure` does not restart a clean exit.
- **Proposal**: `math-llm`: `OOMScoreAdjust=500`, `Restart=always`, `StartLimitIntervalSec=0`, `TimeoutStopSec=15`; `math-embed`:
  `OOMScoreAdjust=200`, `Restart=always`; `math-relay`: `OOMScoreAdjust=-200`, `Restart=always`. **No `MemoryMax`, no `Nice`**
  (section 4). Re-run `04` and `06`, then `calibrate_speed.py` (expect 11.4 / 5.6 within 5%), then `07`. One line in
  `deploy-board.md` §5: "under memory pressure the LLM is killed first and comes back in about 20 s; hints degrade to strategy
  cards with a reason meanwhile".
- **Impact (jury or student)**: medium; it is what makes an OOM a card instead of a dead page.
- **Effort**: S.
- **Risk**: three unit restarts on the board and a calibration re-run: **rehearsal day only, never the morning of**.
- **How to measure**: `systemctl show -p OOMScoreAdjust math-llm math-embed math-relay`; `choom -p $(pidof llama-server)`.
- **Verified**: read only.

## 5. Implementation order, effort, and the before/after measurement

| order | proposal | effort | gate before the demo |
| --- | --- | --- | --- |
| 1 | P2 `predict.py` never dies, `SOLVERS=1` | S (30 min) | suite green |
| 2 | P6 tests sandbox (`tests/__init__.py`) and `07_demo_check.sh` | S + M | `07` green on the board |
| 3 | P5 `start()` contract, blank name, `_least_recent` | S | `demo_rehearse.py` both chains |
| 4 | P1 `Deadline` end to end | M (2 h) | suite green, hang test, one rehearsal |
| 5 | P3 `app.js` error path | M | browser check (banner, `render({error})`) |
| 6 | P4 degrade-never-invent | M | the three reproduction commands |
| 7 | P7 units | S | rehearsal day, `calibrate_speed.py` within 5% |

Before/after, three measurements (the "before" numbers are from this run):

1. **Hung LLM** (`<scratch>/hang_llm.py`, a socket on `LLM_PORT` that never answers, `TIME_LIMIT_SECONDS=3`, `llm_allowed`
   patched True, rung 2 -> `/api/hint`). Before: busy **3.0 s** (`HINT_PREFETCH=off`), **6.1 s** (`full`), card with no
   `error`/`fallback_reason`. After, with `HINT_BUDGET_SECONDS=1` added to the script's environment: busy about **1.0 s** in
   both modes, `kind=strategy`, `fallback_reason` present (`["prefetch-running"]` or `["no-time"]`), one stderr line, and the
   `answer_letter("B")` that the script issues afterwards is accepted without waiting.
2. **Smoke test with one real letter call timed.** Before: `05` reports `worst latency 0.0 s` (vacuous). After:
   `LETTER_MODEL=1 SOLVERS=0 predict.py` on the five samples; measured here for `sample-1`: laptop 0.19 s, `prompt_n` 103,
   board estimate **9.2 s** (expect about 9-10 s real on the board); the assert is on `seconds < 60` of a call that really
   happened, and `07`'s `estimate_tokens(300, 40) = 33.5 s < 57` is the by-construction check of the calibrated rates.
3. **`predict.py` on the edge rows.** Before: `noid.jsonl` -> `KeyError`, header only; `edge.jsonl` -> 6 rows (only because
   `LETTER_MODEL=0`). After: `tests/fixtures/edge_rows.jsonl` (7 made-up rows) -> 7 rows, `row-1,,D,0.0,ok` for the id-less
   one, every answer in A-E, exit 0, also with `LETTER_MODEL=1 LLM_PORT=1` (`status error: ...`, run continues).

## Table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | `board_clock.Deadline`: one budget per step and per problem, consulted before every model call | high | M | yes, suite green + one rehearsal |
| P2 | `predict.py` writes a letter for every row; `SOLVERS=0` honoured | high | S | yes |
| P3 | Page error path: no crash on `{"error"}`, offline banner, no overlapping polls, letters usable while busy | high | M | yes, one browser check |
| P4 | Degrade, never invent: `neighbors()` never raises or fakes, Bridge guarded, startup health line + `servers` | medium-high | M | yes (INTERFACES line first) |
| P5 | `start()` resets only on an explicit course or a new pseudonym; blank name is an error; exhausted bank | high | S | yes |
| P6 | `board/07_demo_check.sh`, sandboxed tests, honest smoke test, two asserts in `demo_rehearse.py` | high | M | yes (it is for the demo) |
| P7 | Units: `OOMScoreAdjust`, `Restart=always`, no `Nice` | medium | S | rehearsal day only |

## Discarded

- **Killing the hint thread or the in-flight request when the deadline passes.** `urllib` has no cancel and llama-server has
  one slot; the `Deadline` bounds what the page waits for and never starts a second request behind a running one, which is
  the observable property. The orphan thread ends when the socket times out.
- **Per-tab sessions** to make the second tab independent: one board, one student by design; P3 makes the second tab
  harmless. After the hackathon if at all.
- **Switching the ten state-changing routes to POST before the demo** (web P3): the brick's POST path was never exercised on
  the board; P5 removes the one GET side effect that hurt. Do it with one `adb forward` test afterwards.
- **`MemoryMax` on `math-llm`**: with `--cache-ram 0` the RSS is flat; a cgroup limit turns a spike into a certain kill
  (board P4's own "do not").
- **Wiring `demo_set.json` into rung 3/4 before the demo** (hints P2): its 13 ids contain none of the four chain ids
  (verified), so it would change nothing the jury sees and adds an INTERFACES change the day before.
- **Trainer P3 (diagnostic at the chosen level) before the demo**: it changes problem 2 of every chain; the pitch narrates
  that problem at 55 s. Right fix, wrong day.
- **A `/api/health` proxy for the page to poll the servers itself**: P4's startup thread plus `servers` in `/api/state`
  gives the teacher page the same dots without a new route the brick must serve.
