# bk_auth 对接 API 网关内部接口协议

本文档用于确认 `bk_auth` 调用 API 网关的 5 个内部接口协议。文档中的路径均为 API 网关对外路径，不是 Dashboard 后端内部的 `/backend/...` 路径。

## 1. 通用约定

### 1.1 接口清单

| 资源名 | Method | Path | 用途 |
| --- | --- | --- | --- |
| `v2_inner_list_mcp_server` | `GET` | `/api/v2/inner/mcp-servers/` | 查询可用 MCP Server |
| `v2_inner_lookup_gateways` | `GET` | `/api/v2/inner/gateways/-/lookup/` | 按名称批量查询网关 |
| `v2_inner_list_gateway_released_resources` | `GET` | `/api/v2/inner/gateways/{gateway_name}/released-resources/` | 查询网关当前已发布资源 |
| `v2_inner_list_oauth2_resource_scopes` | `GET` | `/api/v2/inner/oauth2/client-scopes/resources/` | 查询 OAuth2 客户端可选 API 资源范围 |
| `v2_inner_list_oauth2_mcp_server_scopes` | `GET` | `/api/v2/inner/oauth2/client-scopes/mcp-servers/` | 查询 OAuth2 客户端可选 MCP Server 范围 |

### 1.2 认证与权限

5 个接口均为非公开、应用态接口：

- 必须携带有效的蓝鲸应用身份；
- 不要求用户登录态；
- 调用应用必须拥有对应资源权限；
- `bk_auth` 已在网关定义中预授权这 5 个资源；
- 多租户模式下，网关批量查询、已发布资源及两个 OAuth2 Scope 接口要求认证上下文包含租户 ID，并仅返回全租户数据及当前租户可见数据；MCP Server 列表接口当前不按租户过滤。

认证信息按部署环境的蓝鲸 API 网关调用规范传递，例如：

```http
X-Bkapi-Authorization: {"bk_app_code":"bk_auth","bk_app_secret":"<app-secret>"}
```

### 1.3 通用成功响应

成功响应为 JSON，业务数据位于 `data`：

```json
{
  "data": {}
}
```

列表接口存在两种返回形式：

- 非分页列表：`data` 直接为数组；
- 分页列表：`data` 为 `{count, results}`。`count` 是符合条件的总数，`results` 是当前页数据。

### 1.4 通用错误响应

| HTTP 状态码 | `error.code` | 场景 |
| --- | --- | --- |
| `400` | `INVALID_ARGUMENT` | 参数缺失、类型错误、取值越界或字段不受支持 |
| `401` | `UNAUTHENTICATED` | 应用身份无效或认证失败 |
| `403` | `NO_PERMISSION` | 调用应用未获得接口资源权限 |
| `404` | `NOT_FOUND` | 指定网关不存在或在当前租户下不可见 |
| `405` | `METHOD_NOT_ALLOWED` | 请求方法不支持 |
| `500` | `INTERNAL` / `UNKNOWN` | 服务内部错误 |

错误响应格式：

```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "校验失败: <具体原因>",
    "data": null
  }
}
```

---

## 2. 查询 MCP Server 列表

### 2.1 基本信息

- 资源名：`v2_inner_list_mcp_server`
- Method：`GET`
- Path：`/api/v2/inner/mcp-servers/`
- 请求体：无
- 返回范围：MCP Server、所属网关及所属环境均为启用状态的数据；包括公开和非公开 MCP Server。

### 2.2 Query 参数

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | ---: | --- | --- |
| `keyword` | string | 否 | 空 | 模糊匹配 MCP Server 的 `name`、`title` 或 `description`。空字符串等同于不筛选。 |
| `order_by` | string | 否 | `-updated_time` | 排序字段。支持 `id`、`name`、`updated_time`、`created_time`；前缀 `-` 表示降序。 |
| `mcp_server_ids` | string | 否 | 空 | MCP Server ID 列表，逗号分隔，最多 50 个；每项必须是整数，例如 `1,2,3`。精确匹配。 |
| `mcp_server_names` | string | 否 | 空 | MCP Server 名称列表，逗号分隔，最多 50 个，例如 `server-1,server-2`。精确匹配。 |
| `fields` | string | 否 | 返回全部字段 | 指定 `results` 每项返回的字段，逗号分隔，例如 `id,name,title`。字段集合见下文。 |
| `limit` | integer | 否 | `10` | 当前页最多返回条数，必须为正整数。 |
| `offset` | integer | 否 | `0` | 分页偏移量，必须为非负整数。 |

