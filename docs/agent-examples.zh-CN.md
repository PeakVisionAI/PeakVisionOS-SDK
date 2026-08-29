# 四个 PeakVisionOS SDK 代码样例

本文把 SDK 的四种典型用法写成可安装 Agent。每个样例都能在普通开发电脑上完成
`inspect → test → package`，安装到 AgentOS Ubuntu 节点后由 `agentrund` 托管运行。

四个样例的共同结构是：

```text
AgentOS 节点上的 agent.py
  ├─ agentd：读取节点状态（可选）
  ├─ inferd：调用节点本地推理（不把数据发到公网）
  ├─ memoryd：长期记忆（按 Manifest 授权）
  ├─ fsd：内容寻址和语义文件（按 Manifest 授权）
  └─ ctxd：按 Token 预算组装记忆、文件和历史上下文
```

## 0. 通用准备

在开发电脑安装 SDK：

```bash
git clone https://github.com/PeakVisionAI/PeakVisionOS-SDK.git
cd PeakVisionOS-SDK
python3 -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\\Scripts\\Activate.ps1
python3 -m pip install -e ./python
```

普通开发电脑不需要 GPU，也不需要运行 AgentOS daemon。每个样例目录都可以先做静态
检查和打包：

```bash
cd examples/<sample-directory>
pvos inspect .
pvos test .
pvos package . --output <sample-directory>.agent.tgz
```

把包安装到节点后运行：

```bash
scp <sample-directory>.agent.tgz <ubuntu-user>@<AGENTOS_HOST>:/tmp/
# 按开发者快速开始文档完成可信开发环境安装
ssh <ubuntu-user>@<AGENTOS_HOST> agentrun spawn <agent-name>
ssh <ubuntu-user>@<AGENTOS_HOST> agentrun logs <agent-name>
```

详细的安装路径、`exec` 绝对路径和 Gateway 远程 Run 流程见
[开发者快速开始](developer-quickstart.zh-CN.md)。

## 1. 本地知识与文档处理 Agent

适合企业知识库、项目文档、设计规范和会议材料。Agent 从节点目录摄取 `.txt`/`.md`
文件，写入语义文件系统，检索相关片段，并通过 Context Gateway 生成摘要。

代码：[knowledge-docs-agent/agent.py](../examples/knowledge-docs-agent/agent.py)

```python
import os
from pathlib import Path
import pvos

directory = Path(os.environ.get("AGENT_DOCUMENT_DIR", "/var/lib/agentos/input"))
aos = pvos.PeakVisionOS(caller="knowledge-docs-agent")
for path in directory.rglob("*"):
    if path.suffix.lower() in {".txt", ".md"}:
        aos.fs_put(path.name, path.read_text(encoding="utf-8"))
query = os.environ.get("AGENT_QUERY", "总结关键结论和风险")
context = aos.ctx_assemble(6000, query, want_memory=False, k_files=5)
answer = aos.chat(f"问题：{query}\n上下文：{context['prompt']}")
print(answer)
```

Manifest 只授予 `agent,infer,fs`。完整可运行版本还处理目录为空、文本输入回退和
结构化 JSON 输出。详见该目录的 README。

## 2. 端侧代码、设计与办公 Agent

适合代码方案、接口定义、界面设计说明、会议纪要和办公文稿。模型在端侧生成结果，
Agent 把 Markdown 产物保存到语义文件系统，后续可以按任务语义检索。

代码：[edge-coding-design-office-agent/agent.py](../examples/edge-coding-design-office-agent/agent.py)

```python
import os
import pvos

task = os.environ.get("AGENT_TASK", "为订单接口设计测试用例")
aos = pvos.PeakVisionOS(caller="edge-coding-design-office-agent")
ctx = aos.ctx_assemble(7000, task, want_memory=False, want_files=True)
result = aos.chat(
    f"任务：{task}\n上下文：{ctx['prompt']}\n"
    "请输出方案、交付物、验证步骤和风险。"
)
aos.fs_put("work-result.md", str(result))
print(result)
```

该样例默认不授予 `memory`，也不自动修改工作区或调用外部 SaaS；需要写文件时应让
用户审核具体路径和内容。

## 3. 使用本地模型的行业 Agent

适合船舶设计、服装设计、机床运维、政务等需要端侧数据闭环的任务。Agent 先读取
`inferd` 的硬件和模型目录，可选切换一个已安装模型，再生成行业建议。

代码：[local-model-industry-agent/agent.py](../examples/local-model-industry-agent/agent.py)

```python
import os
import pvos

aos = pvos.PeakVisionOS(caller="local-model-industry-agent")
print("hardware:", aos.hwinfo())
print("models:", aos.models())
if os.environ.get("AGENT_MODEL"):
    aos.load(os.environ["AGENT_MODEL"])
answer = aos.chat(
    "你是机床运维行业助手。根据报警描述给出排查顺序和停机风险："
    + os.environ.get("AGENT_TASK", "主轴温升异常")
)
print(answer)
```

Manifest 只授予 `agent,infer`，不允许该样例把行业数据写入记忆或语义文件。`AGENT_MODEL`
只应填写节点上已经安装并经过验证的模型名。

## 4. 带长期记忆和语义检索的 Agent

适合客户偏好、项目约束、设备历史和持续运营任务。事实写入 `memoryd`，原文写入
`fsd`，两路召回结果再交给 Context Gateway 和本地模型。

代码：[long-memory-semantic-agent/agent.py](../examples/long-memory-semantic-agent/agent.py)

```python
import os
import pvos

aos = pvos.PeakVisionOS(caller="long-memory-semantic-agent")
fact = os.environ.get("AGENT_INPUT", "客户要求先列风险再列行动项")
query = os.environ.get("AGENT_QUERY", "客户有哪些交付要求？")
aos.memory_write(fact)
aos.fs_put("latest-note.txt", fact)
memories = aos.memory_recall(query)
files = aos.fs_search(query)
ctx = aos.ctx_assemble(6000, query, k_memory=5, k_files=5)
answer = aos.chat(f"记忆：{memories}\n文件：{files}\n上下文：{ctx['prompt']}")
print(answer)
```

该样例的 Manifest 授予 `memory`，部署时必须确认数据保留、租户隔离和遗忘策略。

## 5. 四个样例怎么选

| 需求 | 推荐样例 | 关键 API |
| --- | --- | --- |
| 文档入库、问答和摘要 | 知识与文档 | `fs_put`、`fs_search`、`ctx_assemble`、`chat` |
| 写代码/设计/办公交付物 | 代码设计办公 | `ctx_assemble`、`chat`、`fs_put` |
| 数据不能离开设备的行业推理 | 本地模型行业 | `hwinfo`、`models`、`load`、`chat` |
| 跨轮次保留事实和偏好 | 长期记忆语义 | `memory_write`、`memory_recall`、`fs_search`、`ctx_assemble` |

四个样例都可以由开发电脑上的 Gateway SDK 远程创建 Run、查询终态和读取日志，但
四大原语仍只能由 AgentOS 节点内的 Python SDK 通过 Unix Socket 调用。
