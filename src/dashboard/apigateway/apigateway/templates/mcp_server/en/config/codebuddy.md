```json
{
    "mcpServers": {
        "{{name}}": {
{% if protocol_type == "streamable_http" %}
            "transportType": "streamable-http",
{% else %}
            "transportType": "sse",
{% endif %}
            "url": "{{url}}",
            "description": "{{description}}",
            "headers": {
                "X-Bkapi-Authorization": "{\"bk_app_code\": \"your_app_code\", \"bk_app_secret\": \"your_app_secret\", \"{{bk_login_ticket_key}}\": \"your_ticket\"}"
            }
        }
    }
}
```
