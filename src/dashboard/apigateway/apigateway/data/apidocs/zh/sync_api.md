### 描述

同步网关，如果网关不存在，创建网关，如果网关已存在，更新网关。名称输入始终使用原始值，不受请求语言影响。


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名。创建 AI 网关时须以 `bkai-` 开头；非 AI 网关不能使用 `bkai-` 前缀 |

#### 请求参数

| 参数名称    | 参数类型 | 必选 | 描述                   |
| ----------- | -------- |----| ---------------------- |
| display_name | string/null | 否 | 默认展示名，最长 64 字符；创建时省略或为空取技术名；更新时省略保留当前数据库值，显式空值恢复技术名 |
| display_name_en | string/null | 否 | 英文展示名，最长 64 字符；仅自动化同步可写；省略、null、空字符串或纯空白均清为 NULL |
| description | string   | 否  | 网关描述               |
| maintainers | array    | 否  | 网关管理员             |
| is_public   | boolean  | 否  | 网关是否公开，默认公开 |
| is_official | boolean  | 否  | `true` 为官方网关，`false` 为普通网关；新建时默认 `false`，更新时不传则保留原值 |
| kind        | string   | 否  | 网关类型：`normal`（默认）或 `ai`；仅创建时生效 |


名称先去除首尾空白，保留内部空格和原始大小写。非空英文名须完整匹配 `[A-Za-z][A-Za-z0-9 -]*`：以 ASCII 字母开头，其后仅允许 ASCII 字母、数字、空格及横杠。

名称按 `strip().casefold()` 在所有租户、类别和状态的网关间检查。默认名分别查重，英文最终显示值（英文名或默认名回退）分别查重，并双向检查与其他网关技术名的冲突；自身名称可复用，单纯跨语言重名允许。两个数据库唯一索引分别约束默认名和非 NULL 英文名；跨字段检查允许并发竞态，不提供全局串行化。冲突返回既有参数校验错误，整个同步回滚；清空英文名后产生的回退冲突也会拒绝保存。

响应的 `display_name` 按请求语言选择；`name` 仍为技术名。Web 和 Admin 只编辑默认名，Web 读取本地化 `display_name`，写入同名字段始终修改默认名；不存在原始默认名别名、写入标记或独立名称配置接口。

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
| display_name | string | 网关本地化展示名，最长 64 字符；英文请求取英文名，未配置英文名时回退默认名；定位仍使用技术名或数值 ID。 |
| kind        | string   | 网关类型：`normal`、`programmable` 或 `ai` |
| is_official | boolean  | 是否为官方网关                           |
