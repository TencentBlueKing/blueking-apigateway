### 描述

同步资源

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

#### 资源 YAML 字段说明

资源配置通过 OpenAPI Operation 下的 `x-bk-apigateway-resource` 扩展字段导入，支持以下字段：

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| `kind` | string | 否 | 资源类型：`standard` 表示普通 API，`ai` 表示模型代理 API；不传默认为 `standard` |
| `isPublic` | boolean | 否 | 是否公开资源，默认 `true` |
| `allowApplyPermission` | boolean | 否 | 是否允许用户申请资源权限，默认 `true` |
| `matchSubpath` | boolean | 否 | 是否匹配所有子路径，默认 `false`；普通 API 需与 `backend.matchSubpath` 保持一致，模型代理 API 不支持开启 |
| `enableWebsocket` | boolean | 否 | 是否启用 WebSocket，默认 `false`；模型代理 API 不支持开启 |
| `noneSchema` | boolean | 否 | 是否没有请求参数；资源没有 body、path、header、query 参数且需被 MCP Server 使用时，应显式设置为 `true` |
| `backend` | object | 否 | 后端服务配置；普通 API 不传时默认使用 `default` 后端，后端请求方法和路径取当前 Operation；模型代理 API 必须传入且只能包含模型服务名称 |
| `pluginConfigs` | array[object] | 否 | 资源插件配置列表，每项包含 `type` 和 `yaml` |
| `authConfig` | object | 否 | 认证配置，见下方 `authConfig` 字段说明 |
| `descriptionEn` | string | 否 | 资源英文描述 |

`backend` 字段说明：

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| `name` | string | 否 | 后端服务名称，默认 `default`；模型代理 API 必填，且必须对应模型服务 |
| `type` | string | 否 | 后端类型，仅普通 API 支持，当前仅支持 `HTTP`，默认 `HTTP` |
| `method` | string | 普通 API 必填 | 后端请求方法，可选值：`get`、`put`、`post`、`delete`、`options`、`head`、`patch`、`any` |
| `path` | string | 普通 API 必填 | 后端请求路径 |
| `matchSubpath` | boolean | 否 | 是否追加匹配的子路径，默认 `false`；需与资源的 `matchSubpath` 保持一致 |
| `timeout` | integer | 否 | 后端请求超时时间，默认 `0` |
| `upstreams` | object | 否 | 兼容旧版资源 YAML 的后端地址配置 |
| `transformHeaders` | object | 否 | 兼容旧版资源 YAML 的请求头转换配置 |

`authConfig` 字段说明：

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| `userVerifiedRequired` | boolean | 否 | 是否开启用户认证，默认 `true` |
| `appVerifiedRequired` | boolean | 否 | 是否开启应用认证，默认 `true`；为 `false` 时会自动关闭资源权限校验 |
| `resourcePermissionRequired` | boolean | 否 | 是否校验应用资源权限，默认 `true` |
| `oauth2PublicClientEnabled` | boolean | 否 | 是否允许 OAuth2 public client 调用，默认 `false` |
| `oauth2PersonalClientEnabled` | boolean | 否 | 是否允许 OAuth2 personal client 调用，默认 `false` |

AI 网关可以同时导入普通 API 和模型代理 API。模型代理 API 必须满足：

- 网关类型为 AI 网关。
- Operation 请求方法必须为 `post`。
- `x-bk-apigateway-resource.kind` 必须为 `ai`。
- `backend` 只能包含模型服务名称 `name`，且该模型服务需通过环境同步接口的 `ai_backends` 提前导入。
- 不支持开启 `matchSubpath` 和 `enableWebsocket`。

普通 API 示例：

```yaml
x-bk-apigateway-resource:
  kind: standard
  backend:
    name: default
    method: get
    path: /backend/users
    timeout: 30
```

模型代理 API 示例：

```yaml
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
