## 安装

配置 Maven 原生仓库时使用 Maven 坐标；否则下载包含依赖的 distribution ZIP：

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic distribution ZIP 地址>"{% endif %}
```

## 配置

{% include "api_sdk/zh-hans/java_sdk_usage_example.md" %}
