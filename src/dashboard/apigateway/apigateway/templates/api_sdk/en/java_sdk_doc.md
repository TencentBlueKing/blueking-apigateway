## Install

Use the Maven coordinate when native Maven publication is enabled. Otherwise download the distribution ZIP:

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic distribution ZIP URL>"{% endif %}
```

## Configure

{% include "api_sdk/en/java_sdk_usage_example.md" %}
