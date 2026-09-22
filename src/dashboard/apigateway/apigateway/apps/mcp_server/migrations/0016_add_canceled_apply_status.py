from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mcp_server", "0015_mcpserver_oauth2_personal_client_enabled"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mcpserverapppermissionapply",
            name="status",
            field=models.CharField(
                choices=[
                    ("approved", "通过"),
                    ("rejected", "驳回"),
                    ("pending", "待审批"),
                    ("canceled", "已取消"),
                ],
                max_length=16,
            ),
        ),
    ]
