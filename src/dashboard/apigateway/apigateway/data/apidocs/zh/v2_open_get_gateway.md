### 描述

查询网关列表

### 输入参数

| 参数名称 | 参数类型 | 参数位置 | 描述 |
| -------- | -------- | -------- | ---- |
| gateway_name | string | path| 网关名称 |

### 请求参数示例

### 响应示例

```json
{
    "data": {
        "id": 1,
        "name": "bk-apigateway",
        "description": "",
        "maintainers": [
            "admin"
        ]
    }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |

data

| 参数名称    | 参数类型 | 描述       |
| ----------- | -------- | ---------- |
| id          | int      | 网关 ID     |
| name        | string   | 网关名称   |
| description | string   | 网关描述   |
| maintainers | array    | 网关管理员 |
