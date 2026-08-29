# TypeScript 控制面 Agent

```bash
npm install @peakvision/pvos-sdk
PVOS_ENDPOINT=https://gateway.example/gateway/v1/nodes/node-1/api/v1 \
PVOS_TOKEN=short-lived-token node agent.mjs
```

该示例创建 Workspace、Task、Run，并读取终态、日志和事件。
