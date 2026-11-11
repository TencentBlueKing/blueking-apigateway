# 调用方式

每个 Skill 包里的本文件内容相同。要调哪些接口、参数取值和顺序写在 SKILL.md 的「接口清单」和「执行步骤」。这里只说明怎么把一步变成一次调用。有 bk-cli 时用 bk-cli；没有时按下面的 HTTP 方式调用，步骤和取值不变。

## 参数放哪

执行步骤里每次调用是一段 YAML 调用说明。`gateway_name`、`stage_name`、`resource_name`、`method`、`path` 是 Skill 生成器根据步骤 `uses` 和资源定义写入的调用目标；`parameters`、`requestBody`、`responses` 沿用 OpenAPI 3.1 对象结构，但整段说明不是 OpenAPI 文档。

- `parameters` 按 `in` 放：`path` 替换路径里的 `{参数名}`，`query` 放查询串，`header` 放请求头。
- `requestBody` 的 `properties` 组成 JSON 正文。没有 `requestBody` 就不发正文。
- 片段里没列的参数不要传，步骤说明明确要求传的除外。`x-omit-if-unset: true` 的参数取自选填输入，用户没给时整个参数不传。
- `x-value` 是固定值，按 JSON 原样传。
- `x-from: ${{ inputs.<名> }}` 换成用户输入。`x-from: ${{ steps.<步骤 id>.outputs.<字段路径> }}` 换成该步骤响应体里的值。`[0]` 是数组第一个元素，`[]` 是每个元素的该字段组成的数组。
- 没有 `x-from`、`x-value` 的参数按该步的说明取值，例如逐个调用时取当前元素的字段。
- `responses` 是该接口已发布 OpenAPI 的响应字段，字段路径相对响应体，见「返回内容」。
- 使用 bk-cli 时，query 不要自己做 URL 编码，bk-cli 会编码。不使用 bk-cli 时，query 里的保留字符要编码；产物下载接口的 `path` 就是这种值。
- 接口认证不根据凭据字段名判断。认证凭据不向用户要，也不出现在回复里；使用 bk-cli 时由当前 context 按目标网关支持的认证方式注入。不使用 bk-cli 时，按目标网关的调用文档传递认证信息。

## 使用 bk-cli

完成登录后，`bk-cli api` 默认使用当前 context 保存的凭据进行认证。调用前，请确认所用凭据满足接口的应用认证、用户认证及权限要求。

```bash
bk-cli api <gateway> <METHOD> '<path>' --stage <stage> \
  --path '{"id": 123}' \
  --query '{"keyword": "示例", "limit": 10}' \
  --body '{"name": "示例", "enabled": true}'
```

以上为参数格式示例，请按接口定义替换；不需要的选项应删除。

- `<gateway>`、`<stage>`、`<METHOD>`、`<path>` 分别使用调用说明中的 `gateway_name`、`stage_name`、`method`、`path`；这些值需要代入命令，CLI 不会自动读取调用说明。
- 路径中的 `{参数名}` 使用 `--path` 替换，键名必须与占位符一致；路径已填入实际值时，无需传 `--path`。
- 查询参数使用 `--query`；请求头使用 `--header '名字:取值'`，多个请求头重复传入该选项。
- JSON 请求体使用 `--body`，保持接口要求的完整结构，也可使用 `--body @body.json`。
- JSON 字符串使用双引号；数字、布尔值、对象和数组保持各自的 JSON 类型。`--path` 的值仅支持字符串、数字和布尔值。
- 复杂查询参数须按接口要求确认编码方式；表单和文件上传不适用上述 JSON 请求体示例。

## 不使用 bk-cli

对网关发 HTTP 请求。地址由该环境的 URL 模板套上网关名，再接 `/<环境>` 和接口清单里的路径。

```text
{{ gateway_url_template }}
```

接口清单是 bk-sops、prod、`GET /get_task_list/{bk_biz_id}/`，业务 ID 为 2 时：

```bash
curl -H 'X-Bkapi-Authorization: {"bk_app_code":"<应用 ID>","bk_app_secret":"<应用密钥>","bk_token":"<用户 token>"}' \
  '{{ example_url }}'
```

不同网关支持的认证方式和凭据字段可能不同，应以目标网关的调用文档为准。下面仅说明默认蓝鲸认证下 `X-Bkapi-Authorization` 的常见字段，值是 JSON：

- 「用户认证」为「是」：带 `bk_token`，或带已有的 `access_token`，二选一。
- 「应用认证」为「是」：带 `bk_app_code` 和 `bk_app_secret`。
- 某一列为「否」时，不要放对应字段。

有 `requestBody` 时把其中的字段作为 JSON 正文，并加上 `Content-Type: application/json`。`in: query` 的参数拼在 URL 上，`in: header` 的参数作为同名请求头。

## 执行条件、轮询和逐个调用

步骤说明写了执行条件时，条件不成立就跳过该步。步骤说明要求轮询时，按说明的间隔、次数、结束条件和停止条件重复同一步的调用。使用 bk-cli 时外壳 `ok` 为 false 就停止；不使用 bk-cli 时 HTTP 状态不是 2xx 就停止。中间响应不必展开，后续步骤用最后一次响应体。步骤说明要求对数组逐个调用时，每个元素调用一次，没有这样的元素就跳过；后续步骤和输出用到该步时，把每次的结果按顺序汇总。

## 返回内容

SKILL.md 里的字段路径相对网关响应体。使用 bk-cli 时，stdout 是一层 JSON 外壳，响应体在 `data` 里：

```json
{
  "ok": true,
  "status": 200,
  "headers": {"X-Bkapi-Request-Id": "..."},
  "data": {"result": true, "data": {}}
}
```

上例中 `data.task_id` 指外壳的 `data.data.task_id`。不使用 bk-cli 时没有这层外壳，`data.task_id` 就是 HTTP 正文里的 `data.task_id`。

- 使用 bk-cli：HTTP 状态不是 2xx 时 `ok` 为 false。这时退出码仍可能是 0，先看 `ok`。
- 不使用 bk-cli：先看 HTTP 状态。不是 2xx 就停止。
- 网关错误码在响应头：`X-Bkapi-Error-Code`、`X-Bkapi-Error-Message`。`status` 为 403 且错误码 `1640301` 表示没有网关接口权限，按 [permissions.md](permissions.md) 申请。
- 请求到达业务系统后，还要看响应体里的 `result` 或 `status`。`result` 为 false 时把 `message` 告诉用户并停止。业务无权限（如 IAM `9900403`）到业务系统申请，不是网关权限。
