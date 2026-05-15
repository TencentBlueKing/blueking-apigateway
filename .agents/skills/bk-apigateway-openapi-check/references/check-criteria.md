# 检查项详细判定规则

## 目录

- [CHECK-1: 存在性检查](#check-1-存在性检查)
- [CHECK-2: 路径一致性](#check-2-路径一致性)
- [CHECK-3: HTTP 方法一致性](#check-3-http-方法一致性)
- [CHECK-4: 请求参数一致性](#check-4-请求参数一致性)
- [CHECK-5: 响应参数一致性](#check-5-响应参数一致性)
- [CHECK-6: 鉴权配置一致性](#check-6-鉴权配置一致性)
- [CHECK-7: grant_permissions 一致性](#check-7-grant_permissions-一致性)
- [CHECK-8: MCP Server 配置一致性](#check-8-mcp-server-配置一致性)
- [优先级定义](#优先级定义)

---

## CHECK-1: 存在性检查

是否三层都有定义。

| 检查项 | 严重度 | 说明 |
|--------|--------|------|
| YAML 中有定义但代码中无对应路由 | ❌ ERROR | 资源已注册但无实现（排除 core-api / mcp-proxy backend） |
| 代码中有路由但 YAML 中无定义 | ⚠️ WARNING | 代码已实现但未注册到网关 |
| YAML 中有定义但无对应文档 | ⚠️ WARNING | 资源已注册但无 API 文档（排除 .well-known 等特殊路径） |
| 文档存在但 YAML 中无定义 | ⚠️ WARNING | 文档已写但资源未注册 |

## CHECK-2: 路径一致性

| 检查项 | 严重度 | 说明 |
|--------|--------|------|
| YAML path 与代码 URL pattern 不匹配 | ❌ ERROR | 路径不一致将导致 404 |
| YAML backend.path 与代码实际路由不匹配 | ❌ ERROR | 后端转发路径错误 |
| YAML path 参数与代码 URL 参数不一致 | ❌ ERROR | 参数名不匹配 |

## CHECK-3: HTTP 方法一致性

| 检查项 | 严重度 | 说明 |
|--------|--------|------|
| YAML method 与 View 支持的 method 不匹配 | ❌ ERROR | 方法不一致 |
| YAML backend.method 与前端 method 不一致 | ⚠️ WARNING | 通常应一致 |

## CHECK-4: 请求参数一致性

| 检查项 | 严重度 | 说明 |
|--------|--------|------|
| YAML 请求参数与 Serializer 字段不匹配 | ⚠️ WARNING | 参数定义不一致 |
| 文档请求参数与 Serializer 字段不匹配 | ⚠️ WARNING | 文档过时 |
| YAML 请求参数与文档请求参数不匹配 | ⚠️ WARNING | YAML 和文档不同步 |
| 必选字段不一致 | ❌ ERROR | 必选标记不匹配 |
| 字段类型不一致 | ⚠️ WARNING | 类型定义不匹配 |

## CHECK-5: 响应参数一致性

| 检查项 | 严重度 | 说明 |
|--------|--------|------|
| YAML 响应字段与 Serializer 输出字段不匹配 | ⚠️ WARNING | 响应不一致 |
| 文档响应字段与 Serializer 输出字段不匹配 | ⚠️ WARNING | 文档过时 |

## CHECK-6: 鉴权配置一致性

| 检查项 | 严重度 | 说明 |
|--------|--------|------|
| YAML authConfig 与代码中的 permission_classes 不匹配 | ⚠️ WARNING | 鉴权配置不一致 |
| inner API 不应为 isPublic: true | ❌ ERROR | inner API 应为隐藏 |
| sync API 不应为 resourcePermissionRequired: true | ⚠️ WARNING | sync API 使用 related_apps 鉴权 |

## CHECK-7: grant_permissions 一致性

| 检查项 | 严重度 | 说明 |
|--------|--------|------|
| definition.yaml 中授权的 resource_name 在 resources.yaml 中不存在 | ❌ ERROR | 授权了不存在的资源 |
| inner API 被引用但未在 grant_permissions 中授权 | ⚠️ WARNING | 可能缺少授权配置 |

## CHECK-8: MCP Server 配置一致性

| 检查项 | 严重度 | 说明 |
|--------|--------|------|
| mcp_servers 中引用的 resource_names 在 resources.yaml 中不存在 | ❌ ERROR | MCP Server 引用了不存在的资源 |
| resource_names 与 tool_names 数量不匹配 | ⚠️ WARNING | 资源数和工具数不一致 |

---

## 优先级定义

| 优先级 | 含义 | 典型场景 |
|--------|------|----------|
| P0 | 阻断性错误 | 路径不存在、方法不匹配（运行时错误） |
| P1 | 配置错误 | 鉴权不一致、授权资源不存在（权限问题） |
| P2 | 一致性警告 | 参数不匹配、文档过时（开发体验） |
| P3 | 信息提示 | 缺失文档、描述不同（建议改进） |
