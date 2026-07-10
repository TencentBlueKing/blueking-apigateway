{% if install_command %}使用 `{{ install_command }}` 下载该版本。{% endif %}

```rust
use {{ package_name|default:"bkapi_example" }}::apis::configuration::{ApiKey, Configuration};

let mut configuration = Configuration::new();
configuration.base_path = "{{ server_url }}".to_string();
// 该 API key 会写入 X-Bkapi-Authorization 请求头。
configuration.api_key = Some(ApiKey {
    prefix: None,
    key: r#"{"bk_app_code":"<app-code>","bk_app_secret":"<app-secret>"}"#.to_string(),
});

// 将 &configuration 传给生成的 {{ resource_name }} 函数。
```
