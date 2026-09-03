{% if install_command %}使用 `{{ install_command }}` 下载该版本。{% endif %}

```go
package main

import (
    "context"
    {{ package_name|default:"bkapi_example" }} "{{ project_name|default:"example.com/bkapi/example" }}"
)

func main() {
    cfg := {{ package_name|default:"bkapi_example" }}.NewConfiguration()
    cfg.Servers[0].URL = "{{ server_url }}"
    cfg.DefaultHeader["X-Bkapi-Authorization"] = `{"bk_app_code":"<app-code>","bk_app_secret":"<app-secret>"}`
    client := {{ package_name|default:"bkapi_example" }}.NewAPIClient(cfg)
    _ = client
    _ = context.Background() // 使用该 context 调用生成的 {{ resource_name }} 操作。
}
```
