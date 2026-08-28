#!/usr/bin/env python3
"""把任务事实写入长期记忆，并结合语义文件检索后回答新问题。"""
import json
import os
import time

import agentos


def response_text(value):
    if isinstance(value, dict):
        return str(value.get("response", value))
    return str(value)


def main():
    user_input = os.environ.get("AGENT_INPUT", "客户偏好周报用中文，并要求先列风险再列行动项")
    query = os.environ.get("AGENT_QUERY", "客户有哪些偏好和待办要求？")
    aos = agentos.AgentOS(caller="long-memory-semantic-agent")
    memory_text = f"{time.strftime('%Y-%m-%d')} 任务事实：{user_input}"
    written = aos.memory_write(memory_text)
    file_name = "memory-note-" + str(int(time.time())) + ".txt"
    file_info = aos.fs_put(file_name, user_input)
    memories = aos.memory_recall(query)
    files = aos.fs_search(query)
    context = aos.ctx_assemble(6000, query, reserve_output=700, want_memory=True, k_memory=5, want_files=True, k_files=5)
    answer = aos.chat(
        f"问题：{query}\n历史记忆：{memories}\n语义文件：{files}\n"
        f"Context Gateway：{context.get('prompt', context)}\n"
        "请区分已知事实和需要确认的内容。"
    )
    print(json.dumps({
        "agent": "long-memory-semantic-agent",
        "memory_write": written,
        "file_write": file_info,
        "memory_hits": memories,
        "file_hits": files,
        "answer": response_text(answer),
    }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
