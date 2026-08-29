# PeakVisionOS SDK Protocols

This directory records the public contracts shared by the standalone SDKs.

| Contract | Version | Source of truth |
| --- | --- | --- |
| Manifest | v1 | [`../docs/manifest-v1.md`](../docs/manifest-v1.md) |
| Harness Adapter | v1 | [`../docs/harness-adapter-v1.md`](../docs/harness-adapter-v1.md) |
| Control-plane HTTP | v1 | [`../docs/control-plane-api.md`](../docs/control-plane-api.md) and [`openapi.yaml`](openapi.yaml) |
| Run/Event types | v1 | [`../python/agentos/harness.py`](../python/agentos/harness.py) |

An SDK minor release may add optional fields and methods. Removing a field,
changing status semantics or changing authentication requires a new protocol
major version. SDK packages must never embed tokens, private keys or customer
data.

The product name is PeakVisionOS and the new Python import is `pvos`. The
former `agentos` import remains a compatibility alias during the 1.x migration
window. The TypeScript package is `@peakvision/pvos-sdk`; new projects should
use this name.
