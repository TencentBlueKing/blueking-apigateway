### 描述

已申请权限列表


### 输入参数

#### 路径参数

| 参数名称              | 参数类型    | 必选 | 描述                  |
|-------------------|---------|----|---------------------|
| target_app_code   | string  | 是  | 申请权限的应用，应于当前请求的应用一致 |
| expire_days_range | int     | 否  | 过期时间范围               |


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
      "name": "test",
      "gateway_name": "test",
      "gateway_id": 4,
      "description": "",
      "description_en": "",
      "expires_in": null,
      "permission_level": "normal",
      "permission_status": "owned",
      "permission_action": "",
      "doc_link": ""
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
