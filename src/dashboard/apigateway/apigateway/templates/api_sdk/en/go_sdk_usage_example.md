{% if install_command %}Download this version with `{{ install_command }}`.{% endif %}

After extraction, place the SDK module directory containing `go.mod` at `./sdks/bkapi` in your application project, keeping its `go.mod`. The module path identifies the SDK; local references do not require access to that domain or a Git repository.

Run from the application project root:

```shell
go mod edit -replace={{ project_name|default:"bk.tencent.com/bkapi/openapi/example" }}=./sdks/bkapi
```

After adding the import shown below, run `go mod tidy` to add the corresponding `require` and dependencies. Include the SDK directory in your application's source or build inputs; use a separate directory for each SDK when integrating multiple SDKs.

```go
package main

import (
    "context"
    {{ package_name|default:"bkapi_example" }} "{{ project_name|default:"bk.tencent.com/bkapi/openapi/example" }}"
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
