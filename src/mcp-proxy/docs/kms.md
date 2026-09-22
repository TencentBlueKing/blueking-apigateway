# mcp-proxy KMS 配置

设置 `ENABLE_KMS=true`，通过环境变量 `BK_APIGATEWAY_KMS_PRIVATE_KEY` 提供 Base64 PEM
私钥，通过 `/etc/secrets/bk-apigateway-kms` 提供 Base64 加密信封。

默认关闭时保留原配置读取行为；开启时启动阶段将本组件所需凭证覆盖到内存配置，
缺失、为空、类型错误或解密失败时阻止启动，不回退到 YAML 中的旧密码。
不修改环境变量或配置文件，不提供热更新；轮换私钥和信封后重建 Pod。

字段映射、完整共用信封模板和各组件差异见
[共用 KMS 配置说明](../../dashboard/docs/kms.md#go-组件复用同一份信封)。

本组件临时集成的 Go SDK 来源和校验和见
[SDK 快照说明](../third_party/bk-kms-sdk/README.md)。
