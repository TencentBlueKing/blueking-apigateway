## 运行环境与依赖

- Python {{ sdk_runtime_requirements.python|cut:">=" }} 及以上版本。
- 运行依赖：`pydantic >=2.11`、`urllib3 >=2.1.0,<3.0.0`、`python-dateutil >=2.8.2`、`typing-extensions >=4.7.1`，由 pip 自动安装兼容版本。
- Python 使用的 OpenSSL 需为 1.1.1 及以上版本。已有项目需确认依赖范围兼容，尤其是 Pydantic 1.x 或 urllib3 1.x 的约束。

## 安装

使用 SDK 版本中已成功发布的原生 PyPI 坐标或 BKRepo Generic wheel 地址：

```shell
{% if install_command %}{{ install_command }}{% else %}pip install "<BKRepo Generic wheel 地址>"{% endif %}
```

## 使用生成的客户端

该包直接提供 OpenAPI Generator 生成的 Python API。

{% include "api_sdk/zh-hans/python_sdk_usage_example.md" %}
