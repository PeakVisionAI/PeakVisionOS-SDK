# PeakVisionOS SDK 开发者快速开始

本文帮助开发者在自己的 macOS、Windows 或 Linux 电脑上使用 PeakVisionOS SDK 开发、
测试和打包 Agent。完成后你可以：

- 在自己的 IDE 中编写 Agent，不需要在 AgentOS 源码仓库中开发。
- 从开发电脑连接一台 AgentOS Ubuntu 节点，创建任务、启动 Run、读取日志和事件。
- 生成符合 Manifest v1 的 Agent 包，并在 AgentOS 节点上调用本地推理、记忆和语义文件能力。

## 1. 先理解两种连接方式

| 开发位置 | SDK 客户端 | 连接方式 | 能力 |
| --- | --- | --- | --- |
| macOS、Windows、普通 Linux 开发电脑 | Python `GatewayClient` / TypeScript `AgentOS` | HTTP/HTTPS | Agent、Workspace、Task、Run、日志、事件 |
| 安装了 AgentOS 的 Ubuntu 节点 | Python `pvos.PeakVisionOS` | 本机 Unix Socket | 感知、推理、记忆、语义文件、上下文和运行时 |

四大系统原语目前只允许在 AgentOS 节点本机访问。开发电脑不能把 Unix Socket
路径指向远程机器。推荐流程是：**本地 IDE 写代码和管理 Run，Agent 包在 Ubuntu
节点执行模型和系统原语。**

## 2. 准备环境

开发电脑需要：

- Git
- Python 3.8 及以上；推荐 Python 3.12
- TypeScript 开发另需 Node.js 18 及以上；推荐当前 LTS 版本
- VS Code、JetBrains、Vim 等任意 IDE
- 如需端到端运行：一台可 SSH 登录且已运行 AgentOS 的 Ubuntu 节点
- 如控制面已启用鉴权：管理员提供的 AgentOS 控制面 Token；不要把 Token 写进代码或提交到 Git

暂时没有 AgentOS 节点也可以完成 SDK 安装、Agent 代码生成、Manifest 检查、打包和
合约测试；远程 Run 和四大原语调用需要连接 AgentOS 节点。

确认本机工具：

```bash
git --version
python3 --version
node --version   # 仅 TypeScript 需要
```

Windows PowerShell 可以使用 `python` 代替 `python3`。后续 Bash 示例在 Windows 上
可使用 PowerShell、Git Bash 或 IDE Terminal 执行。

## 3. 获取并安装 SDK

在 SDK 尚未正式发布到 PyPI/NPM，或需要最新源码时，使用源码安装：

```bash
git clone https://github.com/PeakVisionAI/AgentOS-SDK.git
cd AgentOS-SDK

python3 -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
python3 -m pip install -e ./python

cd typescript
npm ci
npm run build
cd ..
```

正式包发布后可以直接安装：

```bash
python3 -m pip install peakvisionos-sdk
npm install @peakvision/pvos-sdk
```

检查 Python SDK 和 CLI：

```bash
python3 -c "import pvos; print(pvos.__version__)"
pvos --help
```

## 4. 从开发电脑连接 AgentOS 节点

### 推荐：使用 SSH 隧道

AgentOS 控制面默认只监听节点本机 `127.0.0.1:17680`。在开发电脑执行：

```bash
ssh -N -L 17680:127.0.0.1:17680 <ubuntu-user>@<AGENTOS_HOST>
```

保持这个 Terminal 窗口运行。另开一个 Terminal 检查：

```bash
curl http://127.0.0.1:17680/api/v1/health
```

预期返回包含：

```json
{"ok": true, "service": "agentosd"}
```

设置连接参数：

```bash
export AGENTOS_ENDPOINT=http://127.0.0.1:17680/api/v1
export AGENTOS_TOKEN='<管理员提供的控制面 Token>'
export AGENTOS_AGENT_NAME=my-agent
```

Windows PowerShell：

```powershell
$env:AGENTOS_ENDPOINT = "http://127.0.0.1:17680/api/v1"
$env:AGENTOS_TOKEN = "<管理员提供的控制面 Token>"
$env:AGENTOS_AGENT_NAME = "my-agent"
```

生产环境应使用 HTTPS/mTLS Gateway 和短期 Token。不要为方便开发把无 Token 的控制面
直接暴露到局域网或公网。

## 5. Python：5 分钟完成第一次远程 Run

新建 `quickstart.py`：

