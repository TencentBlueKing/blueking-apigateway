{% if install_command %}使用 `{{ install_command }}` 安装该版本。{% endif %}

```java
import org.openapitools.client.ApiClient;
import org.openapitools.client.Configuration;

ApiClient apiClient = Configuration.getDefaultApiClient();
apiClient.setBasePath("{{ server_url }}");
apiClient.addDefaultHeader("X-Bkapi-Authorization",
    "{\"bk_app_code\":\"<app-code>\",\"bk_app_secret\":\"<app-secret>\"}");

// 使用 apiClient 构造包含 {{ resource_name }} 的生成 API 类。
```
