# Dashboard KMS 配置

`ENABLE_KMS` 默认关闭，关闭时保持原有环境变量、`.env` 和配置文件的读取行为，
不导入 KMS SDK、不读取信封。开启时，在生成数据库、Redis、Celery 等配置之前，
使用 `bk_kms.decrypt()` 解密并校验所需凭证。明文只保存在配置读取器及 Django
配置的内存中；本加载过程不写回 `os.environ` 或文件。

## 部署输入

- `ENABLE_KMS=true`（也支持 `True`）。
- `BK_APIGATEWAY_KMS_PRIVATE_KEY`：Base64 编码的 PEM 私钥内容，不是路径。
- `/etc/secrets/bk-apigateway-kms`：UTF-8 文件，内容为 SDK 格式的 Base64 信封。

这些输入与 Helm 分支 `bk-apigateway-1.25-support-kms` 的约定一致。
私钥、文件不可用，解密失败，或所需字段缺失、不是字符串、为空/纯空白时，
Dashboard 启动失败，不回退到原有密码。错误只显示阶段或字段路径，不输出凭证。
凭证中的空白和 `$` 等字符按原文保留，不执行环境变量替换。

## 运维信封模板

以下是**待加密的 JSON 明文结构**，不是挂载文件的最终内容。所有占位值必须替换为
部署中正在使用的凭证，尤其不要在接入时重新生成加密 key，否则已有加密数据可能无法解密。
`encryptKey` 沿用原 `ENCRYPT_KEY` 的完整字符串，不额外做 Base64 解码。

```json
{
  "bkapp_id_secret": {
    "default": {"app_code": "<网关应用代码>", "app_secret": "<网关应用密钥>"},
    "bk_apigw_test": {"app_code": "<测试应用代码>", "app_secret": "<测试应用密钥>"}
  },
  "mysql": {
    "apigw": {"username": "<网关数据库账号>", "password": "<网关数据库密码>"},
    "esb": {"username": "<ESB 数据库账号>", "password": "<ESB 数据库密码>"}
  },
  "redis": {"default": {"password": "<Redis 密码>"}},
  "etcd": {"default": {"username": "<etcd 账号>", "password": "<etcd 密码>"}},
  "rabbitmq": {"default": {"username": "<RabbitMQ 账号>", "password": "<RabbitMQ 密码>"}},
  "bkrepo": {
    "default": {"username": "<Generic 仓库账号>", "password": "<Generic 仓库密码>"},
    "pypi": {"username": "<PyPI 仓库账号>", "password": "<PyPI 仓库密码>"},
    "maven": {"username": "<Maven 仓库账号>", "password": "<Maven 仓库密码>"}
  },
  "encryption": {
    "encryptKey": "<现有 ENCRYPT_KEY>",
    "bkkrillEncryptSecretKey": "<现有 BKKRILL_ENCRYPT_SECRET_KEY>"
  }
}
```

实例名 `default`、`bk_apigw_test`、`apigw`、`esb`、`pypi`、`maven` 是固定映射名；
`app_code` 和 `username` 的实际值不受这些名称限制。各制品仓库账号独立映射，
即使部署使用相同账号，也应在对应实例中填写。

