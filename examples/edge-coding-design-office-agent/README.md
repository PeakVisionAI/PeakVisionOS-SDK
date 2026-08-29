# 端侧代码、设计与办公 Agent

使用节点本地模型生成代码方案、设计说明、接口定义、会议纪要或办公文稿，
并把最终产物保存到 fsd。

```bash
export AGENT_MODE=code       # code、design 或 office
export AGENT_TASK='为订单服务增加幂等创建接口并给出测试用例'
export AGENT_OUTPUT_NAME=order-api
agentrun spawn edge-coding-design-office-agent
agentrun logs edge-coding-design-office-agent
```

输出应包含 `artifact.name`、`artifact.store` 和 `answer`。示例只生成并保存结果，
不会自动修改宿主机代码或调用外部 SaaS；需要写工作区时必须单独设计文件工具和审批。