`fields` 支持以下字段：

`id`、`name`、`title`、`description`、`is_public`、`labels`、`resource_names`、`tool_names`、`status`、`protocol_type`、`oauth2_public_client_enabled`、`oauth2_personal_client_enabled`、`categories`、`stage`、`gateway`、`tools_count`、`prompts_count`、`url`、`detail_url`、`updated_by`、`created_by`、`updated_time`、`created_time`。

> `fields` 不传时返回全部字段；传入后，每个结果对象只返回指定且受支持的字段，未知字段会被忽略。调用方不应依赖未指定字段存在。

### 2.3 请求示例

```http
GET /api/v2/inner/mcp-servers/?mcp_server_names=log-query,alarm-query&fields=id,name,title,gateway,stage,url&limit=10&offset=0
```

### 2.4 成功响应

```json
{
  "data": {
    "count": 2,
    "results": [
      {
        "id": 101,
        "name": "log-query",
        "title": "日志查询",
        "gateway": {
          "id": 12,
          "name": "bk-log",
          "maintainers": ["admin"],
          "is_official": true
        },
        "stage": {
          "id": 3,
          "name": "prod"
        },
        "url": "https://example.com/api/v1/mcp/log-query/sse"
      }
    ]
  }
}
```

### 2.5 响应字段

#### `data`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `count` | integer | 符合筛选条件的 MCP Server 总数。 |
| `results` | `array<object>` | 当前页 MCP Server 列表。 |

#### `data.results[]`

| 字段 | 类型 | 可空 | 说明 |
| --- | --- | ---: | --- |
| `id` | integer | 否 | MCP Server ID。 |
| `name` | string | 否 | MCP Server 唯一名称。 |
| `title` | string | 否 | 显示名称；未配置标题时回退为 `name`。 |
| `description` | string/null | 是 | MCP Server 描述。 |
| `is_public` | boolean | 否 | 是否公开。 |
| `labels` | `array<string>` | 否 | 标签列表；未配置时为空数组。 |
| `resource_names` | `array<string>` | 否 | MCP Server 暴露的网关资源名称列表。 |
| `tool_names` | `array<string>` | 否 | 对外工具名称列表，与 `resource_names` 按下标一一对应；未单独配置工具名时使用资源名。 |
| `status` | string | 否 | MCP Server 状态。当前接口只返回启用数据，实际值为字符串 `"1"`。 |
| `protocol_type` | string | 否 | MCP 协议类型：`sse` 或 `streamable_http`。 |
| `oauth2_public_client_enabled` | boolean | 否 | 是否允许 OAuth2 公开客户端使用。 |
| `oauth2_personal_client_enabled` | boolean | 否 | 是否允许 OAuth2 个人客户端使用。 |
| `categories` | `array<object>` | 否 | 启用的分类列表；未配置时为空数组。 |
| `stage` | object | 否 | 所属环境。 |
| `gateway` | object | 否 | 所属网关。 |
| `tools_count` | integer | 否 | 工具数量。 |
| `prompts_count` | integer | 否 | Prompt 数量。 |
| `url` | string | 否 | MCP Server 访问地址；系统会根据其最低鉴权要求生成普通地址或应用态地址。 |
| `detail_url` | string | 否 | API 网关站点中的 MCP Server 详情地址。 |
| `updated_by` | string | 否 | 最近更新人。 |
| `created_by` | string | 否 | 创建人。 |
| `updated_time` | string | 否 | 最近更新时间，格式为 `YYYY-MM-DD HH:mm:ss ±HHMM`。 |
| `created_time` | string | 否 | 创建时间，格式为 `YYYY-MM-DD HH:mm:ss ±HHMM`。 |

