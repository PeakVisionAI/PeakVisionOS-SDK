# PeakVisionOS TypeScript Client（源码预览）

TypeScript/Node.js 客户端，用 HTTPS 访问 PeakVisionOS Remote Gateway 控制面。
要求 Node.js 18+，也可在浏览器环境传入自定义 `fetch`。当前项目的公开发布主线是 Python/PyPI；本目录暂不发布到 NPM，适合从源码构建和集成测试。

## 从源码构建与调用

```bash
npm ci
npm run build
```

```ts
import { PeakVisionOS, GatewayError } from "./dist/index.js";

const client = new PeakVisionOS({
  endpoint: "https://gateway.example/gateway/v1/nodes/node-1/api/v1",
  token: process.env.PVOS_TOKEN,
});

try {
  const run = await client.createRun("code-agent", "task-1", "", "", "run-1");
  console.log(await client.run(run.run_id));
} catch (error) {
  if (error instanceof GatewayError) console.error(error.code, error.requestId);
}
```

## 覆盖范围

`PeakVisionOS` 提供 health、agents、workspaces、tasks、runs、logs、events
和增量 `iterEvents()`；`RemoteGateway` 额外提供节点注册、令牌轮换和 snapshot。
请求结果使用 Workspace、Task、Run、RunEvent 等类型，Run status 和错误字段
保持可编程。

每个读取方法和写入方法都可传 `{ signal }`：

```ts
const controller = new AbortController();
const pending = client.events(100, 0, { signal: controller.signal });
controller.abort();
```

SDK 会把 `code`、`message`、`status`、`retryable`、`requestId`、`details` 和
`retryAfter` 保留在 `GatewayError` 上。幂等 GET 自动有限重试；POST 只有提供
`Idempotency-Key` 才允许重试。

## 边界

该包只访问 Remote Gateway，不直接访问节点 Unix Socket，也不提供本地模型、
沙箱、RBAC、离线队列或证书轮换。需要在节点内开发 Agent，请使用 Python
`pvos.PeakVisionOS` 或直接阅读 [四个示例](../examples/README.md)。

## 验证

```bash
npm ci
npm test
```
