### 描述

根据资源名称获取网关下单个资源的基本信息（编辑区数据，非已发布数据）。

供 BKAuth 等第三方系统根据 ResourceID 中的 api_name 解析资源展示信息。

### 输入参数

#### 路径参数

| 参数名称      | 参数类型 | 必选 | 描述     |
| ------------- | -------- | ---- | -------- |
| gateway_name  | string   | 是   | 网关名称 |
| resource_name | string   | 是   | 资源名称 |

### 响应示例

```json
{
    "data": {
        "id": 1,
        "name": "get_user_info",
        "description": "获取用户信息",
        "method": "GET",
        "path": "/api/v1/users/{user_id}/",
        "match_subpath": false,
        "is_public": true
    }
}
```

### 响应参数说明

| 字段 | 类型   | 描述                           |
| ---- | ------ | ------------------------------ |
| data | object | 结果数据，详细信息请见下面说明 |

#### data

| 参数名称      | 参数类型 | 描述           |
| ------------- | -------- | -------------- |
| id            | int      | 资源 ID        |
| name          | string   | 资源名称       |
| description   | string   | 资源描述       |
| method        | string   | 请求方法       |
| path          | string   | 资源路径       |
| match_subpath | boolean  | 是否匹配子路径 |
| is_public     | boolean  | 是否公开       |
