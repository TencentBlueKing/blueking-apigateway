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

## 规范

- 默认：不勾选任何认证方式，并且不需要校验应用权限
- 一个case只测试一项内容
- 测试目录和文件名以`-`分隔，避免用空格

