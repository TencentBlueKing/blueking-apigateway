### 描述

按名称批量查询网关。接口不按网关启用状态或公开状态过滤，但仍遵守租户可见性约束；未匹配的名称不会出现在结果中。

多租户模式下必须通过 `X-Bk-Tenant-Id` 请求头传入当前租户 ID，否则返回 `400`。接口只返回全租户网关及当前租户的单租户网关。

### 输入参数

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| gateway_names | string | 是 | 网关名称列表，多个以逗号分隔，去重后最多 50 个 |
| fields | string | 否 | 返回字段列表，多个以逗号分隔；支持 `id`、`name`、`description`、`maintainers`、`doc_maintainers`、`is_official`；不传时默认返回除 `maintainers` 外的全部字段，`maintainers` 需显式指定 |

### 响应示例

以下示例对应 `fields=id,name,is_official`。

```json
{
  "data": [
    {
      "id": 1,
      "name": "bk-apigateway",
      "is_official": true
    }
  ]
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | array | 按 `name`、`id` 排序的网关列表 |
| data[].id | int | 网关 ID |
| data[].name | string | 网关名称 |
| data[].description | string | 网关描述 |
| data[].maintainers | array | 网关管理员 display_name 列表 |
| data[].doc_maintainers | object | 网关文档维护人员 |
| data[].is_official | bool | 是否为官方网关 |
