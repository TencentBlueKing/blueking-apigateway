{% if install_command %}使用 `{{ install_command }}` 安装该版本。{% endif %}

```typescript
import { Configuration } from '{{ package_name|default:"@bkapi/openapi-example" }}';

const configuration = new Configuration({
  basePath: '{{ server_url }}',
  // 生成的 BkApiAuthorization 认证方案会将 apiKey 写入 X-Bkapi-Authorization。
  apiKey: JSON.stringify({
    bk_app_code: '<app-code>',
    bk_app_secret: '<app-secret>',
  }),
});

// 导入包含 {{ resource_name }} 的生成 API 类，再将 configuration 传入构造函数。
// const api = new GeneratedApi(configuration);
// const result = await api.{{ resource_name }}(...);
```
