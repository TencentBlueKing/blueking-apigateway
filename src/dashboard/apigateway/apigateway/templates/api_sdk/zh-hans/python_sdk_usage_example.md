生成的客户端需要显式配置服务地址和 `X-Bkapi-Authorization`。

{% if install_command %}使用 `{{ install_command }}` 安装该版本。{% endif %}

```python
import json
import {{ package_name|default:"bkapi_example" }}

configuration = {{ package_name|default:"bkapi_example" }}.Configuration(host="{{ server_url }}")
configuration.api_key["BkApiAuthorization"] = json.dumps({
    "bk_app_code": "<app-code>",
    "bk_app_secret": "<app-secret>",
})

with {{ package_name|default:"bkapi_example" }}.ApiClient(configuration) as api_client:
    # 导入包含 {{ resource_name }} 的生成 API 类，并传入 api_client 调用。
    pass
```
