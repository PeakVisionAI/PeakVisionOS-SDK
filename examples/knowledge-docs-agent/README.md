# 本地知识与文档处理 Agent

这个 Agent 从节点本地目录读取 `.txt`/`.md` 文档，写入 AgentOS 语义文件系统，按
自然语言检索相关内容，再通过 Context Gateway 和本地模型生成摘要。

## 输入与运行

```bash
export AGENT_DOCUMENT_DIR=/var/lib/agentos/input
export AGENT_QUERY='总结项目风险和下一步行动'
agentrun spawn knowledge-docs-agent
agentrun logs knowledge-docs-agent
```

没有准备目录时可用一段文本验收：

```bash
export AGENT_DOCUMENT_TEXT='项目将在下周交付；风险是测试覆盖不足。'
export AGENT_QUERY='列出风险和行动项'
```

## 验收

日志中应包含 `documents_ingested`、`semantic_hits` 和模型 `answer`。文档不会离开
AgentOS 节点；Manifest 只授予感知、推理和语义文件能力，不授予长期记忆。
