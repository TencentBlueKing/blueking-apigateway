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
            field=models.BooleanField(default=False, verbose_name="是否返回原始响应"),
        ),
    ]
