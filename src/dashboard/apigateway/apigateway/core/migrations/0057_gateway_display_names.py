from django.db import migrations, models
from django.db.models import F, Q


def initialize_display_names(apps, schema_editor):
    Gateway = apps.get_model("core", "Gateway")
    gateways = Gateway.objects.using(schema_editor.connection.alias)
    gateways.filter(Q(display_name__isnull=True) | Q(display_name="")).update(display_name=F("name"))
    seen = {}
    for pk, value in gateways.values_list("pk", "display_name").iterator():
        trimmed = value.strip()
        normalized = trimmed.lower()
        if not normalized or len(trimmed) > 64 or normalized in seen:
            raise RuntimeError(
                f"Gateway display-name initialization conflict: gateway id={pk}, name={value!r}, "
                f"conflicting gateway id={seen.get(normalized)!r}"
            )
        seen[normalized] = pk
        if value != trimmed:
            gateways.filter(pk=pk).update(display_name=trimmed)


class Migration(migrations.Migration):
    dependencies = [("core", "0056_releasedresource_oauth2_scope_fields")]

    operations = [
        migrations.AddField(
            model_name="gateway", name="display_name", field=models.CharField(max_length=64, null=True, blank=True)
        ),
        migrations.AddField(
            model_name="gateway",
            name="display_name_en",
            field=models.CharField(max_length=64, null=True, blank=True, default=None, unique=True),
        ),
        migrations.RunPython(initialize_display_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="gateway",
            name="display_name",
            field=models.CharField(max_length=64, blank=True, default="", unique=True),
        ),
    ]
