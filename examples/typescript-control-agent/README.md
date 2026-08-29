# TypeScript 控制面 Agent

这个示例不访问本地原语，而是通过 Remote Gateway 创建 Workspace、Task、Run，
读取终态、日志和事件。

```bash
cd ../../typescript
npm ci
npm run build
cd ../examples/typescript-control-agent
PVOS_ENDPOINT=https://gateway.example/gateway/v1/nodes/node-1/api/v1 \
PVOS_TOKEN=short-lived-token node agent.mjs
```

示例直接引用仓库内构建产物；TypeScript 客户端当前不发布到 NPM。

真实环境请使用短期令牌和 HTTPS；不要把令牌写进源码、Manifest 或日志。