```python
import os
import time

from pvos import GatewayClient, GatewayError

client = GatewayClient(
    endpoint=os.environ["AGENTOS_ENDPOINT"],
    token=os.environ.get("AGENTOS_TOKEN", ""),
)

try:
    print("health:", client.health())
    agents = client.agents()
    print("agents:", agents)
    if not agents:
        raise RuntimeError("目标节点还没有可运行的 Agent")

    agent_name = os.environ["AGENTOS_AGENT_NAME"]
    available = {agent["name"] for agent in agents}
    if agent_name not in available:
        raise RuntimeError(f"节点上没有 {agent_name!r}，可用 Agent: {sorted(available)}")
    workspace = client.create_workspace("SDK quickstart")
    task = client.create_task(
        workspace_id=workspace["workspace_id"],
        title="完成一次 SDK 远程运行",
        description="启动 Agent，并读取终态、日志和事件",
        agent=agent_name,
    )
    run = client.create_run(
        agent=agent_name,
        task_id=task["task_id"],
        workspace_id=workspace["workspace_id"],
        idempotency_key=f"quickstart-{task['task_id']}",
    )
    print("created run:", run)

    run_id = run["run_id"]
    terminal_statuses = {"completed", "failed", "stopped", "timeout", "cancelled"}
    for _ in range(60):
        current = client.run(run_id)
        print("status:", current.get("status"))
        if current.get("status") in terminal_statuses:
            break
        time.sleep(1)
    else:
        raise TimeoutError(f"Run {run_id} 在 60 秒内未进入终态")

    print("logs:", client.logs(agent_name))
    for event in client.iter_events(max_pages=5):
        if event.get("run_id") == run_id:
            print("event:", event)
except GatewayError as exc:
    print(f"AgentOS 请求失败: status={exc.status} retryable={exc.retryable} {exc}")
    raise
```

运行：

```bash
python3 quickstart.py
```

验收结果：能列出目标节点的 Agent，创建 Workspace/Task/Run，Run 最终进入
`completed`、`failed`、`stopped`、`timeout` 或 `cancelled`，并能读取日志和对应事件。

如果节点还没有 Agent，先完成第 7 节的 Agent 创建和部署。

## 6. TypeScript：连接同一个控制面

在你的 Node.js 项目中安装 SDK：

```bash
mkdir agentos-ts-demo
cd agentos-ts-demo
npm init -y

# 正式发布后
npm install @peakvision/pvos-sdk

# 尚未发布时，改用本机 AgentOS-SDK/typescript 的实际路径
npm install ../AgentOS-SDK/typescript
```

新建 `quickstart.mjs`：

```javascript
import { PeakVisionOS } from "@peakvision/pvos-sdk";

const client = new PeakVisionOS({
  endpoint: process.env.AGENTOS_ENDPOINT,
  token: process.env.AGENTOS_TOKEN,
});

console.log(await client.health());
const agents = await client.agents();
if (!agents.length) throw new Error("目标节点还没有可运行的 Agent");
const agentName = process.env.AGENTOS_AGENT_NAME;
if (!agentName || !agents.some((agent) => agent.name === agentName)) {
  throw new Error(`请设置 AGENTOS_AGENT_NAME；可用 Agent: ${agents.map((agent) => agent.name).join(", ")}`);
}

const workspace = await client.createWorkspace("TypeScript quickstart");
const task = await client.createTask(
  workspace.workspace_id,
  "完成一次 TypeScript SDK 运行",
  "创建 Run 并读取事件",
  agentName,
);
const run = await client.createRun(
  agentName,
  task.task_id,
  workspace.workspace_id,
  "",
  `quickstart-${task.task_id}`,
);
console.log(run);

const terminalStatuses = new Set(["completed", "failed", "stopped", "timeout", "cancelled"]);
let current;
for (let attempt = 0; attempt < 60; attempt += 1) {
  current = await client.run(run.run_id);
  console.log("status:", current.status);
  if (current.status && terminalStatuses.has(current.status)) break;
  await new Promise((resolve) => setTimeout(resolve, 1000));
}
if (!current?.status || !terminalStatuses.has(current.status)) {
  throw new Error(`Run ${run.run_id} 在 60 秒内未进入终态`);
}

console.log(await client.logs(agentName));
for await (const event of client.iterEvents(0, 200, 5)) {
  if (event.run_id === run.run_id) console.log(event);
}
```

运行：

```bash
node quickstart.mjs
```

## 7. 创建自己的 Agent

在开发电脑的项目目录执行：

```bash
pvos new my-agent
pvos inspect my-agent
pvos test my-agent
pvos package my-agent
```

生成内容：

```text
my-agent/
├── agent.manifest
├── agent.py
└── README.md
my-agent.agent.tgz
```

`pvos test` 在开发电脑检查 Manifest 和 Python 语法，不要求本机有 GPU 或 PeakVisionOS
daemon。生成的默认 `agent.py` 会调用本机原语，所以完整运行必须在 AgentOS Ubuntu
节点上进行。

### Manifest 最小示例

```ini
name=my-agent
exec=/usr/bin/python3 /etc/agent-os/agents/my-agent/agent.py
primitives=agent,infer,memory,fs
memory_max=512M
cpu_quota=100%
autostart=no
restart=on-failure
sandbox=on
network=loopback
```

