# Agent 测试指南

## 三层测试

1. 单元测试：将原语调用封装在函数中，用 Fake `PeakVisionOS` 返回固定 dict。
2. 合约测试：运行仓库 `tests/test-sdk-http.py`、`tests/test-local-client.py` 和 `npm test`。
3. 节点验收：`pvos acceptance` 验证真实 Gateway、Agent、日志、事件和 Run 终态。

Harness 适配器可使用 `EventRecorder` 记录 JSONL，再用 `pvos replay` 离线回放；
用 `pvos eval spec.json --recording run.jsonl` 检查必需事件。测试必须覆盖
completed、failed、stopped、timeout、cancelled 五种终态。

测试数据使用合成内容，结束后显式卸载测试 Agent；不要在共享节点写入客户数据。
