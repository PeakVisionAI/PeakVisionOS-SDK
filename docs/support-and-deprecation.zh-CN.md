# 支持与弃用政策

当前 SDK 为 Alpha：提供 P0/P1 合约的版本化支持，但不承诺远程原语、离线队列、
多租户 RBAC、证书自动轮换或 GPU 后端的跨硬件等未发布能力。

公共方法和协议字段至少提前一个 minor 版本标记弃用，并在 CHANGELOG 和迁移
指南中给出替代方案。`agentos` import/CLI 兼容别名保留至 1.x 迁移窗口结束；
新项目应立即使用 `pvos`。

Issue 请附 SDK 版本、Python/Node 版本、OS、Endpoint 类型、脱敏错误信息和
最小复现；不要上传 Token 或客户数据。
