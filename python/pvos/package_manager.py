"""Install and deploy signed-or-local Agent bundles with path validation."""
from __future__ import annotations

import os
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

from .manifest import validate_manifest_file


SAFE_REMOTE = re.compile(r"^[A-Za-z0-9_.@:-]+$")
MAX_PACKAGE_BYTES = 256 * 1024 * 1024
MAX_PACKAGE_FILES = 4096


def _safe_extract(bundle, destination):
    root = destination.resolve()
    members = bundle.getmembers()
    if len(members) > MAX_PACKAGE_FILES:
        raise ValueError("Agent package contains too many files")
    unpacked = sum(member.size for member in members if member.isfile())
    if unpacked > MAX_PACKAGE_BYTES:
        raise ValueError("Agent package exceeds the unpacked size limit")
    for member in members:
        target = (root / member.name).resolve()
        if target != root and root not in target.parents:
            raise ValueError("package path escapes destination: " + member.name)
        if not (member.isfile() or member.isdir()):
            raise ValueError("package special files and links are not allowed: " + member.name)
    bundle.extractall(root, members=members)


def inspect_package(package, expected_sha256=None, signature_verifier=None,
                    require_signature=False):
    package = pathlib.Path(package).resolve()
    if not package.is_file():
        raise FileNotFoundError(str(package))
    digest_hasher = hashlib.sha256()
    with package.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest_hasher.update(chunk)
    digest = digest_hasher.hexdigest()
    if expected_sha256 and digest.lower() != str(expected_sha256).lower():
        raise ValueError("Agent package SHA-256 does not match")
    if signature_verifier is not None:
        if not signature_verifier(package, digest):
            raise ValueError("Agent package signature is not trusted")
    elif require_signature:
        raise ValueError("a signature_verifier is required for signed-only installation")
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


def _apply_permissions(path, owner=None, group=None, dir_mode=0o750, file_mode=0o640):
    for item in [path] + list(path.rglob("*")):
        if item.is_dir():
            item.chmod(dir_mode)
        elif item.is_file():
            mode = file_mode | (0o110 if item.stat().st_mode & 0o110 else 0)
            item.chmod(mode)
        if owner is not None or group is not None:
            shutil.chown(item, user=owner, group=group)


def install_package(package, root="/etc/agent-os/agents", expected_sha256=None,
                    signature_verifier=None, require_signature=False,
                    owner=None, group=None, dir_mode=0o750, file_mode=0o640,
                    lifecycle=None):
    temporary, staging, manifest = inspect_package(
        package, expected_sha256, signature_verifier, require_signature,
    )
    root_path = pathlib.Path(root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    destination = root_path / manifest.name
    manifest_destination = root_path / (manifest.name + ".agent")
    work = pathlib.Path(tempfile.mkdtemp(prefix="." + manifest.name + "-", dir=str(root_path)))
    backup_root = pathlib.Path(tempfile.mkdtemp(prefix="." + manifest.name + "-backup-", dir=str(root_path)))
    backup_code = backup_root / "code"
    backup_manifest = backup_root / "manifest"
    temp_manifest = root_path / ("." + manifest.name + ".agent.tmp")
    installed_code = False
    installed_manifest = False
    stopped = False
    try:
        for item in staging.iterdir():
            shutil.copytree(item, work / item.name) if item.is_dir() else shutil.copy2(item, work / item.name)
        _apply_permissions(work, owner, group, dir_mode, file_mode)
        shutil.copy2(work / "agent.manifest", temp_manifest)
        temp_manifest.chmod(file_mode)
        if owner is not None or group is not None:
            shutil.chown(temp_manifest, user=owner, group=group)
        if lifecycle is not None:
            lifecycle.stop(manifest.name)
            stopped = True
        if destination.exists():
            os.replace(destination, backup_code)
        if manifest_destination.exists():
            os.replace(manifest_destination, backup_manifest)
        os.replace(work, destination)
        installed_code = True
        os.replace(temp_manifest, manifest_destination)
        installed_manifest = True
        if lifecycle is not None:
            lifecycle.reload(manifest.name)
    except Exception:
        if work.exists():
            shutil.rmtree(work)
        if temp_manifest.exists():
            temp_manifest.unlink()
        if installed_manifest and manifest_destination.exists():
            manifest_destination.unlink()
        if installed_code and destination.exists():
            shutil.rmtree(destination)
        if backup_code.exists():
            os.replace(backup_code, destination)
        if backup_manifest.exists():
            os.replace(backup_manifest, manifest_destination)
        if stopped and lifecycle is not None:
            lifecycle.reload(manifest.name)
        raise
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)
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


def _remote_command(host, args, sudo=True, tty=None):
    """Build an SSH command that works both from a terminal and from CI.

    Interactive deployments need a remote TTY for sudo to ask for a password.
    Non-interactive callers use ``sudo -n`` so they fail immediately instead of
    hanging; those callers can provision a narrowly scoped NOPASSWD rule.
    """
    if not sudo:
        return ["ssh", host, "--", *args]
    if tty is None:
        tty = bool(sys.stdin.isatty())
    ssh = ["ssh"]
    sudo_args = ["sudo", "-H"]
    if tty:
        ssh.append("-tt")
    else:
        sudo_args.insert(1, "-n")
    return [*ssh, host, "--", *sudo_args, *args]


def deploy_package(package, host, root="/etc/agent-os/agents", sudo=True,
                   dry_run=False, sdk_wheel=None, tty=None):
    package = pathlib.Path(package).resolve()
    if not package.is_file():
        raise FileNotFoundError(str(package))
    if not SAFE_REMOTE.fullmatch(host):
        raise ValueError("host contains unsupported characters")
    remote_package = "/tmp/" + package.name
    commands = []
    if sdk_wheel is not None:
        wheel = pathlib.Path(sdk_wheel).resolve()
        if not wheel.is_file() or wheel.suffix != ".whl":
            raise ValueError("sdk_wheel must point to a built .whl file")
        remote_wheel = "/tmp/" + wheel.name
        commands.extend([
            ["scp", str(wheel), host + ":" + remote_wheel],
            _remote_command(
                host,
                ["python3", "-m", "pip", "install", "--no-index",
                 "--break-system-packages", remote_wheel],
                sudo=sudo,
                tty=tty,
            ),
        ])
    else:
        commands.append(["ssh", host, "--", "python3", "-c", "import pvos"])
    install = ["python3", "-m", "pvos.cli", "install", remote_package, "--root", root]
    commands.extend([
        ["scp", str(package), host + ":" + remote_package],
        _remote_command(host, install, sudo=sudo, tty=tty),
    ])
    if not dry_run:
        for command in commands:
            subprocess.run(command, check=True)
    return commands
