# 本地 Mock 与端到端验收

## 本地开发

```bash
python3 -m pip install -e ./python
pvos mock-server --port 17680
```

另开终端：

```bash
export PVOS_ENDPOINT=http://127.0.0.1:17680/api/v1
pvos acceptance
```

Mock 会创建 Workspace、Task、Run，并返回 `run.started`、`run.completed`
事件和日志；不模拟真实推理、GPU、Unix Socket、cgroup 或隔离。

## Ubuntu/AMD395 验收

```bash
export PVOS_ENDPOINT=https://gateway.example/gateway/v1/nodes/amd395/api/v1
export PVOS_TOKEN="短期令牌"
pvos acceptance --agent my-agent --timeout 120
```

通过条件：health 为 `ok=true`；Workspace/Task/Run 创建成功；Run 在超时前
进入 `completed` 且 `exit_code=0`；可读日志；同一 Run 至少收到
`run.started` 和 `run.completed`。失败时保留输出的 ID，用 Gateway events
和 Ubuntu 服务日志定位。
