
创建网关 {{gateway_name}} Client 并调用 API 资源 {{resource_name}} 使用示例：

### 1. Django 项目

对于 Django 项目，在 `shortcuts` 包中提供了额外的辅助函数：

#### 1.1 get_client_by_request

- 适用场景：前后端交互，可获取 django request 的场景
- 封装机制：
    - 1. 自动从 django settings 获取蓝鲸应用信息（app_code=settings.BK_APP_CODE，app_secret=settings.BK_APP_SECRET）
    - 2. 自动从 django request 获取当前用户名，从 Cookies 获取登录态
    - 3. 检测 `settings.BK_API_URL_TMPL` 或 `BK_API_URL_TMPL` 环境变量 设置 endpoint(见注意事项)

```python
from bkapi.{{gateway_name_with_underscore}}.shortcuts import get_client_by_request

client = get_client_by_request(
    request,
    endpoint="{{ django_settings.BK_API_URL_TMPL }}",
    stage="prod",  # 请设置为实际的环境名称，不填则默认为 prod
)

# 请按具体场景修改请求
client.api.{{resource_name}}(...)
```

#### 1.2 get_client_by_username

- 适用场景：后台任务等不能直接获取到 `request` 对象的场景，可调用该函数，读取用户上次缓存的登录态，但可能会因为缓存不存在或用户态失效等情况导致失败。
- 封装机制：
    - 1. 自动从 django settings 获取蓝鲸应用信息（app_code=settings.BK_APP_CODE，app_secret=settings.BK_APP_SECRET）
    - 2. 如果安装了 bkoauth (默认框架带了) 通过 bkoauth sdk 生成 access_token, 使用 access_token 放入认证头;
    - 3. 检测 `settings.BK_API_URL_TMPL` 或 `BK_API_URL_TMPL` 环境变量 设置 endpoint(见注意事项)

```python
from bkapi.{{gateway_name_with_underscore}}.shortcuts import get_client_by_username

client = get_client_by_username(
    username="admin",  # 用户名
    endpoint="{{ django_settings.BK_API_URL_TMPL }}",
    stage="prod",  # 请设置为实际的环境名称，不填则默认为 prod
)

# 请按具体场景修改请求
client.api.{{resource_name}}(...)
```

### 2. 非 Django 项目

```python
from bkapi.{{gateway_name_with_underscore}}.client import Client

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

### 3. 注意事项

创建网关时的 `endpoint` 参数可在具体的网关简介中找到对应的访问地址。

如果没有设置，会自动使用以下方式进行探测：
1. 如果当前为 Django 项目，读取 `settings.BK_API_URL_TMPL` 变量自动生成；
2. 读取 `BK_API_URL_TMPL` 环境变量（蓝鲸开发者中心已默认设置）自动生成；
3. 如果 `endpoint` 为空，请求时会抛出 `EndpointNotSetError` 异常。

本地开发时如果没有设置 `settings.BK_API_URL_TMPL`，并且此时也没有开发者中心运行时注入的环境变量，启动前需要通过 `export BK_API_URL_TMPL=对应环境值`或者先手工设置 `endpoint` 参数。
