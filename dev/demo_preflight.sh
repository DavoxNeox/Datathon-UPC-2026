#!/usr/bin/env bash
# Demo pre-flight: from the laptop, check the board end to end and leave it ready for the pitch.
#
#   dev/demo_preflight.sh            # check everything, rehearse both demo chains, forget the rehearsal aliases
#   dev/demo_preflight.sh --clean    # same, and first wipe data/students.db on the board (app stop / rm / start)
#   dev/demo_preflight.sh --no-chains   # skip the chain rehearsal (faster)
#
# Every line is "ok", "FAIL" or "note". A FAIL names the section of docs/demo/contingency.md to read.
# Needs adb on the laptop and the board on USB. Nothing is typed on the board by hand.
set -u
PORT=7002
BASE="http://127.0.0.1:$PORT"
REPO=/home/arduino/Datathon-UPC-2026
APP=user:math-copilot
CLEAN=0; CHAINS=1
for a in "$@"; do
  case "$a" in --clean) CLEAN=1;; --no-chains) CHAINS=0;; *) echo "unknown option $a"; exit 2;; esac
done
fails=0
ok()   { printf 'ok    %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*"; fails=$((fails + 1)); }
note() { printf 'note  %s\n' "$*"; }
board() { adb shell "$@" 2>/dev/null; }

echo "== 1. USB"
serial=$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device" {print $1}' | head -1)
if [ -n "$serial" ]; then ok "adb sees the board ($serial)"; else fail "adb does not see the board (contingency §2): cable, other port, 'adb kill-server'"; echo "stopping here"; exit 1; fi

echo "== 2. Services and models"
svc=$(board 'systemctl is-active math-llm math-embed math-relay' | tr '\n' ' ')
case "$svc" in "active active active ") ok "math-llm, math-embed, math-relay active";; *) fail "services: $svc (contingency §1)";; esac
for p in 8081 8082; do
  h=$(board "curl -s -m 5 http://127.0.0.1:$p/health")
  case "$h" in *'"ok"'*) ok "server :$p healthy";; *) fail "server :$p not healthy yet ($h); wait 30 s and rerun";; esac
done

echo "== 3. The app"
if [ "$CLEAN" = 1 ]; then
  note "wiping data/students.db on the board"
  board "export TMPDIR=/tmp; arduino-app-cli app stop $APP" >/dev/null
  board "rm -f $REPO/data/students.db"
fi
ps=$(board 'export TMPDIR=/tmp; arduino-app-cli app ps' | grep -c "$APP.*running")
if [ "$ps" = 0 ]; then
  note "app not running: starting it"
  board "export TMPDIR=/tmp; arduino-app-cli app start $APP" >/dev/null
fi
for i in $(seq 1 40); do
  board 'curl -sf -m 2 http://127.0.0.1:7000/api/state' >/dev/null && break
  sleep 2
done
if board 'curl -sf -m 2 http://127.0.0.1:7000/api/state' >/dev/null; then ok "app answers on the board"; else fail "app not answering after 80 s (contingency §3)"; fi
commit_board=$(board "cd $REPO && git rev-parse --short HEAD" | tr -d '\r')
commit_here=$(git rev-parse --short main 2>/dev/null)
if [ -n "$commit_board" ] && [ "$commit_board" = "$commit_here" ]; then ok "board at main $commit_board"; else note "board at $commit_board, laptop main at $commit_here (do not pull on the morning unless the controller says so)"; fi
if board "test -s $REPO/data/options_ocr.jsonl"; then ok "data/options_ocr.jsonl present (options as text)"; else note "data/options_ocr.jsonl missing: those scans show as pieces, nothing breaks"; fi

echo "== 4. The page on the laptop"
adb forward "tcp:$PORT" tcp:7000 >/dev/null 2>&1
for path in / /teacher.html /dashboard.html /api/state; do
  code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "$BASE$path")
  if [ "$code" = 200 ]; then ok "$BASE$path"; else fail "$BASE$path -> HTTP $code (adb forward again; contingency §3)"; fi
done

echo "== 5. LED matrix (look at the board: 2 s fully lit, then the tick)"
all=$(python3 -c 'print(";".join([",".join(["1"]*13)]*8))')
curl -s -o /dev/null -m 20 "$BASE/api/led/path/$all" && sleep 2
tick="0,0,0,0,0,0,0,0,0,0,0,1,0;0,0,0,0,0,0,0,0,0,0,1,1,0;0,0,0,0,0,0,0,0,0,1,1,0,0;1,1,0,0,0,0,0,0,1,1,0,0,0;0,1,1,0,0,0,0,1,1,0,0,0,0;0,0,1,1,0,0,1,1,0,0,0,0,0;0,0,0,1,1,1,1,0,0,0,0,0,0;0,0,0,0,1,1,0,0,0,0,0,0,0"
if curl -s -m 20 "$BASE/api/led/path/$tick" | grep -q '"ok"'; then ok "LED frames accepted by the sketch"; else fail "LED route failed (contingency §5)"; fi

if [ "$CHAINS" = 1 ]; then
  echo "== 6. The two demo chains (also warms the retrieval index)"
  python3 - "$BASE" <<'PY'
import json, sys, time, urllib.request
B = sys.argv[1]
EXPECT = {("Mariona1", 1): ("lvl-1_2024_2", "lvl-3_2019_18"), ("Guillem", 2): ("lvl-2_2020_4", "lvl-4_2010_12")}
def get(p):
    with urllib.request.urlopen(B + p, timeout=120) as r:
        return json.loads(r.read())
def wait_idle():
    t = time.time()
    while get("/api/state")["busy"]:
        time.sleep(0.2)
    return time.time() - t
bad = 0
for (name, level), (p1, p2) in EXPECT.items():
    get("/api/reset")
    s = get("/api/start/%s/%d" % (name, level))
    got1 = s["problem"]["id"]
    kinds, worst = [], 0.0
    for _ in range(2):
        get("/api/hint"); worst = max(worst, wait_idle())
        kinds.append(get("/api/state")["hints"][-1].get("kind"))
    get("/api/answer/A")          # any letter: the trainer only moves on after an answer; the alias is forgotten below
    time.sleep(0.3)
    s = get("/api/next")
    got2 = s["problem"]["id"]
    get("/api/reset")
    good = (got1, got2) == (p1, p2) and kinds[0] == "neighbour" and worst < 10
    print(("ok    " if good else "FAIL  ") + "%s %d: %s then %s; hints %s; slowest hint %.1f s" % (name, level, got1, got2, kinds, worst))
    bad += 0 if good else 1
sys.exit(1 if bad else 0)
PY
  [ $? = 0 ] || fails=$((fails + 1))
fi

echo "== 7. Aliases left in the teacher view"
students=$(curl -s -m 10 "$BASE/api/teacher" | python3 -c 'import json,sys; d=json.load(sys.stdin); s=d.get("students") or []; print(", ".join(x.get("student", x.get("name", str(x))) if isinstance(x, dict) else str(x) for x in s))' 2>/dev/null)
if [ -z "$students" ]; then ok "teacher view empty"; else note "aliases still listed: $students  (rerun with --clean to wipe them, or forget each from the page)"; fi

echo "== 8. Leave it ready"
curl -s -o /dev/null -m 10 "$BASE/api/reset"
echo
if [ "$fails" = 0 ]; then
  echo "READY. Open $BASE/ at 150 %, type the alias and the course, do NOT press Comença. Teacher view: $BASE/teacher.html  Dashboard: $BASE/dashboard.html"
else
  echo "$fails FAIL line(s) above: read the contingency section named on each."
fi
exit $fails
