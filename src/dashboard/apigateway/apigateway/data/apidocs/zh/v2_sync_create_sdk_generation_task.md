### 描述

创建或继续资源版本对应的可观测 SDK 生成任务。相同资源版本和语言会复用已有任务及语言项，已经成功的语言不会重复生成。成功受理时返回 HTTP 202；SDK 生成功能关闭时返回 HTTP 503。

### 输入参数

#### 路径参数

| 参数名称     | 参数类型 | 必选 | 描述   |
| ------------ | -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型      | 必选 | 描述 |
| ---------------- | ------------- | ---- | ---- |
| resource_version | string        | 是   | 资源版本的版本号 |
| languages        | array[string] | 否   | 需要生成 SDK 的语言列表，可选值：python、java、go、javascript，默认为 python |
| version          | string        | 否   | 兼容旧调用保留；服务端忽略此值，包版本固定由资源版本派生 |

### 请求参数示例

```json
{
    "resource_version": "1.0.1",
    "languages": ["python", "javascript"],
    "version": "9.9.9"
}
```

### 响应示例

```json
{
    "data": {
        "id": 1,
        "status": "pending",
        "status_url": "/api/v2/sync/gateways/demo/sdk-generation-tasks/1/"
    }
}
```

status 202

### 响应参数说明

| 字段            | 类型   | 描述                     |
| --------------- | ------ | ------------------------ |
| data.id         | int    | SDK 生成任务 ID          |
| data.status     | string | SDK 生成任务状态         |
| data.status_url | string | SDK 生成任务状态查询地址 |
