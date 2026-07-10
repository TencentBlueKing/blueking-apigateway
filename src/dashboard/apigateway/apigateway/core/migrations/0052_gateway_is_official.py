import json

from django.db import migrations, models

GATEWAY_CONTEXT_SCOPE_TYPE = "api"
GATEWAY_AUTH_CONTEXT_TYPE = "api_auth"
OFFICIAL_API_TYPES = {0, 1}


def forwards_func(apps, schema_editor):
    Gateway = apps.get_model("core", "Gateway")
    Context = apps.get_model("core", "Context")

    official_gateway_ids = []
    contexts = Context.objects.filter(
        scope_type=GATEWAY_CONTEXT_SCOPE_TYPE,
        type=GATEWAY_AUTH_CONTEXT_TYPE,
    ).only("scope_id", "_config")
    for context in contexts.iterator():
        try:
            config = json.loads(context._config or "{}")
        except (TypeError, ValueError):
            continue

        if config.get("api_type") in OFFICIAL_API_TYPES:
            official_gateway_ids.append(context.scope_id)

    if official_gateway_ids:
        Gateway.objects.filter(id__in=official_gateway_ids).update(is_official=True)


def reverse_func(apps, schema_editor):
    Gateway = apps.get_model("core", "Gateway")
    Gateway.objects.update(is_official=False)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0051_rename_publishevent_gateway_publish_index"),
    ]

    operations = [
        migrations.AddField(
            model_name="gateway",
            name="is_official",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(forwards_func, reverse_func),
    ]
