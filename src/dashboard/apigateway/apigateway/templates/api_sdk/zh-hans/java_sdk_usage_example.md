{% if install_command %}使用 `{{ install_command }}` 安装该版本。{% endif %}

```java
import {{ package_name|default:"org.openapitools.client" }}.ApiClient;
import {{ package_name|default:"org.openapitools.client" }}.Configuration;

ApiClient apiClient = Configuration.getDefaultApiClient();
apiClient.updateBaseUri("{{ server_url }}");
apiClient.setRequestInterceptor(builder -> builder.header(
    "X-Bkapi-Authorization",
    "{\"bk_app_code\":\"<app-code>\",\"bk_app_secret\":\"<app-secret>\"}"
));

// 将 GeneratedApi 替换为包含 {{ resource_name }} 的生成 API 类。
// GeneratedApi api = new GeneratedApi(apiClient);
```
