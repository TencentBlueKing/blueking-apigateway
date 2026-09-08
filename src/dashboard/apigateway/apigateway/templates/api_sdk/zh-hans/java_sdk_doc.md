## 运行环境与依赖

- Java 11 及以上版本，使用 JDK 原生 HTTP 客户端。
- Maven 安装会根据 POM 自动解析依赖；手动安装时需将 distribution ZIP 中的 SDK JAR 和 `lib/` 下的依赖 JAR 加入 classpath。

## 安装

配置 Maven 原生仓库时使用 Maven 坐标；否则下载包含依赖的 distribution ZIP：

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic distribution ZIP 地址>"{% endif %}
```

## 使用生成的客户端

该包直接提供 OpenAPI Generator 生成的 Java API。

{% include "api_sdk/zh-hans/java_sdk_usage_example.md" %}
