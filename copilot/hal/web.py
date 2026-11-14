"""The web server behind the student's page: the web_ui brick on the board, http.server in sim.

    routes = [("GET", "/api/answer/{letter}", answer), ...]   # handler(**path_params) -> dict
    serve(routes, assets_dir)                                 # blocks

Both backends serve the same `assets/` folder as static files and the same JSON endpoints,
so the app logic (copilot/webapp.py) never knows which one runs. Path parameters in braces
become keyword arguments, as the web_ui brick does. In sim the port is SIM_WEB_PORT
(config.env, default 7001: on macOS 7000 belongs to AirPlay); the board's brick uses 7000.
"""
import importlib
import json
import mimetypes
import os
import re
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ..config import CONFIG
from .led import runtime

SIM_PORT = int(CONFIG.get("SIM_WEB_PORT", 7001))


def serve(routes, assets_dir, host="127.0.0.1", port=None):
    if runtime() == "board":
        _serve_board(routes)
    else:
        _serve_sim(routes, assets_dir, host, port or SIM_PORT)


def _serve_board(routes):
    # App Lab provides these modules on the board only; loaded by name so the stdlib guard
    # (tests/test_stdlib_only.py) sees no App Lab import outside app/ and copilot/hal/led.py.
    web_ui = importlib.import_module("arduino.app_bricks.web_ui")
    app_utils = importlib.import_module("arduino.app_utils")
    ui = web_ui.WebUI()
    for method, path, handler in routes:
        ui.expose_api(method, path, handler)
    app_utils.App.run()


def _compile(path):
    pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path)
    return re.compile("^" + pattern + "/?$")


def _serve_sim(routes, assets_dir, host, port):
    compiled = [(method, _compile(path), handler) for method, path, handler in routes]
    assets_dir = os.path.abspath(assets_dir)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            line = fmt % args
            if "/api/state" not in line:  # the page polls it twice a second
                sys.stderr.write("  " + line + "\n")

        def send(self, code, body, kind="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def route(self, method):
            path = urllib.parse.unquote(self.path.split("?", 1)[0])
            for m, pattern, handler in compiled:
                match = pattern.match(path)
                if m == method and match:
                    try:
                        return self.send(200, handler(**match.groupdict()))
                    except Exception as error:  # the page must see the error, not a hung request
                        return self.send(500, {"error": f"{type(error).__name__}: {error}"})
            if method == "GET":
                return self.static(path)
            return self.send(404, {"error": "not found"})

        def static(self, path):
            if path in ("", "/"):
                path = "/index.html"
            if path == "/teacher":
                path = "/teacher.html"
            file = os.path.abspath(os.path.join(assets_dir, path.lstrip("/")))
            if not file.startswith(assets_dir + os.sep) or not os.path.isfile(file):
                return self.send(404, {"error": "not found"})
            kind = mimetypes.guess_type(file)[0] or "application/octet-stream"
            if kind.startswith("text/"):
                kind += "; charset=utf-8"
            with open(file, "rb") as f:
                return self.send(200, f.read(), kind)

        def do_GET(self):
            self.route("GET")

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            self.route("POST")

    print(f"Math copilot (sim) on http://{host}:{port}  (teacher view: /teacher)  Ctrl+C to stop", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
