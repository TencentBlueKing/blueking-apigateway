# 关键文件引用与三层映射

## 目录

- [代码层文件](#代码层文件)
- [YAML 资源定义层文件](#yaml-资源定义层文件)
- [API 文档层文件](#api-文档层文件)
- [三层关系映射](#三层关系映射)
- [URL 路径映射](#url-路径映射)
- [Backend 路径映射](#backend-路径映射)
- [文档命名约定](#文档命名约定)

---

所有路径相对于项目根目录 `src/dashboard/apigateway/apigateway/`。

## 代码层文件

| 模块 | 路由 | 视图 | 序列化器 |
|------|------|------|----------|
| open | `apis/v2/open/urls.py` | `apis/v2/open/views.py` | `apis/v2/open/serializers.py` |
| inner | `apis/v2/inner/urls.py` | `apis/v2/inner/views.py` | `apis/v2/inner/serializers.py` |
| inner ESB | 同上 | `apis/v2/inner/views_esb.py` | `apis/v2/inner/serializers_esb.py` |
| sync | `apis/v2/sync/urls.py` | `apis/v2/sync/views.py` | `apis/v2/sync/serializers.py` |
| v2 入口 | `apis/v2/urls.py` | — | — |

## YAML 资源定义层文件

| 文件 | 路径 | 格式 | 说明 |
|------|------|------|------|
| bk-apigateway 资源定义 | `data/apigw-definitions/bk-apigateway-resources.yaml` | OpenAPI 3.0 | 主资源定义，`operationId` 为唯一标识 |
| bk-apigateway 网关定义 | `data/apigw-definitions/bk-apigateway-definition.yaml` | — | 包含 `grant_permissions`、`resource_docs.basedir`、`stages[].mcp_servers` |
| bk-apigateway-inner 资源定义 | `data/apigw-definitions/bk-apigateway-inner-resources.yaml` | Swagger 2.0 | 旧版 inner 网关，与 resources.yaml 中 `v2_inner_*` 并行 |

### x-bk-apigateway-resource 扩展字段

```yaml
x-bk-apigateway-resource:
  isPublic: true/false
  allowApplyPermission: true/false
  authConfig: { ... }
  backend:
    name: default | core-api | mcp-proxy
    method: get/post/put/delete
    path: /backend/api/v2/...
```

## API 文档层文件

- 目录：`data/apidocs/zh/`

## 三层关系映射

```
operationId (唯一标识)
  ├── YAML: bk-apigateway-resources.yaml → paths[path][method].operationId
  ├── 代码: urls.py URL pattern → views.py View → serializers.py Serializer
  └── 文档: apidocs/zh/{operationId}.md
```

## URL 路径映射

| YAML path 前缀 | 代码 URL 前缀 | 代码目录 |
|----------------|---------------|----------|
| `/api/v2/open/` | `open/` (v2/urls.py 挂载) | `apis/v2/open/` |
| `/api/v2/inner/` | `inner/` (v2/urls.py 挂载) | `apis/v2/inner/` |
| `/api/v2/sync/` | `sync/` (v2/urls.py 挂载) | `apis/v2/sync/` |
| `/api/v1/` | 旧版 API | 旧版代码 |

## Backend 路径映射

| backend.name | 说明 | 是否检查代码 |
|--------------|------|-------------|
| `default` | 转发到 dashboard 后端，路径 `/backend/api/v2/{scope}/...` | ✅ 是 |
| `core-api` | 转发到 core-api 服务 | ❌ 跳过 |
| `mcp-proxy` | 转发到 mcp-proxy 服务 | ❌ 跳过 |

## 文档命名约定

| scope | 命名规则 | 示例 |
|-------|----------|------|
| v2 open | `v2_open_{operation}.md` | `v2_open_list_gateways.md` |
| v2 inner | `v2_inner_{operation}.md` | `v2_inner_list_gateways.md` |
| v2 sync | `v2_sync_{operation}.md` | `v2_sync_gateway.md` |
| v1 | `{operation}.md` | `get_apis.md` |
