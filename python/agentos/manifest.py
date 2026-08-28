"""Manifest v1 parser shared by the AgentOS developer toolchain."""
from dataclasses import dataclass, asdict
import pathlib
import re

NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,63}$")
PRIMITIVES = ("agent", "infer", "memory", "fs")
RESTART_POLICIES = ("no", "on-failure", "always")
SANDBOX_MODES = ("on", "off")
NETWORK_MODES = ("loopback", "full")
SIZE_RE = re.compile(r"^[0-9]+(?:K|M|G|T|KiB|MiB|GiB|TiB)?$")
CPU_RE = re.compile(r"^[0-9]+%$")


@dataclass
class Manifest:
    name: str = ""
    exec: str = ""
    primitives: tuple = ()
    memory_max: str = ""
    cpu_quota: str = ""
    autostart: bool = False
    restart: str = "no"
    sandbox: str = "on"
    network: str = "loopback"
    unknown: dict = None

    def __post_init__(self):
        if self.unknown is None:
            self.unknown = {}

    def to_dict(self):
        value = asdict(self)
        value["primitives"] = list(self.primitives)
        return value


def parse_manifest_text(text):
    values = {}
    unknown = {}
    for line_number, raw in enumerate(str(text).splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("line %d: expected key=value" % line_number)
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key:
            raise ValueError("line %d: empty key" % line_number)
        if key in values:
            raise ValueError("line %d: duplicate key %s" % (line_number, key))
        values[key] = value

    manifest = Manifest(
        name=values.pop("name", ""),
        exec=values.pop("exec", ""),
        primitives=tuple(item.strip() for item in values.pop("primitives", "").split(",") if item.strip()),
        memory_max=values.pop("memory_max", ""),
        cpu_quota=values.pop("cpu_quota", ""),
        autostart=values.pop("autostart", "no").lower() in ("yes", "true"),
        restart=values.pop("restart", "no"),
        sandbox=values.pop("sandbox", "on"),
        network=values.pop("network", "loopback"),
        unknown=values,
    )
    return manifest


def load_manifest(path):
    path = pathlib.Path(path)
    return parse_manifest_text(path.read_text(encoding="utf-8"))


def validate_manifest(manifest):
    errors = []
    if not NAME_RE.fullmatch(manifest.name):
        errors.append("name must match [A-Za-z0-9_.-]{1,63}")
    if not manifest.exec:
        errors.append("exec is required")
    if "'" in manifest.exec:
        errors.append("exec must not contain a single quote")
    seen = set()
    for primitive in manifest.primitives:
        if primitive not in PRIMITIVES:
            errors.append("unsupported primitive: %s" % primitive)
        if primitive in seen:
            errors.append("duplicate primitive: %s" % primitive)
        seen.add(primitive)
    if manifest.memory_max and not SIZE_RE.fullmatch(manifest.memory_max):
        errors.append("memory_max must be a systemd size such as 256M")
    if manifest.cpu_quota and not CPU_RE.fullmatch(manifest.cpu_quota):
        errors.append("cpu_quota must be a percentage such as 50%")
    if manifest.restart not in RESTART_POLICIES:
        errors.append("restart must be one of: %s" % ", ".join(RESTART_POLICIES))
    if manifest.sandbox not in SANDBOX_MODES:
        errors.append("sandbox must be on or off")
    if manifest.network not in NETWORK_MODES:
        errors.append("network must be loopback or full")
    return errors


def validate_manifest_file(path):
    try:
        manifest = load_manifest(path)
    except (OSError, UnicodeError, ValueError) as exc:
        return None, [str(exc)]
    return manifest, validate_manifest(manifest)
