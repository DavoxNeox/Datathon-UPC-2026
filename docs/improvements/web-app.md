# Web app and App Lab app: robustness, silent errors, polling, LED, usability

Scope: `copilot/webapp.py`, `copilot/hal/web.py`, `copilot/hal/led.py`, `python/main.py`, `app.yaml`,
`sketch/`, `assets/`, `tests/test_webapp.py`, `docs/app-lab-app.md`, `docs/bilingual-rung.md`.
Builds on the reviewer's C2, C3, I4, I5, M3-M6, M8 (`docs/reviews/review-main-2026-11-14.md` on
`origin/team/review-22fa88`); each is cited where it applies, with new evidence or a concrete fix.

**Summary (5 lines).**
1. The page works fully offline: zero external requests (checked in a real browser), system fonts, relative URLs; the 20 `test_webapp` tests pass; every endpoint answers in under 1 ms on the laptop without the LLM, hints 1-3 settle in under 250 ms.
2. The one thing that can freeze a live demo: rung 3 with the LLM gate open (English page, `areas`) and a slow or hung llama-server keeps `busy=True` for **one or two full `TIME_LIMIT_SECONDS`** (measured 3.0 s and 6.1 s with the limit set to 3 s, so 60-120 s with the real limit), and while busy the page disables the answer buttons, the hint, next and reset. The failure is then silent: a strategy card with no error field and no log line.
3. The page script has no error path: any `{"error": ...}` reply fed to `render()` throws a `TypeError` (reproduced), a Wi-Fi drop shows only "…" and leaves every button clickable with unhandled promise rejections; polling is a fixed 2 req/s of 2.8 KB with no timeout and no back-off.
4. All 15 endpoints are GET, including the seven that change state (reviewer C2, I4, I5 are consequences): a link preview, a second tab or a typed URL answers, resets or starts. `/api/start/%20/auto` wiped my local `demo` pseudonym with one curl.
5. The LED shows the mastery map, a tick or a cross, and nothing while "thinking" or for the hint rung; `Bridge.call` in `hal/led.py` is unguarded, so a Bridge failure on the board would take `answer_letter` and `next` down with it (read only). The sketch does nothing beyond drawing the frame.

## What I ran

All from the worktree, Python 3.14, the shared llama-servers up on 8081/8082 (never stopped).

| Command | Outcome | Kind |
| --- | --- | --- |
| `python3 -m unittest tests.test_webapp -v` | 20 tests OK in 0.04 s | ran |
| `SIM_WEB_PORT=7021 python3 python/main.py` (background, then killed its pid only) | started in 1.5 s, `/api/state` 200 in 1.6 ms, 911 B before start | ran |
| `curl -w` on `/`, `/app.js`, `/style.css`, `/teacher.html`, `/teacher`, `/manip/paths.html`, `/favicon.ico`, `/../config.env` | 3.2 KB / 13.5 KB / 7.7 KB / 7.4 KB; `/teacher` alias 200 (sim only); favicon 404; traversal 404 | ran |
| `/api/start/web-probe/auto` then `/api/state` | 27 ms; problem keys carry `text_eng`/`options_eng` next to `text`/`options`, never `label`; `llm_allowed=false` on the Catalan page | ran |
| `/api/solution` on a fresh problem, then `/api/state` | 0.8 ms, `hints=[solution]` with `label` present, no answer given (reviewer C2 reproduced) | ran |
| `/api/hint` three times with a 250 ms poll loop | rungs 1, 2, 3 = neighbour, strategy, strategy; each settled within 250 ms; `laptop_seconds` 0.016 / 0.0 / 0.0 | ran |
| `/api/translate/show`, then `/api/translate/foo` | both counted as a show (teacher page: 2 uses, 1 problem); state grows 3.2 KB to 3.7 KB | ran |
| Bad inputs: `/api/answer/X`, `/ab`, `/a`, `/api/lang/xx`, `/api/led/path/abc`, `/api/estimate/x/y`, `/api/start/x/99`, `/api/start/%20/auto`, `POST /api/answer/A` | `X`/`ab` → `{"error": "choose A to E"}` 200; `a` accepted and graded; `xx` → silently `cat`; `abc` and `x/y` → 500 with the Python exception text in the body; level 99 → silently `auto`; a blank pseudonym → started **and reset** `demo`; POST → 404 | ran |
| `/api/answer/A` (wrong) then `/api/answer/B`, `/api/hint` | state `answer` carries `label`, message "No és això. La resposta era C."; second answer and hint → `already answered` (reviewer C3 reproduced) | ran |
| `/api/teacher` | 1.6 ms, 3 KB, `source=teacher_report`, every pseudonym ever started is listed | ran |
| 20 sequential and 10 concurrent `/api/state` | min 0.63 ms, median 0.73 ms, max 0.89 ms; concurrent 0.5-1.3 ms | ran |
| `hang_llm.py` (scratchpad): a socket that accepts and never answers as `LLM_PORT`, `TIME_LIMIT_SECONDS=3`, `llm_allowed` patched to True, `Session.rung=2`, `/api/hint` | `HINT_PREFETCH=off`: busy 3.0 s; `HINT_PREFETCH=full`: busy **6.1 s** (prefetch join + own call); result `kind=strategy`, no `error` key, no log line | ran |
| Same with `LLM_PORT=1` (connection refused) | rung 3 falls back to a strategy card in 16 ms; `llm_hint` reports `rejected=['error:... Connection refused']`, dropped by `_rung3` | ran |
| `EMBED_PORT=1`, `hints.get_hint(id, 1)` on a train id and on a val id | train id (vector in `index.db`): neighbour in 11 ms; **val id: raises `URLError`** → `_compute_hint` shows "No he pogut preparar la pista." (281 val ids are not in the 1,466-vector index) | ran |
| Desktop-app browser on `http://127.0.0.1:7021` (student and teacher pages) | the browser showed the curl session's state (one `Session` for every client); `render({error:"busy"})` → `TypeError: Cannot read properties of undefined (reading 'title')`, `<html lang>` flipped to `en` until the next poll; with `fetch` patched to reject for 1.6 s: status "…", all buttons enabled, one unhandled rejection on "Següent"; polls 2.02/s, 2,793 B each, zero external resources; computed font sizes: body 18, text 21, letters 28, meta 14, status 16, mastery 14, footer 13, teacher link 14 px; console clean on both pages | ran |
| `grep -rn "http\|src=\|href=\|url(" assets/`, `grep -rn "@import\|googleapis\|cdn\|unpkg\|jsdelivr" assets/` | nothing external | ran |
| `hal/led.py` on the board, `web_ui` brick threading and POST support, `Bridge.call` blocking semantics | `.skills/unoq-hardware-ui/SKILL.md:50,65,234` only says "keep Bridge calls short, never call the model inside a handler"; board behaviour not verifiable here | read only |
| `copilot/hints.py` 375-470 (prefetch, `_prefetched`, `llm_hint`), `copilot/trainer.py` `_connect` (one connection per call, closed in `finally`), `sketch/sketch.ino`, `app.yaml` | see proposals | read only |

