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
| `name`     | string        | 是  | MCP Server 名字 例如： `"mcp1"`(系统会默认转换为 {gateway_name}-{stage-name}-{name}) |
| `title`    | string        | 否  | MCP Server 中文名/显示名称                                                    |
| `description` | string        | 是  | MCP Server 描述                                                           |
| `labels`   | array[string] | 否  | MCP Server 标签                                                          |
| `resource_names` | array[string] | 是  | MCP Server 关联的 resource 列表                                             |
| `tool_names` | array[string] | 否  | MCP Server 工具名称列表，默认等于 resource_names。如果需要对资源进行重命名，可设置此字段，长度必须与 resource_names 一致，且不能重复                                                              |
| `is_public` | bool          | 否  | 是否公开，默认不公开                                                             |
| `status`   | integer          | 否  | 状态：1：启用，0：关闭(默认关闭)                                                     |
| `protocol_type` | string       | 否  | MCP 协议类型：sse（默认）、streamable_http                                       |
| `target_app_codes`   | array[string]          | 否  | 主动授权的应用列表                                                              |
| `oauth2_public_client_enabled`     | bool                   | 否  | 是否开启 OAuth2 公开客户端模式，开启后将会对 bk_app_code=public 的应用进行授权，默认不开启                     |
| `raw_response_enabled`     | bool                   | 否  | 是否返回原始响应，开启后 mcp-proxy 将直接返回 API 响应结果，不添加 request_id 等额外信息，默认不开启                     |
| `category_names`   | array[string]          | 否  | MCP Server 分类名称列表，不传则不更新分类。当前支持的分类：`Uncategorized`（未分类）、`Official`（官方资源）、`Featured`（精选推荐）、`Monitoring`（监控告警）、`ConfigManagement`（配置管理）、`DevOps`（持续交付）、`Emergency`（故障管理）、`Database`（数据服务）、`Automation`（运维自动化）、`Observability`（可观测性）、`Security`（安全合规）、`ResourceOptimize`（资源优化）、`ChaosEngineering`（混沌工程）、`Network`（网络管理）                                                              |


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
      "title": "服务1",
      "resource_names": [
        "resource1",
        "resource2"
      ],
      "tool_names": [
        "tool1",
        "tool2"
      ],
      "is_public": true,
      "description": "description",
      "status": 1,
      "protocol_type": "sse",
      "target_app_codes": [
        "app1",
        "app2"
      ],
      "oauth2_public_client_enabled": false,
      "raw_response_enabled": false,
      "category_names": [
        "Official"
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
          "action": "created",
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
| action | string   | updated / created |