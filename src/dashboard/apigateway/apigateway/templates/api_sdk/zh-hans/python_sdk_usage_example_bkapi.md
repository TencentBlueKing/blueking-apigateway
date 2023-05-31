创建网关 {{api_name}} 客户端并调用 API 资源 {{resource_name}} 使用示例：

```python
from bkapi.{{api_name_with_underscore}}.client import Client

# 创建网关客户端
client = Client(
    endpoint="{{ django_settings.BK_API_URL_TMPL }}",
    stage="prod",  # 请设置为实际的环境名称，不填则默认为 prod
)

# 请求网关资源，请按具体场景修改请求，参数与 requests 保持兼容
client.api.{{resource_name}}(
    data={...},  # 设置请求参数
    path_params={...},  # 设置路径参数
    params={...},  # 设置 querystring
    headers={...},  # 设置请求头
    timeout=10,  # 设置当前请求超时
)
```

以上仅为示例，具体参数及调用方式请按实际用途修改。

其中，创建网关时的 `endpoint` 参数可在具体的网关简介中找到对应的访问地址。如果没有设置，会自动使用以下方式进行探测：
1. 如果当前为 Django 项目，读取 `settings.BK_API_URL_TMPL` 变量自动生成；
2. 读取 `BK_API_URL_TMPL` 环境变量（蓝鲸开发者中心已默认设置）自动生成；

如果 `endpoint` 为空，请求时会抛出 `EndpointNotSetError` 异常。

对于 Django 项目，在 `shortcuts` 包中提供了额外的辅助函数：

- `get_client_by_request`，可快速通过 Django 中的 `request` 对象生成客户端：

```python
from bkapi.{{api_name_with_underscore}}.shortcuts import get_client_by_request

# 自动从 django settings 获取蓝鲸应用信息（app_code=settings.BK_APP_CODE，app_secret=settings.BK_APP_SECRET）
client = get_client_by_request(
    request,  # 如果请求包含用户登陆态，则自动包含用户信息
    endpoint="{{ django_settings.BK_API_URL_TMPL }}",  # 如果 settings 配置 BK_API_URL_TMPL，则会自动应用，否则请替换为实际的网关访问地址
    stage="prod",  # 请设置为实际的环境名称，不填则默认为 prod
)

# 请按具体场景修改请求
client.api.{{resource_name}}(...)
```

- `get_client_by_username`，对于后台任务等不能直接获取到 `request` 对象的场景，可调用该函数，读取用户上次缓存的登录态，但可能会因为缓存不存在或用户态失效等情况导致失败。

```python
from bkapi.{{api_name_with_underscore}}.shortcuts import get_client_by_username

# 自动从 django settings 获取蓝鲸应用信息（app_code=settings.BK_APP_CODE，app_secret=settings.BK_APP_SECRET）
client = get_client_by_username(
    username="admin",  # 用户名
    endpoint="{{ django_settings.BK_API_URL_TMPL }}",  # 如果 settings 配置 BK_API_URL_TMPL，则会自动应用，否则请替换为实际的网关访问地址
    stage="prod",  # 请设置为实际的环境名称，不填则默认为 prod
)

# 请按具体场景修改请求
client.api.{{resource_name}}(...)
```