# 模型服务多实例后端接口

模型服务在每个环境内可以配置多个主实例和最多一个备用实例。所有实例共用 timeout；实例通过配置内唯一、稳定的 name 标识，重排数组时应保留 name。

## Web 写入

沿用现有接口，无独立实例 CRUD 路由：

- `POST /backend/gateways/{gateway_id}/backends/`：创建模型服务，配置在 `configs[]` 中，每项含 stage_id。
- `PUT /backend/gateways/{gateway_id}/backends/{id}/`：更新模型服务，提交各环境的完整实例数组。
- 环境创建/更新接口中的 `backends[].config` 支持相同的模型服务配置。
- `PUT /backend/gateways/{gateway_id}/stages/{id}/backends/{backend_id}/`：更新某个环境的完整配置，不含 stage_id。

新格式的一个环境配置示例：

```json
{
  "stage_id": 1,
  "timeout": 60,
  "balancer": {"algorithm": "chash"},
  "fallback_strategy": ["http_429", "http_5xx"],
  "instances": [
    {"name": "primary-a", "priority": 10, "provider": "openai", "api_key": "<KEY_A>", "model": "model-a"},
    {"name": "primary-b", "priority": 10, "provider": "openai", "api_key": "<KEY_B>", "model": "model-b"},
    {
      "name": "backup",
      "priority": 0,
      "provider": "openai-compatible",
      "endpoint": "https://llm.example.com/v1/chat/completions",
      "auth_header": {"name": "Authorization", "value": "Bearer <BACKUP_KEY>"},
      "model": "backup-model"
    }
  ]
}
```

实例级 provider、endpoint、model_endpoint、api_key、auth_header、model、model_options 沿用原表单语义；实例内不能配置 timeout。Web 不提供 weight、hash_on 或 key 的编辑。

- priority 默认为 10，表示主实例；0 表示备用实例。其他值不接受。
- 至少一个主实例，最多一个备用实例；重复 name 不接受。
- 所有新数组实例固定 weight=1。
- balancer 为公共配置，algorithm 默认为 roundrobin，可选 chash。chash 固定按 `$bk_app_code` 做一致性哈希。
- 多实例省略 fallback_strategy 时默认启用两项；纯主池可显式传 [] 关闭重试，有备用实例则不能关闭全部重试。
- 删除数组中的元素即删除该实例。单主实例配置不应携带 balancer 或非空 fallback_strategy。
- 保存后数组按优先级和 name 排序；相同配置的输入重排不会改变实例身份。

## Web 查询与旧格式兼容

以下查询使用 `?config_format=instances` 返回统一数组格式；只有一个实例时也返回 name 和 priority：

- Backend 详情。
- Stage 后端列表。
- Stage 后端详情。

外层响应结构和环境信息不变。凭据以掩码返回；balancer 在 Web 响应中只返回 algorithm。

未指定 config_format，或传 legacy，保持原扁平单实例输出。多实例无法用该格式表示，会明确报错并提示使用 config_format=instances；不会只返回第一个实例。非法 config_format 返回参数错误。

旧扁平创建和单实例更新继续有效。旧扁平请求不能覆盖已有多实例配置；如需将池缩减为单实例，应使用新格式显式提交只含一个主实例的完整数组。

同一次请求不能混用外层 provider/api_key 等旧实例字段和 instances 数组。

## Web 凭据编辑

已有实例回传原掩码时，仅在同一 Backend、Stage 和 name 下恢复已有凭据，并保持原有 provider、目标地址 origin、认证 Header 名称检查。修改地址或 Header 后仍回传原掩码，会要求重新输入凭据。

新增、改名、跨环境复制不能恢复其他实例的密钥。Open / Sync 中的字符串始终按字面值处理，不应用这套 Web 恢复规则。

自定义 provider 通过 Open / Sync 保存多个 auth.header 时，Web 无法完整表示该实例，会明确报错，不丢弃额外 Header。

## Open Stage / v2 Sync

沿用原规范化结构：实例使用 auth.header、options、override.endpoint；不使用 Web 的 api_key、auth_header、model 等字段。详见 [Open Stage](../src/dashboard/apigateway/apigateway/data/apidocs/zh/sync_stage.md) 和 [v2 Sync](../src/dashboard/apigateway/apigateway/data/apidocs/zh/v2_sync_stages.md)。

三种入口应用同一套主备、固定权重和重试规则。Open / Sync 多实例可以省略 weight，或显式传 1；chash 可省略 hash_on/key，显式提供时必须等于 vars_combinations / $bk_app_code。旧单实例 weight=0 保持兼容。

## 发布与运行边界

单实例继续发布 ai-proxy，多实例发布 ai-proxy-multi。主实例 priority=10，备用实例 priority=0。当前主池中的候选因允许重试的错误耗尽后才尝试备用实例。

429 指模型上游返回的限流状态；5xx 包括网络错误映射后的状态。400/401/403 和网关自身限流不触发模型 failover。失败切换只作用于当前请求，不提供跨请求熔断。

timeout 以秒保存、以毫秒发布，是每次尝试使用的 HTTP 超时，不是整个重试链的总期限。不额外下发 max_retries。流式输出开始后不保证透明 failover。

chash 按应用编码分流，不保证请求均匀分布；空应用身份或共享应用身份可能集中到同一实例。

连通性测试仍使用原扁平单实例输入，不支持提交整个实例数组进行探测，也不自动选取多实例配置中的第一个实例。
