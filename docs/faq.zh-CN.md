# FAQ

**没有 GPU 能不能开发？** 可以。使用 `pvos mock-server` 和合约测试开发控制面
与 Harness；真实推理必须在 Ubuntu/AMD395 或目标硬件验收。

**SDK 会安装完整操作系统吗？** 不会。SDK 只提供客户端、CLI 和 Agent 包工具；
节点必须预先安装 PeakVisionOS/AgentOS 服务。

**为什么四大原语不能从远程 Gateway 调用？** v1 尚未冻结远程原语协议；本地
Unix Socket 权限由 Manifest 和 agentrund 控制。

**Run 返回 HTTP 200 是不是成功？** 不是。读取 `status`，只有 `completed` 且
`exit_code=0` 才是业务成功。

**如何重试创建 Run？** 每次使用稳定的 `idempotency_key`；没有幂等键的 POST
不会自动重试。
