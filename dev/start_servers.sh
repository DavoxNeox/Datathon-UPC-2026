#!/usr/bin/env bash
# Laptop only: run the board's two llama.cpp servers on this computer, with the same
# commit, models, flags and ports as the board (README steps 3 to 7), so code written
# here moves to the board unchanged.
#
#   dev/start_servers.sh            # build llama.cpp (once), download the models (once), start both
#   dev/start_servers.sh --stop     # stop the servers this script started
#   dev/start_servers.sh --status   # are they up?
#
# CPU only, 4 threads: no Metal, BLAS, CUDA or Vulkan, so the answers stay as close as
# possible to the board's. The latency here is NOT the board's: copilot/board_clock.py
# estimates it from the token counts. macOS and Linux; on Windows use dev/start_servers.ps1.
#
# Overrides, as environment variables: LLM_PORT, EMBED_PORT (when a port is taken on your
# laptop), LLAMA_CPP_DIR, MODELS_DIR, BUILD_JOBS.

# Remember overrides before config.env sets the board's values
_LLM_PORT="${LLM_PORT:-}"; _EMBED_PORT="${EMBED_PORT:-}"
_LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-}"; _MODELS_DIR="${MODELS_DIR:-}"
source "$(dirname "$0")/../board/common.sh"
[ -n "$_LLM_PORT" ] && LLM_PORT="$_LLM_PORT"
[ -n "$_EMBED_PORT" ] && EMBED_PORT="$_EMBED_PORT"
if [ -n "$_LLAMA_CPP_DIR" ]; then LLAMA_CPP_DIR="${_LLAMA_CPP_DIR/#\~/$HOME}"; LLAMA_SERVER="$LLAMA_CPP_DIR/build/bin/llama-server"; fi
if [ -n "$_MODELS_DIR" ]; then MODELS_DIR="${_MODELS_DIR/#\~/$HOME}"; LLM_PATH="$MODELS_DIR/$LLM_FILE"; EMBED_PATH="$MODELS_DIR/$EMBED_FILE"; fi

RUN_DIR="$REPO_DIR/dev/run"; LOG_DIR="$REPO_DIR/dev/logs"
mkdir -p "$RUN_DIR" "$LOG_DIR"
CPU_MARK="$LLAMA_CPP_DIR/build/.cpu-only"   # proves the build has no GPU backend

sha256() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
ncpu() { if command -v nproc >/dev/null; then nproc; else sysctl -n hw.ncpu; fi; }
port_owner() { lsof -nP -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1" (pid "$2")"}' || true; }  # lsof exits 1 when the port is free
healthy() { curl -sf "http://127.0.0.1:$1/health" >/dev/null 2>&1; }

stop_servers() {
  step "Stopping the servers started by this script"
  for name in llm embed; do
    pidfile="$RUN_DIR/$name.pid"
    if [ -f "$pidfile" ]; then
      pid="$(cat "$pidfile")"
      if kill -0 "$pid" 2>/dev/null; then kill "$pid" && ok "$name (pid $pid) stopped"; else warn "$name (pid $pid) was not running"; fi
      rm -f "$pidfile"
    fi
  done
}

status() {
  step "Servers"
  for pair in "LLM:$LLM_PORT" "embeddings:$EMBED_PORT"; do
    name="${pair%%:*}"; port="${pair##*:}"
    if healthy "$port"; then ok "$name answers on 127.0.0.1:$port ($(port_owner "$port"))"
    elif [ -n "$(port_owner "$port")" ]; then warn "$name: port $port is taken by $(port_owner "$port"), and it does not answer /health"
    else fail "$name: nothing on port $port"; fi
  done
}

case "${1:-}" in
  --stop) stop_servers; exit 0 ;;
  --status) status; exit 0 ;;
  "") ;;
  *) die "unknown option $1. Use --stop or --status." ;;
esac

step "Tools"
for tool in git cmake curl python3 lsof; do command -v "$tool" >/dev/null || die "$tool is missing. macOS: brew install $tool. Debian: sudo apt-get install $tool"; done
ok "git, cmake, curl, python3, lsof"

short="${LLAMA_CPP_REF:0:7}"
if [ -x "$LLAMA_SERVER" ] && "$LLAMA_SERVER" --version 2>&1 | grep -q "$short" && [ -f "$CPU_MARK" ]; then
  ok "llama-server already built at commit $short, CPU only"