Answers to the brief's questions, in one place:

- **LLM slow or down**: down = instant silent fallback to a card (16 ms); slow = 60 s (prefetch off) or up to 120 s (prefetch full, the default) of `busy`, page frozen, then a card with no error shown. Only when the LLM gate is open (`llm_allowed`): on the Catalan page it is closed for every topic, on the English page open for `areas` (reviewer I3). No timeout on the page side.
- **Embed server down**: rung 1 on any validation problem raises inside the thread, caught by `_compute_hint`, shown as "No he pogut preparar la pista." with `error` in the hint dict (not shown on the page). Train problems keep working (vectors in `index.db`).
- **Wi-Fi drop**: the page shows "…" in the status line only; every button stays enabled and each click is an unhandled rejection; the pending `fetch` calls pile up (no timeout, `setInterval` keeps firing). Recovery is automatic when the board answers again (verified by restoring `fetch`).
- **Two browsers**: one `Session` object, both see the same student, problem and hints; the second one's click gets `{"error": "already answered"}` which crashes its `render()` for 500 ms (P2). No login, no per-tab identity.
- **Teacher + student open at once**: harmless; the teacher page calls `/api/teacher` every 3 s, which opens SQLite and runs `teacher_report` each time (1.6 ms here).
- **Silent errors**: `hints._rung3` drops `llm_hint`'s `rejected` reasons (fallback card carries no `error`); `hints.warm` returns `{}` on any error; `hints._solved` swallows every solver exception; `webapp._read_image` returns `None`; `Rung0Stats._save` `pass`es on `OSError`; `topics.json` missing → empty table; `webapp.start/reset` turn trainer exceptions into a timeline row only; `hal/led._draw_board` prints ASCII when the import fails; `_compute_hint` puts the exception text into the hint dict but the page never renders it. No `log()` anywhere in `webapp.py`.
- **Threads**: hint thread, `threading.Timer` (3 s), prefetch thread (per problem, never cancelled), the HTTP server's threads. `Session.lock` guards state; `_compute_hint` reads `self.problem["id"]` (line 334) and does the image read outside the lock and outside the `try`, with no `finally: busy = False`: anything raising there leaves `busy=True` forever. SQLite is safe: `trainer._connect()` opens a fresh connection per call and closes it in `finally`. A prefetch for problem N keeps running on the single llama-server slot after "Següent" shows problem N+1, so quick skips queue 28 s calls (gate open only).
- **Polling**: `setInterval(poll, 500)` → 2.02 req/s of 2.8 KB (3.7 KB with rung 0 shown, 63 KB with a visual neighbour per reviewer M6) plus the LED frame in every reply; on the board each poll is a Python request served by the brick's process while llama-server generates on the same 4 cores. Not measured on the board.
- **LED**: `show_mastery` on start, after every `next`, 3 s after an answer and on reset; `show_result` on answer; `show_path` from the paths manipulative. Nothing for "thinking", nothing for the rung. `_draw_board` imports `Bridge` lazily, falls back to ASCII on `ImportError`, and calls `Bridge.call("draw", 104 bytes)` with no `try` and no timeout argument. `runtime()` re-reads `/proc/device-tree/model` on every frame (cheap). The sketch only copies the frame and redraws it every 10 ms; no heartbeat, no input.
- **GET with side effects**: `/api/student`, `/api/start`, `/api/reset`, `/api/lang`, `/api/next`, `/api/answer`, `/api/translate`, `/api/hint`, `/api/solution`, `/api/led/path` (10 of 15).
- **CDN / external URL**: none. **Offline with no DNS**: yes, the only 404 is `/favicon.ico`.

