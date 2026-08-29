import { PeakVisionOS } from "@peakvision/pvos-sdk";

const client = new PeakVisionOS({
  endpoint: process.env.PVOS_ENDPOINT,
  token: process.env.PVOS_TOKEN,
});
const workspace = await client.createWorkspace("TypeScript demo");
const task = await client.createTask(workspace.workspace_id, "Run demo", "", "demo");
const run = await client.createRun("demo", task.task_id, workspace.workspace_id, "", `demo-${Date.now()}`);
let current = run;
while (!["completed", "failed", "stopped", "timeout", "cancelled"].includes(current.status ?? "")) {
  await new Promise((resolve) => setTimeout(resolve, 250));
  current = await client.run(run.run_id);
}
console.log({ run: current, logs: await client.logs("demo"), events: await client.events() });
