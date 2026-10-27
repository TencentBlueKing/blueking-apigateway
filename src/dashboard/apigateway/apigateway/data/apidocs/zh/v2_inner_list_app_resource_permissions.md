### 描述

已申请权限列表


网关本地化展示名，最长 64 字符；英文请求取英文名，未配置英文名时回退默认名；定位仍使用技术名或数值 ID。

### 输入参数

#### 请求参数

| 参数名称              | 参数类型    | 必选 | 描述                  |
|-------------------|---------|----|---------------------|
| target_app_code   | string  | 是  | 申请权限的应用，应与当前请求的应用一致 |
| expire_days_range | int     | 否  | 过期时间范围               |


### 响应示例

```json
{
  "data": [
    {
      "id": 1,
      "name": "test",
      "gateway_display_name": "蓝鲸 API 网关",
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
| gateway_display_name | string | 所属网关的本地化展示名，最长 64 字符；英文名未配置时回退默认名 |
| gateway_id        | int    | 网关ID |
| description       | string | 资源描述 |
| expires_in        | int    | 有效期  |
| permission_level  | string | 权限级别 |
| permission_status | string | 权限状态 |
| permission_action | string | 权限操作 |
| doc_link          | string | 文档地址 |
