"""Read config.env, the settings file shared with the board scripts."""
import os
import shlex

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path=os.path.join(ROOT, "config.env")):
    values = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, raw = line.split("=", 1)
            parts = shlex.split(raw, comments=True)
            values[key.strip()] = os.path.expanduser(parts[0]) if parts else ""
    # Environment variables win, so you can try a setting without editing the file
    for key in values:
        if key in os.environ:
            values[key] = os.environ[key]
    for key in ("LLM_HOST", "EMBED_HOST"):
        values[key] = resolve_host(values.get(key, "auto"))
    return values


# Docker's host-gateway alias that App Lab adds to the app container (extra_hosts). The model
# servers listen on 127.0.0.1 of the host; board/relay.py makes them reachable on that gateway.
APP_LAB_HOST_ALIAS = "msgpack-rpc-router"


def in_app_lab_container():
    """True inside the App Lab app container: APP_HOME is set by its compose file and /app is the mount."""
    return bool(os.environ.get("APP_HOME")) and os.path.isdir("/app")


def resolve_host(value):
    """"auto" = 127.0.0.1 on the host, the host-gateway alias inside the App Lab container."""
    value = (value or "auto").strip()
    if value.lower() != "auto":
        return value
    return APP_LAB_HOST_ALIAS if in_app_lab_container() else "127.0.0.1"


CONFIG = load()
