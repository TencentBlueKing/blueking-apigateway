import json
from datetime import timedelta
from importlib import import_module

import pytest
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

pytestmark = pytest.mark.django_db(transaction=True)

MIGRATE_ZERO = [("rbac", None)]
MIGRATE_SCHEMA = [("rbac", "0001_initial")]
MIGRATE_TO = [("rbac", "0002_backfill_gateway_members")]
MIGRATION_MODULE = import_module("apigateway.apps.rbac.migrations.0002_backfill_gateway_members")


def _create_gateway(gateway_model, name, maintainers="", developers="", doc_maintainers=None):
    return gateway_model.objects.create(
        name=name,
        _maintainers=maintainers,
        _developers=developers,
        _doc_maintainers=doc_maintainers or {},
        tenant_mode="global",
        tenant_id="",
        status=1,
    )


def _table_names(connection):
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _constraints(connection, table_name):
    with connection.cursor() as cursor:
        return connection.introspection.get_constraints(cursor, table_name)


def _json_log_records(captured):
    return [json.loads(line) for line in captured.splitlines() if line.startswith("{")]


def _assert_backfilled_members(
    member_model,
    expected_pairs,
    empty_gateway_id,
    migration_started_at,
    migration_finished_at,
):
    members = list(
        member_model.objects.order_by("gateway_id", "username").values(
            "gateway_id",
            "username",
            "role",
            "expires",
            "created_by",
            "updated_by",
        )
    )
    assert {(member["gateway_id"], member["username"]) for member in members} == expected_pairs
    assert {member["role"] for member in members} == {"administrator"}
    assert {member["created_by"] for member in members} == {"system"}
    assert {member["updated_by"] for member in members} == {"system"}
    assert len({member["expires"] for member in members}) == 1
    assert all(
        migration_started_at + timedelta(days=365) <= member["expires"] <= migration_finished_at + timedelta(days=365)
        for member in members
    )
    assert not member_model.objects.filter(gateway_id=empty_gateway_id).exists()
    assert not member_model.objects.filter(username__in=["developer", "doc_maintainer"]).exists()


def _assert_initial_migration_logs(capsys, empty_gateway_id):
    log_records = _json_log_records(capsys.readouterr().out)
    assert {
        record["gateway_id"]
        for record in log_records
        if record["event"] == "gateway_member_migration.empty_maintainers"
    } == {empty_gateway_id}
    assert any(
        record
        == {
            "created": 6,
            "empty": 1,
            "event": "gateway_member_migration.summary",
            "existing": 0,
            "invalid": 0,
            "scanned": 5,
        }
        for record in log_records
    )


def _assert_idempotent_rerun(connection, apps, member_model, gateway_id, capsys):
    preserved_member = member_model.objects.get(gateway_id=gateway_id, username="admin")
    member_model.objects.filter(id=preserved_member.id).update(role="operator", expires=None)
    with connection.schema_editor() as schema_editor:
        MIGRATION_MODULE.backfill_gateway_members(apps, schema_editor)

    assert member_model.objects.count() == 6
    preserved_member.refresh_from_db()
    assert preserved_member.role == "operator"
    assert preserved_member.expires is None
    rerun_records = _json_log_records(capsys.readouterr().out)
    assert any(
        record["event"] == "gateway_member_migration.summary" and record["created"] == 0 and record["existing"] == 6
        for record in rerun_records
    )


def test_gateway_member_migration_backfills_members_and_is_reversible(monkeypatch, capsys):
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest_migrations = executor.loader.graph.leaf_nodes()

    try:
        executor.migrate(MIGRATE_ZERO)
        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_SCHEMA)
        schema_apps = executor.loader.project_state(MIGRATE_SCHEMA).apps
        Gateway = schema_apps.get_model("core", "Gateway")
        normal_gateway = _create_gateway(Gateway, "member-normal", "admin;guest;;,,")
        duplicate_gateway = _create_gateway(Gateway, "member-duplicate", "owner;owner")
        inner_empty_gateway = _create_gateway(Gateway, "member-inner-empty", "first;;second")
        empty_gateway = _create_gateway(Gateway, "member-empty")
        ignored_fields_gateway = _create_gateway(
            Gateway,
            "member-ignored-fields",
            "maintainer",
            developers="developer",
            doc_maintainers={"type": "user", "contacts": ["doc_maintainer"]},
        )
        migration_started_at = timezone.now()

        monkeypatch.setattr(MIGRATION_MODULE, "BATCH_SIZE", 2)
        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
        migration_finished_at = timezone.now()

        migrated_apps = executor.loader.project_state(MIGRATE_TO).apps
        GatewayMember = migrated_apps.get_model("rbac", "GatewayMember")
        _assert_backfilled_members(
            GatewayMember,
            {
                (normal_gateway.id, "admin"),
                (normal_gateway.id, "guest"),
                (duplicate_gateway.id, "owner"),
                (inner_empty_gateway.id, "first"),
                (inner_empty_gateway.id, "second"),
                (ignored_fields_gateway.id, "maintainer"),
            },
            empty_gateway.id,
            migration_started_at,
            migration_finished_at,
        )

        constraints = _constraints(connection, GatewayMember._meta.db_table)
        assert any(
            constraint["index"] and constraint["columns"] == ["username"] for constraint in constraints.values()
        )
        assert any(
            constraint["unique"] and constraint["columns"] == ["api_id", "username"]
            for constraint in constraints.values()
        )

        _assert_initial_migration_logs(capsys, empty_gateway.id)
        _assert_idempotent_rerun(connection, migrated_apps, GatewayMember, normal_gateway.id, capsys)

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_SCHEMA)
        schema_apps = executor.loader.project_state(MIGRATE_SCHEMA).apps
        assert schema_apps.get_model("rbac", "GatewayMember").objects.count() == 6

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_ZERO)
        assert "core_gateway_member" not in _table_names(connection)
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)


def test_gateway_member_migration_reports_invalid_username_and_can_resume(capsys):
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest_migrations = executor.loader.graph.leaf_nodes()

    try:
        executor.migrate(MIGRATE_ZERO)
        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_SCHEMA)
        schema_apps = executor.loader.project_state(MIGRATE_SCHEMA).apps
        Gateway = schema_apps.get_model("core", "Gateway")
        GatewayMember = schema_apps.get_model("rbac", "GatewayMember")
        valid_gateway = _create_gateway(Gateway, "member-valid-before-failure", "valid")
        invalid_gateway = _create_gateway(Gateway, "member-invalid", "x" * 65)

        executor = MigrationExecutor(connection)
        with pytest.raises(RuntimeError, match="failed to migrate 1 invalid gateway maintainers"):
            executor.migrate(MIGRATE_TO)

        assert GatewayMember.objects.filter(gateway_id=valid_gateway.id, username="valid").count() == 1
        failed_records = _json_log_records(capsys.readouterr().out)
        assert any(
            record["event"] == "gateway_member_migration.invalid_maintainer"
            and record["gateway_id"] == invalid_gateway.id
            and record["reason"] == "username exceeds 64 characters"
            for record in failed_records
        )

        Gateway.objects.filter(id=invalid_gateway.id).update(_maintainers="fixed")
        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
        migrated_apps = executor.loader.project_state(MIGRATE_TO).apps
        migrated_gateway_member = migrated_apps.get_model("rbac", "GatewayMember")
        assert set(migrated_gateway_member.objects.values_list("gateway_id", "username")) == {
            (valid_gateway.id, "valid"),
            (invalid_gateway.id, "fixed"),
        }
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)
