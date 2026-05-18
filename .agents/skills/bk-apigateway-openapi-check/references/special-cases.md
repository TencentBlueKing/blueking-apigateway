# 已知特殊 Case 白名单

以下情况在检查时需特殊处理，不作为错误报告。

| # | operationId / 场景 | 原因 | 处理方式 |
|---|---------------------|------|----------|
| 1 | `v2_open_get_gateway_public_key` | URL 使用 `gateway/` 而非 `gateways/`（历史兼容），backend 转发到 core-api | 跳过代码层检查 |
| 2 | `v2_open_get_gateway_public_key_new` | 同上，`gateways/` 版本，backend 转发到 core-api | 跳过代码层检查 |
| 3 | bk-apigateway-inner 旧版资源 | `bk-apigateway-inner-resources.yaml` 是 Swagger 2.0 格式，与 `bk-apigateway-resources.yaml` 中 `v2_inner_*` 并行 | 不做格式比较，仅检查存在性 |
| 4 | ESB 相关接口 | 仅在非多租户模式下注册（`if not settings.ENABLE_MULTI_TENANT_MODE`） | 检查时标注条件注册 |
| 5 | core-api / mcp-proxy backend | 后端路径不指向 dashboard 代码 | 跳过代码层检查 |
| 6 | `v2_open_oauth_protected_resource` | `.well-known` 路径，无需文档 | 跳过文档存在性检查 |
| 7 | v1 旧版 API | `tags: [v1]` 的 API，代码不在 `apis/v2/` 目录下 | 跳过代码路径检查 |

## 自动跳过规则

脚本中硬编码的自动跳过逻辑：

```python
# 1. 已知特殊 operationId，跳过所有检查
KNOWN_SPECIAL_CASES = {
    "v2_open_get_gateway_public_key",
    "v2_open_get_gateway_public_key_new",
    "v2_open_oauth_protected_resource",
}

# 2. backend.name 为 core-api 或 mcp-proxy 时，跳过代码层检查
if backend_name in ("core-api", "mcp-proxy"):
    # 不报告"代码缺失"

# 3. .well-known 路径，跳过文档检查
if ".well-known" in path:
    # 不报告"文档缺失"
```

## 新增特殊 Case 流程

发现新的特殊 case 时：
1. 在脚本的 `KNOWN_SPECIAL_CASES` 集合中添加 operationId
2. 在本文件中补充说明
3. 在检查报告中以 `[SKIP]` 标注而非 `[PASS]`
