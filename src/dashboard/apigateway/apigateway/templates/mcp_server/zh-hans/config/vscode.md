```json
{
    "servers": {
        "{{name}}": {
            "type": "{{transport_type}}",
            "url": "{{url}}"{% if not oauth2_enabled %},
            "headers": {
                "X-Bkapi-Authorization": "{\"bk_app_code\": \"your_app_code\", \"bk_app_secret\": \"your_app_secret\", \"{{bk_login_ticket_key}}\": \"your_ticket\"}"
            }{% endif %}
        }
    }
}
```
