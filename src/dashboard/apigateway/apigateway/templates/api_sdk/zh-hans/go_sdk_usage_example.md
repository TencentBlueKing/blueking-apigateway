{% if install_command %}使用 `{{ install_command }}` 下载该版本。{% endif %}

解压后，将包含 `go.mod` 的 SDK 模块目录放到业务项目的 `./sdks/bkapi` 下，保留其中的 `go.mod`。模块路径用于标识 SDK，本地引用无需访问对应域名或 Git 仓库。

在业务项目根目录执行：

```shell
go mod edit -replace={{ project_name|default:"bk.tencent.com/bkapi/openapi/example" }}=./sdks/bkapi
```

添加下方代码中的 import 后执行 `go mod tidy`，Go 会补充对应的 `require` 和依赖。请将 SDK 目录一起纳入业务项目的源码或构建输入；引用多个 SDK 时，为每个 SDK 使用独立目录。

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
    _ = ctx // 使用该 context 构造 {{ resource_name }} 请求，再调用 Execute。
}
```
