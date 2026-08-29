# 本地知识与文档 Agent

读取节点本地 `.txt`/`.md`，写入 fsd，按自然语言检索，再由 inferd 生成摘要。

```bash
export AGENT_DOCUMENT_DIR=/var/lib/agentos/input
export AGENT_QUERY='总结项目风险和行动项'
agentrun spawn knowledge-docs-agent
agentrun logs knowledge-docs-agent
```

没有目录时可设置 `AGENT_DOCUMENT_TEXT` 做单文本验收。日志应包含
`documents_ingested`、`semantic_hits` 和 `answer`。该 Agent 不授予 memory 权限，
文档默认不离开节点。
