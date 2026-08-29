# AgentOS SDK → PeakVisionOS SDK 迁移

## Python

```bash
pip uninstall agentos-sdk
pip install peakvisionos-sdk
```

```python
# 旧代码仍可运行
import agentos
aos = agentos.AgentOS()

# 新代码
import pvos
aos = pvos.PeakVisionOS()
```

`AGENTOS_*_SOCK`、`AGENTOS_ENDPOINT`、`AGENTOS_TOKEN` 在 1.x 保持兼容；
新部署可逐步切换为 `PVOS_ENDPOINT` 和 `PVOS_TOKEN`。

## TypeScript

```bash
npm uninstall @peakvision/agentos-sdk
npm install ../PeakVisionOS-SDK/typescript
```

`AgentOS` 类继续导出，新增项目应导入 `PeakVisionOS`。控制面协议仍为 v1，
无需修改 Workspace/Task/Run/Event 字段。TypeScript 客户端当前从源码或本地路径使用，暂不发布到 NPM。
