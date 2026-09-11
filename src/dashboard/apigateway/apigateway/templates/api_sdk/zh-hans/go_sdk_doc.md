## 运行环境与依赖

- Go 1.23 及以上版本。
- 使用 Go Modules 管理依赖，并确保 SDK 的第三方依赖可以下载。

## 安装

从 BKRepo Generic 下载 SDK 的 `.zip` 文件，按下方说明解压并通过本地目录引用：

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic Go module 地址>"{% endif %}
```

## 使用生成的客户端

该模块直接提供 OpenAPI Generator 生成的 Go API。

{% include "api_sdk/zh-hans/go_sdk_usage_example.md" %}
