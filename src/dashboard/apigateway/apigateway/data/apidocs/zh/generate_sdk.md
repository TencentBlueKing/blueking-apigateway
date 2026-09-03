### 描述

异步生成资源版本对应的 SDK。请求受理后，构建完成的包将发布到已配置的软件仓库。

这是兼容旧调用的 V1 接口，成功时保持 HTTP 200 和 `data: []`，不返回任务 ID。旧参数 `golang` 仍可使用并会按 `go` 处理；`version` 参数仍可传入，但服务端会忽略该值，包版本固定由资源版本派生。如需查询任务状态，请使用 V2 的可观测任务接口。

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型      | 必选 | 描述                                                     |
| ---------------- | ------------- | ---- | -------------------------------------------------------- |
| resource_version | string        | 是   | 资源版本的版本号                                         |
| languages        | array[string] | 否   | 需要生成 SDK 的语言列表，可选值：python、java、go、javascript；兼容 golang（按 go 处理），默认为 python |
| version          | string        | 否   | 兼容旧调用保留；服务端忽略此值，包版本固定由资源版本派生 |

### 请求参数示例

```json
{
    "resource_version": "1.0.1",
    "languages": ["python", "javascript"],
    "version": "9.9.9"
}
```

### SDK 调用示例

```shell
curl -X POST '<网关地址>/api/v1/apis/demo/sdk/' \
  -H 'Content-Type: application/json' \
  -d '{"resource_version":"1.0.1","languages":["python","javascript"]}'
```


### 响应示例

```json
{
    "code": 0,
    "message": "SDK generation started",
    "result": true,
    "data": []
}
```

### 响应参数说明

| 字段            | 类型    | 描述                               |
| --------------- | ------- | ---------------------------------- |
| code            | int     | 返回码，0 表示成功，其它值表示失败 |
| message         | string  | 受理结果                           |
| result          | boolean | 是否受理成功                       |
| data            | array   | 为兼容旧调用固定返回空数组         |
