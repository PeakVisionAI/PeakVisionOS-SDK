# AgentOS Harness Adapter Contract v1

Harness Adapter v1 将 DeepSeek Harness、LangGraph、自研 Harness 等规划层与
PeakVisionOS 系统能力隔离。Python 参考接口位于 `pvos.harness`。

注意：本页定义的是 AgentOS 的 Python Adapter Contract，不是 DeepSeek Harness 官方的
TypeScript 插件 API。连接 DeepSeek 官方项目请阅读
[DeepSeek Harness 接入 PeakVisionOS SDK](deepseek-harness-integration.zh-CN.md)。

稳定事件：

```text
run.started
tool.started
tool.completed
tool.failed
tool.retrying
checkpoint.saved
run.completed
run.failed
run.cancelled
```

SDK 以 `pvos.STABLE_EVENT_TYPES` 暴露上述事件名；事件载荷可以增加字段，但不得改变已有字段含义。

稳定工具名称：

```text
agent.system
infer.chat
infer.embed
memory.write
memory.recall
fs.put
fs.search
```

SDK 以 `pvos.STABLE_TOOL_NAMES` 和 `pvos.STABLE_TOOL_SCHEMAS` 暴露工具契约。
Adapter 只能使用稳定工具名，不能依赖 daemon 的 Unix Socket 行协议。

Harness 负责 `plan()` 与 `validate()`；AgentOS 负责工具执行、权限、生命周期和事件。`HarnessResult.status` 使用 `created/running/completed/failed/timeout/cancelled/stopped` 状态集合。

参考实现支持 `RetryPolicy`、`CancellationToken`、`ToolPolicy` 白名单/审批、
单工具 timeout、可选 `checkpoint(task, context)` 回调，以及
`EventRecorder`/`replay_recording` 离线录制回放。重试次数有明确上限；
取消在下一次工具调用前收敛为 `cancelled`。
