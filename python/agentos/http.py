"""HTTP client for the AgentOS control plane and Remote Gateway.

The local :class:`AgentOS` client keeps its zero-dependency Unix Socket
transport.  ``GatewayClient`` is the public remote transport for control
plane operations (health, agents, runs, logs and events); primitive calls
remain local-only until a versioned remote primitive protocol is published.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class GatewayError(RuntimeError):
    """A remote Gateway request failed."""

    def __init__(self, message: str, status: Optional[int] = None,
                 retryable: bool = False):
        super().__init__(message)
        self.status = status
        self.retryable = retryable


@dataclass(frozen=True)
class GatewayRetryPolicy:
    """Bounded retry policy for idempotent control-plane requests."""

    max_attempts: int = 3
    backoff_seconds: float = 0.25
    max_backoff_seconds: float = 4.0
    retry_statuses: tuple = (408, 425, 429, 500, 502, 503, 504)

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.backoff_seconds < 0 or self.max_backoff_seconds < 0:
            raise ValueError("backoff values must be non-negative")


class GatewayClient:
    """Remote AgentOS control-plane client using HTTP/HTTPS.

    ``endpoint`` should point at a node API root, for example
    ``https://gateway.example/gateway/v1/nodes/node-1/api/v1``.  The token is
    sent only as a Bearer header and is never included in URLs or payloads.
    """

    def __init__(self, endpoint: Optional[str] = None, token: Optional[str] = None,
                 timeout: float = 15.0,
                 retry_policy: Optional[GatewayRetryPolicy] = None):
        endpoint = endpoint or os.environ.get("AGENTOS_ENDPOINT", "")
        if not endpoint:
            raise ValueError("endpoint is required (or set AGENTOS_ENDPOINT)")
        endpoint = endpoint.rstrip("/")
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("endpoint must use http:// or https://")
        self.endpoint = endpoint
        self.token = token if token is not None else os.environ.get("AGENTOS_TOKEN", "")
        self.timeout = float(timeout)
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.retry_policy = retry_policy or GatewayRetryPolicy()

    def _request(self, method: str, path: str = "", payload=None,
                 idempotency_key: Optional[str] = None):
        url = self.endpoint + "/" + path.lstrip("/")
        body = None
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=body, headers=headers, method=method)
        can_retry = method.upper() in {"GET", "HEAD", "OPTIONS"} or bool(idempotency_key)
        attempts = self.retry_policy.max_attempts if can_retry else 1
        for attempt in range(attempts):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    if not raw:
                        return {}
                    try:
                        return json.loads(raw.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise GatewayError("Gateway returned invalid JSON", response.status) from exc
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")
                try:
                    parsed = json.loads(detail)
                    detail = parsed.get("error", detail) if isinstance(parsed, dict) else detail
                except json.JSONDecodeError:
                    pass
                retryable = exc.code in self.retry_policy.retry_statuses
                if retryable and attempt + 1 < attempts:
                    self._sleep(attempt)
                    continue
                raise GatewayError(f"Gateway HTTP {exc.code}: {detail}", exc.code, retryable) from exc
            except (URLError, TimeoutError, OSError) as exc:
                reason = getattr(exc, "reason", str(exc))
                if attempt + 1 < attempts:
                    self._sleep(attempt)
                    continue
                raise GatewayError(f"Gateway unavailable: {reason}", retryable=True) from exc

        raise GatewayError("Gateway request exhausted retry policy", retryable=True)

    def _sleep(self, attempt: int):
        delay = min(self.retry_policy.backoff_seconds * (2 ** attempt),
                    self.retry_policy.max_backoff_seconds)
        if delay:
            time.sleep(delay)

    def health(self):
        return self._request("GET", "health")

    def agents(self):
        return self._request("GET", "agents").get("agents", [])

    def workspaces(self):
        return self._request("GET", "workspaces").get("workspaces", [])

    def create_workspace(self, name: str):
        if not name or not name.strip():
            raise ValueError("name is required")
        return self._request("POST", "workspaces", {"name": name.strip()})

    def tasks(self, workspace_id: Optional[str] = None):
        query = {"workspace_id": workspace_id} if workspace_id else {}
        path = "tasks" + ("?" + urlencode(query) if query else "")
        return self._request("GET", path).get("tasks", [])

    def create_task(self, workspace_id: str, title: str, description: str = "",
                    agent: str = ""):
        if not workspace_id or not workspace_id.strip():
            raise ValueError("workspace_id is required")
        if not title or not title.strip():
            raise ValueError("title is required")
        return self._request("POST", "tasks", {
            "workspace_id": workspace_id.strip(), "title": title.strip(),
            "description": description, "agent": agent,
        })

    def runs(self, workspace_id: Optional[str] = None):
        path = "runs"
        if workspace_id:
            path += "?workspace_id=" + quote(workspace_id, safe="")
        return self._request("GET", path).get("runs", [])

    def create_run(self, agent: str, task_id: str = "", workspace_id: str = "",
                   manifest_digest: str = "", idempotency_key: Optional[str] = None):
        if not agent or not agent.strip():
            raise ValueError("agent is required")
        return self._request("POST", "runs", {
            "agent": agent.strip(),
            "task_id": task_id,
            "workspace_id": workspace_id,
            "manifest_digest": manifest_digest,
        }, idempotency_key=idempotency_key)

    def run(self, run_id: str):
        if not run_id:
            raise ValueError("run_id is required")
        return self._request("GET", "runs/" + quote(run_id, safe=""))

    def stop_run(self, run_id: str):
        return self._request("POST", "runs/" + quote(run_id, safe="") + "/stop")

    def logs(self, agent: str):
        return self._request("GET", "agents/" + quote(agent, safe="") + "/logs")

    def events_page(self, limit: int = 200, after: int = 0):
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if after < 0:
            raise ValueError("after must be non-negative")
        return self._request("GET", f"events?limit={int(limit)}&after={int(after)}")

    def events(self, limit: int = 200, after: int = 0):
        return self.events_page(limit, after).get("events", [])

    def iter_events(self, after: int = 0, limit: int = 200, max_pages: Optional[int] = None):
        """Yield events in event-id order until the server has no new page."""
        cursor = after
        pages = 0
        while max_pages is None or pages < max_pages:
            page = self.events_page(limit, cursor)
            items = page.get("events", [])
            if not items:
                return
            for event in items:
                yield event
            ids = [event.get("event_id") for event in items if isinstance(event, dict)]
            next_cursor = max(ids) if ids and all(isinstance(value, int) for value in ids) else cursor
            if next_cursor <= cursor:
                return
            cursor = next_cursor
            pages += 1


class GatewayRegistryClient(GatewayClient):
    """Client for Gateway node registration and node-level snapshots."""

    def nodes(self):
        return self._request("GET", "nodes").get("nodes", [])

    def register_node(self, node_id: str, name: str, base_url: str,
                      token: str, capabilities=None):
        if not node_id or not name or not base_url or not token:
            raise ValueError("node_id, name, base_url and token are required")
        return self._request("POST", "nodes", {
            "node_id": node_id, "name": name, "base_url": base_url,
            "token": token, "capabilities": capabilities or {},
        })

    def rotate_node_token(self, node_id: str, token: str):
        if not node_id or not token:
            raise ValueError("node_id and token are required")
        return self._request("POST", "nodes/" + quote(node_id, safe="") + "/token",
                             {"token": token}, idempotency_key=None)

    def snapshot(self, node_id: str):
        if not node_id:
            raise ValueError("node_id is required")
        return self._request("GET", "nodes/" + quote(node_id, safe="") + "/snapshot")


RemoteGatewayClient = GatewayRegistryClient
