from django.db import migrations, models

from apigateway.apps.data_plane.constants import CURRENT_DATA_PLANE_APISIX_VERSION


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
                default=CURRENT_DATA_PLANE_APISIX_VERSION,
                help_text="APISIX version of the data plane",
                max_length=16,
            ),
        ),
    ]
