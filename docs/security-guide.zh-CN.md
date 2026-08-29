# SDK 安全开发指南

- 使用短期 Token 或 TLS/mTLS；Token 通过环境变量、密钥管理器或 CI Secret 注入。
- 每个 ISV 使用独立 Token，最小化可访问的节点和 Agent；定期轮换并验证旧 Token 失效。
- Manifest 只申请必要的 `agent/infer/memory/fs` 原语、网络模式和 CPU/内存配额。
- 不把客户数据、模型文件、私钥、Token 写入 Agent 包、事件 payload 或日志。
- `pvos install` 会拒绝包内符号链接和目录穿越；安装前校验 Manifest 和包摘要。
- 生产 Gateway 使用 HTTPS，节点本地控制面只监听回环或受控网段。
- 未授权远程原语调用在 v1 中不可用；不要自行转发 Unix Socket。
- 依赖升级和发布必须通过 CI，审查构建产物，避免把 `node_modules` 或缓存发布。
