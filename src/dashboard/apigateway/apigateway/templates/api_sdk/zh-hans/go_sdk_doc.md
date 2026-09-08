## 运行环境与依赖

- Go 1.23 及以上版本。
- 使用 Go Modules 管理依赖，并确保内部 Go Proxy 可访问 SDK 模块及其依赖。

## 安装

从 BKRepo Generic 下载 `.info`、`.mod` 和 `.zip` 文件，并通过内部 Go Proxy 提供：

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic Go module 地址>"{% endif %}
```

## 使用生成的客户端

该模块直接提供 OpenAPI Generator 生成的 Go API。

{% include "api_sdk/zh-hans/go_sdk_usage_example.md" %}