#### `categories[]`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 分类英文标识，例如 `Official`、`Featured`。 |
| `display_name` | string | 分类显示名称。 |

#### `stage`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 环境 ID。 |
| `name` | string | 环境名称，例如 `prod`。 |

#### `gateway`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 网关 ID。 |
| `name` | string | 网关名称。 |
| `maintainers` | `array<string>` | 网关维护者。 |
| `is_official` | boolean | 是否为官方网关。 |

---

## 3. 按名称批量查询网关

### 3.1 基本信息

- 资源名：`v2_inner_lookup_gateways`
- Method：`GET`
- Path：`/api/v2/inner/gateways/-/lookup/`
- 请求体：无
- 分页：不分页

### 3.2 Query 参数

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | ---: | --- |
| `gateway_names` | string | 是 | 网关名称列表，逗号分隔，最多 50 个。空项会被忽略，重复项会去重；至少需要一个有效名称。按名称精确匹配。 |
| `fields` | string | 否 | 返回字段列表，逗号分隔。支持 `id`、`name`、`description`、`maintainers`、`doc_maintainers`、`kind`；不传或传空字符串时返回全部字段。传入不支持的字段返回 `400`。 |

查询结果说明：

- 不存在或当前租户不可见的名称直接忽略，不为单个缺失项返回错误；
- 结果按 `name`、`id` 升序排列；
- 接口按名称查询，不额外限制网关是否公开、启用或已发布。

### 3.3 请求示例

```http
GET /api/v2/inner/gateways/-/lookup/?gateway_names=bk-apigateway,bk-esb&fields=id,name,kind,maintainers
```

### 3.4 成功响应

```json
{
  "data": [
    {
      "id": 1,
      "name": "bk-apigateway",
      "kind": "normal",
      "maintainers": ["admin"]
    },
    {
      "id": 2,
      "name": "bk-esb",
      "kind": "normal",
      "maintainers": ["operator"]
    }
  ]
}
```

### 3.5 响应字段

`data` 为网关数组。若指定 `fields`，每项只包含指定字段。

| 字段 | 类型 | 可空 | 说明 |
| --- | --- | ---: | --- |
| `id` | integer | 否 | 网关 ID。 |
| `name` | string | 否 | 网关唯一名称。 |
| `description` | string | 否 | 按请求语言返回的网关描述，可为空字符串。 |
| `maintainers` | `array<string>` | 否 | 网关管理员显示名列表。 |
| `doc_maintainers` | object | 否 | 网关文档维护者配置，结构见下表。 |
| `kind` | string | 否 | 网关类型：`normal`（普通网关）、`programmable`（可编程网关）或 `ai`（AI 网关）。 |

#### `doc_maintainers`

| 字段 | 类型 | 可空 | 说明 |
| --- | --- | ---: | --- |
| `type` | string | 否 | 维护者类型：`user` 表示用户，`service_account` 表示服务号。 |
| `contacts` | `array<string>` | 否 | 联系人列表。 |
| `service_account` | object | 是 | 服务号信息；非服务号类型时可能为空。 |
| `service_account.name` | string | 是 | 服务号名称。 |
| `service_account.link` | string | 是 | 服务号链接。 |

未匹配到任何网关时：

```json
{
  "data": []
}
```

---

## 4. 查询网关当前已发布资源

### 4.1 基本信息

- 资源名：`v2_inner_list_gateway_released_resources`
- Method：`GET`
- Path：`/api/v2/inner/gateways/{gateway_name}/released-resources/`
- 请求体：无
- 返回范围：指定网关各环境当前 Release 所引用资源版本中的资源并集；同一资源按资源 ID 去重。

### 4.2 Path 参数

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | ---: | --- |
| `gateway_name` | string | 是 | 网关唯一名称，精确匹配。网关不存在或当前租户不可见时返回 `404`。 |

