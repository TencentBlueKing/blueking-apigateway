{% if install_command %}Install this version with `{{ install_command }}`.{% endif %}

```java
import {{ package_name|default:"org.openapitools.client" }}.ApiClient;
import {{ package_name|default:"org.openapitools.client" }}.Configuration;

ApiClient apiClient = Configuration.getDefaultApiClient();
apiClient.updateBaseUri("{{ server_url }}");
apiClient.setRequestInterceptor(builder -> builder.header(
    "X-Bkapi-Authorization",
    "{\"bk_app_code\":\"<app-code>\",\"bk_app_secret\":\"<app-secret>\"}"
));

// Replace GeneratedApi with the generated API class that contains {{ resource_name }}.
// GeneratedApi api = new GeneratedApi(apiClient);
```
