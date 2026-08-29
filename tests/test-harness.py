#!/usr/bin/env python3
"""Harness tool schema, policy and approval contracts."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from pvos import PeakVisionOSHarnessBridge, Task, ToolCall, ToolPolicy  # noqa: E402


class FakeAOS:
    def chat(self, prompt, **_kwargs):
        return {"response": prompt}


class Adapter:
    def __init__(self, calls):
        self.calls = calls

    def plan(self, _task, _context):
        return self.calls

    def validate(self, _task, output, _context):
        return output is not None


bridge = PeakVisionOSHarnessBridge(FakeAOS())
result = bridge.run(Task("hello"), Adapter([ToolCall("infer.chat", {"prompt": "hello"})]))
assert result.status == "completed"
assert result.output["response"] == "hello"

blocked = bridge.run(
    Task("blocked"), Adapter([ToolCall("infer.chat", {"prompt": "no"})]),
    tool_policy=ToolPolicy(allowed_tools=()),
)
assert blocked.status == "failed"
assert blocked.error_code == "tool_not_allowed"

denied = bridge.run(
    Task("approval"), Adapter([ToolCall("infer.chat", {"prompt": "no"})]),
    tool_policy=ToolPolicy(require_approval=("infer.chat",)),
    approval=lambda *_args: False,
)
assert denied.error_code == "approval_required"

try:
    ToolCall("infer.chat", {"prompt": "x"}, timeout_seconds=0)
except ValueError:
    pass
else:
    raise AssertionError("non-positive tool timeout must be rejected")

print("Harness contract: OK")
