### 描述

同步 stage 的 MCP Server，不存在则创建，存在则更新


### 输入参数

#### 路径参数

| 参数名称         | 参数类型 | 必选 | 描述  |
|--------------| -------- | ---- |-----|
| gateway_name | string   | 是   | 网关名 |
| stage_name   | string   | 是   | 环境名 |

#### 请求参数

| 参数名称             | 参数类型       | 必选 | 描述                                                |
|------------------| -------------- | ---- |---------------------------------------------------|
| `mcp_servers`    | array[object]      | 是   | MCP Server 配置列表                                   |


mcp_servers 参数说明
每个 mcp_serve 配置对象包含：

| 参数名称       | 参数类型          | 必选 | 描述                                                                     |
|------------|---------------|----|------------------------------------------------------------------------|
| `name`     | string        | 是  | MCP Server 名字 例如： `"mcp1"`(系统会默认带上 {gateway_name}-{stage-name}-{name}) |
| `description` | string        | 否  | MCP Server 名字 例如： `"mcp1"`(系统会默认带上 {gateway_name}-{stage-name}-{name}) |
| `labels`   | array[string] | 否  | MCP Server 标签                                                          |
| `resource_names` | array[string] | 是  | MCP Server 关联的 resource 列表                                             |
| `is_public` | bool          | 否  | 是否公开，默认不公开                                                             |
| `status`   | integer          | 否  | 状态：1：启用，0：关闭(默认关闭)                                                     |
| `target_app_codes`   | array[string]          | 否  | 主动授权的应用列表                                                              |


### 请求参数示例

```json
{
  "mcp_servers": [
    {
      "labels": [
        "tag1",
        "tag2"
      ],
      "name": "server1",
      "resource_names": [
        "resource1"
      ],
      "is_public": true,
      "description": "description",
      "status": 1,
      "target_app_codes": [
        "app1",
        "app2"
      ]
    }
  ]
}
```



### 响应示例

```json
{
    "data": [
      {
         "name": "gateway-stage-server1",
          "action": "create",
          "id": 1
      }
      
    ]
}
```


#### 响应参数说明


| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |

data

| 参数名称   | 参数类型 | 描述               |
|--------| -------- |------------------|
| id     | integer  | MCP Server ID    |
| name   | string   | MCP Serve name   |
| action | string   | updated / crated |