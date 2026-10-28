### 描述

获取当前应用的网关 API 权限列表

### 输入参数

#### 请求参数

| 参数名称        | 参数类型 | 必选 | 描述                                          |
|-----------------|----------|------|-----------------------------------------------|
| grant_dimension | string   | 是   | 授权维度（gateway：按网关，resource：按资源） |
| gateway_name    | string   | 否   | 网关名称，精确匹配                            |
| resource_name   | string   | 否   | 资源名称，精确匹配，仅按资源维度查询时生效    |
| limit           | int      | 否   | 最大返回条目数量，默认为 10                   |
| offset          | int      | 否   | 相对于完整未分页数据的起始位置，默认为 0      |


### 响应示例

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 1,
        "bk_app_code": "my-app",
        "gateway_name": "bk-demo",
        "resource_name": "user_query",
        "expires": "2026-12-01 10:00:00 +0800",
        "grant_type": "apply"
      }
    ]
  }
}
```

### 响应参数说明

| 字段 | 类型   | 描述                           |
|------|--------|--------------------------------|
| data | object | 结果数据，详细信息请见下面说明 |


#### data

| 参数名称 | 参数类型 | 描述     |
|----------|----------|----------|
| count    | int      | 总数     |
| results  | array    | 权限列表 |


#### data.results

| 参数名称      | 参数类型 | 描述                                                                                                       |
|---------------|----------|------------------------------------------------------------------------------------------------------------|
| id            | int      | 权限记录 ID                                                                                                |
| bk_app_code   | string   | 蓝鲸应用编码                                                                                               |
| gateway_name  | string   | 网关名称                                                                                                   |
| resource_name | string   | 资源名称，按网关维度查询时为空                                                                             |
| expires       | string   | 过期时间                                                                                                   |
| grant_type    | string   | 授权类型（initialize：主动授权，apply：申请审批，renew：续期，auto_renew：自动续期，sync：按网关授权同步） |
