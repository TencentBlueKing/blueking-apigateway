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
对应用例在 `cases/apisix/08-plugins/023-bk-oauth2-app-access/` 和 `cases/dashboard/02-inner-api/25~28`。

环境要求：

- APISIX 的 Helm values 配置了 `bk_gateway.bk_oauth2.bearer_token_rules`（例如 `^bk[oprs]_` 和 `^tai_pat_`）；未配置时应用通道不生效，相关用例会失败
- bkauth 自省接口可用：用例中的 `bko_`/`bkp_`/`bkr_` token 都是未注册的，期望 bkauth 返回 inactive
- 导入后约 30 秒数据面才加载新版本，需等待后再运行用例

以下用例需要真实的 bkauth token，环境变量为空时跳过（`bru.runner.skipRequest()`）：

- `oauth2_app_delegated_token`：签发给 `test_bk_app_code` 的用户委托 token，audience 覆盖 `gateway:oauth2-app/api:*`
- `oauth2_app_only_token`：签发给 `test_bk_app_code` 的应用 token，audience 同上

```
bru run . -r --env e2e --env-var oauth2_app_delegated_token=<token> --env-var oauth2_app_only_token=<token>
```

## 规范

- 默认：不勾选任何认证方式，并且不需要校验应用权限
- 一个case只测试一项内容
- 测试目录和文件名以`-`分隔，避免用空格

