{% if install_command %}Download this version with `{{ install_command }}`.{% endif %}

```go
package main

import (
    "context"
    "{{ package_name|default:"example.com/bkapi/example" }}"
)

func main() {
    cfg := {{ gateway_name_with_underscore }}.NewConfiguration()
    cfg.Servers[0].URL = "{{ server_url }}"
    cfg.DefaultHeader["X-Bkapi-Authorization"] = `{"bk_app_code":"<app-code>","bk_app_secret":"<app-secret>"}`
    client := {{ gateway_name_with_underscore }}.NewAPIClient(cfg)
    _ = client
    _ = context.Background() // Call the generated {{ resource_name }} operation with this context.
}
```
