import assert from "node:assert/strict";
import { AgentOS, GatewayError, RemoteGateway } from "../dist/index.js";

let calls = 0;
const fetcher = async (url, init = {}) => {
  calls += 1;
  assert.equal(init.headers.get("Accept"), "application/json");
  assert.equal(init.headers.get("Authorization"), "Bearer test-token");
  if (url.endsWith("/health") && calls === 1) {
    return new Response(JSON.stringify({ error: "temporary" }), { status: 503 });
  }
  if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true }), { status: 200 });
  if (url.endsWith("/workspaces")) return new Response(JSON.stringify({ workspaces: [{ workspace_id: "ws-1", name: "demo" }] }), { status: 200 });
  if (url.endsWith("/tasks")) return new Response(JSON.stringify({ tasks: [{ task_id: "task-1", title: "demo" }] }), { status: 200 });
  if (url.endsWith("/events?limit=200&after=0")) return new Response(JSON.stringify({ events: [{ event_id: 1, type: "run.completed" }] }), { status: 200 });
  if (url.endsWith("/nodes")) return new Response(JSON.stringify({ nodes: [{ node_id: "node-1", name: "AMD395" }] }), { status: 200 });
  return new Response(JSON.stringify({}), { status: 200 });
};

const client = new AgentOS({ endpoint: "http://127.0.0.1/api/v1", token: "test-token", fetch: fetcher, retry: { backoffMs: 0 } });
assert.equal((await client.health()).ok, true);
assert.equal((await client.workspaces())[0].workspace_id, "ws-1");
assert.equal((await client.tasks())[0].task_id, "task-1");
assert.equal((await client.events())[0].event_id, 1);
assert.equal((await client.run("run-1")).run_id, undefined);
assert.equal(calls, 6);

const registry = new RemoteGateway({ endpoint: "http://127.0.0.1/gateway/v1", token: "test-token", fetch: fetcher, retry: { backoffMs: 0 } });
assert.equal((await registry.nodes())[0].node_id, "node-1");

try {
  await new AgentOS({ endpoint: "http://127.0.0.1/api/v1", fetch: async () => new Response("bad", { status: 401 }) }).health();
} catch (error) {
  assert.ok(error instanceof GatewayError);
}

console.log("TypeScript SDK contract: OK");
