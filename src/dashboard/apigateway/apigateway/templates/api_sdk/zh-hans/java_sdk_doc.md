## 安装

配置 Maven 原生仓库时使用 Maven 坐标；否则下载包含依赖的 distribution ZIP：

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic distribution ZIP 地址>"{% endif %}
```

## 使用生成的客户端

该包直接提供 OpenAPI Generator 生成的 Java API。

{% include "api_sdk/zh-hans/java_sdk_usage_example.md" %}
