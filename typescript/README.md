# @peakvision/agentos-sdk

For workstation setup, SSH tunneling and an end-to-end Run example, see the
[Chinese developer quickstart](../docs/developer-quickstart.zh-CN.md).

TypeScript/Node.js client for the AgentOS remote control plane. Node.js 18+ is
required because the package uses the built-in `fetch` implementation.

```bash
npm install @peakvision/agentos-sdk
```

```ts
import { AgentOS } from "@peakvision/agentos-sdk";

const aos = new AgentOS({
  endpoint: "https://gateway.example/gateway/v1/nodes/node-1/api/v1",
  token: process.env.AGENTOS_TOKEN,
});

console.log(await aos.health());
const run = await aos.createRun("demo");
console.log(await aos.logs("demo"));
```

The client includes bounded exponential retries for idempotent requests,
explicit idempotency-key support for retryable `createRun` calls, typed
Workspace/Task/Run/Event results, paged event reads and `iterEvents()`. It
also covers the complete documented node control plane. Use `RemoteGateway`
for Gateway node listing, registration, token rotation and snapshots.

This first release covers health, Agents, Runs, Logs and Events through
AgentOS `agentosd`/Gateway HTTP APIs. Four system primitives remain local Unix
Socket APIs until a versioned remote primitive protocol is published.

The client also covers Workspaces, Tasks, Run details, Gateway node registry
operations, bounded retries, idempotency-key Run creation, typed event pages
and async event iteration. Server-side RBAC, offline queues, certificate
rotation and remote primitive transport are outside this package.
