{% if install_command %}使用 `{{ install_command }}` 安装该版本。{% endif %}

```javascript
const sdk = require('{{ package_name|default:"bkapi-example" }}');

const apiClient = sdk.ApiClient.instance;
apiClient.basePath = '{{ server_url }}';
// BkApiAuthorization 会写入 X-Bkapi-Authorization 请求头。
apiClient.authentications.BkApiAuthorization.apiKey = JSON.stringify({
  bk_app_code: '<app-code>',
  bk_app_secret: '<app-secret>',
});

// 创建生成的 API 类并调用 {{ resource_name }}。
```
