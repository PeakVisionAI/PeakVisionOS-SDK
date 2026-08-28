# @peakvision/agentos-sdk

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

This first release covers health, Agents, Runs, Logs and Events through
AgentOS `agentosd`/Gateway HTTP APIs. Four system primitives remain local Unix
Socket APIs until a versioned remote primitive protocol is published.
