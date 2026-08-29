"""Dependency-free local PeakVisionOS control-plane simulator."""
from __future__ import annotations

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class MockState:
    def __init__(self):
        self.lock = threading.Lock()
        self.agents = [{"name": "mock-agent", "status": "inactive"}]
        self.workspaces = []
        self.tasks = []
        self.runs = []
        self.events = []

    @staticmethod
    def identifier(prefix):
        return prefix + "_" + uuid.uuid4().hex[:12]

    def event(self, event_type, run_id, **payload):
        item = {
            "event_id": len(self.events) + 1,
            "type": event_type,
            "run_id": run_id,
            "timestamp": time.time(),
            **payload,
        }
        self.events.append(item)
        return item


def make_handler(state, token=""):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PeakVisionOSMock/1.0"

        def log_message(self, *_args):
            return

        def _json(self, status, value):
            raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _authorized(self, path):
            if path == "/api/v1/health" or not token:
                return True
            return self.headers.get("Authorization") == "Bearer " + token

        def _body(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                value = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(value, dict):
                    raise ValueError("body must be an object")
                return value
            except (ValueError, json.JSONDecodeError):
                self._json(400, {"error": {"code": "invalid_json", "message": "JSON object required"}})
                return None

        def _path(self):
            parsed = urlparse(self.path)
            return parsed.path, parse_qs(parsed.query)

        def _guard(self, path):
            if not self._authorized(path):
                self._json(401, {"error": {"code": "unauthorized", "message": "invalid bearer token"}})
                return False
            return True

        def do_GET(self):  # noqa: N802
            path, query = self._path()
            if not self._guard(path):
                return
            if path == "/api/v1/health":
                return self._json(200, {"ok": True, "service": "pvos-mock", "version": "1.0"})
            with state.lock:
                if path == "/api/v1/agents":
                    return self._json(200, {"agents": list(state.agents)})
                if path == "/api/v1/workspaces":
                    return self._json(200, {"workspaces": list(state.workspaces)})
                if path == "/api/v1/tasks":
                    items = list(state.tasks)
                    if query.get("workspace_id"):
                        items = [item for item in items if item["workspace_id"] == query["workspace_id"][0]]
                    return self._json(200, {"tasks": items})
                if path == "/api/v1/runs":
                    items = list(state.runs)
                    if query.get("workspace_id"):
                        items = [item for item in items if item.get("workspace_id") == query["workspace_id"][0]]
                    return self._json(200, {"runs": items})
                if path.startswith("/api/v1/runs/"):
                    run_id = path.rsplit("/", 1)[-1]
                    run = next((item for item in state.runs if item["run_id"] == run_id), None)
                    return self._json(200, run) if run else self._json(404, {"error": {"code": "not_found", "message": "run not found"}})
                if path.startswith("/api/v1/agents/") and path.endswith("/logs"):
                    name = path.split("/")[-2]
                    return self._json(200, {"agent": name, "logs": "mock run completed\n"})
                if path == "/api/v1/events":
                    after = int(query.get("after", ["0"])[0])
                    limit = min(int(query.get("limit", ["200"])[0]), 1000)
                    items = [item for item in state.events if item["event_id"] > after][:limit]
                    next_after = items[-1]["event_id"] if items else after
                    return self._json(200, {"events": items, "after": next_after})
            return self._json(404, {"error": {"code": "not_found", "message": "route not found"}})

        def do_POST(self):  # noqa: N802
            path, _query = self._path()
            if not self._guard(path):
                return
            body = self._body()
            if body is None:
                return
            with state.lock:
                if path == "/api/v1/workspaces":
                    if not str(body.get("name", "")).strip():
                        return self._json(400, {"error": {"code": "validation_error", "message": "name is required"}})
                    item = {"workspace_id": state.identifier("ws"), "name": body["name"], "created_at": time.time()}
                    state.workspaces.append(item)
                    return self._json(201, item)
                if path == "/api/v1/tasks":
                    if not body.get("workspace_id") or not body.get("title"):
                        return self._json(400, {"error": {"code": "validation_error", "message": "workspace_id and title are required"}})
                    item = {"task_id": state.identifier("task"), "workspace_id": body["workspace_id"], "title": body["title"], "description": body.get("description", ""), "agent": body.get("agent", ""), "status": "created"}
                    state.tasks.append(item)
                    return self._json(201, item)
                if path == "/api/v1/runs":
                    if not body.get("agent"):
                        return self._json(400, {"error": {"code": "validation_error", "message": "agent is required"}})
                    run_id = state.identifier("run")
                    item = {"run_id": run_id, "agent": body["agent"], "task_id": body.get("task_id", ""), "workspace_id": body.get("workspace_id", ""), "manifest_digest": body.get("manifest_digest", ""), "status": "completed", "exit_code": 0}
                    state.runs.append(item)
                    state.event("run.started", run_id)
                    state.event("run.completed", run_id, exit_code=0)
                    return self._json(201, item)
                if path.startswith("/api/v1/runs/") and path.endswith("/stop"):
                    run_id = path.split("/")[-2]
                    run = next((item for item in state.runs if item["run_id"] == run_id), None)
                    if not run:
                        return self._json(404, {"error": {"code": "not_found", "message": "run not found"}})
                    run["status"] = "stopped"
                    state.event("run.stopped", run_id)
                    return self._json(200, run)
            return self._json(404, {"error": {"code": "not_found", "message": "route not found"}})

    return Handler


def create_mock_server(host="127.0.0.1", port=17680, token=""):
    state = MockState()
    server = ThreadingHTTPServer((host, port), make_handler(state, token))
    server.state = state
    return server


def serve(host="127.0.0.1", port=17680, token=""):
    server = create_mock_server(host, port, token)
    print("PeakVisionOS mock server: http://%s:%s/api/v1" % server.server_address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
