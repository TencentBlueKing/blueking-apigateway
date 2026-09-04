## 安装

从 BKRepo Generic 安装生成的 npm 包：

```shell
{% if install_command %}{{ install_command }}{% else %}npm install "<BKRepo Generic npm tgz 地址>"{% endif %}
```

## 使用生成的客户端

该包直接提供 OpenAPI Generator `typescript-fetch` 生成的 API。

{% include "api_sdk/zh-hans/javascript_sdk_usage_example.md" %}
