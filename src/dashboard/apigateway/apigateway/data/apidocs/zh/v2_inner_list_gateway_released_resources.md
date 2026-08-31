### 描述

查询指定网关当前各**启用环境**（`stage.status = ACTIVE`）`Release` 引用的资源版本中的资源并集。接口不按网关状态、网关公开状态、资源公开状态或资源 OAuth2 开关过滤，但仍遵守租户可见性约束；已下线环境的 `Release` 不计入当前已发布资源。

多租户模式下必须通过 `X-Bk-Tenant-Id` 请求头传入当前租户 ID，否则返回 `400`。接口仅允许访问全租户网关及当前租户的单租户网关；跨租户访问统一返回 `404`，不暴露网关是否存在。

同一资源 ID 出现在多个当前版本时只返回一个快照，默认选择版本 ID 较大的快照。按资源名称精确查询时，请使用 released resource lookup 接口。

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| gateway_name | string | 是 | 网关名称 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| fields | string | 否 | 返回字段列表，多个以逗号分隔；支持 `id`、`name`、`description`、`is_public`、`oauth2_public_client_enabled`、`oauth2_personal_client_enabled`，不传返回全部字段 |
| limit | int | 否 | 每页数量，默认 10，最大 1000 |
| offset | int | 否 | 分页偏移量，默认 0 |

### 响应示例

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 101,
        "name": "get_user",
        "description": "查询用户",
        "is_public": true,
        "oauth2_public_client_enabled": true,
        "oauth2_personal_client_enabled": false
      }
    ]
  }
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | object | 分页结果 |
| data.count | int | 去重后的资源总数 |
| data.results | array | 按资源名称、资源 ID 排序的当前已发布资源列表 |
| data.results[].id | int | 资源 ID |
| data.results[].name | string | 资源名称 |
| data.results[].description | string | 当前快照中的资源描述，随请求语言返回中文或英文 |
| data.results[].is_public | bool | 资源是否公开 |
| data.results[].oauth2_public_client_enabled | bool | 资源是否允许 OAuth2 公共客户端访问 |
| data.results[].oauth2_personal_client_enabled | bool | 资源是否允许 OAuth2 个人客户端访问 |

网关不存在或对当前租户不可见时返回 `404`；网关不存在当前发布版本时返回空分页结果。