| 信封路径 | 对应配置变量 | 必填条件 |
| --- | --- | --- |
| `bkapp_id_secret.default.app_code/app_secret` | `BK_APP_CODE` / `BK_APP_SECRET` | 总是 |
| `bkapp_id_secret.bk_apigw_test.app_code/app_secret` | `DEFAULT_TEST_APP_CODE` / `DEFAULT_TEST_APP_SECRET` | 总是 |
| `mysql.apigw.username/password` | `BK_APIGW_DATABASE_USER` / `BK_APIGW_DATABASE_PASSWORD` | 总是 |
| `mysql.esb.username/password` | `BK_ESB_DATABASE_USER` / `BK_ESB_DATABASE_PASSWORD` | `ENABLE_MULTI_TENANT_MODE=false` |
| `redis.default.password` | `BK_APIGW_REDIS_PASSWORD` | 总是 |
| `etcd.default.username/password` | `BK_ETCD_USER` / `BK_ETCD_PASSWORD` | 总是 |
| `rabbitmq.default.username/password` | `BK_APIGW_RABBITMQ_USER` / `BK_APIGW_RABBITMQ_PASSWORD` | `BK_APIGW_RABBITMQ_HOST` 非空 |
| `bkrepo.default.username/password` | `BKREPO_USERNAME` / `BKREPO_PASSWORD` | `BKREPO_ENDPOINT_URL` 非空 |
| `bkrepo.pypi.username/password` | `DEFAULT_PYPI_USERNAME` / `DEFAULT_PYPI_PASSWORD` | `DEFAULT_PYPI_REPOSITORY_URL` 或 `DEFAULT_PYPI_INDEX_URL` 非空 |
| `bkrepo.maven.username/password` | `DEFAULT_MAVEN_USERNAME` / `DEFAULT_MAVEN_PASSWORD` | `DEFAULT_MAVEN_REPOSITORY_URL` 非空 |
| `encryption.encryptKey` | `ENCRYPT_KEY`，继续派生 `JWT_CRYPTO_KEY`、`LOG_LINK_SECRET` | 总是 |
| `encryption.bkkrillEncryptSecretKey` | `BKKRILL_ENCRYPT_SECRET_KEY` | `BK_CRYPTO_TYPE` 为 `CLASSIC` 或 `SHANGMI` |

条件不满足的实例可以省略；未消费的字段忽略，允许多个组件共用信封。
当前要求所需账号和密码非空，使用无认证 Redis/etcd 的部署不能直接开启此模式。
地址、端口、库名、TLS 文件路径和功能开关仍沿用原配置。

Dashboard 当前通过 BKLog API 查询日志，不直接消费 `elasticsearch` 账号。
本次没有为 Django `SECRET_KEY`、AI、OTEL、ITSM、Sentry 等增加 KMS 映射。
已有 `SECRET_KEY` 继续生效；如果原本未配置它，仍沿用原代码默认取 `BK_APP_SECRET`
的行为。其他原本默认使用 `BK_APP_SECRET` 的配置也会自然使用解密后的应用密钥。
开发环境的 `local_settings.py` 仍是最后加载的显式覆盖文件。

## 生效范围与轮换

Web、Celery、管理命令和初始化任务共用配置入口。每个加载配置的进程解密一次，
fork 出的 worker 可以继承已加载的配置；不会为每个请求解密，也不会调用远程 KMS API。
更新信封或私钥后需要重建相关 Pod；当前 Helm 使用环境变量和 `subPath` 文件挂载，
不提供凭证热更新。现有凭证使用方保持原行为，例如 SDK 上传仍会将 PyPI 账号写入
工作目录的 `.pypirc`，将 Maven 账号作为命令参数传递；本次没有改造这些使用方。

新开 `kubectl exec ... -- env` 不会看到这层内存覆盖值，子进程也不会通过环境变量
继承这些新解密的值。但原有 ConfigMap/Secret 注入的旧密码仍可能存在于环境变量中；
当前 Chart 不会自动删除它们。应用内存依然包含明文，持有私钥和信封也能解密。

## SDK 包与验证

暂使用仓库内的 [本地 wheel](../vendor/README.md)，由 `pyproject.toml` 和 `uv.lock`
锁定。镜像构建会先复制 wheel 再执行 `uv sync --locked --no-dev`，不依赖开发机目录。
SDK 正式发布后可移除本地 source、wheel 和相关打包步骤，重新生成锁文件。

从 `src/dashboard` 执行：

```bash
uv sync --locked --all-extras --dev
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/conf/test_kms.py'
```

测试使用运行时生成的测试私钥和 RSA/AES 信封，不需要部署凭证或 KMS 服务。
