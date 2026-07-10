{% if install_command %}Download this version with `{{ install_command }}`.{% endif %}

```rust
use {{ package_name|default:"bkapi_example" }}::apis::configuration::{ApiKey, Configuration};

let mut configuration = Configuration::new();
configuration.base_path = "{{ server_url }}".to_string();
// This API key is emitted as the X-Bkapi-Authorization header.
configuration.api_key = Some(ApiKey {
    prefix: None,
    key: r#"{"bk_app_code":"<app-code>","bk_app_secret":"<app-secret>"}"#.to_string(),
});

// Pass &configuration to the generated {{ resource_name }} function.
```
