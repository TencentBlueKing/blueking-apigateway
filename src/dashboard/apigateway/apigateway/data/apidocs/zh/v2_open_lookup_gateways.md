### 描述

按 ID 或名称批量查询公开、已启用且已发布的网关。接口不分页，未匹配或不可见的网关不会出现在结果中；同时传入 ID 和名称时返回两组条件的交集。

### 输入参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| ids | string | 否 | 网关 ID 列表，多个以逗号分隔，最多 50 个；与 `names` 不能同时为空 |
| names | string | 否 | 网关名称列表，精确匹配，多个以逗号分隔，最多 50 个；与 `ids` 不能同时为空 |

### 响应示例

```json
{
  "data": [
    {
      "id": 1,
      "name": "bk-apigateway",
      "description": "蓝鲸 API 网关",
      "maintainers": ["admin"],
      "doc_maintainers": {"type": "user", "contacts": ["admin"]},
      "kind": "normal"
    }
  ]
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | array | 匹配的网关列表，无分页包装 |
| data[].id | int | 网关 ID |
| data[].name | string | 网关名称 |
| data[].description | string | 网关描述 |
| data[].maintainers | array | 网关管理员 |
| data[].doc_maintainers | object | 网关文档维护人员 |
| data[].kind | string | 网关类型 |
