"""agentos CLI —— Agent 开发、测试和打包入口。

安装后可直接使用:
    pip install ./python
    agentos new my-agent
    agentos doctor
    agentos test my-agent
    agentos package my-agent
    agentos registry list
    agentos registry install code-agent 0.1.0
    python3 my-agent/agent.py          # 本地直接跑
    agentrun spawn my-agent            # 由 agentrund 托管跑
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import tarfile
import sys
import urllib.request
import urllib.error
import hashlib
import io

from .client import _SOCKS
from . import __version__

_TEMPLATES = {
    "agent.manifest": """# {NAME} 的 Agent 定义 —— agentrund 读取
name={NAME}
exec=python3 /etc/agent-os/agents/{NAME}/agent.py
# 授予哪些原语(= 注入哪些 socket);去掉某项则该 agent 连不上对应原语
primitives=agent,infer,memory,fs
# 资源边界(systemd 启动器下经 cgroup 生效;fork 启动器忽略)
memory_max=256M
cpu_quota=50%
autostart=no
restart=no
""",
    "agent.py": """#!/usr/bin/env python3
# {NAME} —— 由 `agentos new {NAME}` 生成的示例 Agent。
# 用 AgentOS SDK 调系统原语:感知 -> 认知 -> 记忆 -> 语义文件,跑 3 轮。
# 运行:python3 {NAME}/agent.py(本地直接跑);或由 agentrund 托管(agentrun spawn {NAME})。
import time

import agentos

aos = agentos.AgentOS(caller="{NAME}")   # caller 用于 inferd 算力记账

print(f"==== agent {NAME} 启动 ====")
for rnd in range(1, 4):
    print(f"---- 第 {rnd}/3 轮:感知 -> 认知 -> 记忆 -> 语义文件 ----")
    # 1. 感知(agentd):看系统环境
    env = aos.system() or {}
    print("  [感知 agentd] mem_total_kb =", env.get("mem_total_kb"))
    # 2. 认知(inferd):基于环境说一句话
    reply = aos.chat(f"第 {rnd} 轮:请用一句话描述系统内存状态")
    print("  [认知 inferd]", str((reply or {}).get("response", reply))[:80])
    # 3. 记忆(memoryd):记下这一轮
    aos.memory_write(f"{NAME} 第 {rnd} 轮观察到系统内存 {env.get('mem_total_kb')} KB")
    got = aos.memory_recall("系统 内存 状态")
    print("  [记忆 memoryd] recall ->", got)
    # 4. 语义文件(fsd):存一份报告
    fid = aos.fs_put("round.txt", f"第 {rnd} 轮的报告内容:系统内存 {env.get('mem_total_kb')} KB")
    print("  [语义文件 fsd] 已存入 id =", (fid or {}).get("id"))
    time.sleep(1)
print(f"==== agent {NAME} 完成 3 轮,正常退出 ====")
""",
    "README.md": """# {NAME}

由 `agentos new {NAME}` 生成的示例 Agent。

## 本地直接跑(不需要 agentrund)

```bash
python3 {NAME}/agent.py
```

## 由 AgentOS 托管跑(agentrund 授予原语 + 资源边界)

```bash
# 1. 把 manifest 与代码放进 AgentOS 的 agents 目录
sudo mkdir -p /etc/agent-os/agents/{NAME}
sudo cp {NAME}/agent.manifest /etc/agent-os/agents/
sudo cp {NAME}/agent.py /etc/agent-os/agents/{NAME}/
# 2. 由 agentrund 启动(被授予的原语才连得上)
agentrun spawn {NAME}
agentrun logs {NAME}
```

## 修改成你自己的 agent

