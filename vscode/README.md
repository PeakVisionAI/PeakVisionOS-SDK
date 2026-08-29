# PeakVisionOS Tools for VS Code

PeakVisionOS Tools is a VS Code extension for developing Agents with the PeakVisionOS SDK. It keeps the SDK CLI as the single execution boundary, so the extension does not duplicate Manifest validation, packaging, permissions, Gateway protocol, or Agent runtime behavior.

## What it provides

- Diagnose the local PeakVisionOS/AgentOS sockets with `pvos doctor`.
- Create a new Agent skeleton with `pvos new`.
- Inspect, test, and package an Agent from the Command Palette or an `agent.manifest` context menu.
- Run Gateway acceptance checks with the configured endpoint and token environment variable.
- Stream command output to the `PeakVisionOS` Output Channel.
- Open the SDK documentation from the Command Palette.

## Requirements

- VS Code 1.85 or newer.
- Python 3.8+ with the `peakvisionos-sdk` package installed, or a development checkout exposing the `pvos` command.
- A running PeakVisionOS node is only required for real socket or Gateway operations. Agent syntax, Manifest and packaging checks work on a development computer without a GPU.

## Download from GitHub

The current pre-release VSIX is available from the GitHub Release page:

- [Download `peakvisionos-vscode-0.1.0.vsix`](https://github.com/PeakVisionAI/PeakVisionOS-SDK/releases/download/vscode-v0.1.0/peakvisionos-vscode-0.1.0.vsix)
- [View all VS Code releases](https://github.com/PeakVisionAI/PeakVisionOS-SDK/releases?q=vscode)

In VS Code, open the Command Palette and choose **Extensions: Install from VSIX...**, then select the downloaded file.

Install the SDK first:

```bash
python -m pip install peakvisionos-sdk
pvos --help
```

## Build the extension from source

```bash
cd vscode
npm ci
npm run compile
npm run package
```

Then open the generated `.vsix` file in VS Code with **Extensions: Install from VSIX...**.

The GitHub workflow rebuilds this VSIX and attaches it to a release whenever a `vscode-v*` tag is pushed.

## Commands

Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and search for `PeakVisionOS`:

| Command | CLI call |
| --- | --- |
| Diagnose Local Node | `pvos doctor` |
| New Agent | `pvos new <name>` |
| Inspect Agent | `pvos inspect <agent>` |
| Test Agent | `pvos test <agent>` |
| Package Agent | `pvos package <agent>` |
| Run Gateway Acceptance | `pvos acceptance` |

Right-click an `agent.manifest` file in Explorer to inspect, test, or package its Agent.

## Settings

```json
{
  "peakvisionos.pvosPath": "pvos",
  "peakvisionos.gatewayEndpoint": "http://127.0.0.1:17680/api/v1",
  "peakvisionos.tokenEnvironmentVariable": "PVOS_TOKEN",
  "peakvisionos.packageOutputDirectory": ""
}
```

The extension never stores a Gateway token in VS Code settings. Set the configured environment variable before launching VS Code, or start VS Code from a shell that already contains it:

```bash
export PVOS_TOKEN="short-lived-token"
code .
```

For a local source checkout, set `peakvisionos.pvosPath` to the absolute path of the `pvos` executable in your virtual environment.

## Development

```bash
npm ci
npm test
```

Press `F5` in VS Code to launch an Extension Development Host. The extension is intentionally small: all SDK behavior remains implemented and tested in the Python package.

## Scope

This extension is a local developer tool. It does not replace the PeakVisionOS GUI, does not grant permissions, does not embed a model, and does not make Unix Socket protocols remotely accessible. Use the Python SDK and the [main documentation](../README.md) for Agent code and production deployment.
