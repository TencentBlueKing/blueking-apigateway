## Install

Download the `.info`, `.mod`, and `.zip` files from BKRepo Generic and expose them through your Go proxy:

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic Go module URL>"{% endif %}
```

## Configure

{% include "api_sdk/en/go_sdk_usage_example.md" %}
