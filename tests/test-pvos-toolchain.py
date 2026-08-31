#!/usr/bin/env python3
"""P0 toolchain contracts: pvos import, mock control plane and package lifecycle."""
import pathlib
import tempfile
import threading
import tarfile
import sys
import os
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import pvos  # noqa: E402
from pvos.acceptance import run_acceptance  # noqa: E402
from pvos.mock_server import create_mock_server  # noqa: E402
from pvos.package_manager import deploy_package, install_package, uninstall_package  # noqa: E402


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

    original_source = (install_root / "knowledge-docs-agent" / "agent.py").read_bytes()
    original_manifest = (install_root / "knowledge-docs-agent.agent").read_bytes()
    real_replace = os.replace

    failure_injected = [False]

    def fail_manifest_switch(source_path, destination_path):
        if str(destination_path).endswith("knowledge-docs-agent.agent") and not failure_injected[0]:
            failure_injected[0] = True
            raise OSError("simulated manifest switch failure")
        return real_replace(source_path, destination_path)

    with mock.patch("pvos.package_manager.os.replace", side_effect=fail_manifest_switch):
        try:
            install_package(bundle, install_root)
        except OSError:
            pass
        else:
            raise AssertionError("simulated install failure must propagate")
    assert (install_root / "knowledge-docs-agent" / "agent.py").read_bytes() == original_source
    assert (install_root / "knowledge-docs-agent.agent").read_bytes() == original_manifest
    assert uninstall_package("knowledge-docs-agent", install_root)

    wheel = temp / "peakvisionos_sdk.whl"
    wheel.write_bytes(b"test wheel")
    with mock.patch("pvos.package_manager.subprocess.run") as run:
        commands = deploy_package(
            bundle,
            "qwer@example",
            sdk_wheel=wheel,
            dry_run=False,
            tty=False,
        )
    assert commands[1] == [
        "ssh", "qwer@example", "--", "sudo", "-n", "-H", "python3", "-m", "pip",
        "install", "--no-index", "--break-system-packages", "/tmp/peakvisionos_sdk.whl",
    ]
    assert commands[-1][-4:] == ["install", "/tmp/demo.agent.tgz", "--root", "/etc/agent-os/agents"]
    assert [call.args[0] for call in run.call_args_list] == commands

server.shutdown()
print("PeakVisionOS toolchain contract: OK")
