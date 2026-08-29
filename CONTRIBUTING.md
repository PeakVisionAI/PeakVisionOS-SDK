# Contributing to PeakVisionOS SDK

感谢参与 PeakVisionOS SDK。新代码请使用 `pvos` / `@peakvision/pvos-sdk`；
`agentos` 仅用于兼容测试。

## 开发流程

1. Fork 或创建分支，说明要解决的问题和兼容影响。
2. 运行 Python 合约/工具链测试和 `cd typescript && npm test`。
3. 协议或公共 API 变更必须同时更新 `protocol/openapi.yaml`、API Reference、
   兼容矩阵和 CHANGELOG。
4. 不提交 Token、证书、客户数据、模型文件、构建缓存或 `node_modules`。

Pull Request 应包含变更目的、测试命令、迁移说明和已知限制。
