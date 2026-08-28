"""agentos —— AgentOS 的 Python SDK(面向 ISV 与 Agent 开发者)

把四大原语 + 运行时封装成几行 Python API。零第三方依赖(仅标准库),
socket 路径与 C 客户端一致,支持 env 覆盖(AGENTOS_*_SOCK)便于本地开发。

快速上手:
    import agentos
    aos = agentos.AgentOS(caller="my-agent")   # caller 用于 inferd 配额记账
    aos.chat("帮我写个快速排序")
    aos.memory_write("用户偏好用 Rust 写系统级代码")
    hits = aos.fs_search("第三季度营收")
    aos.agentrun_spawn("demo")
"""
import json
import os
import socket

__version__ = "1.5.0a1"

# 原语 -> (env 名, 默认 socket 路径),与 C 客户端/daemon 保持一致
_SOCKS = {
    "agent":     ("AGENTOS_AGENTD_SOCK",    "/run/agentd/agentd.sock"),
    "infer":     ("AGENTOS_INFERD_SOCK",    "/run/inferd/inferd.sock"),
    "memory":    ("AGENTOS_MEMORYD_SOCK",   "/run/memoryd/memoryd.sock"),
    "fs":        ("AGENTOS_FSD_SOCK",       "/run/fsd/fsd.sock"),
    "agentrund": ("AGENTOS_AGENTRUND_SOCK", "/run/agentrund/agentrund.sock"),
    "ctx":       ("AGENTOS_CTXD_SOCK",      "/run/ctxd/ctxd.sock"),
}

DEFAULT_TIMEOUT = 30.0


def _sock_path(key):
    env, default = _SOCKS[key]
    return os.environ.get(env, default)


def _clean(text):
    """协议安全:剔除 \\r\\n(与 daemon/网关层一致,防注入行协议)。"""
    return str(text).replace("\r", " ").replace("\n", " ")


def _call(key, line, timeout=DEFAULT_TIMEOUT, raw=False, body=None):
    """连原语 socket,发一行协议(可选 body 紧随其后),读全部响应。

    raw=True 返回 bytes(用于 fs_get 裸字节);否则解析 JSON 返回 dict。
    """
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(timeout)
    try:
        s.connect(_sock_path(key))
        s.sendall(line.encode("utf-8") + b"\n")
        if body is not None:
            s.sendall(body)
        s.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            d = s.recv(65536)
            if not d:
                break
            chunks.append(d)
        data = b"".join(chunks)
    finally:
        s.close()
    if raw:
        return data
    if not data:
        return {}
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        return {"_raw": data.decode("utf-8", errors="replace")}


