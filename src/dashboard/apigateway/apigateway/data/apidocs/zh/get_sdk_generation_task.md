### 描述

查询异步 SDK 生成任务的状态、各语言执行结果和产物信息。

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述            |
| -------- | -------- | ---- | --------------- |
| api_name | string   | 是   | 网关名          |
| task_id  | int      | 是   | SDK 生成任务 ID |

### 响应示例

```json
{
    "code": 0,
    "message": "OK",
    "result": true,
    "data": {
        "id": 1,
        "status": "running",
        "resource_version": {
            "id": 10,
            "version": "1.0.1"
        },
        "items": [
            {
                "id": 2,
                "language": "python",
                "status": "running",
                "attempt_count": 1,
                "error": null,
                "artifacts": []
            }
        ]
    }
}
```

### 响应参数说明

| 字段                          | 类型        | 描述                                   |
| ----------------------------- | ----------- | -------------------------------------- |
| data.id                       | int         | SDK 生成任务 ID                        |
| data.status                   | string      | 任务状态                               |
| data.resource_version         | object      | 任务对应的资源版本                     |
| data.items                    | array       | 各语言的执行状态                       |
| data.items[].error            | object/null | 失败代码和错误消息                     |
| data.items[].artifacts        | array       | 已生成或已发布的产物、坐标和下载地址   |
