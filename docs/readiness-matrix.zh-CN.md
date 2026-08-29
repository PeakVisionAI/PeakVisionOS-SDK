# SDK P0/P1/P2 就绪矩阵

这份矩阵区分“SDK 已修复/已验证”和“必须由 AgentOS 节点或后续协议完成”的边界，
避免把本地 Mock 结果当成真机发布结论。

| 优先级 | 项目 | 当前结果 | 证据/剩余工作 |
| --- | --- | --- | --- |
| P0 | memoryd `recall` 行协议 | 已修复 | SDK 只发送 `recall <query>`；`top_k` 客户端截断；`test-local-client.py` |
| P0 | pvos 包/CLI 未进 CI | 已修复 | CI 编译 `pvos`，运行 toolchain、Harness 和本地 socket 合约 |
| P0 | 无本地原语 Mock | 已修复 | `pvos.PrimitiveMock` 覆盖 agentd/inferd/memoryd/fsd 基础成功/失败路径 |
| P1 | HTTP 错误不可编程 | 已修复 | `GatewayError`/TS `GatewayError` 暴露 code、message、status、retryable、request id、details |
| P1 | Async API 不对齐 | 已修复 | events_page、iter_events、nodes、注册、轮换、snapshot；取消语义写入文档 |
| P1 | 包安装不具备回滚/边界 | 已修复 | 包大小/文件类型/路径校验、摘要/签名入口、权限、代码+Manifest 回滚 |
| P1 | 远程部署依赖目标机已有 pvos | 已缓解 | `pvos deploy --sdk-wheel` 支持先上传 wheel；无 wheel 时显式探测并失败 |
| P1 | Harness 工具边界不清 | 已修复 | 工具 Schema、白名单、审批、单工具 timeout、事件记录/回放 |
| P2 | README/协议分散和旧命名 | 已修复 | 根 README、语言 README、示例 README、协议 README、`docs/README.md` 统一入口 |
| P2 | 真实节点能力 | 未由 SDK 单独解决 | Ubuntu/AMD395 仍需验收 TLS/mTLS、真实推理、cgroup、权限和 Run 生命周期 |
| P2 | 远程原语、流式推理、namespace/多租户 | 未纳入 v1 稳定协议 | 需服务端协议、数据边界和安全评审后进入下一主版本 |

## 发布门禁

合并前必须通过 Python/TypeScript CI、OpenAPI 解析、Markdown 链接检查和 wheel/sdist
构建。发布前还必须保留一份真实 Ubuntu 节点验收记录，包括节点版本、硬件/后端、
授权拒绝、TLS 证书、Run 终态、日志和事件 ID。
