### 描述

查询网关资源列表


### 输入参数

| 参数名称            | 参数类型 | 必选 | 描述                  |
|-----------------| -------- | ---- |---------------------|
| target_app_code | string   | 是   | 申请权限的应用，应于当前请求的应用一致 |
| gateway_name    | string   | 是   | 网关名称                |

### 请求参数示例

```json
{}
```


### 响应示例

```json
{
  "data": [
    {
      "id": 2321,
      "name": "test",
      "gateway_name": "test-gateway",
      "gateway_id": 6,
      "description": "",
      "description_en": null,
      "expires_in": null,
      "permission_level": "normal",
      "permission_status": "pending",
      "permission_action": "",
      "doc_link": "http://test.com/"
    }
  ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称              | 参数类型   | 描述   |
|-------------------|--------|------|
| id                | int    | 资源ID |
| name              | string | 资源名称 |
| gateway_name      | string | 网关名称 |
| gateway_id        | int    | 网关ID |
| description       | string | 资源描述 |
| expires_in        | int    | 有效期  |
| permission_level  | string | 权限级别 |
| permission_status | string | 权限状态 |
| permission_action | string | 权限操作 |
| doc_link          | string | 文档地址 |
