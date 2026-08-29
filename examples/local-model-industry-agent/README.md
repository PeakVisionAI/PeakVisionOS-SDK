# 本地模型行业 Agent

通过 inferd 发现硬件和已安装模型，可选切换模型后完成行业任务。所有推理
留在节点本地。

```bash
export AGENT_INDUSTRY='机床运维'
export AGENT_TASK='根据报警描述给出排查顺序和停机风险'
export AGENT_MODEL='my-local-model'  # 可选，必须已安装
agentrun spawn local-model-industry-agent
```

日志应包含 `hardware`、`available_models` 和 `answer`。Manifest 不授予网络、
记忆或文件权限，适合验证本地模型后端。
