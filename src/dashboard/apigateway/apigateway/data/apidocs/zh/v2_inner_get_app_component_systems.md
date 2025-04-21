### 描述

已申请权限列表


### 输入参数

#### 路径参数

| 参数名称            | 参数类型    | 必选    | 描述       |
|-------------------|-----------|-------|----------|
| target_app_code   | string    | 是     | 待授权应用    |
| expire_days_range | int       | 否     | 过期时间范围   |

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

| 字段    | 类型     | 描述                               |
| ------- |--------| ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称              | 参数类型   | 描述   |
|-------------------|--------|------|
| id                | int    | 组件ID |
| name              | string | 组件名称 |
| system_name       | string | 系统名称 |
| system_id         | int    | 系统ID |
| description       | string | 组件描述 |
| expires_in        | int    | 有效期  |
| permission_level  | string | 权限级别 |
| permission_status | string | 权限状态 |
| permission_action | string | 权限操作 |
| doc_link          | string | 文档地址 |
| tag               | string | 标签   |
