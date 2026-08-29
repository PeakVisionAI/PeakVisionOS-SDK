# PeakVisionOS 公共协议

这里是 Python、TypeScript 和服务端共同依赖的机器可读/可审查契约。

| 协议 | 版本 | 规范 |
| --- | --- | --- |
| Agent Manifest | v1 | [`docs/manifest-v1.md`](../docs/manifest-v1.md) |
| Harness Adapter | v1 | [`docs/harness-adapter-v1.md`](../docs/harness-adapter-v1.md) |
| Control-plane HTTP | v1 | [`openapi.yaml`](openapi.yaml) 与 [`docs/control-plane-api.md`](../docs/control-plane-api.md) |
| Run/Event | v1 | [`python/pvos/harness.py`](../python/pvos/harness.py) |
| 本地原语 | v1 | AgentOS [`ARCHITECTURE.md`](https://github.com/PeakVisionAI/AgentOS/blob/main/ARCHITECTURE.md) |

## 兼容规则

小版本只能新增可选字段、工具和事件；客户端必须忽略未知字段。删除字段、
改变状态含义、改变认证或改变 Unix Socket 行协议时，必须发布新的协议主版本。
服务端错误统一为 `{error:{code,message,details?,retry_after?},request_id?}`。

四大原语是 `agentd`、`inferd`、`memoryd`、`fsd`；`agentrund` 和 `ctxd` 是
系统服务而不是原语。远程 Gateway 目前只承载控制面，不把内部原语协议伪装成
稳定公网接口。
