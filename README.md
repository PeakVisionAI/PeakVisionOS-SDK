# PeakVisionOS SDK

PeakVisionOS SDK 是端侧智能体的开发与控制工具链。它连接已经运行
PeakVisionOS 的 Ubuntu 节点，让 ISV 使用熟悉的 Python 或 TypeScript 开发
Agent，同时通过统一协议启动 Run、读取日志和追踪事件。

本仓库是 SDK，不是操作系统镜像，也不替代节点上的 `agentd`、`inferd`、
`memoryd`、`fsd`、`agentrund` 和 `ctxd` 服务。

## 适用场景

- 在开发电脑上编写、测试、打包 Agent。
- 在端侧节点调用本地推理、记忆、语义文件和系统感知能力。
- 通过 Remote Gateway 管理节点、Workspace、Task、Run、日志和事件。
- 把 DeepSeek Harness、LangGraph 或自研 Harness 接到稳定工具契约。

## 安装

```bash
python3 -m pip install peakvisionos-sdk
npm install @peakvision/pvos-sdk
```

Python 导入名是 `pvos`，TypeScript 包名是 `@peakvision/pvos-sdk`。旧的
`agentos` 导入和 CLI 在 1.x 兼容窗口内保留，新项目请使用新名称。

## 5 分钟快速开始

无真实节点时，先运行离线 Mock：

```bash
pvos mock-server --port 17680 --token dev-token
pvos acceptance --endpoint http://127.0.0.1:17680/api/v1 --token dev-token
```

远程控制面：

```python
from pvos import GatewayClient

client = GatewayClient(
    endpoint="https://gateway.example/gateway/v1/nodes/node-1/api/v1",
    token="<短期令牌>",
)
print(client.health())
run = client.create_run("my-agent", idempotency_key="run-2026-001")
print(client.run(run["run_id"]))
print(list(client.iter_events(max_pages=1)))
```

节点本地 Agent：

```python
import pvos

aos = pvos.PeakVisionOS(caller="my-agent")
print(aos.system())
answer = aos.chat("根据当前系统状态给出一句建议")
aos.memory_write("用户偏好简洁的运行报告")
print(aos.memory_recall("用户偏好" , top_k=3))
```

## 两种传输边界

| 位置 | SDK | 传输 | 能力 |
| --- | --- | --- | --- |
| AgentOS 节点内 | `pvos.PeakVisionOS` | Unix Socket | 六个本地 daemon；四大原语是 `agentd/inferd/memoryd/fsd` |
| 开发机、GUI、CI | `pvos.GatewayClient` 或 TS `PeakVisionOS` | HTTP/HTTPS | 控制面资源和运行观测 |

远程客户端目前不代理四大原语。未经版本化的 Unix Socket 路径不能作为公网
API 使用。

## Agent 生命周期

```bash
pvos new my-agent
pvos test my-agent
pvos package my-agent -o my-agent.agent.tgz
pvos install my-agent.agent.tgz --root /etc/agent-os/agents
agentrun spawn my-agent
agentrun status my-agent
agentrun logs my-agent
```

安装器校验 Manifest、阻止路径穿越和特殊文件，支持 SHA-256/签名验证入口，
并以代码目录与 Manifest 双文件原子切换；失败会恢复上一版本。

## 文档入口

- [Python SDK](python/README.md)
- [TypeScript SDK](typescript/README.md)
- [四个 Agent 示例](examples/README.md)
- [开发者快速开始](docs/developer-quickstart.zh-CN.md)
- [API 参考](docs/api-reference.zh-CN.md) 与 [OpenAPI](protocol/openapi.yaml)
- [Harness Adapter v1](docs/harness-adapter-v1.md)
- [DeepSeek Harness 接入](docs/deepseek-harness-integration.zh-CN.md)
- [安全指南](docs/security-guide.zh-CN.md)、[错误与状态机](docs/errors-and-state-machine.zh-CN.md)、[测试指南](docs/testing-guide.zh-CN.md)、[兼容矩阵](docs/compatibility-matrix.zh-CN.md)
- [P0/P1/P2 就绪矩阵](docs/readiness-matrix.zh-CN.md)

## 本地验证

```bash
PYTHONPATH=python python3 tests/test-local-client.py
PYTHONPATH=python python3 tests/test-sdk-http.py
PYTHONPATH=python python3 tests/test-pvos-toolchain.py
cd typescript && npm ci && npm test
python3 -m build python
```

测试不需要 GPU；真实发布前仍必须在目标 Ubuntu 节点验收 Unix Socket 权限、
TLS/mTLS、真实推理后端、cgroup 和 Run 生命周期。

## 版本边界

`peakvisionos-sdk 1.5.x` 与 Manifest v1、Harness Adapter v1、Control-plane
HTTP v1 对齐。新增可选字段保持兼容；删除字段、改变状态含义或认证方式需要
新的协议主版本。SDK 不负责服务端 RBAC、证书轮换、离线队列、强隔离或多租户。
