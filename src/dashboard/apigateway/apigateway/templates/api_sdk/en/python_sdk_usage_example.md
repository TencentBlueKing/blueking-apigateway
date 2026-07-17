The generated client requires an explicit server URL and `X-Bkapi-Authorization` value.

{% if install_command %}Install this version with `{{ install_command }}`.{% endif %}

```python
import json
import {{ package_name|default:"bkapi_example" }}

configuration = {{ package_name|default:"bkapi_example" }}.Configuration(host="{{ server_url }}")
configuration.api_key["BkApiAuthorization"] = json.dumps({
    "bk_app_code": "<app-code>",
    "bk_app_secret": "<app-secret>",
})

with {{ package_name|default:"bkapi_example" }}.ApiClient(configuration) as api_client:
    # Import the generated API class that contains {{ resource_name }} and call it with api_client.
    pass
```
