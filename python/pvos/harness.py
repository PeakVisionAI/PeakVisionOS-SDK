"""Stable Harness Adapter Contract for AgentOS 1.5."""
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Protocol
import json
import pathlib
import threading
import time
import uuid

# Release 1.5 stable contract. New events/tools may be added in later
# versions, but these names and their meanings remain backward compatible.
RUN_STATUSES = ("created", "running", "completed", "failed", "timeout", "cancelled", "stopped")
STABLE_EVENT_TYPES = (
    "run.started", "tool.started", "tool.completed", "tool.failed",
    "tool.retrying", "checkpoint.saved", "run.completed", "run.failed",
    "run.cancelled",
)
STABLE_TOOL_NAMES = (
    "agent.system", "infer.chat", "infer.embed", "memory.write",
    "memory.recall", "fs.put", "fs.search",
)

@dataclass
class Task:
    input: str
    task_id: str = field(default_factory=lambda: "task-" + uuid.uuid4().hex[:12])
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    tool: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    call_id: str = field(default_factory=lambda: "call-" + uuid.uuid4().hex[:12])


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    backoff_seconds: float = 0.0

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.backoff_seconds < 0:
            raise ValueError("backoff_seconds must not be negative")


class CancellationToken:
    def __init__(self):
        self._event = threading.Event()

    def cancel(self):
        self._event.set()

    @property
    def cancelled(self):
        return self._event.is_set()


@dataclass
class RunEvent:
    type: str
    task_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class HarnessResult:
    status: str
    output: Any = None
    events: list = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self):
        if self.status not in RUN_STATUSES:
            raise ValueError("unsupported run status: " + str(self.status))


class EventRecorder:
    """Append-only JSONL recorder for deterministic task replay."""

    def __init__(self, path):
        self.path = pathlib.Path(path)

    def write(self, event: RunEvent):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"type": event.type, "task_id": event.task_id,
                                     "payload": event.payload, "timestamp": event.timestamp},
                                    ensure_ascii=False, default=str) + "\n")


def load_recording(path):
    events = []
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            events.append(RunEvent(item["type"], item["task_id"], item.get("payload", {}), item.get("timestamp", time.time())))
    return events


def replay_recording(path):
    """Validate and summarize a recorded run without calling any daemon."""
    events = load_recording(path)
    if not events or events[0].type != "run.started":
        raise ValueError("recording must start with run.started")
    terminal = {"run.completed": "completed", "run.failed": "failed", "run.cancelled": "cancelled"}
    if events[-1].type not in terminal:
        raise ValueError("recording must end with a terminal run event")
    task_id = events[0].task_id
    if any(event.task_id != task_id for event in events):
        raise ValueError("recording contains multiple task ids")
    started = set()
    output = None
    for event in events:
        call_id = event.payload.get("call_id")
        if event.type == "tool.started":
            if not call_id:
                raise ValueError("tool.started is missing call_id")
            started.add(call_id)
        elif event.type == "tool.completed":
            if call_id not in started:
                raise ValueError("tool.completed has no matching tool.started")
            output = event.payload.get("output")
    error = events[-1].payload.get("error") or events[-1].payload.get("reason")
    return HarnessResult(terminal[events[-1].type], output, events, error)


class HarnessAdapter(Protocol):
    def plan(self, task: Task, context: Dict[str, Any]) -> Iterable[ToolCall]: ...
    def validate(self, task: Task, output: Any, context: Dict[str, Any]) -> bool: ...


class PeakVisionOSHarnessBridge:
    """Run an adapter plan through stable PeakVisionOS tool names."""

    def __init__(self, agentos, recorder=None):
        self.aos = agentos
        self.recorder = recorder

    def _event(self, events, event):
        events.append(event)
        if self.recorder:
            self.recorder.write(event)

    def _call_tool(self, call: ToolCall):
        args = call.arguments
        table = {
            "infer.chat": lambda: self.aos.chat(args["prompt"]),
            "infer.embed": lambda: self.aos.embed(args["text"]),
            "memory.write": lambda: self.aos.memory_write(args["text"]),
            "memory.recall": lambda: self.aos.memory_recall(args["query"]),
            "fs.put": lambda: self.aos.fs_put(args["name"], args["text"]),
            "fs.search": lambda: self.aos.fs_search(args["query"]),
            "agent.system": self.aos.system,
        }
        if call.tool not in table:
            raise ValueError("unsupported tool: " + call.tool)
        return table[call.tool]()

    def run(self, task: Task, adapter: HarnessAdapter, context=None, retry_policy=None,
            cancellation_token=None) -> HarnessResult:
        ctx = dict(context or {})
        retry = retry_policy or RetryPolicy()
        cancel = cancellation_token or CancellationToken()
        events = []
        self._event(events, RunEvent("run.started", task.task_id))
        outputs = []
        try:
            for call in adapter.plan(task, ctx):
                if cancel.cancelled:
                    self._event(events, RunEvent("run.cancelled", task.task_id, {"reason": "cancel_requested"}))
                    return HarnessResult("cancelled", outputs[-1] if outputs else None, events, "cancel_requested")
                output = None
                for attempt in range(1, retry.max_attempts + 1):
                    if cancel.cancelled:
                        self._event(events, RunEvent("run.cancelled", task.task_id,
                                                     {"reason": "cancel_requested"}))
                        return HarnessResult("cancelled", outputs[-1] if outputs else None,
                                             events, "cancel_requested")
                    payload = {"call_id": call.call_id, "tool": call.tool, "attempt": attempt}
                    self._event(events, RunEvent("tool.started", task.task_id, payload))
                    try:
                        output = self._call_tool(call)
                        break
                    except Exception as exc:
                        failed = dict(payload, error=str(exc))
                        self._event(events, RunEvent("tool.failed", task.task_id, failed))
                        if attempt == retry.max_attempts:
                            raise
                        self._event(events, RunEvent("tool.retrying", task.task_id, failed))
                        if retry.backoff_seconds:
                            time.sleep(retry.backoff_seconds)
                outputs.append(output)
                ctx[call.call_id] = output
                self._event(events, RunEvent("tool.completed", task.task_id,
                                             {"call_id": call.call_id, "tool": call.tool,
                                              "attempt": attempt, "output": output}))
                checkpoint = getattr(adapter, "checkpoint", None)
                if callable(checkpoint):
                    checkpoint_id = checkpoint(task, dict(ctx))
                    self._event(events, RunEvent("checkpoint.saved", task.task_id,
                                                 {"call_id": call.call_id, "checkpoint_id": checkpoint_id}))
            final = outputs[-1] if outputs else None
            if not adapter.validate(task, final, ctx):
                self._event(events, RunEvent("run.failed", task.task_id, {"reason": "validation_failed"}))
                return HarnessResult("failed", final, events, "validation_failed")
            self._event(events, RunEvent("run.completed", task.task_id))
            return HarnessResult("completed", final, events)
        except Exception as exc:
            self._event(events, RunEvent("run.failed", task.task_id, {"error": str(exc)}))
            return HarnessResult("failed", outputs[-1] if outputs else None, events, str(exc))


AgentOSHarnessBridge = PeakVisionOSHarnessBridge
