import json

import pytest
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

pytestmark = pytest.mark.django_db(transaction=True)

MIGRATE_FROM = [("core", "0053_resource_oauth2_client_fields")]
MIGRATE_TO = [("core", "0054_releasedresource_oauth2_scope_fields")]
PROJECTED_FIELDS = {
    "is_public",
    "oauth2_public_client_enabled",
    "oauth2_personal_client_enabled",
}
INDEX_NAMES = {
    "rr_oauth_pub_scope_idx",
    "rr_oauth_personal_scope_idx",
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
        assert _index_columns(connection, migrated_released_resource._meta.db_table) == EXPECTED_INDEX_COLUMNS

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_FROM)
        assert PROJECTED_FIELDS.isdisjoint(_column_names(connection, migrated_released_resource._meta.db_table))
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)
