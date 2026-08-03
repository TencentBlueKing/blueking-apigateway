import json
from importlib import import_module
from types import SimpleNamespace

import pytest
from django.db import DatabaseError, connections, models
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

pytestmark = pytest.mark.django_db(transaction=True)

MIGRATE_FROM = [("core", "0055_resource_oauth2_client_fields")]
MIGRATE_TO = [("core", "0056_releasedresource_oauth2_scope_fields")]
RELEASE_BACKPORT_MIGRATION = ("core", "0054_releasedresource_oauth2_scope_fields")
PROJECTED_FIELDS = {
    "is_public",
    "oauth2_public_client_enabled",
    "oauth2_personal_client_enabled",
}
INDEX_NAMES = {
    "rr_oauth_pub_scope_idx",
    "rr_oauth_personal_scope_idx",
}
INDEX_FIELDS = {
    "rr_oauth_pub_scope_idx": [
        "oauth2_public_client_enabled",
        "is_public",
        "gateway",
        "resource_version_id",
        "resource_id",
    ],
    "rr_oauth_personal_scope_idx": [
        "oauth2_personal_client_enabled",
        "is_public",
        "gateway",
        "resource_version_id",
        "resource_id",
    ],
}
EXPECTED_INDEX_COLUMNS = {
    "rr_oauth_pub_scope_idx": [
        "oauth2_public_client_enabled",
        "is_public",
        "api_id",
        "resource_version_id",
        "resource_id",
    ],
    "rr_oauth_personal_scope_idx": [
        "oauth2_personal_client_enabled",
        "is_public",
        "api_id",
        "resource_version_id",
        "resource_id",
    ],
}
MIGRATION_MODULE = import_module("apigateway.core.migrations.0056_releasedresource_oauth2_scope_fields")


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        return {
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }


def _constraint_names(connection, table_name):
    with connection.cursor() as cursor:
        return set(connection.introspection.get_constraints(cursor, table_name))


def _index_columns(connection, table_name):
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, table_name)
    return {name: constraints[name]["columns"] for name in INDEX_NAMES}


def _add_release_backport_schema(connection, released_resource_model):
    with connection.schema_editor() as schema_editor:
        for field_name in PROJECTED_FIELDS:
            field = models.BooleanField(null=True)
            field.contribute_to_class(released_resource_model, field_name)
            schema_editor.add_field(released_resource_model, field)

        for index_name, fields in INDEX_FIELDS.items():
            schema_editor.add_index(released_resource_model, models.Index(fields=fields, name=index_name))


def _resource_data(*, is_public, public_enabled=False, personal_enabled=False, auth_config=None):
    if auth_config is None:
        auth_config = json.dumps(
            {
                "oauth2_public_client_enabled": public_enabled,
                "oauth2_personal_client_enabled": personal_enabled,
            }
        )
    return {
        "id": 1,
        "name": "get_user",
        "method": "GET",
        "path": "/users/{id}",
        "is_public": is_public,
        "contexts": {"resource_auth": {"config": auth_config}},
    }


def test_released_resource_scope_backfill_flushes_full_batches_and_remainder(mocker, monkeypatch):
    resources = [
        SimpleNamespace(data=_resource_data(is_public=True, public_enabled=True)),
        SimpleNamespace(data=_resource_data(is_public=False, personal_enabled=True)),
        SimpleNamespace(data=_resource_data(is_public=True, auth_config="not-json")),
    ]
    manager = mocker.Mock()
    manager.only.return_value.order_by.return_value.iterator.return_value = iter(resources)
    flushed_batch_sizes = []
    manager.bulk_update.side_effect = lambda objects, fields, batch_size: flushed_batch_sizes.append(len(objects))
    released_resource_model = type("ReleasedResource", (), {"objects": manager})
    apps = mocker.Mock()
    apps.get_model.return_value = released_resource_model
    monkeypatch.setattr(MIGRATION_MODULE, "BATCH_SIZE", 2)
    monkeypatch.setattr(MIGRATION_MODULE, "_release_backport_was_applied", lambda schema_editor: False)

    MIGRATION_MODULE.backfill_released_resource_scope_fields(apps, mocker.Mock())

    assert flushed_batch_sizes == [2, 1]
    assert [
        (
            resource.is_public,
            resource.oauth2_public_client_enabled,
            resource.oauth2_personal_client_enabled,
        )
        for resource in resources
    ] == [
        (True, True, False),
        (False, False, True),
        (True, False, False),
    ]


