# Agent 示例

每个目录都包含 `agent.manifest`、`agent.py` 和运行说明。示例使用真实的
Python SDK API；开发电脑可做语法、Manifest 和打包检查，调用原语必须连接
已经启动 PeakVisionOS 服务的 Ubuntu 节点。

## 通用流程

```bash
python3 -m pip install peakvisionos-sdk
pvos inspect examples/knowledge-docs-agent
pvos test examples/knowledge-docs-agent
pvos package examples/knowledge-docs-agent
```

将 `.agent.tgz` 安装到节点后：

```bash
pvos install knowledge-docs-agent.agent.tgz
agentrun spawn knowledge-docs-agent
agentrun status knowledge-docs-agent
agentrun logs knowledge-docs-agent
```

| 示例 | 主要能力 | 最小授权 |
| --- | --- | --- |
| `knowledge-docs-agent` | 文档摄取、语义检索、摘要 | `agent,infer,fs` |
| `edge-coding-design-office-agent` | 代码、设计、办公产物 | `agent,infer,fs` |
| `local-model-industry-agent` | 本地模型与行业任务 | `agent,infer` |
| `long-memory-semantic-agent` | 长期记忆、语义文件、上下文 | `agent,infer,memory,fs` |
| `typescript-control-agent` | Gateway 控制面操作 | HTTPS token |

每个示例 README 都列出环境变量、验收输出和为什么授予这些权限。
