#!/usr/bin/env python3
"""Contract test for the standalone Python GatewayClient."""
import asyncio
import json
import pathlib
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from pvos import (AsyncGatewayClient, GatewayClient, GatewayError, GatewayRegistryClient,
                     GatewayRetryPolicy)  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    retry_count = 0

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
        if self.path.endswith("/runs/run-1"):
            return self._send(200, {"run_id": "run-1", "agent": "demo", "status": "completed"})
        if self.path.startswith("/api/v1/runs"):
            return self._send(200, {"runs": [{"run_id": "run-1"}]})
        if self.path.startswith("/api/v1/events"):
            return self._send(200, {"events": [{"event_id": 1, "type": "run.completed"}], "after": 0})
        if self.path.endswith("/nodes"):
            return self._send(200, {"nodes": [{"node_id": "node-1", "name": "AMD395"}]})
        if self.path.endswith("/snapshot"):
            return self._send(200, {"health": {"ok": True}, "agents": [], "runs": [], "events": []})
        if self.path.endswith("/agents/demo/logs"):
            return self._send(200, {"logs": "ok"})
        if self.path.startswith("/api/v1/workspaces"):
            return self._send(200, {"workspaces": [{"workspace_id": "ws-1", "name": "demo"}]})
        if self.path.startswith("/api/v1/tasks"):
            return self._send(200, {"tasks": [{"task_id": "task-1", "workspace_id": "ws-1", "title": "demo"}]})
        if self.path.endswith("/retry"):
            Handler.retry_count += 1
            if Handler.retry_count == 1:
                return self._send(503, {"error": "temporary"})
            return self._send(200, {"ok": True})
        if self.path.endswith("/structured-error"):
            self.send_response(429)
            raw = json.dumps({"error": {"code": "rate_limited", "message": "slow down",
                                         "details": {"limit": 10}, "retry_after": 2}}).encode()
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Request-Id", "req-123")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            return self.wfile.write(raw)
        return self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        assert self.headers.get("Authorization") == "Bearer test-token"
        if self.path.endswith("/runs"):
            return self._send(201, {"run_id": "run-2"})
        if self.path.endswith("/nodes"):
            return self._send(201, {"node_id": "node-2", "name": "new"})
        if self.path.startswith("/api/v1/workspaces"):
            return self._send(201, {"workspace_id": "ws-2", "name": "new"})
        if self.path.endswith("/tasks"):
            return self._send(201, {"task_id": "task-2", "title": "new"})
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
assert client.workspaces()[0]["workspace_id"] == "ws-1"
assert client.create_workspace("new")["workspace_id"] == "ws-2"
assert client.tasks("ws-1")[0]["task_id"] == "task-1"
assert client.create_task("ws-1", "new")["task_id"] == "task-2"
assert client.create_run("demo")["run_id"] == "run-2"
assert client.run("run-1")["run_id"] == "run-1"
assert client.stop_run("run-2")["status"] == "stopped"
assert client.logs("demo")["logs"] == "ok"
assert client.events()[0]["type"] == "run.completed"
assert client.events_page()["events"]
assert list(client.iter_events(max_pages=1))
assert client._request("GET", "retry")["ok"] is True
try:
    client._request("GET", "structured-error")
except GatewayError as exc:
    assert exc.code == "rate_limited"
    assert exc.message == "slow down"
    assert exc.status == 429
    assert exc.retryable is True
    assert exc.request_id == "req-123"
    assert exc.details == {"limit": 10}
    assert exc.retry_after == 2
else:
    raise AssertionError("structured HTTP errors must remain machine-readable")
registry = GatewayRegistryClient(
    f"http://127.0.0.1:{server.server_port}/gateway/v1",
    token="test-token",
    retry_policy=GatewayRetryPolicy(backoff_seconds=0),
)
assert registry.nodes()[0]["node_id"] == "node-1"
assert registry.register_node("node-2", "new", "http://node", "secret")["node_id"] == "node-2"
assert registry.snapshot("node-1")["health"]["ok"] is True


async def check_async_parity():
    async_client = AsyncGatewayClient(
        f"http://127.0.0.1:{server.server_port}/gateway/v1",
        token="test-token",
        retry_policy=GatewayRetryPolicy(backoff_seconds=0),
    )
    assert (await async_client.nodes())[0]["node_id"] == "node-1"
    assert (await async_client.snapshot("node-1"))["health"]["ok"] is True


asyncio.run(check_async_parity())
try:
    client.create_run("")
except ValueError:
    pass
else:
    raise AssertionError("empty agent must be rejected")
server.shutdown()

try:
    GatewayClient("http://127.0.0.1:1/api/v1", timeout=0.1).health()
except GatewayError:
    pass
else:
    raise AssertionError("unreachable Gateway must raise GatewayError")
print("SDK HTTP contract: OK")
