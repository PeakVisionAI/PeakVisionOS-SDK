# AgentOS Agent Manifest v1

Manifest v1 是 Agent 与 `agentrund` 的稳定部署合同。文件扩展名为 `.agent`，使用 `key=value` 格式；未知字段必须被忽略，以便向后兼容。

| 字段 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `name` | 是 | - | `[A-Za-z0-9_.-]`，最长 63 字符 |
| `exec` | 是 | - | Agent 启动命令 |
| `primitives` | 否 | 空 | `agent,infer,memory,fs` 的子集 |
| `memory_max` | 否 | 不限制 | systemd `MemoryMax` |
| `cpu_quota` | 否 | 不限制 | systemd `CPUQuota` |
| `autostart` | 否 | `no` | 是否随 agentrund 启动 |
| `restart` | 否 | `no` | `no/on-failure/always` |
| `sandbox` | 否 | `on` | `namespace-seccomp`/systemd launcher 强隔离；`off` 仅限可信调试 |
| `network` | 否 | `loopback` | `loopback/full` |

生命周期状态固定为 `inactive/running/completed/failed/stopped`。正常退出必须为 `completed` 且 `exit_code=0`；非零退出为 `failed`。暂时不可确定的远程状态不得直接标记失败。

兼容规则：v1 内新增字段必须有安全默认值；删除、改名或改变已有字段语义需要新的 Manifest 主版本。

Python SDK 提供 `agentos.inspect` 对应的 `parse_manifest_text()` / `validate_manifest_file()`；`agentos test` 和 `agentos package` 在执行语法检查或打包前强制使用同一校验器。未知字段会出现在 `Manifest.unknown`，但不影响 v1 Agent 运行。
