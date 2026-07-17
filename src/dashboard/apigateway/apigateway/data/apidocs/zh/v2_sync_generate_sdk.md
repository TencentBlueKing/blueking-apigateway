### 描述

异步生成资源版本对应的 SDK。接口返回 HTTP 202 后，构建完成的包将发布到已配置的软件仓库。

### 输入参数

#### 路径参数

| 参数名称         | 参数类型 | 必选 | 描述   |
|--------------| -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型      | 必选 | 描述                                                     |
| ---------------- | ------------- | ---- | -------------------------------------------------------- |
| resource_version | string        | 是   | 资源版本的版本号                                         |
| languages        | array[string] | 否   | 需要生成 SDK 的语言列表，可选值：python、java、go、javascript、rust，默认为 python |

### 请求参数示例

```json
{
    "resource_version": "1.0.1",
    "languages": ["python", "go"]
}
```



### 响应示例

```json
{
    "data": {
        "message": "SDK generation started"
    }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | object | 异步任务受理结果                   |
| message | string | 固定为 `SDK generation started`    |
