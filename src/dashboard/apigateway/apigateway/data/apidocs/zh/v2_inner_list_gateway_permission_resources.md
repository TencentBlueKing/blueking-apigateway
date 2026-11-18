### 描述

查询网关资源列表，供应用检索可调用的资源并申请权限。

只返回已发布的公开资源，按资源是否校验应用权限决定是否列出：

| 资源配置 | 是否列出 | permission_level |
|---------|---------|------------------|
| 校验应用权限，且要求应用认证、允许主动申请权限 | 是 | normal |
| 校验应用权限，但要求应用认证、允许主动申请权限任一不满足 | 否 | - |
| 不校验应用权限（含无需认证） | 是，即使不允许主动申请权限 | unlimited，无需申请权限；调用时仍须满足资源的认证要求 |


### 输入参数

#### 路径参数

| 参数名称            | 参数类型 | 必选 | 描述                  |
|-----------------| -------- | ---- |---------------------|
| gateway_name    | string   | 是   | 网关名称                |


#### 请求参数

| 参数名称            | 参数类型     | 必选  | 描述                  |
|-----------------|----------|-----|---------------------|
| target_app_code | string   | 是   | 申请权限的应用，应与当前请求的应用一致 |


### 响应示例

```json
{
  "data": [
    {
      "id": 2321,
      "name": "test",
      "gateway_name": "test-gateway",
      "gateway_display_name": "蓝鲸 API 网关",
      "gateway_id": 6,
      "description": "",
      "description_en": null,
      "expires_in": null,
      "permission_level": "normal",
      "permission_status": "pending",
      "permission_action": "",
      "doc_link": "http://test.com/",
      "approval_url": "https://dashboard.example.com/6/permission/apply"
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
| gateway_display_name | string | 所属网关的展示名 |
| gateway_id        | int    | 网关ID |
| description       | string | 资源描述 |
| expires_in        | int    | 有效期  |
| permission_level  | string | 权限级别 |
| permission_status | string | 权限状态 |
| permission_action | string | 权限操作 |
| doc_link          | string | 文档地址 |
| approval_url      | string | 权限审批 URL；优先返回 ITSM 工单地址，否则返回 `{DASHBOARD_FE_URL}/{gateway_id}/permission/apply` |
