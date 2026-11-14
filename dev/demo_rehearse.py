"""Replay the demo's click script against the web app and time every step.

Works against the laptop sim (SIM_WEB_PORT=7006 python3 python/main.py) or the board over
USB (adb forward tcp:7002 tcp:7000, then --base http://127.0.0.1:7002). Prints the real
seconds of each call and the board estimate the app keeps in /api/state "timeline".
Problems are shown by id, topic and level only: no text is printed.

    python3 dev/demo_rehearse.py --base http://127.0.0.1:7006 Mariona1 1 C A
    python3 dev/demo_rehearse.py --base http://127.0.0.1:7006 Guillem 2 A B --hints 2 --hints2 0

Positional: pseudonym, start level, letter for problem 1, letter for problem 2.
Each problem: `--hints N` rungs climbed before answering (default 2 for the first, 0 for the second).
"""
import argparse
import json
import sys
import time
import urllib.request

LIMIT = 10.0   # a demo step must stay under this many estimated board seconds


def call(base, path, timeout=90):
    started = time.perf_counter()
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        data = json.loads(r.read().decode())
    return data, time.perf_counter() - started


def wait_idle(base, timeout=90):
    """Poll /api/state until busy is false, like the page does."""
    started = time.perf_counter()
    while True:
        state, _ = call(base, "/api/state")
        if not state.get("busy"):
            return state, time.perf_counter() - started
        if time.perf_counter() - started > timeout:
            raise SystemExit("still busy after %.0f s" % timeout)
        time.sleep(0.2)


def show(label, seconds, state=None, extra=""):
    board = ""
    if state and state.get("timeline"):
        last = state["timeline"][-1]
        board = f"  board est {last['board_s']:.1f} s ({last['action']})"
        if last["board_s"] > LIMIT:
            board += "  <-- OVER %.0f s" % LIMIT
    print(f"{label:34} {seconds:6.2f} s real{board}  {extra}")


def problem_line(state):
    p = state.get("problem") or {}
    return f"{p.get('id')} {p.get('topic')} L{p.get('level')} image={p.get('has_image')}"


def one_problem(base, letter, hints, want_solution=False):
    state, _ = call(base, "/api/state")
    print("   problem:", problem_line(state))
    for i in range(hints):
        _, s = call(base, "/api/hint")
        state, waited = wait_idle(base)
        hint = state["hints"][-1]
        nb = hint.get("problem") or {}
        extra = f"rung {hint['rung']} {hint['kind']}"
        if nb:
            extra += f" -> {nb.get('id')} L{nb.get('level')} sim={nb.get('similarity')} image={'yes' if nb.get('image_b64') else 'no'} easier={hint.get('easier')}"
        if hint.get("manipulative"):
            extra += f" manipulative={hint['manipulative']}"
        show(f"   Pista ({i + 1})", s + waited, state, extra)
    if want_solution:
        _, s = call(base, "/api/solution")
        state, waited = wait_idle(base)
        show("   Solució", s + waited, state, state["hints"][-1]["kind"])
    state, s = call(base, f"/api/answer/{letter}")
    a = state.get("answer") or {}
    led_on = sum(sum(row) for row in state.get("led") or [])
    show(f"   Resposta {letter}", s, state,
         f"correct={a.get('correct')} label={a.get('label')} mastery {a.get('mastery_before')}->{a.get('mastery_after')} LED pixels on={led_on}")
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:7006")
    ap.add_argument("student"); ap.add_argument("level", type=int)
    ap.add_argument("letter1"); ap.add_argument("letter2")
    ap.add_argument("--hints", type=int, default=2)
    ap.add_argument("--hints2", type=int, default=0)
    ap.add_argument("--solution2", action="store_true", help="press Solució on problem 2 before answering")
    ap.add_argument("--no-reset", action="store_true")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    total = time.perf_counter()
    state, s = call(base, "/api/state")
    show("GET /api/state (page load)", s)
    state, s = call(base, f"/api/start/{args.student}/{args.level}")
    show(f"Comença {args.student} nivell {args.level}", s, state, problem_line(state))
    print("Problema 1")
    one_problem(base, args.letter1, args.hints)
    time.sleep(3.2)   # the tick or cross stays 3 s, then the mastery map returns
    state, s = call(base, "/api/next")
    show("Següent problema", s, state, problem_line(state))
    print("Problema 2")
    state = one_problem(base, args.letter2, args.hints2, args.solution2)
    time.sleep(3.2)
    state, s = call(base, "/api/state")
    print("mastery:", {k: v for k, v in state["mastery"].items() if v})
    teacher, s = call(base, "/api/teacher")
    show("Vista del professor", s, None, f"students={list(teacher.get('students', {}))}")
    if not args.no_reset:
        state, s = call(base, "/api/reset")
        show("Reinicia", s, state, f"started={state.get('started')} reset_supported={state.get('reset_supported')}")
    over = [t for t in state.get("timeline", []) if t["board_s"] > LIMIT]
    print(f"total {time.perf_counter() - total:.1f} s wall (includes two 3.2 s waits);"
          f" steps over {LIMIT:.0f} s estimated on the board: {len(over)}")
    print("timeline:", json.dumps(state.get("timeline"), ensure_ascii=False))


if __name__ == "__main__":
    main()
