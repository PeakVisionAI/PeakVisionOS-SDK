#!/usr/bin/env python3
"""P0 toolchain contracts: pvos import, mock control plane and package lifecycle."""
import pathlib
import tempfile
import threading
import tarfile
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import pvos  # noqa: E402
from pvos.acceptance import run_acceptance  # noqa: E402
from pvos.mock_server import create_mock_server  # noqa: E402
from pvos.package_manager import install_package, uninstall_package  # noqa: E402


server = create_mock_server(port=0, token="dev-token")
threading.Thread(target=server.serve_forever, daemon=True).start()
endpoint = "http://127.0.0.1:%d/api/v1" % server.server_port
result = run_acceptance(endpoint, token="dev-token", timeout=5)
assert result["ok"] is True
assert result["status"] == "completed"

with tempfile.TemporaryDirectory(prefix="pvos-test-") as temp:
    temp = pathlib.Path(temp)
    source = ROOT / "examples" / "knowledge-docs-agent"
    bundle = temp / "demo.agent.tgz"
    with tarfile.open(bundle, "w:gz") as archive:
        archive.add(source / "agent.manifest", arcname="agent.manifest")
        archive.add(source / "agent.py", arcname="agent.py")
    install_root = temp / "installed"
    installed = install_package(bundle, install_root)
    assert installed["name"] == "knowledge-docs-agent"
    assert (install_root / "knowledge-docs-agent" / "agent.py").is_file()
    assert uninstall_package("knowledge-docs-agent", install_root)

server.shutdown()
print("PeakVisionOS toolchain contract: OK")
