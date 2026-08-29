"""PeakVisionOS Python SDK for ISVs and Agent developers.

把四大原语 + 运行时封装成几行 Python API。零第三方依赖(仅标准库),
socket 路径与 C 客户端一致,支持 env 覆盖(AGENTOS_*_SOCK)便于本地开发。

快速上手:
    import pvos
    aos = pvos.PeakVisionOS(caller="my-agent")
    aos.chat("帮我写个快速排序")
    aos.memory_write("用户偏好用 Rust 写系统级代码")
    hits = aos.fs_search("第三季度营收")
    aos.agentrun_spawn("demo")
"""
from .client import AgentOS, AgentOSClientError, PeakVisionOS, PVOSClientError, _call
from .harness import (AgentOSHarnessBridge, PeakVisionOSHarnessBridge, CancellationToken, EventRecorder, HarnessAdapter, HarnessResult,
                      RUN_STATUSES, STABLE_EVENT_TYPES, STABLE_TOOL_NAMES, STABLE_TOOL_SCHEMAS,
                      RetryPolicy, RunEvent, Task, ToolCall, ToolPolicy, load_recording, replay_recording)
from .manifest import Manifest, load_manifest, parse_manifest_text, validate_manifest, validate_manifest_file
from .http import (AsyncGatewayClient, GatewayClient, GatewayError,
                   GatewayRegistryClient, GatewayRetryPolicy,
                   RemoteGatewayClient)
from .acceptance import run_acceptance
from .mock_server import create_mock_server
from .mock_primitives import PrimitiveMock
from .package_manager import deploy_package, install_package, uninstall_package

__all__ = ["PeakVisionOS", "PVOSClientError", "AgentOS", "AgentOSClientError", "_call", "GatewayClient", "AsyncGatewayClient", "GatewayError", "GatewayRegistryClient", "RemoteGatewayClient", "GatewayRetryPolicy", "PeakVisionOSHarnessBridge", "AgentOSHarnessBridge", "CancellationToken", "EventRecorder", "HarnessAdapter", "HarnessResult", "RUN_STATUSES", "STABLE_EVENT_TYPES", "STABLE_TOOL_NAMES", "STABLE_TOOL_SCHEMAS", "RetryPolicy", "RunEvent", "Task", "ToolCall", "ToolPolicy", "load_recording", "replay_recording", "Manifest", "load_manifest", "parse_manifest_text", "validate_manifest", "validate_manifest_file", "run_acceptance", "create_mock_server", "PrimitiveMock", "deploy_package", "install_package", "uninstall_package"]
__version__ = "1.5.0a1"
