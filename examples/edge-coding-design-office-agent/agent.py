#!/usr/bin/env python3
"""在端侧模型上完成代码、设计或办公类任务，并保存可复用产物。"""
import json
import os
import re

import pvos


def response_text(value):
    if isinstance(value, dict):
        return str(value.get("response", value))
    return str(value)


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")[:48] or "result"


def main():
    task = os.environ.get("AGENT_TASK", "为一个库存管理页面设计清晰的接口和验收标准")
    mode = os.environ.get("AGENT_MODE", "office")
    aos = pvos.PeakVisionOS(caller="edge-coding-design-office-agent")
    system = aos.system()
    context = aos.ctx_assemble(
        7000,
        task,
        system_prompt=(
            "你是端侧代码、设计和办公协作 Agent。先给出可执行的步骤，"
            "再产出结构化结果；不要声称执行了没有执行的外部操作。"
        ),
        want_memory=False,
        want_files=True,
    )
    prompt = (
        f"工作模式：{mode}\n任务：{task}\n"
        f"节点资源概况：{system}\n上下文：{context.get('prompt', context)}\n"
        "请输出：方案、关键文件或交付物、验证步骤、风险。"
    )
    answer = response_text(aos.chat(prompt))
    artifact_name = safe_name(os.environ.get("AGENT_OUTPUT_NAME", f"{mode}-result")) + ".md"
    stored = aos.fs_put(artifact_name, answer)
    print(json.dumps({
        "agent": "edge-coding-design-office-agent",
        "mode": mode,
        "task": task,
        "artifact": {"name": artifact_name, "store": stored},
        "answer": answer,
    }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
