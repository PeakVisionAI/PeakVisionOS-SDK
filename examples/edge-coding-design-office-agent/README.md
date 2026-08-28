# 端侧代码、设计与办公 Agent

这个 Agent 使用 AgentOS 节点上的模型完成代码方案、界面设计说明、接口定义、会议
纪要或办公文稿，并把最终产物写入语义文件系统，方便后续检索和审计。

## 输入与运行

```bash
export AGENT_MODE=code
export AGENT_TASK='为订单服务增加幂等创建接口，给出 Python 示例和测试用例'
export AGENT_OUTPUT_NAME=order-api
agentrun spawn edge-coding-design-office-agent
agentrun logs edge-coding-design-office-agent
```

`AGENT_MODE` 可使用 `code`、`design` 或 `office`。该 Agent 只生成和保存结果，不会
自动修改宿主机代码或调用外部 SaaS；需要写入工作区时，应另行设计并审核文件工具。

## 验收

输出 JSON 中应有 `artifact.name`、`artifact.store` 和 `answer`，并可通过
`fs_search` 按任务描述检索保存的 Markdown 产物。
