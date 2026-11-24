test
=============

存放测试相关的脚本/测试用例等

该目录在部署后，可以执行用以验证功能正确性，相当于集成测试

## run

### config file

准备好

`./cases/environments/e2e.bru`

```
cp cases/environments/dev.bru cases/environments/e2e.bru
vim cases/environments/e2e.bru
```

注意需要生成一个 access_token, 进入 bkssm 容器内

```bash
$ curl -H "X-Bk-App-Code:bk_apigateway" -H "X-Bk-App-Secret:358627d8-d3e8-4522-8f16-b5530776bbb8" http://0.0.0.0:5000/api/v1/auth/access-tokens  -d '
{
  "grant_type": "authorization_code",
  "id_provider": "bk_login",
  "bk_token": "bkcrypt%24gAAAAABoiwnmlllMUYyjdzJUSaL_fH33Xer-KBJHHygVMGK6V_IS12Eudi9V9QuigT2VejBuEsZgztE4zla2eCycplTZ0Ji7Jo06TSveRw0YHmCtH5eYExE%3D"
}'

{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "yBnxr6qWvk35FikZMWz2LEkatnxyiL",
    "refresh_token": "ekzDlfS9p7E1SNjNaCLCDtRQ30NBkD",
    "expires_in": 43200,
    "identity": {
      "username": "admin",
      "user_type": "bkuser"
    }
  }
}
```

### run

in bash

```
cd cases && ./run.sh e2e
```

via docker

```
docker build --tag apigateway_test .
docker run --rm apigateway_test:latest
```

### OAuth2 应用通道

`sync/run.sh` 会导入两个网关：`oauth2-app`（应用通道开关打开）和 `oauth2-app-off`（开关关闭）。
`oauth2_app_enabled` 只有 v2 同步接口支持，所以这两个网关使用 apigw-manager 5.x 导入。
对应用例在 `cases/apisix/08-plugins/023-bk-oauth2-app-access/` 和 `cases/dashboard/02-inner-api/25~31`。
`smoke` 等用 apigw-manager 4.x 导入的网关没有传开关，默认开启应用通道，`001-bk-auth` 等现有用例同时验证旧凭证在这类路由上的兼容。

环境要求：

- APISIX 版本不低于 3.16，否则 Dashboard 不下发 OAuth2 插件
- APISIX 配置了 `bk_gateway.hosts.bk-apigateway-api.tmpl`，401 响应的 `WWW-Authenticate` 才带 `resource_metadata`
- `bk_gateway.bk_oauth2.bearer_token_rules` 可不配置，默认前缀为 `^bk[oprs]_`、`^tai_pat_`；如果覆盖，需要包含 `^bkp_`、`^bko_`、`^bkr_`
- bkauth 自省接口可用。对于用例内写死的未知 token（含 `bkp_short`），需返回 200 且 `active=false`。返回非 200 时网关响应 503，相关用例会失败。
- `access_token` 环境变量是有效的旧版 access_token（与 `001-bk-auth` 相同）
- 导入后约 30 秒数据面才加载新版本，需等待后再运行用例

以下变量供需要有效 token 的用例使用。通过 `bru run` 运行时，默认跳过对应变量为空的用例。

- `oauth2_app_delegated_token`：签发给 `test_bk_app_code` 的用户委托 token，audience 只覆盖 `gateway:oauth2-app/api:*`
- `oauth2_app_only_token`：签发给 `test_bk_app_code` 的应用 token，audience 同上；不能覆盖 `smoke` 网关（`36-app-token-audience-mismatch` 用它验证 audience 不匹配）
- `oauth2_app_no_permission_token`：签发给另一个应用的有效应用 token，audience 覆盖 `gateway:oauth2-app/api:app_p1`。该应用没有 `oauth2-app` 的网关授权或 `app_p1` 的资源授权。用例 37 应收到 403 `APP_NO_PERMISSION`。

可用本地 bkauth mock 的 active 响应验证网关链路。上线验收时，在私有 Bruno 环境文件中配置三个实际签发的 token 和 `oauth2_app_tokens_required: true`，缺少 token 时对应用例直接失败。在 `test/cases` 下运行：

```bash
bru run . -r --env-file environments/e2e.bru
```

## 规范

- 默认：不勾选任何认证方式，并且不需要校验应用权限
- 一个case只测试一项内容
- 测试目录和文件名以`-`分隔，避免用空格

