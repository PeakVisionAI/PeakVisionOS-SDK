"""Repeatable control-plane acceptance checks."""
from __future__ import annotations

import time

from .http import GatewayClient


TERMINAL_STATUSES = {"completed", "failed", "stopped", "timeout", "cancelled"}


def run_acceptance(endpoint, token="", agent="mock-agent", timeout=30.0):
    client = GatewayClient(endpoint=endpoint, token=token, timeout=min(timeout, 15.0))
    started = time.time()
    health = client.health()
    if not health.get("ok"):
        raise AssertionError("health check did not return ok=true")
    stamp = str(int(started * 1000))
    workspace = client.create_workspace("SDK acceptance " + stamp)
    task = client.create_task(workspace["workspace_id"], "Complete SDK acceptance", agent=agent)
    run = client.create_run(agent, task_id=task["task_id"], workspace_id=workspace["workspace_id"], idempotency_key="acceptance-" + stamp)
    while run.get("status") not in TERMINAL_STATUSES:
        if time.time() - started > timeout:
            raise AssertionError("run did not reach a terminal state")
        time.sleep(0.2)
        run = client.run(run["run_id"])
    if run.get("status") != "completed" or run.get("exit_code", 0) != 0:
        raise AssertionError("acceptance run failed: %r" % run)
    logs = client.logs(agent)
    events = client.events(limit=200)
    event_types = {item.get("type") for item in events if item.get("run_id") == run["run_id"]}
    if not {"run.started", "run.completed"}.issubset(event_types):
        raise AssertionError("run lifecycle events are incomplete")
    return {"ok": True, "workspace_id": workspace["workspace_id"], "task_id": task["task_id"], "run_id": run["run_id"], "status": run["status"], "logs_present": bool(logs.get("logs")), "event_types": sorted(event_types)}
