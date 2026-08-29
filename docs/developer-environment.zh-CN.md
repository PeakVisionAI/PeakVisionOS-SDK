# 开发者环境开通

节点管理员需要向每个 ISV 提供：Gateway Endpoint、节点 ID、可用 Agent、
开发 Token 或 mTLS 证书、Manifest 原语和资源配额、包安装目录，以及
Token 轮换和故障联系人。

Token 只通过密码管理器或 CI Secret 传递，不写入代码、Manifest、日志或
Agent 包。生产环境不直接暴露本地控制面端口；每个 ISV 使用独立 Token。
开发环境没有节点时，先使用 `pvos mock-server`。
