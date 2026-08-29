import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const commands = manifest.contributes.commands.map((command) => command.command);
for (const command of [
  "peakvisionos.doctor",
  "peakvisionos.newAgent",
  "peakvisionos.inspectAgent",
  "peakvisionos.testAgent",
  "peakvisionos.packageAgent",
  "peakvisionos.acceptance",
]) {
  assert.ok(commands.includes(command), `missing command: ${command}`);
}
assert.equal(manifest.main, "./dist/extension.js");
assert.equal(manifest.license, "Apache-2.0");
assert.equal(manifest.contributes.configuration.properties["peakvisionos.pvosPath"].default, "pvos");
assert.match(fs.readFileSync(path.join(root, "dist", "extension.js"), "utf8"), /runPvos/);
console.log("VS Code extension contract: OK");
