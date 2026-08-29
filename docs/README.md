# PeakVisionOS SDK 文档

本文档集对应 SDK `1.5.x`、Manifest v1、Harness Adapter v1 和
Control-plane HTTP v1。

## 从这里开始

| 目标 | 文档 |
| --- | --- |
| 在 VS Code 中开发 Agent | [PeakVisionOS Tools 扩展](../vscode/README.md) |
| 5 分钟跑通 SDK | [开发者快速开始](developer-quickstart.zh-CN.md) |
| 查看 Python/TS 方法 | [API 参考](api-reference.zh-CN.md) |
| 没有节点也能开发 | [Mock 与验收](mock-and-acceptance.zh-CN.md) |
| 编写真实 Agent | [四个代码样例](agent-examples.zh-CN.md) |
| 接入 Harness | [Harness Adapter v1](harness-adapter-v1.md) |
| 接入 DeepSeek Harness | [DeepSeek Harness 集成](deepseek-harness-integration.zh-CN.md) |
| 上生产前检查 | [安全指南](security-guide.zh-CN.md)与[测试指南](testing-guide.zh-CN.md) |
| 查看 P0/P1/P2 完成边界 | [就绪矩阵](readiness-matrix.zh-CN.md) |

## 契约与运维

- [Manifest v1](manifest-v1.md)
- [Control-plane API](control-plane-api.md)与[OpenAPI](../protocol/openapi.yaml)
- [错误与 Run 状态机](errors-and-state-machine.zh-CN.md)
- [Remote Gateway](remote-gateway.md)
- [兼容矩阵](compatibility-matrix.zh-CN.md)
- [旧 `agentos` 入口迁移](migration-pvos.zh-CN.md)
- [支持与弃用政策](support-and-deprecation.zh-CN.md)

本地 Mock 证明接口和工具链，不证明真实模型、硬件加速、权限隔离或 TLS。
发布前必须在目标 Ubuntu/PeakVisionOS 节点执行真机验收。