## Proposals

### P1. One visible budget for rung 3: never freeze the page for 60-120 s
- **Where**: `copilot/hints.py:421-426` (`_prefetched` joins up to `LLM_TIMEOUT`), `hints.py:49` (`LLM_TIMEOUT = TIME_LIMIT_SECONDS`), `hints.py:449-456` (`llm_hint` error path), `copilot/webapp.py:332-353` (`_compute_hint`), `assets/app.js:106,113` (buttons disabled while `busy`).
- **Problem / opportunity**: with a hung server the hint handler waits the prefetch join (60 s) and then its own call (60 s): measured 6.1 s with `TIME_LIMIT_SECONDS=3`, i.e. **120 s** with the real value, during which `busy=True` disables the five answer buttons, "Pista", "Solució", "Següent" and "Reinicia". The result is a strategy card with no `error`, so the presenter never learns what happened. Reviewer M3 names the join; the measurement and the frozen answer buttons are new. Reachable only with the LLM gate open (English + `areas`), which is exactly the "look, the model writes a hint" moment of a pitch.
- **Proposal**: (1) in `hints.py` add `HINT_BUDGET_SECONDS=20` to `config.env` and use it as the `timeout` of `_prefetched` and of `_call` inside `llm_hint` (the prefetch keeps the full 60 s in its own thread); (2) in `_rung3`, when `result.get("ok")` is false copy `result["rejected"]` into the fallback card as `"fallback_reason"` and write one `sys.stderr` line; (3) in `webapp._compute_hint`, wrap everything after `get_hint` in `try/finally: self.busy = False` and read `problem_id` under the lock; (4) in `app.js` keep the answer buttons enabled while busy (`b.disabled = !!a`), only the hint buttons wait. Test: `tests/test_webapp.py` with a fake `hints.get_hint` that sleeps 0.5 s and a `HINT_BUDGET_SECONDS=0.1` patch → `busy` false within 0.3 s and `fallback_reason` present; a second test where `_read_image` raises → `busy` false.
- **Impact (jury or student)**: high; a frozen page in minute 2 of a 3-minute demo is the worst visible failure, and it is the one path that calls the model live.
- **Effort**: M.
- **Risk**: none to INTERFACES.md (the hint dict gains an optional key). Safe before the demo; the 20 s budget is below the 28 s measured hint time, so set it to 35 s if the English `areas` hint must still land, or close the gate for the demo (reviewer I3).
- **How to measure**: the scratchpad `hang_llm.py` with `TIME_LIMIT_SECONDS=3 HINT_BUDGET_SECONDS=1` → busy ≈ 1.0 s both with prefetch off and full, and the card carries `fallback_reason`.
- **Verified**: ran (6.1 s / 3.0 s / 16 ms measurements).

