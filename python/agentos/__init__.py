"""agentos —— AgentOS 的 Python SDK(面向 ISV 与 Agent 开发者)

把四大原语 + 运行时封装成几行 Python API。零第三方依赖(仅标准库),
socket 路径与 C 客户端一致,支持 env 覆盖(AGENTOS_*_SOCK)便于本地开发。

快速上手:
    import agentos
    aos = agentos.AgentOS(caller="my-agent")   # caller 用于 inferd 配额记账
    aos.chat("帮我写个快速排序")
    aos.memory_write("用户偏好用 Rust 写系统级代码")
    hits = aos.fs_search("第三季度营收")
    aos.agentrun_spawn("demo")
"""
from .client import AgentOS, _call
from .harness import (AgentOSHarnessBridge, CancellationToken, EventRecorder, HarnessAdapter, HarnessResult,
                      RUN_STATUSES, STABLE_EVENT_TYPES, STABLE_TOOL_NAMES,
                      RetryPolicy, RunEvent, Task, ToolCall, load_recording, replay_recording)
from .manifest import Manifest, load_manifest, parse_manifest_text, validate_manifest, validate_manifest_file
from .http import GatewayClient, GatewayError

__all__ = ["AgentOS", "_call", "GatewayClient", "GatewayError", "AgentOSHarnessBridge", "CancellationToken", "EventRecorder", "HarnessAdapter", "HarnessResult", "RUN_STATUSES", "STABLE_EVENT_TYPES", "STABLE_TOOL_NAMES", "RetryPolicy", "RunEvent", "Task", "ToolCall", "load_recording", "replay_recording", "Manifest", "load_manifest", "parse_manifest_text", "validate_manifest", "validate_manifest_file"]
__version__ = "1.5.0a1"
