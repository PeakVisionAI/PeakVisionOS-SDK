# AgentOS SDK Agent 示例

这些示例是四个可以用 `pvos package` 打包、安装到 AgentOS Ubuntu 节点并由
`agentrund` 托管运行的最小 Agent。它们不是模拟服务：代码使用 Python SDK 的真实
Unix Socket API，模型和数据仍由节点上的 AgentOS 服务提供。

## 运行方式

在开发电脑上安装 SDK 后，进入任意示例目录：

```bash
agentos inspect .
agentos test .
pvos package . --output my-agent.agent.tgz
```

然后按照[开发者快速开始](../docs/developer-quickstart.zh-CN.md#7-创建自己的-agent)
上传并安装到 Ubuntu 节点。安装完成后：

```bash
agentrun spawn <agent-name>
agentrun status <agent-name>
agentrun logs <agent-name>
```

直接运行 `python3 agent.py` 只适合已经安装并运行 AgentOS daemon 的节点；普通开发
电脑可以做 Manifest 检查、Python 语法检查和打包，但不能调用节点本地原语。

## 示例索引

| 示例 | 目录 | 主要能力 | 默认授权 |
| --- | --- | --- | --- |
| 本地知识与文档处理 Agent | `knowledge-docs-agent` | 文档摄取、语义检索、上下文摘要 | `agent,infer,fs` |
| 端侧代码设计办公 Agent | `edge-coding-design-office-agent` | 本地任务规划、产物生成、语义文件保存 | `agent,infer,fs` |
| 使用本地模型的行业 Agent | `local-model-industry-agent` | 硬件/模型发现、可选模型切换、行业回答 | `agent,infer` |
| 长期记忆与语义检索 Agent | `long-memory-semantic-agent` | 长期记忆、语义文件、上下文组装 | `agent,infer,memory,fs` |

每个目录的 README 都说明输入环境变量、安装后的验收标准和最小权限原因。
