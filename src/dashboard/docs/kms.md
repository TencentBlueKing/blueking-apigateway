# KMS 配置（Dashboard 与 Go 组件）

Dashboard 的 `ENABLE_KMS` 默认关闭，关闭时保持原有环境变量、`.env` 和配置文件的读取行为，
不导入 KMS SDK、不读取信封。开启时，在生成数据库、Redis、Celery 等配置之前，
使用 `bk_kms.decrypt()` 解密并校验所需凭证。明文只保存在配置读取器及 Django
配置的内存中；本加载过程不写回 `os.environ` 或文件。

## 部署输入

- `ENABLE_KMS` 仅接受字面值 `true` 或 `True`；未设置或其他值均关闭，不忽略大小写或首尾空白。
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
  "etcd": {
    "default": {"username": "<控制面 etcd 账号>", "password": "<控制面 etcd 密码>"},
    "apisix": {"username": "<数据面 etcd 账号>", "password": "<数据面 etcd 密码>"}
  },
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

实例名 `default`、`bk_apigw_test`、`apigw`、`esb`、`apisix`、`pypi`、`maven` 是固定映射名；
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
| `rabbitmq.default.username/password` | `BK_APIGW_RABBITMQ_USER` / `BK_APIGW_RABBITMQ_PASSWORD` | `BK_APIGW_RABBITMQ_HOST`、`BK_APIGW_RABBITMQ_PORT`、`BK_APIGW_RABBITMQ_VHOST` 均非空 |
| `bkrepo.default.username/password` | `BKREPO_USERNAME` / `BKREPO_PASSWORD` | `BKREPO_ENDPOINT_URL` 非空 |
| `bkrepo.pypi.username/password` | `DEFAULT_PYPI_USERNAME` / `DEFAULT_PYPI_PASSWORD` | `DEFAULT_PYPI_REPOSITORY_URL` 非空 |
| `bkrepo.maven.username/password` | `DEFAULT_MAVEN_USERNAME` / `DEFAULT_MAVEN_PASSWORD` | `DEFAULT_MAVEN_REPOSITORY_URL` 非空 |
| `encryption.encryptKey` | `ENCRYPT_KEY`，继续派生 `JWT_CRYPTO_KEY`、`LOG_LINK_SECRET` | 总是 |
| `encryption.bkkrillEncryptSecretKey` | `BKKRILL_ENCRYPT_SECRET_KEY` | `BK_CRYPTO_TYPE` 为 `CLASSIC` 或 `SHANGMI` |

条件不满足的实例可以省略；未消费的字段忽略，允许多个组件共用信封。
RabbitMQ 的地址、端口或 vhost 缺失时，Celery 仍沿用 Redis；三项齐全时必须提供信封中的
RabbitMQ 账号密码，缺失即阻止启动，不回退到旧凭证或 Redis。
仅配置 `DEFAULT_PYPI_INDEX_URL` 下载索引时不要求上传凭证。
Dashboard 要求所需账号和密码非空，使用无认证 Redis/etcd 的部署不能直接开启此模式。
地址、端口、库名、TLS 文件路径和功能开关仍沿用原配置。

Dashboard 当前通过 BKLog API 查询日志，不直接消费 `elasticsearch` 账号。
本次没有为 Django `SECRET_KEY`、AI、OTEL、ITSM、Sentry 等增加 KMS 映射。
已有 `SECRET_KEY` 继续生效；如果原本未配置它，仍沿用原代码默认取 `BK_APP_SECRET`
的行为。其他原本默认使用 `BK_APP_SECRET` 的配置也会自然使用解密后的应用密钥。
开发环境的 `local_settings.py` 仍是最后加载的显式覆盖文件。

## Go 组件复用同一份信封

`core-api`、`operator`、`mcp-proxy` 使用相同的 `ENABLE_KMS` 开关、私钥环境变量和
信封文件路径。三者在 `config.Load()` 中解密，仅替换内存配置中的以下字段，
不修改环境变量或 YAML 文件。每个组件只要求自己消费的字段，允许信封包含其他组件的字段。

| 组件 | 信封路径 | 配置字段 |
| --- | --- | --- |
| Core API | `mysql.apigw.username/password` | `databases[id=apigateway].user/password`，随后生成 `DatabaseMap` |
| Core API | `bkapp_id_secret.default.app_secret` | `auth.secret` |
| MCP Proxy | `mysql.apigw.username/password` | `databases[id=apigateway].user/password`，随后生成 `DatabaseMap` |
| MCP Proxy | `encryption.encryptKey` | `mcpServer.encryptKey`，优先于旧的 `ENCRYPT_KEY` 环境变量 |
| Operator | `bkapp_id_secret.default.app_secret` | `auth.secret` |
| Operator | `etcd.default.username/password` | `dashboard.etcd.username/password` |
| Operator | `etcd.apisix.username/password` | `apisix.etcd.username/password` |

Core API 和 MCP Proxy 如配置了其他数据库 ID，则从 `mysql.<数据库ID>` 读取账号密码；
例如 `id=esb` 对应 `mysql.esb`。每个已配置数据库都必须提供凭证，不从其他实例回退。
非凭证配置仍从原 YAML/环境变量读取，例如数据库地址、TLS、网关实例 ID 和 cryptoNonce。
`auth.id` 是网关实例 ID，不是 `app_code`，不会被应用代码覆盖；三个 Go 组件没有需要新增
`app_code` 映射的配置字段。Core API 和 Operator 的 `auth.secret` 在现有 Helm 中使用
网关应用密钥，因此仍映射到同一个 `bkapp_id_secret.default.app_secret`。

Operator 的控制面、数据面 etcd 可以使用不同账号；即使实际共用账号，也需要分别填写
`etcd.default` 和 `etcd.apisix`。某一侧显式设置 `withoutAuth: true` 时，该侧保持原来的
无认证行为，不要求该侧的信封字段。KMS 模式下不再打印 Operator 的完整 debug 配置，
避免解密后的凭证进入标准输出。关闭 KMS 时保留原有 debug 行为。

Go SDK 暂以相同源码快照保存在各组件的 `third_party/bk-kms-sdk` 中，通过相对路径
`replace` 引用，现有 Docker 构建目录无需改变，也无需在构建时拉取 SDK 仓库。
来源版本和文件校验和见各目录的 `README.md`、`MANIFEST.sha256`。SDK 在 CBC 解密前
拒绝长度不足或未按分组对齐的密文；应用直接调用 SDK，将返回的解密错误转换为不含凭证内容的启动错误。

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
