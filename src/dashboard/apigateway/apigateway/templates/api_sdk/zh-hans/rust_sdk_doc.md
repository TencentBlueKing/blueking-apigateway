## 安装

从 BKRepo Generic 下载生成的 crate，然后在 `Cargo.toml` 中引用解压后的本地路径：

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic crate 地址>"{% endif %}
```

## 配置

{% include "api_sdk/zh-hans/rust_sdk_usage_example.md" %}
