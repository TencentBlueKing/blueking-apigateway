import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

pytestmark = pytest.mark.django_db(transaction=True)

MIGRATE_FROM = [("core", "0052_gateway_is_official")]
MIGRATE_TO = [("core", "0053_add_ai_gateway_model_kinds")]


def test_ai_gateway_model_kinds_migration_backfills_existing_rows():
    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_FROM)
    old_apps = executor.loader.project_state(MIGRATE_FROM).apps

    Gateway = old_apps.get_model("core", "Gateway")
    Backend = old_apps.get_model("core", "Backend")
    Resource = old_apps.get_model("core", "Resource")

    gateway = Gateway.objects.create(
        name="legacy-kind-gateway",
        status=1,
        tenant_mode="single",
        tenant_id="",
    )
    backend = Backend.objects.create(gateway_id=gateway.id, name="legacy-backend")
    resource = Resource.objects.create(
        gateway_id=gateway.id,
        method="GET",
        path="/legacy",
        proxy_id=1,
    )

    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_TO)
    new_apps = executor.loader.project_state(MIGRATE_TO).apps

    migrated_gateway = new_apps.get_model("core", "Gateway")
    migrated_backend = new_apps.get_model("core", "Backend")
    migrated_resource = new_apps.get_model("core", "Resource")

    assert migrated_gateway.objects.get(id=gateway.id).kind == 0
    assert migrated_backend.objects.get(id=backend.id).kind == "standard"
    assert migrated_resource.objects.get(id=resource.id).kind == "standard"
