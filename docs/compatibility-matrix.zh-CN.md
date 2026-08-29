# 版本兼容矩阵

| SDK | 产品/协议 | Python | Node.js | 状态 |
| --- | --- | --- | --- | --- |
| `peakvisionos-sdk 1.5.x` | PeakVisionOS/AgentOS Manifest v1、Control Plane v1、Harness v1 | 3.8+ | - | Alpha |
| TypeScript 源码客户端 `1.5.x` | Control Plane v1 | - | 18+ | 源码预览，未发布 NPM |

1.x 允许新增可选字段和方法；删除字段、改变状态语义、认证方式或远程原语
协议必须升级协议主版本。旧 `agentos` import/CLI 在 1.x 迁移窗口内保留，
新项目应使用 `pvos`。Python 发布时更新包版本和 CHANGELOG；TypeScript 客户端暂从源码构建。
