# Generated by Django 4.2.16 on 2024-12-04 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0041_auto_20240826_1737"),
    ]

    operations = [
        # alter, with default, no need to migrate the legacy records
        migrations.AlterField(
            model_name="gateway",
            name="tenant_id",
            field=models.CharField(blank=True, default="default", max_length=32),
        ),
        migrations.AlterField(
            model_name="gateway",
            name="tenant_mode",
            field=models.CharField(
                choices=[("global", "全租户"), ("single", "单租户")],
                default="single",
                max_length=32,
            ),
        ),
        # alter, remove the default value
        migrations.AlterField(
            model_name="gateway",
            name="tenant_id",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name="gateway",
            name="tenant_mode",
            field=models.CharField(
                choices=[("global", "全租户"), ("single", "单租户")], max_length=32
            ),
        ),
    ]