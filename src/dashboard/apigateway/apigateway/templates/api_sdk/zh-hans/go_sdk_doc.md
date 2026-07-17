## 安装

从 BKRepo Generic 下载 `.info`、`.mod` 和 `.zip` 文件，并通过内部 Go Proxy 提供：

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic Go module 地址>"{% endif %}
```

## 配置

{% include "api_sdk/zh-hans/go_sdk_usage_example.md" %}
