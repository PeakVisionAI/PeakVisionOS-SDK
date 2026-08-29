"""Offline Unix Socket primitive simulator for SDK development and CI.

The simulator deliberately follows the AgentOS v1 line protocols. It is not a
model or a security boundary; it only makes request shape and error handling
testable on a workstation without AgentOS daemons or accelerator hardware.
"""
from __future__ import annotations

import json
import os
import pathlib
import socket
import socketserver
import tempfile
import threading


_ENV = {
    "agent": "AGENTOS_AGENTD_SOCK",
    "infer": "AGENTOS_INFERD_SOCK",
    "memory": "AGENTOS_MEMORYD_SOCK",
    "fs": "AGENTOS_FSD_SOCK",
    "agentrund": "AGENTOS_AGENTRUND_SOCK",
    "ctx": "AGENTOS_CTXD_SOCK",
}


class _UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True


class PrimitiveMock:
    """Context manager that exposes fake agentd/inferd/memoryd/fsd sockets."""

    def __init__(self, failures=None):
        self.failures = failures or {}
        self.requests = {name: [] for name in _ENV}
        self._servers = []
        self._directory = None
        self._previous = {}
        self._memory = []
        self._files = {}

    def __enter__(self):
        self._directory = tempfile.TemporaryDirectory(prefix="pvos-primitives-")
        for name, env in _ENV.items():
            path = str(pathlib.Path(self._directory.name) / (name + ".sock"))
            self._previous[env] = os.environ.get(env)
            os.environ[env] = path
            handler = self._handler(name)
            server = _UnixServer(path, handler)
            self._servers.append(server)
            threading.Thread(target=server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *_exc):
        for server in self._servers:
            server.shutdown()
            server.server_close()
        for env, value in self._previous.items():
            if value is None:
                os.environ.pop(env, None)
            else:
                os.environ[env] = value
        if self._directory:
            self._directory.cleanup()

    def _handler(self, name):
        owner = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                raw = self.rfile.read()
                if b"\n" not in raw:
                    self.wfile.write(b'{"error":{"code":"invalid_request","message":"newline required"}}')
                    return
                line, body = raw.split(b"\n", 1)
                command = line.decode("utf-8", "replace").strip()
                owner.requests[name].append(command)
                method_parts = command.split(" ", 1)
                method = method_parts[0].lstrip("@").split(" ")[-1]
                if name == "infer" and command.startswith("@"):
                    method = command.split(" ", 2)[1]
                failure = owner.failures.get(name, {}).get(method) if isinstance(owner.failures.get(name), dict) else None
                if failure:
                    self.wfile.write(json.dumps({"error": {"code": failure, "message": failure}}).encode())
                    return
                if name == "agent":
                    value = {"ok": True, "mem_total_kb": 1024, "cpu_count": 4} if method == "system" else {"ok": True}
                    self.wfile.write(json.dumps(value).encode())
                    return
                if name == "infer":
                    prompt = command.split(" ", 2)[-1] if method == "chat" else ""
                    value = {"response": "mock: " + prompt} if method == "chat" else {"ok": True, "models": ["mock"]}
                    self.wfile.write(json.dumps(value).encode())
                    return
                if name == "memory":
                    if method == "write":
                        text = command.split(" ", 1)[1] if " " in command else ""
                        owner._memory.append(text)
                        self.wfile.write(json.dumps({"ok": True, "id": str(len(owner._memory))}).encode())
                    elif method == "recall":
                        hits = [{"text": item, "score": 1.0} for item in owner._memory]
                        self.wfile.write(json.dumps({"hits": hits, "count": len(hits)}).encode())
                    else:
                        self.wfile.write(b'{"ok":true}')
                    return
                if name == "fs":
                    if method == "put":
                        parts = command.split(" ", 2)
                        file_id = "file-" + str(len(owner._files) + 1)
                        name_value = parts[1] if len(parts) > 1 else "file"
                        expected = int(parts[2]) if len(parts) > 2 else len(body)
                        owner._files[file_id] = (name_value, body[:expected])
                        self.wfile.write(json.dumps({"ok": True, "id": file_id, "name": name_value}).encode())
                    elif method == "get":
                        file_id = command.split(" ", 1)[1]
                        self.wfile.write(owner._files.get(file_id, ("", b""))[1])
                    elif method == "search":
                        hits = [{"id": fid, "name": item[0], "score": 1.0} for fid, item in owner._files.items()]
                        self.wfile.write(json.dumps({"hits": hits, "count": len(hits)}).encode())
                    else:
                        self.wfile.write(b'{"ok":true}')
                    return
                self.wfile.write(b'{"ok":true}')

        return Handler
