{% if install_command %}Download this version with `{{ install_command }}`.{% endif %}

```go
package main

import (
    "context"
    {{ package_name|default:"bkapi_example" }} "{{ project_name|default:"example.com/bkapi/example" }}"
)

func main() {
    cfg := {{ package_name|default:"bkapi_example" }}.NewConfiguration()
    cfg.Servers[0].URL = "{{ server_url }}"
    cfg.AddDefaultHeader("X-Bkapi-Authorization", `{"bk_app_code":"<app-code>","bk_app_secret":"<app-secret>"}`)
    client := {{ package_name|default:"bkapi_example" }}.NewAPIClient(cfg)
    ctx := context.Background()
    _ = client
    _ = ctx // Call the generated {{ resource_name }} request builder with this context, then Execute it.
}
```
