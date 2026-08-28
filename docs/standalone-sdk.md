# Standalone SDK Release Guide

This repository is the public distribution boundary for AgentOS client SDKs.
It is intentionally independent from the AgentOS operating-system repository:
daemon implementation, GUI, model files and Ubuntu image tooling do not ship
here.

## Repository layout

```text
python/       Python package and agentos CLI
typescript/   TypeScript/NPM package
protocol/     Versioned public contract index
docs/         Manifest, Harness and Gateway contract details
tests/        Dependency-free SDK contract tests
```

## Package responsibilities

`agentos-sdk` is for Agent code running on an AgentOS node. Its `AgentOS` client
connects to local Unix Sockets and exposes the system primitives and runtime
helpers. `GatewayClient` is for developer tools and automation outside the
node; it only calls the stable control-plane HTTP API.

`@peakvision/agentos-sdk` targets Node.js 18+ and browsers with a compatible
`fetch` implementation. It provides the same remote control-plane operations.

Neither package installs AgentOS itself, downloads models, or grants a caller
new permissions. Manifest authorization and Gateway token policy remain owned
by the target AgentOS deployment.

## Versioning

The current alpha line is `1.5.x` and maps to Manifest v1, Harness Adapter v1,
Control-plane HTTP v1 and Run/Event v1. Adding optional fields is minor-version
compatible. Removing fields, changing status semantics, changing auth, or
introducing Remote Primitive Protocol requires a protocol major version.

## Publishing checklist

1. Update `python/pyproject.toml` and `typescript/package.json` to the same release intent.
2. Run Python syntax, HTTP contract, package build and TypeScript build checks.
3. Confirm the package contents contain no tokens, private keys, customer data, `node_modules` or build caches.
4. Configure PyPI Trusted Publishing for the GitHub repository and environment.
5. Configure a least-privilege `NPM_TOKEN` repository secret for `@peakvision/agentos-sdk`.
6. Push a signed or protected `sdk-v<version>` tag and verify both registry pages.
7. Announce the compatibility line and migration notes to ISVs and community maintainers.

Publish alpha builds to a pre-release channel first. Do not claim remote
primitive support until the corresponding protocol and server implementation
are both released and tested.