else
  step "Getting llama.cpp at commit $short"
  if [ -d "$LLAMA_CPP_DIR/.git" ] && [ ! -f "$CPU_MARK" ] && [ -d "$LLAMA_CPP_DIR/build" ]; then
    warn "$LLAMA_CPP_DIR/build exists but was not built by this script (maybe with a GPU backend). Rebuilding it CPU only."
    rm -rf "$LLAMA_CPP_DIR/build"
  fi
  if [ ! -d "$LLAMA_CPP_DIR/.git" ]; then
    git init -q "$LLAMA_CPP_DIR"
    git -C "$LLAMA_CPP_DIR" remote add origin "$LLAMA_CPP_REPO"
  fi
  git -C "$LLAMA_CPP_DIR" fetch --depth 1 origin "$LLAMA_CPP_REF"
  git -C "$LLAMA_CPP_DIR" checkout -q --detach FETCH_HEAD
  ok "source at $(git -C "$LLAMA_CPP_DIR" rev-parse --short HEAD)"

  step "Configuring: CPU only, no GPU backend"
  cmake -S "$LLAMA_CPP_DIR" -B "$LLAMA_CPP_DIR/build" -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON \
    -DGGML_METAL=OFF -DGGML_BLAS=OFF -DGGML_ACCELERATE=OFF -DGGML_CUDA=OFF -DGGML_VULKAN=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF

  jobs="${BUILD_JOBS:-$(ncpu)}"
  step "Building llama-server and llama-cli with $jobs jobs"
  start=$(date +%s)
  cmake --build "$LLAMA_CPP_DIR/build" --config Release -j"$jobs" --target llama-server llama-cli
  touch "$CPU_MARK"
  ok "built in $(( $(date +%s) - start )) s: $("$LLAMA_SERVER" --version 2>&1 | grep -m1 version)"
fi

download() {
  local repo="$1" revision="$2" file="$3" sha="$4"
  local target="$MODELS_DIR/$file"   # separate line: $file is not set yet on the line above
  step "$file"
  if [ -f "$target" ] && [ "$(sha256 "$target")" = "$sha" ]; then ok "already downloaded and verified"; return; fi
  curl -L --fail --progress-bar --continue-at - -o "$target.part" "https://huggingface.co/$repo/resolve/$revision/$file"
  if [ "$(sha256 "$target.part")" = "$sha" ]; then mv "$target.part" "$target"; ok "verified: $(du -h "$target" | cut -f1)"
  else rm -f "$target.part"; die "$file doesn't match its SHA256. Run the script again."; fi
}
mkdir -p "$MODELS_DIR"
download "$LLM_REPO" "$LLM_REVISION" "$LLM_FILE" "$LLM_SHA256"
download "$EMBED_REPO" "$EMBED_REVISION" "$EMBED_FILE" "$EMBED_SHA256"

# The flags below are the board's: board/systemd/math-llm.service and math-embed.service
launch() {
  local name="$1" port="$2"; shift 2
  if healthy "$port"; then ok "$name already answers on port $port"; return; fi
  local owner; owner="$(port_owner "$port")"
  [ -n "$owner" ] && die "port $port is taken by $owner. Stop it, or run with $(echo "$name" | tr a-z A-Z)_PORT=<free port>."
  nohup "$LLAMA_SERVER" "$@" >"$LOG_DIR/$name.log" 2>&1 &
  echo $! >"$RUN_DIR/$name.pid"
  wait_for_health "$port" 120 || die "$name didn't start. See $LOG_DIR/$name.log"
  ok "$name on 127.0.0.1:$port (pid $(cat "$RUN_DIR/$name.pid"), log $LOG_DIR/$name.log)"
}
step "Starting the language model (port $LLM_PORT)"
launch llm "$LLM_PORT" -m "$LLM_PATH" --host 127.0.0.1 --port "$LLM_PORT" --threads "$LLM_THREADS" --ctx-size "$LLM_CTX" \
  --parallel 1 --cache-ram 0 --ctx-checkpoints 2 --jinja --reasoning off --reasoning-budget 0 --alias "$LLM_ALIAS"
step "Starting the embedding model (port $EMBED_PORT)"
launch embed "$EMBED_PORT" -m "$EMBED_PATH" --embedding --host 127.0.0.1 --port "$EMBED_PORT" --threads "$EMBED_THREADS" \
  --ctx-size "$EMBED_CTX" --parallel 1 --cache-ram 0 --batch-size "$EMBED_CTX" --ubatch-size "$EMBED_CTX"

step "Hello world (README step 5.5), with the board estimate"
RESPONSE="$(curl -s "http://127.0.0.1:$LLM_PORT/v1/chat/completions" -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello! What is 7 times 8? Answer in one sentence."}], "temperature": 0, "max_tokens": 40}')"
RESPONSE="$RESPONSE" REPO_DIR="$REPO_DIR" python3 - <<'PY'
import json, os, sys
sys.path.insert(0, os.environ["REPO_DIR"])
r = json.loads(os.environ["RESPONSE"]); t = r["timings"]
print("  answer:", r["choices"][0]["message"]["content"].strip())
print(f"  laptop: read {t['prompt_n']} tok at {t['prompt_per_second']:.0f} tok/s, wrote {t['predicted_n']} tok at {t['predicted_per_second']:.0f} tok/s")
from copilot.board_clock import estimate
print(f"  board estimate: {estimate(t):.1f} s (the README measured about 4 s for this request on the board)")
PY
ok "Both servers run. Stop them with: dev/start_servers.sh --stop"
