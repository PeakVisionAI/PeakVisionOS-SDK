# 错误处理与 Run 状态机

## 传输错误

| 错误 | 处理 | 是否重试 |
| --- | --- | --- |
| `PVOSClientError` | 检查节点 Socket、Manifest 授权和对应 daemon | 仅在业务允许时 |
| HTTP 401 | 申请/轮换 Token，确认 Endpoint | 否 |
| HTTP 404 | 检查资源 ID 和 `/api/v1` 前缀 | 否 |
| HTTP 409 | 读取当前 Run 状态，避免重复启动 | 否 |
| HTTP 502/503 | 检查 agentrund、Gateway 到节点的连接 | GET 可重试 |
| HTTP 408/425/429/500/504 | 遵循 SDK 有上限的退避策略 | GET 或幂等 POST |

## Run 状态

```text
created -> running -> completed
                   -> failed
                   -> timeout
                   -> cancelled
                   -> stopped
```

`created` 和 `running` 不是成功。只有 `completed` 且 `exit_code=0` 才是
业务成功。停止请求与自然退出可能竞态，客户端必须以服务端最终状态为准。
创建 Run 时使用稳定的 `idempotency_key`，断线重试不会重复创建。

事件按递增 `event_id` 分页读取；断线后从最后一个已确认 ID 继续。v1 不
保证跨不同 Run 的全局因果顺序，只保证同一事件流的 ID 单调递增。
