### 描述

获取 mcp_server 列表

### 输入参数

#### 请求参数

| 参数名称        | 参数类型    | 必选    | 描述                          |
|-------------|---------|-------|-----------------------------|
| is_public   | boolean | 否     | 是否公开，true：公开，false：不公开，不传或传空则查询全部  |
| keyword     | string  | 否     | 筛选条件，支持模糊匹配 MCPServer 名称或描述 |
| limit       | int     | 否     | 最大返回条目数量，默认为 10             |
| offset      | int     | 否     | 相对于完整未分页数据的起始位置，默认为 0       |


### 响应示例

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 2,
        "name": "test",
        "description": null,
        "is_public": true,
        "labels": [],
        "resource_names": [],
        "status": 1,
        "stage": {
          "id": 3,
          "name": "prod"
        },
        "gateway": {
          "id": 2,
          "name": "bk-esb",
          "maintainers": [
            "admin"
          ],
          "is_official": true
        },
        "tools_count": 0,
        "url": "",
        "detail_url": "",
        "updated_by": "admin",
        "created_by": "admin",
        "updated_time": "2025-09-01 00:00:00 +0800",
        "created_time": "2025-09-01 00:00:00 +0800"
      }
    ]
  }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |


#### data

| 参数名称           | 参数类型    | 描述                         |
|----------------|---------|----------------------------|
| id             | int     | mcp_server ID              |
| name           | string  | mcp_server 名称              |
| description    | string  | mcp_server 描述              |
| is_public      | boolean | mcp_server 是否公开            |
| labels         | array   | mcp_server 标签              |
| resource_names | array   | mcp_server 资源名称            |
| status         | int     | mcp_server 状态（0：已停用，1：启用中） |
| tools_count    | int     | mcp_server 工具数量            |
| url            | string  | mcp_server 访问地址            |
| detail_url     | string  | mcp_server 网关站点详情地址        |
| updated_by     | string  | 更新人                        |
| created_by     | string  | 创建人                        |
| updated_time   | string  | 更新时间                       |
| created_time   | string  | 创建时间                       |
| gateway        | object  | mcp_server 网关信息            |
| stage          | object  | mcp_server 环境信息            |


#### data.gateway

| 参数名称          | 参数类型    | 描述           |
|---------------|---------|--------------|
| id            | int     | 网关 ID        |
| name          | string  | 网关名称         |
| maintainers   | array   | 网关管理员        |
| is_official   | boolean | 是否为官方网关      |


#### data.stage

| 参数名称          | 参数类型    | 描述    |
|---------------|---------|-------|
| id            | int     | 环境 ID |
| name          | string  | 环境名称  |

