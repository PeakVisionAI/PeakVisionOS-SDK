# AgentOS 控制面 HTTP API

## 基本约定

- 本地控制面默认地址：http://127.0.0.1:17680
- API 前缀：/api/v1
- JSON 请求体上限：1 MiB
- 配置 AGENTOS_CONTROL_TOKEN 后，除 health 外请求需要 Bearer Token。

当前 API 是本机/可信网络控制面，不提供多用户 RBAC。

## 端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/health | 健康状态；不要求 Token |
| GET | /api/v1/agents | Agent 列表和运行状态 |
| GET | /api/v1/agents/{name}/logs | 指定 Agent 的最近运行日志 |
| GET/POST | /api/v1/workspaces | 列表/创建 Workspace |
| GET/POST | /api/v1/tasks | 列表/创建 Task |
| GET/POST | /api/v1/runs | 列表/创建 Run |
| GET | /api/v1/runs/{id} | Run 详情并触发状态收敛 |
| POST | /api/v1/runs/{id}/stop | 停止 Run |
| GET | /api/v1/events | 事件列表 |

## 示例

~~~bash
curl -fsS -X POST http://127.0.0.1:17680/api/v1/workspaces \
  -H 'Content-Type: application/json' \
  -d '{"name":"Local development"}'

curl -fsS -X POST http://127.0.0.1:17680/api/v1/runs \
  -H 'Content-Type: application/json' \
  -d '{"agent":"demo","workspace_id":"ws_xxx","task_id":"task_xxx"}'

curl -fsS 'http://127.0.0.1:17680/api/v1/events?after=0&limit=200'
~~~

## Run 状态

| 状态 | 含义 |
| --- | --- |
| created | 已建记录，尚未确认启动 |
| running | agentrund 确认运行 |
| completed | 正常退出且 exit_code=0 |
| failed | 非零退出或运行时失败 |
| stopped | 用户请求停止 |
| timeout/cancelled | 稳定契约保留；具体流程按事件收敛 |

## 错误码

| HTTP | 场景 |
| --- | --- |
| 400 | JSON 或必填字段错误 |
| 401 | Bearer Token 无效 |
| 404 | 资源不存在 |
| 405 | 方法错误 |
| 409 | Agent 已运行或 Run 不可停止 |
| 502 | agentrund 拒绝请求 |
| 503 | agentrund 不可达 |

Remote Gateway 代理路径见 [remote-gateway.md](remote-gateway.md)。
