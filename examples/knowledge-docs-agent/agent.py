#!/usr/bin/env python3
"""摄取本地文档，进行语义检索，再生成一份可追溯摘要。"""
import json
import os
from pathlib import Path

import pvos


def response_text(value):
    if isinstance(value, dict):
        return str(value.get("response", value))
    return str(value)


def load_documents():
    directory = Path(os.environ.get("AGENT_DOCUMENT_DIR", "/var/lib/agentos/input"))
    if directory.is_dir():
        files = sorted(path for path in directory.rglob("*") if path.suffix.lower() in {".txt", ".md"})
        if files:
            return [(path.name, path.read_text(encoding="utf-8")) for path in files]
    text = os.environ.get("AGENT_DOCUMENT_TEXT", "")
    if text:
        return [("input.txt", text)]
    return []


def main():
    query = os.environ.get("AGENT_QUERY", "请总结这些文档的关键结论、风险和待办事项")
    documents = load_documents()
    if not documents:
        raise SystemExit("没有找到文档；设置 AGENT_DOCUMENT_DIR 或 AGENT_DOCUMENT_TEXT")

    aos = pvos.PeakVisionOS(caller="knowledge-docs-agent")
    stored = []
    for name, text in documents:
        stored.append({"name": name, "result": aos.fs_put(name, text)})
    hits = aos.fs_search(query)
    context = aos.ctx_assemble(6000, query, want_memory=False, want_files=True, k_files=5)
    answer = aos.chat(
        "请基于以下 AgentOS Context Gateway 内容回答用户问题。\n"
        f"用户问题：{query}\n上下文：{context.get('prompt', context)}"
    )
    report = {
        "agent": "knowledge-docs-agent",
        "documents_ingested": [item["name"] for item in stored],
        "semantic_hits": hits,
        "answer": response_text(answer),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
