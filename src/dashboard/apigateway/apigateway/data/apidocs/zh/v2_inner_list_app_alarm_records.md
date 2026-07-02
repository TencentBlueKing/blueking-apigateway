### 描述

应用维度告警记录列表

### 输入参数

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| target_app_code | string | 是 | 目标应用编码，必须与当前请求应用一致 |
| status | string | 否 | 告警状态：received、skipped、success、failure |
| gateway_name | string | 否 | 网关名称（精确匹配） |
| resource_name | string | 否 | 资源名称（精确匹配） |
| time_start | int | 是 | 开始时间（Unix 时间戳，秒） |
| time_end | int | 是 | 结束时间（Unix 时间戳，秒） |
| offset | int | 否 | 偏移量，默认 0 |
| limit | int | 否 | 限制条数，默认 10 |

### 响应示例

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 1,
        "alarm_id": "26661111",
        "status": "success",
        "status_display": "告警成功",
        "created_time": "2026-07-02 10:00:00 +0800",
        "gateway_name": "bk-example",
        "stage": "prod",
        "resource_id": 12,
        "resource_name": "list_users",
        "request_id": "f1a0f0f4aef149d88b36e5",
        "message": "..."
      }
    ]
  }
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | object | 结果数据，包含 count 与 results |

#### data.results

| 参数名称 | 参数类型 | 描述 |
|---|---|---|
| id | int | 告警记录 ID |
| alarm_id | string | 告警平台事件 ID |
| status | string | 告警状态 |
| status_display | string | 告警状态描述 |
| created_time | string | 告警创建时间 |
| gateway_name | string | 网关名称 |
| stage | string | 环境名称 |
| resource_id | int | 资源 ID |
| resource_name | string | 资源名称 |
| request_id | string | 请求 ID，可用于工具箱联动排查 |
| message | string | 告警消息 |