class AgentOS:
    """AgentOS 客户端:一行 API 调感知/认知/记忆/语义文件/运行时/上下文。

    caller:可选,标识调用方 —— 发给 inferd 的请求自动带 `@<caller> ` 前缀,
    算力调度按 caller 记账/配额。agentrund 托管的 agent 会注入 AGENTOS_AGENT_NAME,
    这里默认从该 env 取,也可显式传入覆盖。
    """

    def __init__(self, caller=None):
        self._caller = caller or os.environ.get("AGENTOS_AGENT_NAME") or None

    # -- 内部:拼行协议 ------------------------------------------------
    def _line(self, method, *args, infer=False):
        """拼一行协议。infer=True 时带 `@<caller> ` 前缀 —— 只有 inferd 支持
        caller 记账前缀;memoryd/fsd/agentrund/ctxd 的协议不带。"""
        parts = [method]
        for a in args:
            if a is None:
                continue
            parts.append(_clean(a))
        line = " ".join(parts)
        if infer and self._caller:
            line = "@" + self._caller + " " + line
        return line

    # -- 感知 agentd ---------------------------------------------------
    def world(self):
        """世界快照:主机/内核/负载等概览。"""
        return _call("agent", "world")

    def system(self):
        """系统资源:内存/CPU 等数字。"""
        return _call("agent", "system")

    def processes(self):
        """当前进程列表。"""
        return _call("agent", "processes")

    # -- 认知 inferd ----------------------------------------------------
    def chat(self, prompt):
        """与当前模型对话,返回 {response, tokens_in, tokens_out, ...}。"""
        return _call("infer", self._line("chat", prompt, infer=True))

    def embed(self, text):
        """文本转向量(语义召回的向量来源)。"""
        return _call("infer", self._line("embed", text, infer=True))

    def models(self):
        """列出可用模型。"""
        return _call("infer", "models")

    def status(self):
        """当前驱动与加载的模型。"""
        return _call("infer", "status")

    def hwinfo(self):
        """硬件探测结果 + 自动选中的后端。"""
        return _call("infer", "hwinfo")

    def load(self, name):
        """加载模型(切换当前模型)。"""
        return _call("infer", self._line("load", name, infer=True))

    def sched(self):
        """算力调度状态(各 caller 配额/记账/in-flight)。"""
        return _call("infer", "sched")

    # -- 记忆 memoryd ---------------------------------------------------
    def memory_write(self, text):
        """写入一条长期记忆。"""
        return _call("memory", self._line("write", text))

    def memory_set(self, key, text):
        """写单值槽位(旧 active 同 key 自动 superseded,版本链)。"""
        return _call("memory", self._line("set", key, text))

    def memory_recall(self, query, top_k=5):
        """按意思召回相关记忆。"""
        return _call("memory", self._line("recall", query))

    def memory_list(self, all_=False):
        """列出记忆(默认只列 active;all_=True 含 superseded/rejected)。"""
        return _call("memory", "list all" if all_ else "list")

    def memory_forget(self, target):
        """按 id 或关键词遗忘。"""
        return _call("memory", self._line("forget", target))

    def memory_history(self, key):
        """查单值槽位的版本链。"""
        return _call("memory", self._line("history", key))

    # -- 语义文件 fsd ----------------------------------------------------
    def fs_put(self, name, text):
        """存入一段文本(内容寻址 + 抽向量),返回 {id, dedup, embed}。"""
        data = text.encode("utf-8")
        head = "put %s %d" % (_clean(name), len(data))
        return _call("fs", head, body=data)

    def fs_search(self, query, top_k=5):
        """按意思召回最相关的文件。"""
        return _call("fs", self._line("search", top_k, query))

    def fs_get(self, fid):
        """按 id 取回原始字节(bytes)。"""
        return _call("fs", self._line("get", fid), raw=True)

    def fs_list(self):
        """列出全部文件。"""
        return _call("fs", "list")

    def fs_forget(self, fid):
        """按 id 删除文件。"""
        return _call("fs", self._line("forget", fid))

    # -- 运行时 agentrund ------------------------------------------------
    def agentrun_list(self):
        """列出全部 agent(运行态/授予的原语)。"""
        return _call("agentrund", "list")

    def agentrun_spawn(self, name):
        """启动一个 agent。"""
        return _call("agentrund", self._line("spawn", name))

    def agentrun_stop(self, name):
        """停止一个 agent。"""
        return _call("agentrund", self._line("stop", name))

    def agentrun_status(self, name):
        """查 agent 状态。"""
        return _call("agentrund", self._line("status", name))

    def agentrun_logs(self, name):
        """查 agent 日志。"""
        return _call("agentrund", self._line("logs", name))

    # -- 上下文 ctxd ------------------------------------------------------
    def ctx_assemble(self, budget, query, reserve_output=512, system_prompt=None,
                     messages=None, want_memory=True, k_memory=5,
                     want_files=True, k_files=3):
        """Context Gateway:按 token 预算装配本轮上下文(自动拉记忆+语义文件)。

        返回 {prompt, segments, total_tokens, dropped, summarized, ...}。
        """
        body = {
            "budget": budget,
            "reserve_output": reserve_output,
            "query": query,
            "want_memory": want_memory,
            "k_memory": k_memory,
            "want_files": want_files,
            "k_files": k_files,
        }
        if system_prompt:
            body["system_prompt"] = system_prompt
        if messages:
            body["messages"] = messages
        return _call("ctx", "assemble\n" + json.dumps(body, ensure_ascii=False))
