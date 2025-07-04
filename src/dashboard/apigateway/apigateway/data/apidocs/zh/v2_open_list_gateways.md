### 描述

查询网关列表

### 输入参数
无

### 响应示例

```json
{
    "data": [
        {
            "id": 1,
            "name": "bk-apigateway",
            "description": "",
            "maintainers": [
                "admin"
            ]
        }
    ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | array  | 结果数据，详细信息请见下面说明     |

data[]

| 参数名称    | 参数类型 | 描述       |
| ----------- | -------- | ---------- |
| id          | int      | 网关 ID     |
| name        | string   | 网关名称   |
| description | string   | 网关描述   |
| maintainers | array    | 网关管理员 |
