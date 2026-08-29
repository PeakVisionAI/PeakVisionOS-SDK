import * as cp from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import * as vscode from "vscode";

const output = vscode.window.createOutputChannel("PeakVisionOS");

type CommandContext = vscode.Uri | undefined;

function workspaceRoot(): string | undefined {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

async function resolveAgentPath(uri?: vscode.Uri): Promise<string | undefined> {
  if (uri) {
    const candidate = uri.fsPath.endsWith("agent.manifest") ? path.dirname(uri.fsPath) : uri.fsPath;
    if (fs.existsSync(path.join(candidate, "agent.manifest"))) {
      return candidate;
    }
  }

  const root = workspaceRoot();
  if (!root) {
    vscode.window.showErrorMessage("Open an Agent workspace before running this command.");
    return undefined;
  }
  const input = await vscode.window.showInputBox({
    prompt: "Agent directory or path relative to the workspace",
    value: ".",
    validateInput: (value) => value.trim() ? undefined : "Enter an Agent directory."
  });
  if (!input) {
    return undefined;
  }
  const candidate = path.resolve(root, input);
  if (!fs.existsSync(path.join(candidate, "agent.manifest"))) {
    vscode.window.showErrorMessage(`No agent.manifest found in ${candidate}`);
    return undefined;
  }
  return candidate;
}

function configuredEnvironment(): NodeJS.ProcessEnv {
  const config = vscode.workspace.getConfiguration("peakvisionos");
  const env = { ...process.env };
  const endpoint = config.get<string>("gatewayEndpoint", "").trim();
  const tokenName = config.get<string>("tokenEnvironmentVariable", "PVOS_TOKEN").trim();
  if (endpoint) {
    env.PVOS_ENDPOINT = endpoint;
  }
  if (tokenName && process.env[tokenName]) {
    env.PVOS_TOKEN = process.env[tokenName];
  }
  return env;
}

function pvosPath(): string {
  return vscode.workspace.getConfiguration("peakvisionos").get<string>("pvosPath", "pvos").trim() || "pvos";
}

function runPvos(args: string[], cwd?: string): Promise<number> {
  const command = pvosPath();
  const workdir = cwd || workspaceRoot() || process.cwd();
  output.show(true);
  output.appendLine(`$ ${command} ${args.join(" ")}`);
  output.appendLine(`cwd: ${workdir}`);

  return new Promise((resolve) => {
    const child = cp.spawn(command, args, {
      cwd: workdir,
      env: configuredEnvironment(),
      shell: false,
    });
    child.stdout.on("data", (chunk: Buffer) => output.append(chunk.toString()));
    child.stderr.on("data", (chunk: Buffer) => output.append(chunk.toString()));
    child.on("error", (error) => {
      output.appendLine(`\n[error] ${error.message}`);
      vscode.window.showErrorMessage(`Unable to run ${command}: ${error.message}`);
      resolve(127);
    });
    child.on("close", (code) => {
      const exitCode = code ?? 1;
      output.appendLine(`\n[exit ${exitCode}]`);
      if (exitCode === 0) {
        vscode.window.showInformationMessage("PeakVisionOS command completed.");
      } else {
        vscode.window.showErrorMessage(`PeakVisionOS command failed (exit ${exitCode}). See Output → PeakVisionOS.`);
      }
      resolve(exitCode);
    });
  });
}

async function newAgent(): Promise<void> {
  const root = workspaceRoot();
  if (!root) {
    vscode.window.showErrorMessage("Open a workspace before creating an Agent.");
    return;
  }
  const name = await vscode.window.showInputBox({
    prompt: "Agent name",
    placeHolder: "my-agent",
    validateInput: (value) => /^[A-Za-z_][A-Za-z0-9_-]*$/.test(value.trim()) ? undefined : "Use letters, numbers, hyphens or underscores; do not start with a number."
  });
  if (name) {
    await runPvos(["new", name.trim()], root);
  }
}

async function agentCommand(command: "inspect" | "test" | "package", uri?: vscode.Uri): Promise<void> {
  const agent = await resolveAgentPath(uri);
  if (!agent) {
    return;
  }
  const args = [command, agent];
  if (command === "package") {
    const configuredOutput = vscode.workspace.getConfiguration("peakvisionos").get<string>("packageOutputDirectory", "").trim();
    if (configuredOutput) {
      const outputDir = path.resolve(workspaceRoot() || path.dirname(agent), configuredOutput);
      fs.mkdirSync(outputDir, { recursive: true });
      args.push("-o", path.join(outputDir, `${path.basename(agent)}.agent.tgz`));
    }
  }
  await runPvos(args, workspaceRoot() || path.dirname(agent));
}

async function openSdkReadme(extensionRoot: vscode.Uri): Promise<void> {
  const readme = path.resolve(extensionRoot.fsPath, "README.md");
  if (!fs.existsSync(readme)) {
    vscode.window.showWarningMessage("The SDK README is not available in this installation.");
    return;
  }
  await vscode.commands.executeCommand("markdown.showPreview", vscode.Uri.file(readme));
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    output,
    vscode.commands.registerCommand("peakvisionos.doctor", () => runPvos(["doctor"])),
    vscode.commands.registerCommand("peakvisionos.newAgent", newAgent),
    vscode.commands.registerCommand("peakvisionos.inspectAgent", (uri?: CommandContext) => agentCommand("inspect", uri)),
    vscode.commands.registerCommand("peakvisionos.testAgent", (uri?: CommandContext) => agentCommand("test", uri)),
    vscode.commands.registerCommand("peakvisionos.packageAgent", (uri?: CommandContext) => agentCommand("package", uri)),
    vscode.commands.registerCommand("peakvisionos.acceptance", () => runPvos(["acceptance"])),
    vscode.commands.registerCommand("peakvisionos.openSdkReadme", () => openSdkReadme(context.extensionUri)),
  );
}

export function deactivate(): void {
  output.dispose();
}