### P2. Give `app.js` an error path: no crash on `{"error"}`, a "board unreachable" banner, bounded polling
- **Where**: `assets/app.js:41-47` (`api()` ignores `r.ok` and `data.error`), `:157-167` (`render` assumes a state), `:169-171` (`poll`), `:173-182` (every handler does `render(await api(...))`), `:196` (`setInterval(poll, 500)`).
- **Problem / opportunity**: `render({error: "busy"})` throws `TypeError` (verified in the browser) because `lang = s.lang` becomes `undefined` and `t()` is `undefined`; `<html lang>` flips to `en` until the next poll. It happens on every `already answered`, `busy`, `no problem` reply: a double click, a second browser, "Següent" during a hint. On a Wi-Fi drop the page shows "…" and nothing else; buttons stay enabled; `setInterval` keeps starting fetches that never finish (no `AbortController`), so when the board comes back it receives a burst.
- **Proposal**: `api(path, method="GET")` → `fetch(path, {method, cache: "no-store", signal: AbortSignal.timeout(4000)})`; if `!r.ok || data.error`, write `data.error` (translated: `busy` → "Un moment…", `already answered` → "Ja has respost") into `#status` and return `null`; every handler does `const s = await api(...); if (s) render(s);`. Replace `setInterval` by a self-rescheduling `setTimeout` (500 ms after the previous poll finished, 1,500 ms after a failure); after 3 consecutive failures show a fixed banner "La placa no respon. Espera un moment." / "The board is not answering." and disable the buttons; clear it on the next success. Test: a small Node-free check is not possible in the suite; add `tests/test_assets.py` that asserts `app.js` contains no bare `render(await api(` (grep) and that `index.html` has the banner element; manual check with the browser's `fetch` patched as I did.
- **Impact (jury or student)**: high; a 10-year-old double-clicks, and the demo Wi-Fi/adb link is the least reliable part of the stack (deploy guide: the page came back "20 s later" after a reconnect).
- **Effort**: M.
- **Risk**: none to INTERFACES.md; pure page change; safe before the demo if rehearsed once.
- **How to measure**: in the browser console, `render({error:"busy"})` no longer throws; patch `fetch` to reject for 5 s → banner visible, buttons disabled, restored after; `performance.getEntriesByType("resource")` shows no overlapping `/api/state` requests.
- **Verified**: ran (TypeError, lang flip, unhandled rejection, 2.02 polls/s).

### P3. State-changing endpoints become POST (the root of reviewer C2, I4, I5)
- **Where**: `copilot/webapp.py:432-449` (the route table), `copilot/hal/web.py:68-79,98-100` (the sim already dispatches POST and reads the body), `assets/app.js:173-182`, `assets/manip/paths.html:66`, `docs/app-lab-app.md:28` ("all GET").
- **Problem / opportunity**: ten of the fifteen routes change state over GET. Browsers prefetch and preview GET links, a typed URL in a second tab answers or resets, and my own probe `/api/start/%20/auto` silently started and **reset the `demo` pseudonym** (the teacher page now shows `demo 0/1`). `POST /api/answer/A` returns 404 today, so nothing depends on POST yet.
- **Proposal**: change the method of `/api/student`, `/api/start`, `/api/reset`, `/api/lang`, `/api/next`, `/api/answer`, `/api/translate`, `/api/hint`, `/api/solution`, `/api/led/path` to `"POST"` in `routes()`; `app.js` `api(path, "POST")` for those; `paths.html` likewise; `/api/state`, `/api/image`, `/api/led`, `/api/teacher`, `/api/estimate` stay GET. The brick's `expose_api(method, path, handler)` already takes the method (`.skills/unoq-hardware-ui/SKILL.md:33`). Test: `tests/test_webapp.py::RoutesTest` asserts the method per path and that a `GET` to `/api/reset` in `_serve_sim` returns 404 (start the server on an ephemeral port in the test, as `test_relay` does). Update the endpoints table in `docs/app-lab-app.md` and INTERFACES.md line 222 (`GET /api/translate/{show|hide}`).
- **Impact (jury or student)**: medium for the jury ("guide without revealing" needs the answer not to be one GET away), high for a classroom.
- **Effort**: S-M.
- **Risk**: touches INTERFACES.md (one line). The brick's POST handling is not verifiable off the board: do it only with one `adb forward` test before the demo, otherwise after.
- **How to measure**: `curl -X POST .../api/reset` → 200, `curl .../api/reset` → 404; the page flow unchanged in the browser.
- **Verified**: ran (404 on POST today, the accidental reset).