只申请业务真正需要的原语。例如只做本地推理的 Agent 可以使用
`primitives=infer`。详细字段见 [Manifest v1](manifest-v1.md)。

### 将开发包安装到测试节点

先从开发电脑上传：

```bash
scp my-agent.agent.tgz <ubuntu-user>@<AGENTOS_HOST>:/tmp/
ssh <ubuntu-user>@<AGENTOS_HOST>
```

然后在 AgentOS Ubuntu 节点执行。以下是可信开发环境的手动安装方式；生产环境应通过
签名 Registry 或组织的软件发布流程安装：

```bash
package_dir=$(mktemp -d)
tar -xzf /tmp/my-agent.agent.tgz -C "$package_dir"

sudo install -d -o root -g agentos -m 0750 \
  /etc/agent-os/agents/my-agent
sudo install -o root -g agentos -m 0750 \
  "$package_dir/agent.py" \
  /etc/agent-os/agents/my-agent/agent.py
sudo install -o root -g agentos -m 0640 \
  "$package_dir/agent.manifest" \
  /etc/agent-os/agents/my-agent.agent

sudo systemctl restart agentrund
agentrun spawn my-agent
agentrun status my-agent
agentrun logs my-agent
```

安装路径必须与 Manifest 的 `exec` 完全一致。每次安装前先执行 `pvos inspect`，
不要安装来源不明、摘要不匹配或包含 Token/私钥的包。

## 8. 在 AgentOS 节点调用四大原语

Agent 进入 Ubuntu 节点后，使用 `pvos.PeakVisionOS`：

```python
import pvos

aos = pvos.PeakVisionOS(caller="my-agent")

system = aos.system()
answer = aos.chat("根据当前系统状态给出一句建议")
aos.memory_write("本次任务已经完成")
memory = aos.memory_recall("任务状态")
file_info = aos.fs_put("result.txt", str(answer))
context = aos.ctx_assemble(4096, "汇总任务结果")

print(system, answer, memory, file_info, context)
```

在节点上检查服务和权限：

```bash
pvos doctor
agentrun list
inferctl status
```

当 `pvos doctor` 中某个 Socket 不存在时，应修复对应 daemon 或 Manifest 授权，
不要把 Socket 文件复制到开发电脑。

## 9. 测试与调试

不连接 AgentOS 节点也可以运行 SDK 合约测试：

```bash
PYTHONPATH=python python3 tests/test-local-client.py
PYTHONPATH=python python3 tests/test-sdk-http.py
cd typescript && npm test
```

常用诊断：

```bash
# SSH 隧道是否正常
curl -v http://127.0.0.1:17680/api/v1/health

# Token 是否有效
curl -H "Authorization: Bearer $AGENTOS_TOKEN" \
  http://127.0.0.1:17680/api/v1/agents

# SDK 是否来自当前虚拟环境
python3 -c "import pvos; print(pvos.__file__, pvos.__version__)"
```

## 10. 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| `Connection refused` | SSH 隧道未启动、端口不一致，或节点的 `agentosd` 未运行 |
| HTTP 401 | Token 缺失或已轮换；向管理员申请新 Token |
| HTTP 404 | Endpoint 缺少 `/api/v1`，或 Run/Agent 名称不存在 |
| HTTP 409 | Agent 已运行，或正在停止一个非运行态 Run |
| HTTP 502/503 | `agentrund` 拒绝请求或不可达；查看节点服务日志 |
| `AgentOSClientError: ... socket` | 在普通开发电脑调用了本机原语，或节点上 daemon/授权未就绪 |
| `agents()` 返回空列表 | 节点尚未安装 Agent Manifest，先部署一个 Agent |
| Run 一直是 `running` | 检查 `client.run(run_id)`、Agent 日志和节点 `agentrund` 状态 |

## 11. 提交与上线前检查

- 不提交 Token、密码、私钥、客户数据和模型文件。
- Manifest 只申请必要原语、网络和资源配额。
- 所有创建 Run 的自动化使用稳定的 `idempotency_key`。
- 对 `completed/failed/stopped/timeout/cancelled` 都做业务处理，不把 HTTP 200 等同于任务完成。
- 在 AMD395 或目标硬件上验证真实推理、日志、事件、停止和异常恢复。
- 生产环境使用 TLS/mTLS Gateway，不直接暴露本地控制面端口。

更多协议细节：

- [四个 PeakVisionOS SDK 代码样例](agent-examples.zh-CN.md)
- [控制面 HTTP API](control-plane-api.md)
- [Remote Gateway](remote-gateway.md)
- [Harness Adapter v1](harness-adapter-v1.md)
- [DeepSeek Harness 接入 PeakVisionOS SDK](deepseek-harness-integration.zh-CN.md)
- [独立 SDK 发布说明](standalone-sdk.md)
