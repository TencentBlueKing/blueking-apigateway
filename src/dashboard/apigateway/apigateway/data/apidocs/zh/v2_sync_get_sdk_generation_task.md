### 描述

查询异步 SDK 生成任务的状态、各语言执行结果和产物信息。

### 输入参数

#### 路径参数

| 参数名称     | 参数类型 | 必选 | 描述            |
| ------------ | -------- | ---- | --------------- |
| gateway_name | string   | 是   | 网关名          |
| task_id      | int      | 是   | SDK 生成任务 ID |

### 响应示例

```json
{
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
                "native_status": "pending",
                "attempt_count": 1,
                "error": null,
                "native_error": null,
                "download_url": "",
                "artifacts": []
            }
        ]
    }
}
```

### 响应参数说明

| 字段                          | 类型        | 描述                                 |
| ----------------------------- | ----------- | ------------------------------------ |
| data.id                       | int         | SDK 生成任务 ID                      |
| data.status                   | string      | 任务状态                             |
| data.resource_version         | object      | 任务对应的资源版本                   |
| data.items                    | array       | 各语言的执行状态                     |
| data.items[].status           | string      | 生成状态：pending、running、success 或 failed |
| data.items[].native_status    | string      | 原生仓库发布状态；不影响 Generic 下载结果      |
| data.items[].attempt_count    | int         | 生成阶段累计执行次数                         |
| data.items[].error            | object/null | 生成失败代码和错误消息                       |
| data.items[].native_error     | object/null | 原生仓库发布失败代码和错误消息               |
| data.items[].download_url     | string      | 首选 BKRepo Generic 制品下载地址              |
| data.items[].artifacts        | array       | 已成功发布的产物、坐标、校验和及下载地址      |
