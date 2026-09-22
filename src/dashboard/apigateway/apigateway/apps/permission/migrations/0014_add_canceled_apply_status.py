from django.db import migrations, models

APPLY_STATUS_CHOICES = [
    ("partial_approved", "部分通过"),
    ("approved", "全部通过"),
    ("rejected", "全部驳回"),
    ("pending", "待审批"),
    ("canceled", "已取消"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("permission", "0013_add_permission_handled_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="apppermissionapply",
            name="status",
            field=models.CharField(choices=APPLY_STATUS_CHOICES, db_index=True, max_length=16),
        ),
        migrations.AlterField(
            model_name="apppermissionapplystatus",
            name="status",
            field=models.CharField(choices=APPLY_STATUS_CHOICES, max_length=16),
        ),
        migrations.AlterField(
            model_name="apppermissionrecord",
            name="status",
            field=models.CharField(choices=APPLY_STATUS_CHOICES, db_index=True, max_length=16),
        ),
    ]
