# 调用方式

每个 Skill 包里的本文件内容相同。要调哪些接口、参数取值和顺序写在 SKILL.md 的「接口清单」和「执行步骤」。这里只说明怎么把一步变成一次调用。有 bk-cli 时用 bk-cli；没有时按下面的 HTTP 方式调用，步骤和取值不变。

## 参数放哪

执行步骤里每次调用是一段 OpenAPI 3.1 片段。`paths` 下的键是路径，再下一层是方法；`x-bk-gateway`、`x-bk-stage` 是网关和环境。

- `parameters` 按 `in` 放：`path` 替换路径里的 `{参数名}`，`query` 放查询串，`header` 放请求头。
- `requestBody` 的 `properties` 组成 JSON 正文。没有 `requestBody` 就不发正文。
- 片段里没列的参数不要传。`x-omit-if-unset: true` 的参数取自选填输入，用户没给时整个参数不传。
- `x-value` 是固定值，按 JSON 原样传。
- `x-from: inputs.<名>` 换成用户输入。`x-from: <步骤>.<资源>.<字段路径>` 换成该次响应体里的值。`[0]` 是数组第一个元素，`[]` 是每个元素的该字段组成的数组。`each.<字段>` 只在逐个调用时换成当前元素。`x-where` 表示只取满足条件的元素。
- `responses` 只列要读的字段，字段路径相对响应体，见「返回内容」。
- 使用 bk-cli 时，query 不要自己做 URL 编码，bk-cli 会编码。不使用 bk-cli 时，query 里的保留字符要编码；产物下载接口的 `path` 就是这种值。
- `access_token`、`bk_token`、`bk_ticket`、`bk_app_secret` 不写进执行步骤的请求参数，不向用户要，也不出现在回复里。使用 bk-cli 时由登录态注入。不使用 bk-cli 时放进请求头 `X-Bkapi-Authorization`。某个接口的文档仍把 `access_token` 列为必填 query 时，把同一个用户 access token 放进 query，仍然不要写进回复。

## 使用 bk-cli

登录后调用会带上用户身份。接口清单里「应用认证」为「是」的接口，使用已配置的蓝鲸应用。

```bash
bk-cli api <gateway> <METHOD> '<path>' --stage <stage> \
  --path '{"路径参数": "<取值>"}' \
  --query '{"查询参数": "<取值>"}' \
  --body '{"请求体参数": <取值>}'
```

`<METHOD>`、`<path>` 取片段里的方法和路径，`<gateway>`、`<stage>` 取 `x-bk-gateway`、`x-bk-stage`。`in: path` 的参数放 `--path`，`in: query` 放 `--query`，`requestBody` 的字段放 `--body`，`in: header` 用 `--header '名字:取值'`。string 和路径参数的占位符带引号，数字、布尔、对象、数组不加引号。

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

`X-Bkapi-Authorization` 的值是 JSON。按接口清单取舍字段：

- 「用户认证」为「是」：带 `bk_token`，或带已有的 `access_token`，二选一。
- 「应用认证」为「是」：带 `bk_app_code` 和 `bk_app_secret`。
- 某一列为「否」时，不要放对应字段。

有 `requestBody` 时把其中的字段作为 JSON 正文，并加上 `Content-Type: application/json`。`in: query` 的参数拼在 URL 上，`in: header` 的参数作为同名请求头。

## 轮询

执行步骤写了「轮询」时，按该步的间隔、次数、结束条件和停止条件重复同一次调用。使用 bk-cli 时外壳 `ok` 为 false 就停止；不使用 bk-cli 时 HTTP 状态不是 2xx 就停止。中间响应不必展开，后续步骤用最后一次响应体。

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
