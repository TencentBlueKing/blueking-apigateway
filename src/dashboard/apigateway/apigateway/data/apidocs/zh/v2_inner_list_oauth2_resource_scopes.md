### 描述

查询 bkauth 生成个人 Token 或公开客户端 Token 时可选择的 API 资源授权范围。结果按网关聚合和分页。

资源范围是当前所有 `Release` 引用的资源版本合集。仅当同一份资源快照同时满足 `is_public=true` 和 `oauth_client_type` 对应的 OAuth2 开关时，该资源才会返回。相同网关下的资源按资源 ID 去重；多个有效快照同时存在时，展示 `resource_version_id` 最大的快照。

该接口不按 Stage 过滤，也不使用 `disabled_stages`。多租户模式下只返回全租户网关和请求租户所属的单租户网关。

### 输入参数

#### query 参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|----------|----------|------|------|
| oauth_client_type | string | 是 | OAuth2 客户端类型：`personal` 或 `public` |
| gateway_name | string | 否 | 网关名称，包含匹配，最长 64 个字符 |
| resource_name | string | 否 | 资源名称，包含匹配，最长 256 个字符 |
| limit | int | 否 | 每页网关数量，范围 1～1000，默认 10 |
| offset | int | 否 | 网关分页偏移量，必须大于或等于 0，默认 0 |

同时传入 `gateway_name` 和 `resource_name` 时，两个过滤条件均须满足。

### 响应示例

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 1,
        "name": "bk-apigateway",
        "is_official": true,
        "resource_count": 1,
        "resources": [
          {
            "id": 100,
            "name": "get_user",
            "description": "获取用户信息"
          }
        ]
      }
    ]
  }
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|------|------|------|
| data.count | int | 过滤后的网关总数，用于网关维度分页 |
| data.results | array | 当前页网关列表，按网关名称、网关 ID 稳定排序 |
| data.results[].id | int | 网关 ID |
| data.results[].name | string | 网关名称 |
| data.results[].is_official | bool | 是否为官方网关 |
| data.results[].resource_count | int | 当前过滤条件下该网关包含的去重资源数量 |
| data.results[].resources | array | 当前过滤条件下该网关包含的资源列表 |
| data.results[].resources[].id | int | 资源 ID |
| data.results[].resources[].name | string | 资源名称 |
| data.results[].resources[].description | string | 资源描述，按请求语言返回已有翻译，否则回退到默认描述 |
