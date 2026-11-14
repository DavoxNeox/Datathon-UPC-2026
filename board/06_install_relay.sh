#!/usr/bin/env bash
# Install the math-relay service: the model servers, which listen on 127.0.0.1 only, become
# reachable from the App Lab container through Docker's host-gateway address (docker0), and
# from nowhere else. Run it again after moving the repository.
source "$(dirname "$0")/common.sh"

command -v docker >/dev/null || die "docker not found: App Lab is not installed on this board"
ip -4 -o addr show docker0 >/dev/null 2>&1 || die "no docker0 interface yet. Start an App Lab app once, then run this again."

step "Installing math-relay.service"
sed -e "s|@USER@|$USER|g" -e "s|@REPO_DIR@|$REPO_DIR|g" \
    -e "s|@LLM_PORT@|$LLM_PORT|g" -e "s|@EMBED_PORT@|$EMBED_PORT|g" \
    "$REPO_DIR/board/systemd/math-relay.service" | sudo tee /etc/systemd/system/math-relay.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable math-relay
sudo systemctl restart math-relay
sleep 1
gateway="$(ip -4 -o addr show docker0 | awk '{print $4}' | cut -d/ -f1)"
for port in "$LLM_PORT" "$EMBED_PORT"; do
  curl -sf "http://$gateway:$port/health" >/dev/null && ok "port $port reachable on $gateway (and still not on the Wi-Fi address)" \
    || fail "port $port not answering on $gateway. See: journalctl -u math-relay -n 20"
done
ok "Next: start the app, arduino-app-cli app start user:math-copilot"
