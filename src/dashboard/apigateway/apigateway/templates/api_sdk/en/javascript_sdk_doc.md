## Install

Install the generated npm package archive from BKRepo Generic:

```shell
{% if install_command %}{{ install_command }}{% else %}npm install "<BKRepo Generic npm tgz URL>"{% endif %}
```

## Use the generated client

The package exposes the native OpenAPI Generator `typescript-fetch` API.

{% include "api_sdk/en/javascript_sdk_usage_example.md" %}