### P4. After a wrong answer: no letter, one more try, hints still open (reviewer C3, with the implementation)
- **Where**: `copilot/webapp.py:257-282` (`answer_letter`), `:267` (`self.answer = {"letter": letter, **result}` puts `label` in `/api/state`), `:273-275` (message), `:315-316` (`hint()` refuses after an answer), `assets/app.js:103-117` (`renderAnswer` highlights `a.label`, disables hints, status "Ja has respost. Pots veure la solució.").
- **Problem / opportunity**: reproduced: one wrong click shows "No és això. La resposta era C.", paints C green, disables "Pista" and pushes the solution. The ladder is unreachable after a mistake, which is when a child needs it; the status line literally invites the student to look at the answer.
- **Proposal**: in `Session`, keep the trainer's result private (`self._graded`) and publish `self.answer = {"letter", "correct", "attempt": n}` only. First miss: `record_answer` as today (mastery bookkeeping unchanged), message "No és això. Demana una pista o prova una altra lletra." / "Not this time. Ask for a hint or try another letter.", `hint()` allowed, letters re-enabled except the one tried (`self.tried = ["A"]`). Second miss or rung 4: add `label` to `self.answer`, show the letter. Second attempt is not sent to the trainer (its contract is one answer per problem); it goes in the timeline as `answer2:B:wrong` and in `Rung0Stats`-style counters if wanted. `app.js`: `b.classList.toggle("right", a?.label === l)` already tolerates a missing label; disable only `tried` letters; status text "Encara pots demanar una pista." Tests: after one wrong answer `json.dumps(state)` contains no `"label"`; `hint()` succeeds; after the second wrong answer `label` is present; the trainer mock receives exactly one `record_answer`.
- **Impact (jury or student)**: high; this is the jury's first criterion and the reviewer's C3, and the presenter can then show a wrong click *and* the ladder on the same problem.
- **Effort**: M.
- **Risk**: `/api/state.answer` loses `label` until the reveal: INTERFACES.md's state description changes (one line). Safe before the demo if the two tests pass; rehearse the wrong-then-hint path once.
- **How to measure**: `curl /api/answer/A; curl /api/state | grep -c '"label"'` → 0; `curl /api/hint` → `ok`.
- **Verified**: ran (reproduction) / read only (fix).

### P5. `/api/solution` needs an attempt or rung 3 first, plus a confirmation (reviewer C2)
- **Where**: `copilot/webapp.py:323-330`, `assets/app.js:176` (no `confirm()`), `app.js:186-193` (keyboard: no key for the solution, good).
- **Problem / opportunity**: reproduced in 0.8 ms: fresh problem, one GET, `label` and `value` in the state. The "Solució" button sits next to "Pista" in the same size.
- **Proposal**: `solution()` returns `{"error": "answer first or climb to rung 3"}` unless `self.answer` or `self.rung >= 3`; the page greys the button until then (`$("solution").disabled = s.busy || !(s.answer || s.rung >= 3)`) and asks `confirm(t().confirm_solution)` ("Vols veure la solució? Després d'això el problema no compta per al domini."). Test: `solution()` on a fresh session → error; after `rung=3` → thread started.
- **Impact (jury or student)**: high for the jury, medium for the student.
- **Effort**: S.
- **Risk**: none to INTERFACES.md; safe before the demo.
- **How to measure**: `curl /api/start/x/auto; curl /api/solution` → error; after three `/api/hint` → ok.
- **Verified**: ran (reproduction).

### P6. `start()` must not reset a known pseudonym (reviewer I4), and a blank name must not become `demo`
- **Where**: `copilot/webapp.py:199` (`student.strip()[:32] or "demo"`), `:205-208` (unconditional `start_student`), `:190-191` (`set_student` = start), `docs/app-lab-app.md:33`.
- **Problem / opportunity**: `start_student` begins with `reset_student` (reviewer I4). New evidence: a blank pseudonym (`/api/start/%20/auto`, or "Comença" with an empty box) starts **and wipes** `demo`, the pseudonym the demo is most likely to use. The teacher page then shows only the current session.
- **Proposal**: in `start()`: `known = student in {r["student_id"] for r in (trainer.teacher_report() or {}).get("students", [])}` (the report exists on `main`); call `start_student` only when `not known`, or when `chosen is not None` and differs from the stored `base_level`/start level in the report's row; otherwise just set `self.student` and `_load_next()`. An empty box: keep the start screen and focus the input (page side), and server side return `{"error": "name?"}` instead of `demo`. Test: start `Mar`, answer once (mock), start `Mar` again → `start_student` not called; start `Mar` with level 3 → called with 3.
- **Impact (jury or student)**: high; "mastery lives on the board" and the LED map are only true if the pseudonym survives a second "Comença". Also removes the reviewer's demo risk 1.
- **Effort**: S.
- **Risk**: none to INTERFACES.md if `teacher_report` is used; safe before the demo (it only removes a reset).
- **How to measure**: `curl /api/start/Mar/auto; curl /api/answer/A; curl /api/start/Mar/auto; curl /api/teacher` → `Mar` still has 1 attempt.
- **Verified**: ran (the wipe) / read only (fix).

