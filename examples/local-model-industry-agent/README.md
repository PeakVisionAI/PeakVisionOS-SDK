# 使用本地模型的行业 Agent

这个 Agent 通过 `inferd` 发现节点硬件和可用模型，可选地切换一个已安装模型，随后
使用本地模型完成行业任务。没有设置 `AGENT_MODEL` 时不会切换当前模型，适合共享
推理节点的只读验证。

## 输入与运行

```bash
export AGENT_INDUSTRY='机床运维'
export AGENT_TASK='根据报警描述给出排查顺序和停机风险'
# 可选：只填写节点上已经安装的模型名
export AGENT_MODEL='my-local-model'
agentrun spawn local-model-industry-agent
agentrun logs local-model-industry-agent
```

## 验收

日志中应有 `hardware`、`available_models` 和 `answer`。确认 `answer` 由节点本地
`inferd` 产生；Manifest 不授予网络、记忆或文件权限，行业数据不会因该 Agent 自动
写入外部服务。
