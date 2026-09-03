### 描述

异步生成资源版本对应的 SDK。请求受理后，构建完成的包将发布到已配置的软件仓库。

兼容说明：此 V1 接口由同步生成调整为异步受理，响应中的 `data` 已由 SDK 下载信息数组调整为任务信息对象，调用方需通过 `data.status_url` 查询结果。旧参数 `golang` 仍可使用并会按 `go` 处理；`version` 参数仍可传入，但包版本固定由资源版本派生，该参数不再改变包版本。

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型      | 必选 | 描述                                                     |
| ---------------- | ------------- | ---- | -------------------------------------------------------- |
| resource_version | string        | 是   | 资源版本的版本号                                         |
| languages        | array[string] | 否   | 需要生成 SDK 的语言列表，可选值：python、java、go、javascript、rust；兼容 golang（按 go 处理），默认为 python |
| version          | string        | 否   | 兼容旧调用保留；包版本固定由资源版本派生，此参数不再改变包版本 |

### 请求参数示例

```json
{
    "resource_version": "1.0.1",
    "languages": ["python", "golang"],
    "version": "1.0.1"
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.generate_sdk(
    {
        "resource_version": "1.0.1",
        "languages": ["python", "golang"],
        "version": "1.0.1"
    }
)
```


### 响应示例

```json
{
    "code": 0,
    "message": "SDK generation started",
    "result": true,
    "data": {
        "id": 1,
        "status": "pending",
        "status_url": "/api/v1/apis/demo/sdk/tasks/1/"
    }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code            | int     | 返回码，0 表示成功，其它值表示失败 |
| message         | string  | 受理结果                           |
| result          | boolean | 是否受理成功                       |
| data.id         | int     | SDK 生成任务 ID                    |
| data.status     | string  | SDK 生成任务状态                   |
| data.status_url | string  | SDK 生成任务状态查询地址           |
