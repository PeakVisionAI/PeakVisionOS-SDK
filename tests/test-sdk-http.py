#!/usr/bin/env python3
"""Contract test for the standalone Python GatewayClient."""
import json
import pathlib
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from agentos import GatewayClient, GatewayError  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):  # noqa: N802
        assert self.headers.get("Authorization") == "Bearer test-token"
        if self.path.endswith("/health"):
            return self._send(200, {"ok": True})
        if self.path.endswith("/agents"):
            return self._send(200, {"agents": [{"name": "demo"}]})
        if self.path.startswith("/api/v1/runs"):
            return self._send(200, {"runs": [{"run_id": "run-1"}]})
        if self.path.startswith("/api/v1/events"):
            return self._send(200, {"events": [{"type": "run.completed"}]})
        if self.path.endswith("/agents/demo/logs"):
            return self._send(200, {"logs": "ok"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        assert self.headers.get("Authorization") == "Bearer test-token"
        if self.path.endswith("/runs"):
            return self._send(201, {"run_id": "run-2"})
        if self.path.endswith("/runs/run-2/stop"):
            return self._send(200, {"status": "stopped"})
        return self._send(404, {"error": "not found"})

    def log_message(self, *_):
        pass


server = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
client = GatewayClient(f"http://127.0.0.1:{server.server_port}/api/v1", token="test-token")
assert client.health()["ok"] is True
assert client.agents()[0]["name"] == "demo"
assert client.runs()[0]["run_id"] == "run-1"
assert client.create_run("demo")["run_id"] == "run-2"
assert client.stop_run("run-2")["status"] == "stopped"
assert client.logs("demo")["logs"] == "ok"
assert client.events()[0]["type"] == "run.completed"
server.shutdown()

try:
    GatewayClient("http://127.0.0.1:1/api/v1", timeout=0.1).health()
except GatewayError:
    pass
else:
    raise AssertionError("unreachable Gateway must raise GatewayError")
print("SDK HTTP contract: OK")
