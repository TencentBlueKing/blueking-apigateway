### 描述

获取 mcp_server 的权限列表


#### 路径参数

| 参数名称            | 参数类型 | 必选 | 描述                    |
|-----------------|------|----|-----------------------|
| mcp_server_id   | int  | 是  | mcp_server ID         |
| limit           | int  | 否  | 最大返回条目数量，默认为 10       |
| offset          | int  | 否  | 相对于完整未分页数据的起始位置，默认为 0 |


### 响应示例

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 1,
        "bk_app_code": "bk-001",
        "expires": "2100-01-01 08:00:00 +0800",
        "grant_type": "apply",
        "mcp_server": {
          "id": 1,
          "name": "mcp_1",
          "description": null
        }
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

| 参数名称         | 参数类型   | 描述                       |
|--------------|--------|--------------------------|
| id           | int    | 权限记录 ID                  |
| bk_app_code  | string | 蓝鲸应用编码                   |
| expires      | string | 过期时间                     |
| grant_type   | string | 授权类型（grant：授权，apply：申请）  |
| mcp_server   | object | mcp_server 信息            |


#### data.mcp_server

| 参数名称          | 参数类型    | 描述              |
|---------------|---------|-----------------|
| id            | int     | mcp_server ID   |
| name          | string  | mcp_server 名称   |
| description   | string  | mcp_server 描述   |
