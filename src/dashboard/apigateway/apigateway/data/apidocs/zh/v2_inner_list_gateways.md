### 描述

查询网关列表


### 输入参数

### 请求参数示例

```json
{}
```


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
            ],
          "doc_maintainers": {
            "type": "user",
            "contacts": [
              "admin"
            ],
            "service_account": {
              "name": "",
              "link": ""
            }
          }
        }
    ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称            | 参数类型     | 描述       |
|-----------------|----------|----------|
| id              | int      | 网关ID     |
| name            | string   | 网关名称     |
| description     | string   | 网关描述     |
| maintainers     | array    | 网关管理员    |
| doc_maintainers | object   | 网关文档维护人员 |

#### doc_maintainers

| 名称              | 类型       | 说明                                 |
|-----------------|----------|------------------------------------|
| type            | string   | 类型，user 表示用户，service_account 表示服务号 |
| contacts        | array    | 联系人                                |
| service_account | object   | 服务号                                |

#### service_account

| 名称            | 类型         | 说明    |
|---------------|------------|-------|
| name          | string     | 服务号名称 |
| link          | string     | 服务号链接 |
