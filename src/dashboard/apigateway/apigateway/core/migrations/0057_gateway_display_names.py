from django.db import migrations, models
from django.db.models import F


def initialize_display_names(apps, schema_editor):
    Gateway = apps.get_model("core", "Gateway")
    Gateway.objects.using(schema_editor.connection.alias).update(display_name=F("name"))


class Migration(migrations.Migration):
    dependencies = [("core", "0056_releasedresource_oauth2_scope_fields")]

    operations = [
        migrations.AddField(
            model_name="gateway",
            name="display_name",
            field=models.CharField(max_length=64, null=True, blank=True, default=None, unique=True),
        ),
        migrations.AddField(
            model_name="gateway",
            name="display_name_en",
            field=models.CharField(max_length=64, null=True, blank=True, default=None, unique=True),
        ),
        migrations.RunPython(initialize_display_names, migrations.RunPython.noop),
    ]