- `primitives=` 决定它能用哪些原语(agent/infer/memory/fs)
- `agent.py` 里 `aos.xxx()` 就是各原语的一行 API,见 SDK 文档
""",
}


def cmd_new(args):
    name = args.name.strip()
    if not name or not all(c.isalnum() or c in "-_" for c in name) or name[0].isdigit():
        sys.exit(f"非法 agent 名: {name!r}(只能字母/数字/-/_,且不以数字开头)")
    d = pathlib.Path(name)
    if d.exists():
        sys.exit(f"目录已存在: {name}")
    d.mkdir()
    for fname, content in _TEMPLATES.items():
        # 模板里除 {NAME} 外的花括号(如 {rnd}、{env.get(...)}、空 {})是生成代码自身的语法:
        # 全部转义为 {{ }},再把 {NAME} 还原为唯一要 format 的占位符
        content = content.replace("{", "{{").replace("}", "}}").replace("{{NAME}}", "{NAME}")
        (d / fname).write_text(content.format(NAME=name))
    print(f"✅ 已生成 agent 骨架: {name}/")
    print(f"   ├── agent.manifest    agentrund 的 agent 定义(primitives= 授权原语)")
    print(f"   ├── agent.py          示例:感知→认知→记忆→语义文件")
    print(f"   └── README.md         运行说明")
    print()
    print(f"本地直接跑:   python3 {name}/agent.py")
    print(f"系统托管跑:   agentrun spawn {name}   (需先拷到 /etc/agent-os/agents/)")


def _agent_name_path(name):
    path = pathlib.Path(name)
    if not path.exists():
        sys.exit(f"Agent 路径不存在: {name}")
    return path


def _exec_cli(binary, *args):
    command = shutil.which(binary)
    if not command:
        sys.exit(f"缺少命令: {binary}")
    result = subprocess.run([command, *args], text=True)
    return result.returncode


def cmd_doctor(_args):
    checks = {}
    for key, (env, default) in _SOCKS.items():
        path = pathlib.Path(os.environ.get(env, default))
        checks[key] = {"path": str(path), "exists": path.exists(), "socket": path.is_socket()}
    checks["python"] = sys.version.split()[0]
    checks["sdk"] = __version__
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    missing = [key for key, value in checks.items() if isinstance(value, dict) and not value["socket"]]
    return 0 if not missing else 1


def cmd_run(args):
    path = _agent_name_path(args.name)
    if args.local:
        return subprocess.run([sys.executable, str(path / "agent.py"), *args.args]).returncode
    return _exec_cli("agentrun", "spawn", path.name)


def cmd_status(args):
    return _exec_cli("agentrun", "status", args.name)


def cmd_logs(args):
    return _exec_cli("agentrun", "logs", args.name)


def cmd_test(args):
    path = _agent_name_path(args.name)
    source = path / "agent.py"
    if not source.exists():
        sys.exit(f"缺少 {source}")
    from .manifest import validate_manifest_file
    manifest, errors = validate_manifest_file(path / "agent.manifest")
    if errors:
        for error in errors:
            print("[FAIL] manifest: " + error)
        return 1
    result = subprocess.run([sys.executable, "-m", "py_compile", str(source)], text=True)
    if result.returncode:
        return result.returncode
    test_script = path / "test.sh"
    if test_script.exists():
        return subprocess.run(["bash", str(test_script)], text=True).returncode
    print(f"[OK] {source} Python 语法检查通过")
    return 0


def cmd_package(args):
    path = _agent_name_path(args.name)
    manifest = path / "agent.manifest"
    source = path / "agent.py"
    if not manifest.exists() or not source.exists():
        sys.exit("Agent 包必须包含 agent.manifest 和 agent.py")
    from .manifest import validate_manifest_file
    parsed, errors = validate_manifest_file(manifest)
    if errors:
        for error in errors:
            print("[FAIL] manifest: " + error)
        return 1
    output = pathlib.Path(args.output or f"{path.name}.agent.tgz")
    with tarfile.open(output, "w:gz") as bundle:
        for item in sorted(path.iterdir()):
            if item.name == output.name:
                continue
            bundle.add(item, arcname=item.name)
    print(f"[OK] 已打包 {output}")
    return 0


def cmd_inspect(args):
    from .manifest import validate_manifest_file
    manifest, errors = validate_manifest_file(pathlib.Path(args.name) / "agent.manifest")
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False))
        return 1
    print(json.dumps({"valid": True, "manifest": manifest.to_dict()}, ensure_ascii=False))
    return 0


def _registry_request(args, path):
    base = args.url.rstrip("/")
    request = urllib.request.Request(base + path)
    if args.token:
        request.add_header("Authorization", "Bearer " + args.token)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        sys.exit(f"Registry 请求失败 HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        sys.exit(f"Registry 不可达: {exc.reason}")


def cmd_registry_list(args):
    payload = json.loads(_registry_request(args, "/registry/v1/packages"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_registry_install(args):
    if not args.name or not args.version:
        sys.exit("registry install 需要 name 和 version")
    metadata = json.loads(_registry_request(args, f"/registry/v1/packages/{args.name}/{args.version}"))
    artifact = _registry_request(args, f"/registry/v1/packages/{args.name}/{args.version}/download")
    digest = "sha256:" + hashlib.sha256(artifact).hexdigest()
    if metadata.get("digest") != digest:
        sys.exit(f"Registry 摘要不匹配: expected={metadata.get('digest')} actual={digest}")
    target = pathlib.Path(args.dest).resolve()
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(artifact), mode="r:gz") as bundle:
        for member in bundle.getmembers():
            path = (target / member.name).resolve()
            if target != path and target not in path.parents:
                sys.exit(f"包路径越界: {member.name}")
        bundle.extractall(target)
    print(f"[OK] 已安装 {args.name}@{args.version} 到 {target}")


def cmd_eval(args):
    spec_path = pathlib.Path(args.spec)
    if not spec_path.exists():
        sys.exit(f"评估规格不存在: {spec_path}")
    try:
        spec = json.loads(spec_path.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"评估规格不是合法 JSON: {exc}")
    required = {"name", "task", "assertions"}
    missing = required - set(spec)
    if missing or not isinstance(spec.get("assertions"), list):
        sys.exit("评估规格必须包含 name、task、assertions[]")
    recording = pathlib.Path(args.recording) if args.recording else None
    if recording:
        from .harness import load_recording
        events = load_recording(recording)
        types = {event.type for event in events}
        missing_events = [item for item in spec.get("required_events", []) if item not in types]
        if missing_events:
            print(json.dumps({"status": "failed", "missing_events": missing_events}, ensure_ascii=False))
            return 1
    print(json.dumps({"status": "ready", "name": spec["name"], "task": spec["task"],
                      "assertions": len(spec["assertions"]), "recording": bool(recording)}, ensure_ascii=False))
    return 0


def cmd_replay(args):
    from .harness import replay_recording
    try:
        result = replay_recording(args.recording)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": result.status, "events": len(result.events),
                      "output": result.output, "error": result.error}, ensure_ascii=False, default=str))
    return 0 if result.status == "completed" else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="agentos",
        description="AgentOS SDK 命令行:生成 agent 骨架等",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new", help="生成一个新的 agent 骨架")
    p.add_argument("name", help="agent 名(字母/数字/-/_)")
    p.set_defaults(func=cmd_new)
    p = sub.add_parser("doctor", help="检查本地 SDK、原语和运行时 socket")
    p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("run", help="启动 Agent（默认由 agentrund 托管）")
    p.add_argument("name", help="Agent 目录或名称")
    p.add_argument("--local", action="store_true", help="本地直接运行，不经过 agentrund")
    p.add_argument("args", nargs="*", help="local 模式下传给 agent.py 的参数")
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("status", help="查看受管 Agent 状态")
    p.add_argument("name")
    p.set_defaults(func=cmd_status)
    p = sub.add_parser("logs", help="查看 Agent 日志")
    p.add_argument("name")
    p.set_defaults(func=cmd_logs)
    p = sub.add_parser("test", help="运行 Agent 语法和项目测试")
    p.add_argument("name")
    p.set_defaults(func=cmd_test)
    p = sub.add_parser("package", help="将 Agent 打包为 .agent.tgz")
    p.add_argument("name")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_package)
    p = sub.add_parser("inspect", help="解析并校验 Agent Manifest v1")
    p.add_argument("name", help="Agent 目录")
    p.set_defaults(func=cmd_inspect)
    p = sub.add_parser("registry", help="访问 AgentOS Registry")
    p.add_argument("action", choices=["list", "install"], help="Registry 操作")
    p.add_argument("name", nargs="?", help="安装时的包名")
    p.add_argument("version", nargs="?", help="安装时的版本")
    p.add_argument("--url", default="http://127.0.0.1:17880", help="Registry 地址")
    p.add_argument("--token", default=os.environ.get("AGENTOS_REGISTRY_TOKEN", ""), help="Bearer Token")
    p.add_argument("--dest", default=".", help="安装目标目录")
    p.set_defaults(func=lambda args: cmd_registry_list(args) if args.action == "list" else cmd_registry_install(args))
    p = sub.add_parser("eval", help="校验任务评估规格，可结合 JSONL 运行记录回放")
    p.add_argument("spec", help="评估规格 JSON")
    p.add_argument("--recording", help="Harness 事件 JSONL 记录")
    p.set_defaults(func=cmd_eval)
    p = sub.add_parser("replay", help="离线校验并回放 Harness JSONL 运行记录")
    p.add_argument("recording", help="Harness 事件 JSONL 记录")
    p.set_defaults(func=cmd_replay)
    a = ap.parse_args(argv)
    result = a.func(a)
    if isinstance(result, int):
        raise SystemExit(result)


if __name__ == "__main__":
    main()
