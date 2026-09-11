{% if install_command %}Install this version with `{{ install_command }}`.{% endif %}

```typescript
import { Configuration } from '{{ package_name|default:"@bkapi/openapi-example" }}';

const configuration = new Configuration({
  basePath: '{{ server_url }}',
  // The generated BkApiAuthorization scheme writes apiKey to X-Bkapi-Authorization.
  apiKey: JSON.stringify({
    bk_app_code: '<app-code>',
    bk_app_secret: '<app-secret>',
  }),
});

// Import the generated API class that contains {{ resource_name }}, then pass configuration to its constructor.
// const api = new GeneratedApi(configuration);
// const result = await api.{{ resource_name }}(...);
```
