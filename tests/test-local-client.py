#!/usr/bin/env python3
"""Contracts for local Unix Socket calls and the offline primitive simulator."""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from pvos import AgentOS, AgentOSClientError, PrimitiveMock  # noqa: E402

os.environ["AGENTOS_AGENTD_SOCK"] = "/tmp/agentos-sdk-socket-does-not-exist"
try:
    AgentOS().system()
except AgentOSClientError:
    pass
else:
    raise AssertionError("missing local socket must raise AgentOSClientError")

with PrimitiveMock() as mock:
    client = AgentOS(caller="contract-test")
    assert client.system()["mem_total_kb"] > 0
    assert client.chat("hello")["response"] == "mock: hello"
    client.memory_write("alpha")
    client.memory_write("beta")
    recalled = client.memory_recall("anything", top_k=1)
    assert len(recalled["hits"]) == 1
    assert mock.requests["memory"][-1] == "recall anything"
    stored = client.fs_put("note.txt", "offline content")
    assert client.fs_get(stored["id"]) == b"offline content"
    assert client.fs_search("offline", top_k=1)["hits"][0]["name"] == "note.txt"

with PrimitiveMock(failures={"infer": {"chat": "backend_unavailable"}}):
    try:
        AgentOS().chat("must fail")
    except AgentOSClientError as exc:
        assert "backend_unavailable" in str(exc)
    else:
        raise AssertionError("primitive failures must raise AgentOSClientError")

print("Local client error contract: OK")
