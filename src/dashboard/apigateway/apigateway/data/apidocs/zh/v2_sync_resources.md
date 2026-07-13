### 描述

同步资源

资源类型通过 OpenAPI operation 的 `x-bk-apigateway-resource.kind` 指定。缺省或 `standard` 表示普通 API，`ai` 表示模型代理 API。AI Resource 仅允许同步到 AI 网关，且其 `backend` 只关联模型 Backend 名称；Resource 创建后不能修改类型。


### 输入参数

#### 路径参数

| 参数名称         | 参数类型 | 必选 | 描述   |
|--------------| -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称 | 参数类型    | 必选 | 描述                                                                     |
| -------- |---------| ---- |------------------------------------------------------------------------|
| content  | string  | 是   | 网关资源 swagger 描述，可为 yaml 格式文本，具体参考网关资源导出的资源配置                           |
| delete   | boolean | 否   | 是否删除未指定的资源，如果为 true，则删除网关中未在 content 中指定的资源，以确保网关中资源和 content 中描述的资源一致 |
| doc_language   | string  | 否   | 生成接口文档的语言：en: 英文，zh: 中文，不传不生成                                          |

AI Resource 的 `content` 示例：

```yaml
openapi: 3.0.1
info:
  title: AI resources
  version: 1.0.0
paths:
  /chat/completions:
    post:
      operationId: chat_completions
      x-bk-apigateway-resource:
        kind: ai
        backend:
          name: openai-primary
```

### 请求参数示例

```json
{
    "content": "xxx",
    "delete": false
}
```


### 响应示例

```json
{
    "data": {
        "added": [{"id": 1}],
        "updated": [{"id": 2}],
        "deleted": [{"id": 3}]
    }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |

data

| 参数名称 | 参数类型 | 描述                                |
| -------- | -------- | ----------------------------------- |
| added    | array    | 新增的资源，其中数据，id 表示资源ID |
| updated  | array    | 更新的资源，其中数据，id 表示资源ID |
| deleted  | array    | 删除的资源，其中数据，id 表示资源ID |
