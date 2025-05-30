### 描述

MCPServer 申请权限/批量申请权限


### 输入参数

#### 路径参数

#### 请求参数

| 参数名称                     | 参数类型       | 必选 | 描述                   |
|--------------------------|------------|----|----------------------|
| target_app_code          | string     | 是  | 申请权限的应用，应于当前请求的应用一致  |
| mcp_server_ids           | array[int] | 是  | mcp_server ID 列表     |
| applied_by               | string     | 是  | 申请人                  |
| reason                   | string     | 是  | 申请理由                 |

### 请求参数示例

```json
{
  "target_app_code": "test",
  "mcp_server_ids": [1, 2],
  "applied_by": "admin",
  "reason": "test"
}
```


### 响应示例

```json
{
  "data": {
    
  }
}

```
