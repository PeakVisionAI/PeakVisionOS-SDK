# Agent 测试指南

## 三层测试

1. 单元测试：将原语调用封装在函数中，用 Fake `PeakVisionOS` 返回固定 dict。
2. 本地原语合约：使用 `pvos.PrimitiveMock` 验证 Unix Socket 请求、响应和失败路径。
3. SDK 合约：运行 `tests/test-sdk-http.py`、`tests/test-local-client.py`、`tests/test-pvos-toolchain.py` 和 `npm test`。
4. 节点验收：`pvos acceptance` 验证真实 Gateway、Agent、日志、事件和 Run 终态。

Harness 适配器可使用 `EventRecorder` 记录 JSONL，再用 `pvos replay` 离线回放；
用 `pvos eval spec.json --recording run.jsonl` 检查必需事件。测试必须覆盖
completed、failed、stopped、timeout、cancelled 五种终态。

测试数据使用合成内容，结束后显式卸载测试 Agent；不要在共享节点写入客户数据。

## 一键发布门禁

仓库提供 `scripts/release-gate.sh`，无副作用地串联本地合约测试、Python 编译和
wheel/sdist 构建：

```bash
./scripts/release-gate.sh
```

需要连真实节点时，先建立 SSH 隧道或使用 HTTPS Gateway，再设置 endpoint；脚本会
额外执行 `pvos acceptance`，验证 Run 终态、日志和生命周期事件：

```bash
export PVOS_GATEWAY_ENDPOINT=http://127.0.0.1:18080/api/v1
export PVOS_AGENT=demo-agent
export PVOS_TIMEOUT=30
./scripts/release-gate.sh
```

脚本不会自动部署、重启服务或修改远端节点。部署请先按 README 的
`pvos deploy --sdk-wheel` 流程完成，再运行 live acceptance；鉴权环境还需设置
`PVOS_TOKEN`。
