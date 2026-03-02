### 描述

批量根据网关 ID 或名称查询网关展示名称和描述

供 BKAuth 等第三方系统根据 ResourceID 中的 gateway_name 批量解析网关展示信息。

### 输入参数

#### 请求体参数（JSON）

| 参数名称 | 参数类型 | 必选 | 描述                                                                 |
| -------- | -------- | ---- | -------------------------------------------------------------------- |
| ids      | array    | 否   | 网关 ID 列表（ids 和 names 至少提供一个）                             |
| names    | array    | 否   | 网关名称列表（ids 和 names 至少提供一个）                             |
| fields   | string   | 否   | 指定返回的字段列表，逗号分隔，如 `fields=id,name,description`；不传默认返回 `id` 和 `name` |

### 请求示例

```json
{
    "names": ["bk-apigateway", "bk-esb"],
    "fields": "id,name,description"
}
```

### 响应示例

#### 默认返回（不传 fields）

```json
{
    "data": [
        {
            "id": 1,
            "name": "bk-apigateway"
        },
        {
            "id": 2,
            "name": "bk-esb"
        }
    ]
}
```

#### 指定字段（fields=id,name,description）

```json
{
    "data": [
        {
            "id": 1,
            "name": "bk-apigateway",
            "description": "蓝鲸 API 网关"
        },
        {
            "id": 2,
            "name": "bk-esb",
            "description": "蓝鲸 ESB"
        }
    ]
}
```

### 响应参数说明

| 字段 | 类型  | 描述                           |
| ---- | ----- | ------------------------------ |
| data | array | 结果数据，详细信息请见下面说明 |

#### data[]

| 参数名称    | 参数类型 | 描述     |
| ----------- | -------- | -------- |
| id          | int      | 网关 ID  |
| name        | string   | 网关名称 |
| description | string   | 网关描述 |
