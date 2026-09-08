## Runtime requirements and dependencies

- Python {{ sdk_runtime_requirements.python|cut:">=" }} or later.
- Runtime dependencies: `pydantic >=2.11`, `urllib3 >=2.1.0,<3.0.0`, `python-dateutil >=2.8.2`, and `typing-extensions >=4.7.1`. pip installs compatible versions automatically.
- Python must use OpenSSL 1.1.1 or later. Check compatibility with existing project dependencies, especially constraints requiring Pydantic 1.x or urllib3 1.x.

## Install

Use the successful native PyPI package reference or BKRepo Generic wheel URL shown for the SDK version:

```shell
{% if install_command %}{{ install_command }}{% else %}pip install "<BKRepo Generic wheel URL>"{% endif %}
```

## Use the generated client

The package exposes the native OpenAPI Generator Python API.

{% include "api_sdk/en/python_sdk_usage_example.md" %}
