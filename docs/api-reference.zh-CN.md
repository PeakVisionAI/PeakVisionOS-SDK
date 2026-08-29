# PeakVisionOS SDK API Reference（v1）

机器可读控制面定义见 [`../protocol/openapi.yaml`](../protocol/openapi.yaml)。

## Python

```python
import pvos
node = pvos.PeakVisionOS(caller="my-agent")
gateway = pvos.GatewayClient(endpoint=..., token=...)
```

本地方法：`world()`、`system()`、`processes()`（`agent`）；`chat()`、
`embed()`、`models()`、`status()`、`hwinfo()`、`load()`、`sched()`（`infer`）；
`memory_write()`、`memory_set()`、`memory_recall(query, top_k=5)`、
`memory_list()`、`memory_forget()`、`memory_history()`（`memory`）；
`fs_put()`、`fs_search()`、`fs_get()`、`fs_list()`、`fs_forget()`（`fs`）；
`ctx_assemble()`（`ctxd`）；`agentrun_list/spawn/stop/status/logs`（`agentrund`）。

稳定工具调用支持请求级 `timeout`。`memory_recall()` 只向 memoryd 发送
`recall <query>`，`top_k` 由 SDK 对返回的 `hits` 截断。

方法返回 JSON 可映射的 `dict`，`fs_get()` 返回 `bytes`。本地失败抛出
`pvos.PVOSClientError`。Manifest 只授予对应原语，未授权调用会失败。

`GatewayClient` 与 `AsyncGatewayClient` 提供相同的 health、Agents、
Workspace、Task、Run、Logs、Events 方法。失败抛出 `pvos.GatewayError`，
其 `code/message/status/retryable/request_id/details/retry_after` 属性可用于恢复策略。GET 和带
`idempotency_key` 的 Run 创建才会自动重试。

## TypeScript

```ts
import { PeakVisionOS } from "@peakvision/pvos-sdk";
const client = new PeakVisionOS({ endpoint, token });
```

`AgentOS` 仍作为兼容导出；新代码使用 `PeakVisionOS`。资源类型包括
`Agent`、`Workspace`、`Task`、`Run`、`RunEvent`、`GatewayNode`。
`iterEvents()` 提供按 `event_id` 的分页增量读取；各方法接受可选
`RequestOptions.signal`；v1 尚无 SSE/WebSocket。
