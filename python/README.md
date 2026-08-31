# PeakVisionOS Python SDK

Python SDK 面向运行在 PeakVisionOS 节点上的 Agent，以及从开发电脑管理
节点的 ISV 工具。仅使用 Python 标准库，支持 Python 3.8+。

## 安装

```bash
python3 -m pip install peakvisionos-sdk
# 源码开发
python3 -m pip install -e ./python
```

```python
import pvos
aos = pvos.PeakVisionOS(caller="my-agent")
```

## 本地原语

```python
print(aos.world())                    # agentd
print(aos.chat("写一个排序函数"))       # inferd
aos.memory_write("项目代号为海风")       # memoryd
print(aos.memory_recall("项目代号", top_k=3))
file_info = aos.fs_put("brief.md", "项目将在下周交付")  # fsd
print(aos.fs_search("交付时间", top_k=3))
print(aos.ctx_assemble(8000, "项目风险")["prompt"])     # ctxd
```

`memoryd` 的服务端协议是 `recall <query>`；SDK 的 `top_k` 在客户端对返回
的 `hits` 截断，不会把未支持的参数发给 daemon。所有本地调用都可传
`timeout=<秒数>`。

默认 Socket 和覆盖变量：

| 服务 | 环境变量 | 默认路径 |
| --- | --- | --- |
| agentd | `AGENTOS_AGENTD_SOCK` | `/run/agentd/agentd.sock` |
| inferd | `AGENTOS_INFERD_SOCK` | `/run/inferd/inferd.sock` |
| memoryd | `AGENTOS_MEMORYD_SOCK` | `/run/memoryd/memoryd.sock` |
| fsd | `AGENTOS_FSD_SOCK` | `/run/fsd/fsd.sock` |
| agentrund | `AGENTOS_AGENTRUND_SOCK` | `/run/agentrund/agentrund.sock` |
| ctxd | `AGENTOS_CTXD_SOCK` | `/run/ctxd/ctxd.sock` |

## Remote Gateway

```python
from pvos import GatewayClient, GatewayError

client = GatewayClient(endpoint="https://host/gateway/v1/nodes/n1/api/v1",
                       token="short-lived-token")
try:
    run = client.create_run("my-agent", idempotency_key="build-001")
except GatewayError as exc:
    print(exc.code, exc.status, exc.retryable, exc.request_id)
```

客户端覆盖 health、agents、workspaces、tasks、runs、logs、events；
`GatewayRegistryClient` 额外提供 nodes、注册、令牌轮换和 snapshot。
`AsyncGatewayClient` 提供同等方法；它在线程池中运行标准库 HTTP，取消协程
会停止等待，但无法中断已经发出的 urllib 请求，timeout 仍是上限。

## Harness 与打包

实现 `plan(task, context)` 和 `validate(task, output, context)`，通过
`PeakVisionOSHarnessBridge` 执行稳定工具名。`ToolPolicy` 控制白名单和审批，
`ToolCall.timeout_seconds` 控制单次本地调用，`EventRecorder` 记录 JSONL，
`pvos replay` 离线校验终态。

```bash
pvos new my-agent
pvos test my-agent
pvos package my-agent
pvos inspect my-agent
```

### SSH 远程部署

目标机是 Ubuntu 24.04 等启用 PEP 668 的系统时，使用 `--sdk-wheel` 上传本地构建
的 SDK wheel。交互式终端默认分配 SSH TTY，远端 `sudo` 会正常提示密码：

```bash
python -m build python
pvos deploy my-agent.agent.tgz user@agentos-host \
  --sdk-wheel python/dist/peakvisionos_sdk-1.5.0a1-py3-none-any.whl
```

无终端的 CI 使用 `--no-tty`，要求部署用户已配置最小权限的 NOPASSWD sudo。SDK
不会接收或保存 sudo 密码；`--dry-run` 可用于审查将执行的 SSH 命令：

```bash
pvos deploy my-agent.agent.tgz user@agentos-host \
  --sdk-wheel python/dist/peakvisionos_sdk-1.5.0a1-py3-none-any.whl \
  --no-tty --dry-run
```

部署器通过 `python3 -m pvos.cli install` 安装 Agent，因此不要求 `pvos` 命令已经
出现在目标机 PATH 中。`--sdk-wheel` 安装完成后会重用系统 Python，systemd 启动的
Agent 可以直接 `import pvos`。

Manifest 的 `primitives=` 是最小权限声明；安装器默认拒绝链接、特殊文件和
超大包。生产环境应传入 `expected_sha256` 或 `signature_verifier`，并在升级前
确认停止/重新加载策略。

## 没有节点时

```python
from pvos import PrimitiveMock
with PrimitiveMock():
    print(pvos.PeakVisionOS().chat("离线合约测试"))
```

`PrimitiveMock` 只验证请求形状和失败处理，不提供真实模型、隔离或安全保证。

更多内容见[开发者快速开始](../docs/developer-quickstart.zh-CN.md)、[API 参考](../docs/api-reference.zh-CN.md)和[测试指南](../docs/testing-guide.zh-CN.md)。
