```json
{
    "servers": {
        "{{name}}": {
            "type": "{{transport_type}}",
            "url": "{{url}}"{% if not oauth2_public_client_enabled or enable_multi_tenant_mode and user_tenant_id %},
            "headers": {
                {% if not oauth2_public_client_enabled %}"X-Bkapi-Authorization": "{\"bk_app_code\": \"your_app_code\", \"bk_app_secret\": \"your_app_secret\", \"{{bk_login_ticket_key}}\": \"your_ticket\"}"{% if enable_multi_tenant_mode and user_tenant_id %},{% endif %}
                {% endif %}{% if enable_multi_tenant_mode and user_tenant_id %}"X-Bk-Tenant-Id": "{{user_tenant_id}}",
                "X-Bkapi-Allowed-Headers": "X-Bk-Tenant-Id"{% endif %}
            }{% endif %}
        }
    }
}
```
