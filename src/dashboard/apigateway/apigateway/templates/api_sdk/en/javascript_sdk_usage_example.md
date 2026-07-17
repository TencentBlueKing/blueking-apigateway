{% if install_command %}Install this version with `{{ install_command }}`.{% endif %}

```javascript
const sdk = require('{{ package_name|default:"bkapi-example" }}');

const apiClient = sdk.ApiClient.instance;
apiClient.basePath = '{{ server_url }}';
// BkApiAuthorization is emitted as the X-Bkapi-Authorization header.
apiClient.authentications.BkApiAuthorization.apiKey = JSON.stringify({
  bk_app_code: '<app-code>',
  bk_app_secret: '<app-secret>',
});

// Create the generated API class and call {{ resource_name }}.
```
