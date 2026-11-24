# 批量 AI 文档翻译

批量翻译在入队前校验所有文档属于请求网关，任务携带 `gateway_id`，
并在调用 AI 前再次读取和校验整个批次。外部、缺失或已转移的文档 ID
会使整批校验失败，不调用 AI，也不写入译文。

已确认保留整批终止策略：如果两份合法文档入队后其中一份被删除，
worker 启动时会终止整个批次，剩余文档也不会翻译。用户需要在原网关
重新选择仍有效的文档并提交。API 返回的任务启动提示只表示已经安排任务，
不能证明 worker 已完成翻译。这一校验发生在 AI 调用前；通过校验后各文档
分别翻译和写入，不保证整个批次的事务原子性。

旧批量消息只有文档 ID 和目标语言，缺少可信的请求网关。新 worker 保留
旧参数格式的绑定兼容性，但缺少 `gateway_id` 时返回 `success=False`，
不调用 AI、不写译文。不能通过文档归属反推调用者的授权范围。
旧单文档任务保持原签名，读取单份文档的网关后交给受限批量查询。

已确认的升级方案需要协调暂停批量翻译：

1. 暂停所有 producer 的批量翻译提交，并停止所有旧版翻译 worker。
2. 升级全部消费该任务的 worker，确认它们都支持 `gateway_id`。
3. 更新 producer，使批量任务携带请求网关，再恢复批量翻译提交。
4. 通过指定网关的批量接口重新提交旧格式批次和因文档失效终止的批次，
   只选择仍有效的文档。已有非空译文仍会跳过。

新版 producer 的消息不能交给旧 worker：旧任务签名不接受 `gateway_id`。
此方案是发布前提，本文不表示已执行暂停、升级或重提。真实 broker、
多版本 worker 发布及生产 AI 尚未验证；SQLite 和模拟 AI 的单元测试
覆盖授权校验、整批终止、重新提交和单文档兼容行为。

实现入口：
[请求校验](apigateway/apigateway/apis/web/ai_completion/serializers.py)、
[任务入队](apigateway/apigateway/apis/web/ai_completion/views.py)、
[worker 校验与翻译](apigateway/apigateway/apps/support/task.py)。
生命周期回归见
[任务测试](apigateway/apigateway/tests/apps/support/test_task.py)。
