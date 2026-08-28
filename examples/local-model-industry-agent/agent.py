#!/usr/bin/env python3
"""展示如何发现并使用 inferd 管理的本地模型完成行业任务。"""
import json
import os

import agentos


def response_text(value):
    if isinstance(value, dict):
        return str(value.get("response", value))
    return str(value)


def main():
    industry = os.environ.get("AGENT_INDUSTRY", "船舶设计")
    task = os.environ.get("AGENT_TASK", "检查设计变更中的关键风险，并给出复核清单")
    model = os.environ.get("AGENT_MODEL", "")
    aos = agentos.AgentOS(caller="local-model-industry-agent")
    hardware = aos.hwinfo()
    models = aos.models()
    loaded = None
    if model:
        loaded = aos.load(model)
    answer = aos.chat(
        f"你是{industry}行业的端侧助手。只能依据输入给出可审计建议。\n"
        f"任务：{task}\n请按‘结论、依据、待确认项、风险’输出。"
    )
    print(json.dumps({
        "agent": "local-model-industry-agent",
        "industry": industry,
        "task": task,
        "hardware": hardware,
        "available_models": models,
        "model_loaded": loaded,
        "answer": response_text(answer),
    }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
