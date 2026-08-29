# 长期记忆与语义检索 Agent

把事实写入 memoryd，把原文写入 fsd，同时召回两者，由 ctxd 按 Token 预算组装，
再交给 inferd 回答。

```bash
export AGENT_INPUT='项目代号是海风；交付前必须人工复核。'
export AGENT_QUERY='这个项目交付前有哪些要求？'
agentrun spawn long-memory-semantic-agent
```

输出应包含 `memory_write`、`file_write`、`memory_hits`、`file_hits` 和 `answer`。
生产部署前必须定义租户/项目 namespace、保留期限和遗忘策略。
