# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mcp_server", "0012_mcpserver_oauth2_public_client_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="mcpserver",
            name="raw_response",
            field=models.BooleanField(
                default=False,
                help_text="是否返回原始响应，开启后 mcp-proxy 将直接返回 API 响应结果，不添加 request_id 等额外信息",
            ),
        ),
    ]
