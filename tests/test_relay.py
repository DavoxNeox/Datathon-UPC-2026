import http.server
import json
import socket
import threading
import unittest
import urllib.request

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "board"))
import relay  # noqa: E402


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"status": "ok", "path": self.path}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class RelayTest(unittest.TestCase):
    def test_forwards_http_to_the_target(self):
        upstream = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=upstream.serve_forever, daemon=True).start()
        port = upstream.server_address[1]
        # The relay listens on the loopback alias 127.0.0.2 (same port) and forwards to 127.0.0.1
        listen = "127.0.0.2" if sys.platform.startswith("linux") else "127.0.0.1"
        if listen == "127.0.0.1":
            self.skipTest("needs a second loopback address to relay the same port (Linux)")
        ready = threading.Event()
        threading.Thread(target=relay.serve, args=(listen, port, "127.0.0.1", lambda p: ready.set()), daemon=True).start()
        self.assertTrue(ready.wait(2))
        with urllib.request.urlopen(f"http://{listen}:{port}/health", timeout=3) as r:
            self.assertEqual(json.loads(r.read())["status"], "ok")
        upstream.shutdown()

    def test_resolve_listen_accepts_addresses(self):
        self.assertEqual(relay.resolve_listen("172.17.0.1"), "172.17.0.1")

    def test_pump_copies_both_ways(self):
        a1, a2 = socket.socketpair()
        b1, b2 = socket.socketpair()
        t = threading.Thread(target=relay.pump, args=(a2, b1), daemon=True)
        t.start()
        a1.sendall(b"ping")
        self.assertEqual(b2.recv(4), b"ping")
        b2.sendall(b"pong")
        self.assertEqual(a1.recv(4), b"pong")
        a1.close(); b2.close()
        t.join(2)


if __name__ == "__main__":
    unittest.main()
