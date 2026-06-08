from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_plane", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataplane",
            name="apisix_version",
            field=models.CharField(
                choices=[("3.13", "3.13"), ("3.16", "3.16")],
                default="3.13",
                help_text="APISIX version of the data plane",
                max_length=16,
            ),
        ),
    ]
