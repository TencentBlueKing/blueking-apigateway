## Install

Download the generated crate from BKRepo Generic, then reference the local crate path in `Cargo.toml`:

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic crate URL>"{% endif %}
```

## Configure

{% include "api_sdk/en/rust_sdk_usage_example.md" %}
