# agentos —— AgentOS Python SDK

第一次接入请先阅读[开发者快速开始](../docs/developer-quickstart.zh-CN.md)，其中包含
macOS、Windows、Linux 环境准备、SSH 隧道、完整 Run 示例和 Agent 部署边界。

四个可直接打包的业务样例见[AgentOS SDK 代码样例](../docs/agent-examples.zh-CN.md)，
覆盖知识文档、代码/设计/办公、本地模型行业任务以及长期记忆语义检索。

把 AgentOS 的四大系统原语 + 运行时封装成几行 Python API,**零第三方依赖**(仅标准库)。
面向 ISV 与 Agent 开发者:拿到峰瞰硬件 / 任何装了 AgentOS 的机器,`pip install` 即可开发。

## 安装

```bash
# 发布版（PyPI）
pip install agentos-sdk

# 从源码装(仓库内)
pip install ./python

# 或开发模式(改代码即时生效)
pip install -e ./python
```

装完有两个入口:

- **库**:`import agentos; aos = agentos.AgentOS()`
- **命令行**:`agentos new my-agent`(生成 agent 骨架)

PyPI 分发名是 `agentos-sdk`，Python 导入名保持为 `agentos`。SDK 不要求安装
AgentOS 源码仓库；运行时只需连接目标机器上已启动的 AgentOS 服务。

## 远程 Gateway 控制面

需要从开发机查看节点、启动/停止 Run、读取日志和事件时，使用
`GatewayClient` 通过 HTTPS 访问 Gateway：

```python
from agentos import GatewayClient

client = GatewayClient(
    endpoint="https://gateway.example/gateway/v1/nodes/node-1/api/v1",
    token="<短期访问令牌>",
)
print(client.health())
run = client.create_run(agent="my-agent", task_id="task-001")
print(client.logs("my-agent"))
```

生产客户端特性：

- 对 GET/HEAD/OPTIONS 使用有上限的指数退避重试；POST 只有显式提供
  `idempotency_key` 时才会重试。
- `GatewayError.status` 和 `GatewayError.retryable` 提供可编程错误判定。
- `events_page()` 返回游标页，`iter_events()` 按 `event_id` 增量读取，避免一次性加载全部事件。
- `workspaces()`、`tasks()`、`run()` 覆盖控制面其余资源；Gateway 节点管理使用
  `GatewayRegistryClient`。

也可以通过 `AGENTOS_ENDPOINT` 和 `AGENTOS_TOKEN` 提供默认值。`GatewayClient`
只覆盖远程控制面 HTTP API（health、agents、runs、logs、events）；四大系统原语
仍通过目标节点本机 Unix Socket 访问，避免把尚未冻结的远程原语协议伪装成稳定接口。

## 快速上手

```python
import agentos

aos = agentos.AgentOS(caller="my-agent")   # caller 用于 inferd 算力记账

# 感知(agentd)
aos.system()            # 系统资源

# 认知(inferd)
aos.chat("帮我写个快速排序")          # 与当前模型对话
aos.embed("语义召回的向量来源")       # 文本转向量
aos.hwinfo()                          # 这台机器选了哪个推理后端

# 记忆(memoryd)
aos.memory_write("用户偏好用 Rust 写系统级代码")
aos.memory_recall("用户用什么语言")   # 按意思召回,不用关键词精确匹配

# 语义文件(fsd)
aos.fs_put("report.txt", "第三季度营收增长 15%")
aos.fs_search("营收")                 # 按意思召回文件
data = aos.fs_get(fid)                # 取回原始字节(bytes)

# 运行时(agentrund)
aos.agentrun_spawn("demo")
aos.agentrun_logs("demo")

# 上下文(Context Gateway):按 token 预算装好本轮上下文
ctx = aos.ctx_assemble(8000, "营收情况")
prompt = ctx["prompt"]
```

## 脚手架:`agentos new`

```bash
agentos new my-agent
# 生成 my-agent/{agent.manifest, agent.py, README.md}

agentos doctor                     # 检查本地原语和运行时
agentos test my-agent              # 语法/项目测试
agentos package my-agent           # 生成 .agent.tgz
agentos inspect my-agent           # 校验并查看 Manifest v1
agentos run my-agent               # 交给 agentrund 托管
agentos run my-agent --local       # 本地直接运行
agentos status my-agent
agentos logs my-agent
agentos replay events.jsonl            # 离线校验 Harness 运行记录

python3 my-agent/agent.py        # 本地直接跑(3 轮:感知→认知→记忆→语义文件)
agentrun spawn my-agent          # 由 agentrund 托管跑(能力注入 + 资源边界)
```

生成的 `agent.manifest` 里 `primitives=agent,infer,memory,fs` 决定 agent 能用哪些原语;
`sandbox=on` 和 `network=loopback` 默认启用 systemd 隔离，只有受信任调试场景才应关闭;
`agent.py` 里每个 `aos.xxx()` 就是原语的一行 API。
`agentos test/package` 会复用同一套 Manifest v1 校验，未知字段保留并忽略，以支持向后兼容。

## Harness 录制、重试与回放

`AgentOSHarnessBridge.run()` 支持有限重试、协作式取消和可选 checkpoint。传入
`EventRecorder("events.jsonl")` 后，每次工具调用及结果会写入 JSONL；使用
`agentos replay events.jsonl` 可在不连接模型或 daemon 的环境中校验终态和调用链。

## 环境变量

socket 路径与 C 客户端一致,默认走 `/run/...`;本地开发/测试用 env 覆盖(不必装系统):

| 原语 | env | 默认 |
|---|---|---|
| 感知 agentd | `AGENTOS_AGENTD_SOCK` | `/run/agentd/agentd.sock` |
| 认知 inferd | `AGENTOS_INFERD_SOCK` | `/run/inferd/inferd.sock` |
| 记忆 memoryd | `AGENTOS_MEMORYD_SOCK` | `/run/memoryd/memoryd.sock` |
| 语义文件 fsd | `AGENTOS_FSD_SOCK` | `/run/fsd/fsd.sock` |
| 运行时 agentrund | `AGENTOS_AGENTRUND_SOCK` | `/run/agentrund/agentrund.sock` |
| 上下文 ctxd | `AGENTOS_CTXD_SOCK` | `/run/ctxd/ctxd.sock` |

## 说明

- 请求经 Unix socket 直连原语 daemon,零网络开销、数据不出端。
- 文本参数里的换行会被剔除(与 daemon/网关层一致的协议安全约定)。
- `caller` 只在调 inferd 时带 `@<caller>` 前缀(算力调度按 caller 记账);其他原语协议不带。

## 版本兼容

- `agentos-sdk` `1.5.x` 对应 AgentOS Manifest v1、Harness Adapter v1 和 Control-plane HTTP v1。
- 同一主版本内，新增字段和事件类型向后兼容；客户端必须忽略未知字段。
- 需要远程调用四大原语时，等待 Remote Primitive Protocol 正式发布，不要直接依赖内部 Unix Socket 路径或未文档化 HTTP 路由。

## 生产使用边界

SDK 客户端已提供有上限的重试、幂等 Run 创建、结构化错误、输入校验和事件增量读取。
真正上线仍需在 AgentOS Ubuntu 节点完成 TLS/mTLS、Token、Unix Socket 权限和 Run 生命周期
验收；SDK 不负责替代服务端的多租户 RBAC、离线队列或证书轮换。