### 4.3 Query 参数

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | ---: | --- | --- |
| `resource_names` | string | 否 | 空 | 资源名称列表，逗号分隔，最多 50 个；空项忽略、重复项去重。按名称精确匹配。 |
| `fields` | string | 否 | 全部字段 | 返回字段列表，逗号分隔。支持 `id`、`name`、`description`；传入不支持的字段返回 `400`。 |
| `limit` | integer | 否 | `10` | 当前页条数，范围为 `1`～`20`。 |
| `offset` | integer | 否 | `0` | 分页偏移量，必须大于或等于 `0`。 |

资源按 `name`、`id` 升序排列。

### 4.4 请求示例

```http
GET /api/v2/inner/gateways/bk-apigateway/released-resources/?resource_names=get_gateway,list_gateways&fields=id,name,description&limit=10&offset=0
```

### 4.5 成功响应

```json
{
  "data": {
    "count": 2,
    "results": [
      {
        "id": 1001,
        "name": "get_gateway",
        "description": "获取网关"
      },
      {
        "id": 1002,
        "name": "list_gateways",
        "description": "获取网关列表"
      }
    ]
  }
}
```

### 4.6 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data.count` | integer | 筛选、去重后的已发布资源总数。 |
| `data.results` | `array<object>` | 当前页资源列表。 |
| `data.results[].id` | integer | 资源 ID。 |
| `data.results[].name` | string | 资源名称。 |
| `data.results[].description` | string | 按请求语言返回的资源描述；未配置时为空字符串。 |

若网关存在但当前没有已发布资源，返回：

```json
{
  "data": {
    "count": 0,
    "results": []
  }
}
```

---

## 5. 查询 OAuth2 客户端可选 API 资源范围

### 5.1 基本信息

- 资源名：`v2_inner_list_oauth2_resource_scopes`
- Method：`GET`
- Path：`/api/v2/inner/oauth2/client-scopes/resources/`
- 请求体：无
- 分页单位：网关；每个当前页网关下返回该网关全部符合条件的资源。

可选资源必须同时满足：

- 所属网关已启用且公开；
- 资源公开；
- 资源属于网关当前 Release 引用的资源版本；
- 资源已开启所请求 OAuth2 客户端类型对应的开关。

### 5.2 Query 参数

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | ---: | --- | --- |
| `oauth_client_type` | string | 是 | 无 | OAuth2 客户端类型：`public` 或 `personal`。`public` 对应资源的公开客户端开关，`personal` 对应个人客户端开关。 |
| `gateway_name` | string | 否 | 空 | 按网关名称包含匹配，最大 64 个字符。 |
| `resource_name` | string | 否 | 空 | 按资源名称包含匹配，最大 256 个字符。 |
| `limit` | integer | 否 | `10` | 当前页网关数，范围为 `1`～`20`。 |
| `offset` | integer | 否 | `0` | 网关分页偏移量，必须大于或等于 `0`。 |

网关按 `name`、`id` 升序排列；网关内资源按 `name`、`id` 升序排列。同一资源在多个当前资源版本中出现时，按资源 ID 去重并取最新资源版本中的字段。

### 5.3 请求示例

```http
GET /api/v2/inner/oauth2/client-scopes/resources/?oauth_client_type=public&gateway_name=bk-&resource_name=query&limit=10&offset=0
```

### 5.4 成功响应

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 12,
        "name": "bk-log",
        "is_official": true,
        "resource_count": 2,
        "resources": [
          {
            "id": 201,
            "name": "query_log",
            "description": "查询日志"
          },
          {
            "id": 202,
            "name": "query_index_set",
            "description": "查询索引集"
          }
        ]
      }
    ]
  }
}
```

### 5.5 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data.count` | integer | 符合条件的网关总数，不是资源总数。 |
| `data.results` | `array<object>` | 当前页网关列表。 |
| `data.results[].id` | integer | 网关 ID。 |
| `data.results[].name` | string | 网关名称。 |
| `data.results[].is_official` | boolean | 是否为官方网关。 |
| `data.results[].resource_count` | integer | 该网关下符合当前筛选条件的去重资源数量。 |
| `data.results[].resources` | `array<object>` | 该网关下全部符合当前筛选条件的资源。 |
| `data.results[].resources[].id` | integer | 资源 ID。 |
| `data.results[].resources[].name` | string | 资源名称。 |
| `data.results[].resources[].description` | string | 按请求语言返回的资源描述；未配置时为空字符串。 |

