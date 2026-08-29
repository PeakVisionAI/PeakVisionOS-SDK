"""Install and deploy signed-or-local Agent bundles with path validation."""
from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import tarfile
import tempfile

from .manifest import validate_manifest_file


SAFE_REMOTE = re.compile(r"^[A-Za-z0-9_.@:-]+$")


def _safe_extract(bundle, destination):
    root = destination.resolve()
    for member in bundle.getmembers():
        target = (root / member.name).resolve()
        if target != root and root not in target.parents:
            raise ValueError("package path escapes destination: " + member.name)
        if member.issym() or member.islnk():
            raise ValueError("package links are not allowed: " + member.name)
    bundle.extractall(root)


def inspect_package(package):
    package = pathlib.Path(package).resolve()
    if not package.is_file():
        raise FileNotFoundError(str(package))
    temporary = tempfile.TemporaryDirectory(prefix="pvos-package-")
    staging = pathlib.Path(temporary.name)
    try:
        with tarfile.open(package, "r:gz") as bundle:
            _safe_extract(bundle, staging)
        manifest_path = staging / "agent.manifest"
        source_path = staging / "agent.py"
        if not manifest_path.is_file() or not source_path.is_file():
            raise ValueError("Agent package must contain agent.manifest and agent.py")
        manifest, errors = validate_manifest_file(manifest_path)
        if errors:
            raise ValueError("invalid manifest: " + "; ".join(errors))
        return temporary, staging, manifest
    except Exception:
        temporary.cleanup()
        raise


def install_package(package, root="/etc/agent-os/agents"):
    temporary, staging, manifest = inspect_package(package)
    root_path = pathlib.Path(root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    destination = root_path / manifest.name
    manifest_destination = root_path / (manifest.name + ".agent")
    work = pathlib.Path(tempfile.mkdtemp(prefix="." + manifest.name + "-", dir=str(root_path)))
    backup = root_path / ("." + manifest.name + ".backup")
    try:
        for item in staging.iterdir():
            shutil.copytree(item, work / item.name) if item.is_dir() else shutil.copy2(item, work / item.name)
        if backup.exists():
            shutil.rmtree(backup)
        if destination.exists():
            os.replace(destination, backup)
        os.replace(work, destination)
        temp_manifest = root_path / ("." + manifest.name + ".agent.tmp")
        shutil.copy2(destination / "agent.manifest", temp_manifest)
        os.replace(temp_manifest, manifest_destination)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if work.exists():
            shutil.rmtree(work)
        if backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    finally:
        temporary.cleanup()
    return {"name": manifest.name, "root": str(root_path), "code": str(destination), "manifest": str(manifest_destination)}


def uninstall_package(name, root="/etc/agent-os/agents"):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,63}", name):
        raise ValueError("invalid Agent name")
    root_path = pathlib.Path(root).resolve()
    destination = root_path / name
    manifest = root_path / (name + ".agent")
    removed = []
    if destination.exists():
        shutil.rmtree(destination)
        removed.append(str(destination))
    if manifest.exists():
        manifest.unlink()
        removed.append(str(manifest))
    return removed


def deploy_package(package, host, root="/etc/agent-os/agents", sudo=True, dry_run=False):
    package = pathlib.Path(package).resolve()
    if not package.is_file():
        raise FileNotFoundError(str(package))
    if not SAFE_REMOTE.fullmatch(host):
        raise ValueError("host contains unsupported characters")
    remote_package = "/tmp/" + package.name
    install = (["sudo"] if sudo else []) + ["pvos", "install", remote_package, "--root", root]
    commands = [["scp", str(package), host + ":" + remote_package], ["ssh", host, "--", *install]]
    if not dry_run:
        for command in commands:
            subprocess.run(command, check=True)
    return commands
