## Runtime requirements and dependencies

- Go 1.23 or later.
- Use Go Modules and ensure your internal Go proxy can access the SDK module and its dependencies.

## Install

Download the `.info`, `.mod`, and `.zip` files from BKRepo Generic and expose them through your Go proxy:

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic Go module URL>"{% endif %}
```

## Use the generated client

The module exposes the native OpenAPI Generator Go API.

{% include "api_sdk/en/go_sdk_usage_example.md" %}
