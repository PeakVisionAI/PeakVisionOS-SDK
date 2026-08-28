"""HTTP client for the AgentOS control plane and Remote Gateway.

The local :class:`AgentOS` client keeps its zero-dependency Unix Socket
transport.  ``GatewayClient`` is the public remote transport for control
plane operations (health, agents, runs, logs and events); primitive calls
remain local-only until a versioned remote primitive protocol is published.
"""
from __future__ import annotations

import json
import os
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GatewayError(RuntimeError):
    """A remote Gateway request failed."""

    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


class GatewayClient:
    """Remote AgentOS control-plane client using HTTP/HTTPS.

    ``endpoint`` should point at a node API root, for example
    ``https://gateway.example/gateway/v1/nodes/node-1/api/v1``.  The token is
    sent only as a Bearer header and is never included in URLs or payloads.
    """

    def __init__(self, endpoint: Optional[str] = None, token: Optional[str] = None,
                 timeout: float = 15.0):
        endpoint = endpoint or os.environ.get("AGENTOS_ENDPOINT", "")
        if not endpoint:
            raise ValueError("endpoint is required (or set AGENTOS_ENDPOINT)")
        endpoint = endpoint.rstrip("/")
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("endpoint must use http:// or https://")
        self.endpoint = endpoint
        self.token = token if token is not None else os.environ.get("AGENTOS_TOKEN", "")
        self.timeout = float(timeout)

    def _request(self, method: str, path: str = "", payload=None):
        url = self.endpoint + "/" + path.lstrip("/")
        body = None
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            try:
                detail = json.loads(detail).get("error", detail)
            except json.JSONDecodeError:
                pass
            raise GatewayError(f"Gateway HTTP {exc.code}: {detail}", exc.code) from exc
        except (URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", str(exc))
            raise GatewayError(f"Gateway unavailable: {reason}") from exc

    def health(self):
        return self._request("GET", "health")

    def agents(self):
        return self._request("GET", "agents").get("agents", [])

    def runs(self, workspace_id: Optional[str] = None):
        path = "runs"
        if workspace_id:
            path += "?workspace_id=" + quote(workspace_id, safe="")
        return self._request("GET", path).get("runs", [])

    def create_run(self, agent: str, task_id: str = "", workspace_id: str = "",
                   manifest_digest: str = ""):
        return self._request("POST", "runs", {
            "agent": agent,
            "task_id": task_id,
            "workspace_id": workspace_id,
            "manifest_digest": manifest_digest,
        })

    def stop_run(self, run_id: str):
        return self._request("POST", "runs/" + quote(run_id, safe="") + "/stop")

    def logs(self, agent: str):
        return self._request("GET", "agents/" + quote(agent, safe="") + "/logs")

    def events(self, limit: int = 200, after: int = 0):
        return self._request("GET", f"events?limit={int(limit)}&after={int(after)}").get("events", [])