### P7. The LED says "thinking" and shows the rung; `Bridge.call` can fail without taking the app down
- **Where**: `copilot/hal/led.py:44-50` (`_draw_board`, no `try` around `Bridge.call`), `:57-63` (`show_mastery`: 8 rows × 13 columns, all used), `copilot/webapp.py:158,270,286` (the three LED calls), `:318-320` (`busy` set, LED untouched), `sketch/sketch.ino:13-15,25-27`.
- **Problem / opportunity**: during the only slow moment of the demo (rung 3, 28 s) the matrix keeps the mastery map, so the jury sees nothing happen on the hardware; after a hint there is no trace of the rung on the board either. The skill's own advice is "show thinking on the matrix" (`SKILL.md:65`). Robustness: if the Bridge raises (sketch not flashed, router restarting; not verifiable here) the exception leaves `answer_letter` after `record_answer` (DB written, message and timer not set) and `_load_next` fails on every "Següent": the page is stuck with no error. `_draw_sim` prints 8 lines per frame to stdout, which in the container goes to the App Lab log on every poll-less frame (fine) but would also run at 4 Hz with an animation.
- **Proposal**: (1) `led.show_thinking(step)`: a 3-LED chaser on row 7 (`boards`, bottom) that leaves rows 0-6 as the mastery map; `Session.hint()` starts a `threading.Timer`-based pulse at 4 Hz while `busy`, `_compute_hint`'s `finally` stops it and redraws `show_mastery`; (2) `led.show_rung(rung)`: light `rung` LEDs at the right end of row 7 for the rest of the problem (`show_mastery(mastery, rung=self.rung)`); (3) wrap `Bridge.call` in `try/except Exception as error: sys.stderr.write(f"led: Bridge.call failed: {error}\n")` and keep `_last_frame`, so the page's canvas still shows the frame; (4) `_draw_sim` prints only when `RUNTIME=sim` and a `LED_PRINT=0` switch silences it in tests. Tests: `show_thinking(0..3)` returns 4 distinct frames and never touches rows 0-6; a fake `Bridge` whose `call` raises → `show_result(True)` returns and `last_frame()` is the tick.
- **Impact (jury or student)**: medium-high for the jury ("use the board"); the Bridge guard is insurance.
- **Effort**: M.
- **Risk**: INTERFACES.md `hal/led.py` section gains two functions (additive). Safe before the demo for (3); (1)-(2) need one look on the real matrix (the 10 ms sketch loop redraws whatever Python last sent, so a 4 Hz update is fine).
- **How to measure**: `curl /api/hint` with the LLM gate open: `/api/led` changes every 250 ms while `busy`; the app log shows one line on a Bridge failure instead of a traceback.
- **Verified**: read only (board), ran (sim frames via `/api/led/path`).

### P8. Log what is swallowed, validate the path parameters, and do not leak Python exceptions to the page
- **Where**: `copilot/hints.py:261-287` (`_rung3` drops `result["rejected"]`), `:384-394` (`warm` → `{}`), `:246-252` (`_solved` → `None`), `copilot/webapp.py:81-91` (`_save` `pass`), `:421-426` (`_read_image` → `None`), `:207-211,225-230` (trainer errors → timeline row), `:245-248` (`set_lang("xx")` → `cat`), `:288-308` (`translate("foo")` counts as a show), `:199-200` (level 99 → `auto`), `:363-370` (`led_path` `int()` on raw input), `copilot/hal/web.py:75-76` (500 body = `TypeError: ...`).
- **Problem / opportunity**: verified: the LLM-down card carries no error; `/api/translate/foo` was counted as a rung-0 use (teacher page: 2 uses after one real show); `/api/lang/xx` and `/api/start/x/99` succeed silently; `/api/led/path/abc` and `/api/estimate/x/y` return 500 with the exception text; the hint `error` text ("No he pogut preparar la pista." + `NameError: ...`) reaches the state but the page shows only the Catalan sentence. During the demo nobody can tell *why* a hint became a card.
- **Proposal**: one helper `copilot/log.py` with `log(event, **fields)` writing `time, event, key=value` to `sys.stderr` (the App Lab log and the sim terminal), stdlib only. Call it at the nine places above (`hint.llm_rejected`, `warm.failed`, `solver.failed`, `image.missing`, `rung0.save_failed`, `trainer.start_failed`, …) and from `_compute_hint` when `result.get("error")`. Validate: `set_lang` and `translate` return `{"error": "..."}` on unknown values; `start` returns `{"error": "level 0..7 or auto"}`; `led_path` and `estimate` validate with a regex and return 400-style errors; `hal/web.py` sends `{"error": "internal", "type": type(error).__name__}` and logs the traceback. Tests: `translate("foo")` leaves `rung0.uses` at 0; `set_lang("xx")` returns an error and keeps the language; `led_path("abc")` returns `{"error"}` without raising.
- **Impact (jury or student)**: medium; it is what makes P1 and P7 diagnosable in the hall, and it stops the rung-0 counter from being inflated by a typo.
- **Effort**: S-M.
- **Risk**: none to INTERFACES.md; safe before the demo.
- **How to measure**: the curl list in "What I ran" returns `{"error": ...}` for `foo`, `xx`, `99`, `abc`, `x/y`; `LLM_PORT=1 ... get_hint(id, 3)` writes one `hint.llm_rejected` line to stderr.
- **Verified**: ran.

