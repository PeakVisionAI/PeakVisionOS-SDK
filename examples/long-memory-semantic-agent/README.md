# 带长期记忆和语义检索的 Agent

这个 Agent 把任务事实写入 `memoryd`，把原文写入 `fsd`，再同时召回记忆和语义文件，
交给 Context Gateway 按 Token 预算组装，最后由本地模型回答新问题。

## 输入与运行

```bash
export AGENT_INPUT='项目代号是海风；客户要求所有交付先经过人工复核。'
export AGENT_QUERY='这个项目交付前有哪些要求？'
agentrun spawn long-memory-semantic-agent
agentrun logs long-memory-semantic-agent
```

重复运行几次后，用不同措辞设置 `AGENT_QUERY`，应仍能召回相同事实，体现语义检索而
不是关键词精确匹配。生产环境应根据租户或业务域设计记忆隔离和遗忘策略。

## 验收

输出 JSON 中应有 `memory_write`、`file_write`、`memory_hits`、`file_hits` 和
`answer`。Manifest 授予了长期记忆权限，部署前应确认该 Agent 可以保存哪些数据。
