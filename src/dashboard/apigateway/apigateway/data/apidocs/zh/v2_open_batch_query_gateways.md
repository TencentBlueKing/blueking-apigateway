### 描述

批量根据网关名称查询网关展示名称和描述

供 BKAuth 等第三方系统根据 ResourceID 中的 gateway_name 批量解析网关展示信息。

### 输入参数

#### 请求体参数（JSON）

| 参数名称 | 参数类型 | 必选 | 描述             |
| -------- | -------- | ---- | ---------------- |
| names    | array    | 是   | 网关名称列表     |

### 请求示例

```json
{
    "names": ["bk-apigateway", "bk-esb"]
}
```

### 响应示例

```json
{
    "data": [
        {
            "name": "bk-apigateway",
            "description": "蓝鲸 API 网关"
        },
        {
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
| name        | string   | 网关名称 |
| description | string   | 网关描述 |