def test_released_resource_oauth2_scope_fields_are_backfilled_and_reversible():
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest_migrations = executor.loader.graph.leaf_nodes()

    try:
        executor.migrate(MIGRATE_FROM)
        old_apps = executor.loader.project_state(MIGRATE_FROM).apps
        Gateway = old_apps.get_model("core", "Gateway")
        ReleasedResource = old_apps.get_model("core", "ReleasedResource")
        gateway = Gateway.objects.create(
            name="migration-scope-gateway",
            tenant_mode="global",
            tenant_id="",
            status=1,
        )

        rows = [
            (11, 1, _resource_data(is_public=True, public_enabled=True)),
            (12, 2, _resource_data(is_public=False, personal_enabled=True)),
            (13, 3, _resource_data(is_public=True, auth_config="not-json")),
            (14, 4, _resource_data(is_public="false", public_enabled="false", personal_enabled="false")),
            (15, 5, _resource_data(is_public=1, public_enabled=1, personal_enabled=1)),
        ]
        for resource_version_id, resource_id, data in rows:
            ReleasedResource.objects.create(
                gateway_id=gateway.id,
                resource_version_id=resource_version_id,
                resource_id=resource_id,
                resource_name=data["name"],
                resource_method=data["method"],
                resource_path=data["path"],
                data=data,
            )

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
        new_apps = executor.loader.project_state(MIGRATE_TO).apps
        migrated_released_resource = new_apps.get_model("core", "ReleasedResource")
        values = list(
            migrated_released_resource.objects.order_by("resource_id").values_list(
                "is_public",
                "oauth2_public_client_enabled",
                "oauth2_personal_client_enabled",
            )
        )

        assert values == [
            (True, True, False),
            (False, False, True),
            (True, False, False),
            (False, False, False),
            (False, False, False),
        ]
        assert _constraint_names(connection, migrated_released_resource._meta.db_table) >= INDEX_NAMES

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_FROM)
        assert PROJECTED_FIELDS.isdisjoint(_column_names(connection, migrated_released_resource._meta.db_table))
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)


def test_released_resource_scope_migration_accepts_schema_created_by_release_backport(monkeypatch):
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest_migrations = executor.loader.graph.leaf_nodes()
    recorder = MigrationRecorder(connection)

    try:
        executor.migrate(MIGRATE_FROM)
        old_apps = executor.loader.project_state(MIGRATE_FROM).apps
        ReleasedResource = old_apps.get_model("core", "ReleasedResource")
        _add_release_backport_schema(connection, ReleasedResource)
        recorder.record_applied(*RELEASE_BACKPORT_MIGRATION)

        schema_editor_class = connection.SchemaEditorClass
        original_add_field = schema_editor_class.add_field

        def reject_duplicate_columns(schema_editor, model, field):
            if field.column in _column_names(connection, model._meta.db_table):
                raise DatabaseError(f"duplicate column: {field.column}")
            return original_add_field(schema_editor, model, field)

        with monkeypatch.context() as patch:
            patch.setattr(schema_editor_class, "add_field", reject_duplicate_columns)
            executor = MigrationExecutor(connection)
            executor.migrate(MIGRATE_TO)

        assert _column_names(connection, ReleasedResource._meta.db_table) >= PROJECTED_FIELDS
        assert _constraint_names(connection, ReleasedResource._meta.db_table) >= INDEX_NAMES
        assert _index_columns(connection, ReleasedResource._meta.db_table) == EXPECTED_INDEX_COLUMNS

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_FROM)
        assert _column_names(connection, ReleasedResource._meta.db_table) >= PROJECTED_FIELDS
        assert _constraint_names(connection, ReleasedResource._meta.db_table) >= INDEX_NAMES
        assert _index_columns(connection, ReleasedResource._meta.db_table) == EXPECTED_INDEX_COLUMNS

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
    finally:
        recorder.record_unapplied(*RELEASE_BACKPORT_MIGRATION)
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)
