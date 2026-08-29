# PeakVisionOS SDK

> 中文开发者入口：[AgentOS SDK 开发者快速开始](docs/developer-quickstart.zh-CN.md)
>
> Harness 接入：[DeepSeek Harness 接入 AgentOS SDK](docs/deepseek-harness-integration.zh-CN.md)
>
> 四个可运行样例：[AgentOS SDK Agent 样例](docs/agent-examples.zh-CN.md)

AgentOS SDK lets an independent ISV build against an installed AgentOS node
without cloning or installing the AgentOS daemon source tree. This repository
publishes two clients from one versioned protocol contract:

- `peakvisionos-sdk` on PyPI: local Unix Socket primitives, Agent runtime helpers,
  Harness adapter, CLI and remote Gateway client.
- `@peakvision/pvos-sdk` on NPM: TypeScript/Node.js remote Gateway client.

## Install

```bash
python3 -m pip install peakvisionos-sdk
npm install @peakvision/pvos-sdk
```

The packages contain client libraries only. The target machine must already
run AgentOS services for local primitive or Gateway calls.

The Python `GatewayClient` and TypeScript `AgentOS` clients cover the complete
documented node control plane: health, agents, workspaces, tasks, runs (list,
create, detail and stop), logs and event pages/iteration. `GatewayRegistryClient`
(Python) and `RemoteGateway` (TypeScript) cover Gateway node listing,
registration, token rotation and snapshots.

The production baseline also includes bounded exponential retries, structured
HTTP/local transport errors, input validation, idempotency-key support for
retryable Run creation, typed TypeScript results, and a Python `py.typed`
marker. These guarantees are covered by the repository contract tests.

## Choose a transport

| Use case | Client | Transport | Stable operations |
| --- | --- | --- | --- |
| Agent code on an AgentOS node | `pvos.PeakVisionOS` | Unix Socket | agentd, inferd, memoryd, fsd, agentrund, ctxd |
| Developer workstation, GUI or CI | `pvos.GatewayClient` / TypeScript `PeakVisionOS` | HTTP/HTTPS Gateway | health, agents, runs, logs, events |

The four system primitives are intentionally local-only until a versioned
Remote Primitive Protocol is released. The Gateway clients must not be used as
an undocumented proxy for primitive sockets.

## Quick start

```python
from pvos import GatewayClient

client = GatewayClient(
    endpoint="https://gateway.example/gateway/v1/nodes/node-1/api/v1",
    token="<short-lived-token>",
)
print(client.health())
run = client.create_run("code-agent", task_id="task-001")
print(client.logs("code-agent"))
```

For local Agent development, see [Python SDK](python/README.md). For the
TypeScript client, see [TypeScript SDK](typescript/README.md). Shared contracts
and compatibility rules are in [protocols](protocol/README.md).

## Development and tests

```bash
python3 -m pip install -e ./python
PYTHONPATH=python python3 tests/test-sdk-http.py
cd typescript && npm ci && npm test
```

The HTTP contract test uses a standard-library mock server and does not require
GPU hardware or a running AgentOS node. Real acceptance must still verify Unix
Socket permissions, Gateway TLS, authorization and Run lifecycle on Ubuntu.

For a complete local flow, run `pvos mock-server` in one terminal and
`pvos acceptance` in another. See [Mock and acceptance](docs/mock-and-acceptance.zh-CN.md).

## Releases

Push an `sdk-v*` tag to run `.github/workflows/publish-sdk.yml`. Python uses
PyPI Trusted Publishing through GitHub OIDC. NPM uses the repository
`NPM_TOKEN` secret and publishes provenance metadata. Update both package
versions together and run CI before tagging.

See [standalone SDK release guide](docs/standalone-sdk.md) for credential,
compatibility and ISV onboarding details.

开发资料：

- [API Reference](docs/api-reference.zh-CN.md) 与 [OpenAPI](protocol/openapi.yaml)
- [本地 Mock/端到端验收](docs/mock-and-acceptance.zh-CN.md)
- [开发环境开通](docs/developer-environment.zh-CN.md)
- [错误与状态机](docs/errors-and-state-machine.zh-CN.md)、[安全](docs/security-guide.zh-CN.md)、[测试](docs/testing-guide.zh-CN.md)
- [版本兼容](docs/compatibility-matrix.zh-CN.md)、[迁移](docs/migration-pvos.zh-CN.md)、[FAQ](docs/faq.zh-CN.md)

New API details are in the [API Reference](docs/api-reference.zh-CN.md), with
the machine-readable contract in [`protocol/openapi.yaml`](protocol/openapi.yaml).

Release changes are tracked in [CHANGELOG.md](CHANGELOG.md).

This is an SDK client release, not a replacement for the AgentOS operating
system. Remote primitive calls, offline command queues, multi-tenant RBAC and
certificate lifecycle management remain server-side or future protocol work.
