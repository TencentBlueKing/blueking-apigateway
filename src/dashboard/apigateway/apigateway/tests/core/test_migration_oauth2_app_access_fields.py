import json
from importlib import import_module
from types import SimpleNamespace

import pytest
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

pytestmark = [pytest.mark.migration, pytest.mark.django_db(transaction=True)]

MIGRATE_FROM = [("core", "0058_resource_deprecation")]
MIGRATE_TO = [("core", "0059_oauth2_app_access_fields")]
APP_FLAG_FIELDS = {"oauth2_app_delegated_enabled", "oauth2_app_only_enabled"}
INDEX_NAMES = {"rr_oauth_app_dlg_scope_idx", "rr_oauth_app_only_scope_idx"}
MIGRATION_MODULE = import_module("apigateway.core.migrations.0059_oauth2_app_access_fields")


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        return {column.name for column in connection.introspection.get_table_description(cursor, table_name)}


def _constraint_names(connection, table_name):
    with connection.cursor() as cursor:
        return set(connection.introspection.get_constraints(cursor, table_name))


def _resource_data(resource_id, auth_config):
    return {
        "id": resource_id,
        "name": f"resource_{resource_id}",
        "method": "GET",
        "path": f"/r/{resource_id}",
        "is_public": True,
        "contexts": {"resource_auth": {"config": auth_config}},
    }


def _auth_config(user_required, app_required):
    return json.dumps({"auth_verified_required": user_required, "app_verified_required": app_required})


class _FakeReleasedResourceManager:
    """Supports filter(id__gt=...).order_by("id").only(...)[:n] used by the keyset pagination"""

    def __init__(self, rows):
        self.rows = rows
        self.queries = []
        self.flushed = []
        self._last_id = 0

    def filter(self, id__gt):
        self._last_id = id__gt
        return self

    def order_by(self, *fields):
        return self

    def only(self, *fields):
        return self

    def __getitem__(self, item):
        self.queries.append(self._last_id)
        rows = [row for row in self.rows if row.id > self._last_id]
        return rows[item]

    def bulk_update(self, objects, fields, batch_size):
        self.flushed.append([obj.id for obj in objects])


def test_backfill_pages_by_primary_key_and_skips_rows_without_app_channel(mocker, monkeypatch):
    resources = [
        SimpleNamespace(id=1, data=_resource_data(1, _auth_config(True, True))),
        SimpleNamespace(id=2, data=_resource_data(2, _auth_config(False, True))),
        SimpleNamespace(id=3, data=_resource_data(3, _auth_config(True, False))),
        SimpleNamespace(id=5, data=_resource_data(5, _auth_config(True, True))),
    ]
    manager = _FakeReleasedResourceManager(resources)
    apps = mocker.Mock()
    apps.get_model.return_value = type("ReleasedResource", (), {"objects": manager})
    monkeypatch.setattr(MIGRATION_MODULE, "BATCH_SIZE", 2)

    MIGRATION_MODULE.backfill_released_resource_app_flags(apps, mocker.Mock())

    assert manager.queries == [0, 2, 5]
    assert manager.flushed == [[1, 2], [5]]
    assert (resources[0].oauth2_app_delegated_enabled, resources[0].oauth2_app_only_enabled) == (True, False)
    assert (resources[1].oauth2_app_delegated_enabled, resources[1].oauth2_app_only_enabled) == (False, True)
    assert not hasattr(resources[2], "oauth2_app_delegated_enabled")


def test_oauth2_app_access_fields_backfill_db_defaults_and_reverse():
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest_migrations = executor.loader.graph.leaf_nodes()

    try:
        executor.migrate(MIGRATE_FROM)
        old_apps = executor.loader.project_state(MIGRATE_FROM).apps
        old_gateway_model = old_apps.get_model("core", "Gateway")
        old_released_resource_model = old_apps.get_model("core", "ReleasedResource")
        gateway = old_gateway_model.objects.create(
            name="migration-app-gateway", tenant_mode="global", tenant_id="", status=1
        )
        rows = [
            (1, _auth_config(True, True)),
            (2, _auth_config(False, True)),
            (3, _auth_config(True, False)),
            (4, "not-json"),
        ]
        rows.append((5, _auth_config(True, True)))
        for resource_id, auth_config in rows:
            data = _resource_data(resource_id, auth_config)
            if resource_id == 5:
                data["plugins"] = [{"type": "bk-access-token-source", "config": {"source": "bearer"}}]
            old_released_resource_model.objects.create(
                gateway_id=gateway.id,
                resource_version_id=resource_id,
                resource_id=resource_id,
                resource_name=data["name"],
                resource_method=data["method"],
                resource_path=data["path"],
                data=data,
            )

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
        new_apps = executor.loader.project_state(MIGRATE_TO).apps
        new_gateway_model = new_apps.get_model("core", "Gateway")
        new_released_resource_model = new_apps.get_model("core", "ReleasedResource")

        assert new_gateway_model.objects.get(id=gateway.id).oauth2_app_enabled is True
        assert list(
            new_released_resource_model.objects.order_by("resource_id").values_list(
                "oauth2_app_delegated_enabled", "oauth2_app_only_enabled"
            )
        ) == [(True, False), (False, True), (False, False), (False, False), (False, False)]
        assert _constraint_names(connection, new_released_resource_model._meta.db_table) >= INDEX_NAMES

        # Rolled-back Dashboard code does not know the new columns; database defaults must fill them.
        old_gateway = old_gateway_model.objects.create(
            name="old-code-gateway", tenant_mode="global", tenant_id="", status=1
        )
        old_released_resource_model.objects.create(
            gateway_id=old_gateway.id,
            resource_version_id=100,
            resource_id=100,
            resource_name="old_code",
            resource_method="GET",
            resource_path="/old",
            data=_resource_data(100, _auth_config(True, True)),
        )
        assert new_gateway_model.objects.get(id=old_gateway.id).oauth2_app_enabled is True
        old_code_row = new_released_resource_model.objects.get(resource_version_id=100)
        assert (old_code_row.oauth2_app_delegated_enabled, old_code_row.oauth2_app_only_enabled) == (False, False)

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_FROM)
        assert APP_FLAG_FIELDS.isdisjoint(_column_names(connection, new_released_resource_model._meta.db_table))
        assert "oauth2_app_enabled" not in _column_names(connection, new_gateway_model._meta.db_table)
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)


def test_oauth2_app_access_fields_rerun_after_partial_ddl():
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest_migrations = executor.loader.graph.leaf_nodes()

    try:
        executor.migrate(MIGRATE_FROM)
        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)

        # Simulate a non-atomic run that failed after the first column and index were created.
        model = executor.loader.project_state(MIGRATE_TO).apps.get_model("core", "ReleasedResource")
        only_index = next(idx for idx in model._meta.indexes if idx.name == "rr_oauth_app_only_scope_idx")
        with connection.schema_editor() as schema_editor:
            schema_editor.remove_index(model, only_index)
            schema_editor.remove_field(model, model._meta.get_field("oauth2_app_only_enabled"))
        MigrationRecorder(connection).record_unapplied(*MIGRATE_TO[0])

        table = model._meta.db_table
        assert "oauth2_app_only_enabled" not in _column_names(connection, table)

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)

        assert _column_names(connection, table) >= APP_FLAG_FIELDS
        assert _constraint_names(connection, table) >= INDEX_NAMES
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)
