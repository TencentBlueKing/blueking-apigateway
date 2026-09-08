## Runtime requirements and dependencies

- Go 1.23 or later.
- Use Go Modules and ensure the SDK's third-party dependencies can be downloaded.

## Install

Download the SDK `.zip` file from BKRepo Generic, then extract and reference it locally as described below:

```shell
{% if install_command %}{{ install_command }}{% else %}curl -fLO "<BKRepo Generic Go module URL>"{% endif %}
```

## Use the generated client

The module exposes the native OpenAPI Generator Go API.

{% include "api_sdk/en/go_sdk_usage_example.md" %}
