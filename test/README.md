test
=============

存放测试相关的脚本/测试用例等

该目录在部署后，可以执行用以验证功能正确性，相当于集成测试

## run

### config file

准备好

`./cases/environments/e2e.bru`

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