---

## 6. 查询 OAuth2 客户端可选 MCP Server 范围

### 6.1 基本信息

- 资源名：`v2_inner_list_oauth2_mcp_server_scopes`
- Method：`GET`
- Path：`/api/v2/inner/oauth2/client-scopes/mcp-servers/`
- 请求体：无
- 分页单位：网关；每个当前页网关下返回该网关全部符合条件的 MCP Server。

可选 MCP Server 必须同时满足：

- 所属网关已启用且公开；
- 所属环境已启用；
- MCP Server 已启用且公开；
- MCP Server 已开启所请求 OAuth2 客户端类型对应的开关。

### 6.2 Query 参数

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | ---: | --- | --- |
| `oauth_client_type` | string | 是 | 无 | OAuth2 客户端类型：`public` 或 `personal`。`public` 对应 MCP Server 的公开客户端开关，`personal` 对应个人客户端开关。 |
| `gateway_name` | string | 否 | 空 | 按网关名称包含匹配，最大 64 个字符。 |
| `mcp_server_name` | string | 否 | 空 | 按 MCP Server 名称包含匹配，最大 64 个字符。 |
| `limit` | integer | 否 | `10` | 当前页网关数，范围为 `1`～`20`。 |
| `offset` | integer | 否 | `0` | 网关分页偏移量，必须大于或等于 `0`。 |

网关按 `name`、`id` 升序排列；网关内 MCP Server 按 `name`、`id` 升序排列。

### 6.3 请求示例

```http
GET /api/v2/inner/oauth2/client-scopes/mcp-servers/?oauth_client_type=personal&gateway_name=bk-&mcp_server_name=query&limit=10&offset=0
```

### 6.4 成功响应

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 12,
        "name": "bk-log",
        "is_official": true,
        "mcp_server_count": 1,
        "mcp_servers": [
          {
            "id": 301,
            "name": "log-query",
            "title": "日志查询"
          }
        ]
      }
    ]
  }
}
```

### 6.5 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data.count` | integer | 符合条件的网关总数，不是 MCP Server 总数。 |
| `data.results` | `array<object>` | 当前页网关列表。 |
| `data.results[].id` | integer | 网关 ID。 |
| `data.results[].name` | string | 网关名称。 |
| `data.results[].is_official` | boolean | 是否为官方网关。 |
| `data.results[].mcp_server_count` | integer | 该网关下符合当前筛选条件的 MCP Server 数量。 |
| `data.results[].mcp_servers` | `array<object>` | 该网关下全部符合当前筛选条件的 MCP Server。 |
| `data.results[].mcp_servers[].id` | integer | MCP Server ID。 |
| `data.results[].mcp_servers[].name` | string | MCP Server 唯一名称。 |
| `data.results[].mcp_servers[].title` | string | MCP Server 显示名称；未配置标题时回退为 `name`。 |

---

## 7. 协议确认重点

1. 网关批量查询路径中包含固定占位段 `-/`：`/api/v2/inner/gateways/-/lookup/`。
2. 所有接口均为 `GET`，参数位于 Path 或 Query，不接收 JSON 请求体。
3. 分页响应统一为 `data.count` 和 `data.results`，不返回 `has_next`、`has_previous`。
4. MCP Server 列表和已发布资源列表的 `fields` 会改变每个结果对象实际包含的字段。
5. 两个 OAuth2 Scope 接口按“网关”分页；嵌套的资源或 MCP Server 列表不单独分页。
6. OAuth2 `public` 与 `personal` 会分别检查对象的公开客户端开关和个人客户端开关。
7. 网关批量查询遇到未匹配名称时不会报错，而是仅返回实际匹配项；已发布资源接口指定的网关不存在时返回 `404`。
