#!/usr/bin/env python3
"""Contract checks for local Unix Socket error handling."""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from agentos import AgentOS, AgentOSClientError  # noqa: E402

os.environ["AGENTOS_AGENTD_SOCK"] = "/tmp/agentos-sdk-socket-does-not-exist"
try:
    AgentOS().system()
except AgentOSClientError:
    pass
else:
    raise AssertionError("missing local socket must raise AgentOSClientError")

print("Local client error contract: OK")
