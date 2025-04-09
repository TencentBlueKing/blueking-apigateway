### 描述

查询网关权限列表

### 输入参数

| 参数名称 | 参数类型 | 参数位置 | 描述 |
| -------- | -------- | -------- | ---- |
| gateway_name | string | path | 网关名称 |
| bk_app_code | string | query | 应用编码 |
| grant_dimension | string | query | 授权维度，gateway 为网关，resource 为资源 |

### 请求参数示例

### 响应示例

```json
{
    "data": {
        "count": 1,
        "results": [
            {
                "bk_app_code": "bk_apigateway",
                "expires": "2100-01-01T00:00:00Z",
                "grant_dimension": "gateway",
                "id": 1
            }
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
| count       | int      | 总数       |
| results     | array    | 权限列表   |

results[]

| 参数名称    | 参数类型 | 描述       |
| ----------- | -------- | ---------- |
| bk_app_code | string   | 应用编码   |
| expires     | string   | 过期时间   |
| grant_dimension | string   | 授权维度   |
| id          | int      | 权限记录 ID     |
| resource_id | int      | 资源 ID(resource 维度时存在)     |
| resource_name | string   | 资源名称 (resource 维度时存在)  |