### P9. A page a 10-year-old can read: sizes, words, shortcuts on the buttons, no "portàtil" (reviewer M5, M8)
- **Where**: `assets/style.css:24` (`.meta` 14 px), `:58,65` (`.hint .kind`, `.hint .time` 12 px), `:67` (`.status` 16 px), `:68` (`.mastery` 14 px), `:71` (footer 13 px), `:15` (teacher link 14 px); `assets/app.js:8-21` (Catalan strings), `:13` (`laptop: "portàtil"`), `:186-193` (shortcuts A-E, P/H, T, N never shown on screen), `assets/index.html:23` ("Àlies"), `:57` (the rung dots carry no text), `:65` ("Domini per tema"); `assets/teacher.html:54` (legend "1 sempre falla").
- **Problem / opportunity**: computed in the browser: the problem text (21 px), the letters (28 px) and the buttons (18 px) are right for a child, but the hint header, the hint time, the footer and the meta line are 12-14 px grey on white (#5c667a on #fff is 5.9:1, fine for contrast, small for a child at arm's length from a laptop on a stand). Words: "Àlies" is a word no 10-year-old uses (Catalan primary pupils say "nom" or "sobrenom"); "Domini per tema" and "esglaó" are teacher words; "Pensant una pista…" is good; "No és això." is good. The verdict "La resposta era C." goes with P4. The keyboard shortcuts exist but nothing on screen says so, and the start screen's `<select>` lists "5è de primària (nivell 0)": the "(nivell 0)" is for us, not for the child. The footer says "portàtil" on the board (reviewer M5); `teacher.html:54` says "1 sempre falla" under a student with 1/1 correct (seen on my teacher page for `web-probe`, reviewer I7).
- **Proposal**: `style.css`: `.meta`, `.status`, `.mastery`, `.hint .kind` ≥ 15 px, `.hint .time` and footer 14 px, and `.hint` body 20 px; `app.js` strings: "Àlies" → "Com et dius? (un nom inventat val)", "Domini per tema" → "Com vas per tema", "esglaó" → "pista" in the hint header ("Pista 2 · estratègia"), the `<option>` text without "(nivell n)" on the Catalan page; show the shortcut on the buttons as a small key cap ("Pista P", "Llegeix-lo en anglès T", "Següent N") with `kbd` styling; label the measured column from `RUNTIME` (`state.runtime` added by `webapp.state()`: "placa (mesurat)" on the board, "portàtil" in sim); teacher legend "1 ha començat". Test: `tests/test_assets.py` greps `style.css` for no `font-size: 1[0-3]px` outside `footer`/`dialog`, and `index.html` has `lang="ca"` (it does).
- **Impact (jury or student)**: medium; the student test (teach-measurement protocol) and the Project Hub screenshots both show this page.
- **Effort**: S.
- **Risk**: none; safe before the demo (CSS and strings only).
- **How to measure**: `getComputedStyle` of `.meta`, `.hint .kind`, `.status` ≥ 15 px in the browser; a native Catalan speaker reads the start screen and the hint header aloud.
- **Verified**: ran (sizes, strings on screen).

### P10. Polling that the board can afford: slower when idle, faster when busy, image by id (reviewer M6)
- **Where**: `assets/app.js:196` (`setInterval(poll, 500)`), `copilot/webapp.py:173-188` (`state()` rebuilds `_public_problem` with both languages and the LED frame per poll), `:342-345` (neighbour `image_b64` inlined into every state), `assets/teacher.html:103` (`setInterval(load, 3000)` → `teacher_report` = a SQLite pass every 3 s).
- **Problem / opportunity**: 2.02 req/s × 2.8 KB measured (3.7 KB with rung 0, 63 KB with a visual neighbour per reviewer M6) → 170 requests a minute for a page that changes a handful of times per problem. On the laptop a poll costs 0.7 ms; on the board the brick's Python process serves it on the same four cores that run the 5.6 tok/s generation during rung 3, which is when the page polls hardest. Not measured on the board; the order of magnitude (hundreds of JSON encodes of the problem text per minute) is what matters.
- **Proposal**: add a monotonically increasing `version` to `Session` (bump on every state change) and `/api/state?v=N` → `{"unchanged": true, "version": N}` (a few bytes) when nothing changed; `app.js` polls every 1,000 ms when idle, 300 ms while `busy`, and keeps rendering only on a new version (fold into P2's scheduler). Serve the neighbour picture through `/api/image/{id}` (the route exists for the current problem; add the id form) and send only `image_id` in the hint. Teacher page: 10 s interval. Tests: two `state()` calls with no change give the same `version`; `hint` bumps it; the neighbour hint dict has no `image_b64`.
- **Impact (jury or student)**: medium; it removes the only self-inflicted load on the board during the live hint, and the 63 KB bursts over `adb forward`.
- **Effort**: M.
- **Risk**: `/api/state` gains `version` and the neighbour hint loses `image_b64` (INTERFACES.md's state description: one line each). Safe before the demo only with P2 in place (same file); otherwise after.
- **How to measure**: `performance.getEntriesByType("resource")` in the browser: ≤ 1 `/api/state` per second idle, replies under 100 B when unchanged; on the board, `top` during rung 3 shows the app container's CPU under 5 %.
- **Verified**: ran (sizes and rates on the laptop), read only (board cost).

### P11. Docs that match the app: the endpoint table, `/teacher` on the board, the favicon 404
- **Where**: `docs/app-lab-app.md:28-41` (table says "all GET", lists `/api/student` as "choose the pseudonym and load their next problem", omits `/api/start`, `/api/reset`, `/api/translate`, `/api/estimate`, `/api/lang` semantics), `docs/app-lab-app.md:17` and `docs/deploy-board.md:114` (teacher view at `/teacher`), `copilot/hal/web.py:84-85` (the `/teacher` alias exists only in the sim server; `index.html:17` links `teacher.html`, which is right), `docs/bilingual-rung.md:22` ("press the pill … or the key `T`" is correct), `assets/index.html` (no `<link rel="icon">`, so every load logs a `/favicon.ico` 404 in the brick).
- **Problem / opportunity**: a jury member or a teammate following `docs/app-lab-app.md` on the board types `/teacher` and gets the brick's 404 (not verified on the board; the alias is sim-only by construction). The table is the public description of the API and it is out of date on five rows; after P3 it must say which rows are POST.
- **Proposal**: rewrite the table with method, path, side effect (yes/no), and the five missing rows; say "teacher view: `/teacher.html` (also `/teacher` in sim)"; add `<link rel="icon" href="data:image/svg+xml,...">` with a tiny inline SVG (no network) to `index.html` and `teacher.html`; add one paragraph "What fails how" listing the three degradations measured here (LLM down → card; embed down → rung 1 message on val ids; board unreachable → banner, after P2).
- **Impact (jury or student)**: low-medium (the README and the Project Hub article link here).
- **Effort**: S.
- **Risk**: none; safe before the demo.
- **How to measure**: every path in the table answers 200 in sim with the stated method; `curl -s -o /dev/null -w '%{http_code}' /favicon.ico` is no longer needed by the browser (no request in `performance` entries).
- **Verified**: ran (sim 200 on `/teacher`, 404 on favicon), read only (board).

## Table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | One visible budget for rung 3: never freeze the page for 60-120 s | high | M | yes |
| P2 | `app.js` error path: no crash on `{"error"}`, board-unreachable banner, bounded polling | high | M | yes |
| P3 | State-changing endpoints become POST | medium | S-M | only after one test on the board |
| P4 | Wrong answer: no letter, one more try, hints still open (C3) | high | M | yes, with the two tests |
| P5 | `/api/solution` needs an attempt or rung 3, plus a confirmation (C2) | high | S | yes |
| P6 | `start()` must not reset a known pseudonym; blank name is not `demo` (I4) | high | S | yes |
| P7 | LED "thinking" and rung; `Bridge.call` guarded | medium-high | M | guard yes; animation after one look at the matrix |
| P8 | Log what is swallowed, validate path parameters, no exception text to the page | medium | S-M | yes |
| P9 | Readable for a 10-year-old: sizes, words, visible shortcuts, no "portàtil" (M5, M8) | medium | S | yes |
| P10 | Polling the board can afford: version, idle/busy rates, image by id (M6) | medium | M | only together with P2 |
| P11 | Docs match the app: endpoint table, `/teacher` on the board, favicon | low-medium | S | yes |

## Discarded

- **Server-sent events or a WebSocket instead of polling**: the `web_ui` brick's support for streaming responses is unknown and cannot be tested off the board; the sim server is `http.server`. P10's version check gets most of the benefit with plain GET.
- **A service worker to cache the page for offline use**: the page is served by the board itself and already loads nothing external; a service worker adds a cache to debug during the demo for no gain.
- **Per-tab sessions (a token per browser)**: the app is one board, one student by design (`Session` docstring); two students at once would also need the trainer to serve two pending problems. Out of scope for the demo; P2 makes the second tab harmless instead.
- **Cancelling the previous problem's prefetch on "Següent"**: `urllib` has no cancel and llama-server has one slot; the only clean fix is a request id the server ignores. With the LLM gate closed on the Catalan page it never happens in the demo; noted under P1 as a known queue.
- **A client-side `fetch` of the LLM's `/health` to show a green/red dot**: the page must not reach 8081 directly (the servers listen on the board's loopback, not on the container's network: `docs/deploy-board.md:84-87`); a `/api/health` route proxied by `webapp.py` would be fine but is a nice-to-have behind P1's logging.
