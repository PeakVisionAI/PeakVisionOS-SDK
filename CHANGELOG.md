# Changelog

## Unreleased

- Added a Chinese developer quickstart covering macOS, Windows and Linux setup,
  secure node connectivity, Python/TypeScript control-plane examples, Agent packaging,
  local primitive usage and troubleshooting.
- Added Apache-2.0 license files to the repository and both distributable packages.
- Added complete documented control-plane client coverage: Workspaces, Tasks, Run detail,
  event pages/iteration, and Gateway node registry/snapshot operations.
- Added bounded exponential retries for idempotent requests and explicit idempotency keys
  for retryable Run creation.
- Added structured Gateway/local transport errors, input validation, TypeScript resource
  types, Python `py.typed`, and Python 3.8/3.9/3.12 plus Node 18/20 CI matrices.
- Added dependency-free Python and TypeScript runtime contract tests.

The current package version remains `1.5.0-alpha.1` until a live Ubuntu AgentOS node,
Gateway TLS/mTLS and an ISV pilot complete release acceptance.
