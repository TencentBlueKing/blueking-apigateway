### 描述

查询系统权限组件


### 输入参数

#### 路径参数

| 参数名称            | 参数类型     | 必选  | 描述                  |
|-----------------|----------|-----|---------------------|
| target_app_code | string   | 是   | 申请权限的应用，应于当前请求的应用一致 |
| system_id       | string   | 是   | 系统ID                |


### 请求参数示例

```json
{}
```


### 响应示例
```
{
  "data": [
    {
      "id": 1,
      "name": "get_doc_link_by_path",
      "system_name": "BK_DOCS_CENTER",
      "system_id": 16,
      "description": "根据md名查询md所在链接",
      "description_en": "Query the link of the document according to the MD name",
      "expires_in": null,
      "permission_level": "unlimited",
      "permission_status": "unlimited",
      "permission_action": "",
      "doc_link": "",
      "tag": ""
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
