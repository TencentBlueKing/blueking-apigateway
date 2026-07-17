{% if install_command %}Install this version with `{{ install_command }}`.{% endif %}

```java
import org.openapitools.client.ApiClient;
import org.openapitools.client.Configuration;

ApiClient apiClient = Configuration.getDefaultApiClient();
apiClient.setBasePath("{{ server_url }}");
apiClient.addDefaultHeader("X-Bkapi-Authorization",
    "{\"bk_app_code\":\"<app-code>\",\"bk_app_secret\":\"<app-secret>\"}");

// Construct the generated API class for {{ resource_name }} with apiClient.
```
