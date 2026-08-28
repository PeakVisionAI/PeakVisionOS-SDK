# AgentOS Remote Gateway

## 定位

Remote Gateway 运行在管理节点，维护 AgentOS 节点注册表，并把受保护的管理请求代理到各节点本地 agentosd。它不是 MCP 网络传输层，也不是多租户云控制面。

## 端点

~~~text
GET  /gateway/v1/health
GET  /gateway/v1/nodes
POST /gateway/v1/nodes
POST /gateway/v1/nodes/{node_id}
POST /gateway/v1/nodes/{node_id}/token
GET  /gateway/v1/nodes/{node_id}/snapshot
*    /gateway/v1/nodes/{node_id}/api/v1/*
~~~

除 health 外，配置 AGENTOS_GATEWAY_TOKEN 后都需要 Gateway Bearer Token。

## 注册节点

~~~json
{
  "node_id": "amd395-01",
  "name": "AMD395",
  "base_url": "http://10.0.0.8:17680",
  "token": "node-secret",
  "capabilities": {"backend": "vulkan"}
}
~~~

base_url 只接受 http/https。Gateway 访问节点时会把客户端 Authorization 替换为节点 Token。

## 持久化和状态

- 默认文件：/var/lib/agentos-gateway/nodes.json
- systemd StateDirectory 权限：0700
- 文件权限：0600
- 默认离线阈值：5 分钟

节点注册或心跳会更新 last_seen 和 online。超过 AGENTOS_GATEWAY_NODE_STALE 后，GET nodes 返回 offline。状态计算不会删除注册信息。

## Token 轮换

~~~http
POST /gateway/v1/nodes/amd395-01/token
Content-Type: application/json
Authorization: Bearer <gateway-token>

{"token":"new-node-secret"}
~~~

轮换后必须同步更新节点 agentosd 的 AGENTOS_CONTROL_TOKEN 并重启服务。旧 Token 应立即验证为不可用。

## TLS 和 mTLS

配置：

~~~bash
AGENTOS_GATEWAY_LISTEN=0.0.0.0:17780
AGENTOS_GATEWAY_TOKEN=<secret>
AGENTOS_GATEWAY_TLS_CERT=/etc/agent-os/tls/gateway.crt
AGENTOS_GATEWAY_TLS_KEY=/etc/agent-os/tls/gateway.key
AGENTOS_GATEWAY_CLIENT_CA=/etc/agent-os/tls/client-ca.crt
~~~

- TLS_CERT 和 TLS_KEY 必须同时配置。
- CLIENT_CA 只能在 TLS 已启用时使用。
- 配置 CLIENT_CA 后，没有合法客户端证书的连接在 HTTP handler 前被拒绝。
- 非回环监听没有管理 Token 时服务拒绝启动。

生产证书应由组织 CA 签发，不要复用文档或测试中的临时证书。

## 代理示例

~~~bash
curl -fsS \
  -H "Authorization: Bearer <gateway-token>" \
  https://gateway.example/gateway/v1/nodes/amd395-01/api/v1/health
~~~

query string 和请求方法会被保留。节点不可达返回 502。

## systemd 运维

~~~bash
systemctl status agentos-gateway
journalctl -u agentos-gateway -f
curl -fsS http://127.0.0.1:17780/gateway/v1/health
~~~

修改配置后：

~~~bash
sudo systemctl restart agentos-gateway
~~~

## 已验收

- Go 单元测试：注册、列表、代理、鉴权、非法 URL、持久化、坏状态拒绝、离线状态和 Token 轮换。
- AMD395：注册、代理 agentosd、服务重启后恢复、0700/0600 权限。
- AMD395 临时 CA：无客户端证书拒绝，合法 mTLS + Bearer 成功。

## 当前代码已补齐

- 节点代理会透传 `/api/v1/agents/{name}/logs`，本地工作台在远程节点选择后可读取同一日志接口。
- 节点代理会透传 Runs、Events 和停止请求，远程节点与本地节点使用同一套控制面 API。
- `snapshot` 一次读取远程节点的 health、agents、runs 和 events，适合工作台刷新和断线重连后的全量校准。
- 节点注册、Token 轮换、心跳、代理成功/失败会追加写入 `audit.jsonl`（默认与节点注册表同目录，权限 0600）。

## 尚未完成

- 离线命令队列、幂等键和断线重连。
- 生产证书轮换演练和审计日志导出/集中留存。
- 多租户 RBAC、节点分组和策略下发。
