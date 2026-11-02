### 描述

同步网关，如果网关不存在，创建网关，如果网关已存在，更新网关。


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名。创建 AI 网关时须以 `bkai-` 开头；非 AI 网关不能使用 `bkai-` 前缀 |

#### 请求参数

| 参数名称    | 参数类型 | 必选 | 描述                   |
| ----------- | -------- |----| ---------------------- |
| display_name | string/null | 否 | 网关展示名，最长 64 字符；创建时不填或为空默认为 name，更新时不填保持不变，传空值恢复为 name |
| display_name_en | string/null | 否 | 英文展示名，最长 64 字符，以英文字母开头，仅支持英文字母、数字、空格和横杠；不填或为空表示清空 |
| description | string   | 否  | 网关描述               |
| maintainers | array    | 否  | 网关管理员             |
| is_public   | boolean  | 否  | 网关是否公开，默认公开 |
| is_official | boolean  | 否  | `true` 为官方网关，`false` 为普通网关；新建时默认 `false`，更新时不传则保留原值 |
| kind        | string   | 否  | 网关类型：`normal`（默认）或 `ai`；仅创建时生效 |


两个展示名字段分别唯一，不区分大小写，并会去除首尾空白。

### 请求参数示例

```json
{
    "display_name": "示例网关",
    "display_name_en": "Example Gateway",
    "description": "just for test",
    "maintainers": ["admin"],
    "is_public": true,
    "is_official": false,
    "kind": "normal"
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.sync_api(
    {
        "display_name": "示例网关",
        "display_name_en": "Example Gateway",
        "description": "just for test",
        "maintainers": ["admin"],
        "is_public": True,
        "is_official": False,
        "kind": "normal"
    },
    path_params={
        "api_name": "demo",
    },
    headers={"Content-Type": "application/json"},
)
```


### 响应示例

```json
{
    "code": 0,
    "message": "OK",
    "data": {
        "id": 1,
        "display_name": "示例网关",
        "name": "demo",
        "kind": "normal",
        "is_official": false
    }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code    | int    | 返回码，0 表示成功，其它值表示失败 |
| message | string | 错误信息                           |
| data    | object | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称    | 参数类型 | 描述                                     |
| ----------- | -------- | ---------------------------------------- |
| id          | int      | 网关ID                                   |
| name        | string   | 网关名称                                 |
| display_name | string | 网关展示名 |
| kind        | string   | 网关类型：`normal`、`programmable` 或 `ai` |
| is_official | boolean  | 是否为官方网关                           |
