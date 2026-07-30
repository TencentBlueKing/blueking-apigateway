import pytest
from django.db import DatabaseError, connections, models
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

pytestmark = pytest.mark.django_db(transaction=True)

MIGRATE_FROM = [("core", "0054_backendconfig_private_config")]
MIGRATE_TO = [("core", "0055_resource_oauth2_client_fields")]
RELEASE_BACKPORT_MIGRATION = ("core", "0053_resource_oauth2_client_fields")
OAUTH2_FIELD_NAMES = (
    "oauth2_personal_client_enabled",
    "oauth2_public_client_enabled",
)


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        return {
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }


def _add_release_backport_columns(connection, resource_model):
    with connection.schema_editor() as schema_editor:
        for field_name in OAUTH2_FIELD_NAMES:
            # Keep SQLite on ALTER TABLE ADD COLUMN so adding the second field
            # doesn't rebuild the table from stale migration state.
            field = models.BooleanField(null=True)
            field.set_attributes_from_name(field_name)
            field.model = resource_model
            schema_editor.add_field(resource_model, field)


def test_oauth2_fields_migration_accepts_columns_created_by_release_backport(monkeypatch):
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest_migrations = executor.loader.graph.leaf_nodes()
    recorder = MigrationRecorder(connection)

    try:
        executor.migrate(MIGRATE_FROM)
        old_apps = executor.loader.project_state(MIGRATE_FROM).apps
        Resource = old_apps.get_model("core", "Resource")

        _add_release_backport_columns(connection, Resource)
        recorder.record_applied(*RELEASE_BACKPORT_MIGRATION)
        assert MIGRATE_TO[0] not in recorder.applied_migrations()
        assert set(OAUTH2_FIELD_NAMES) <= _column_names(connection, Resource._meta.db_table)

        schema_editor_class = connection.SchemaEditorClass
        original_add_field = schema_editor_class.add_field
        added_fields = []

        def reject_duplicate_columns(schema_editor, model, field):
            added_fields.append(field.column)
            if field.column in _column_names(connection, model._meta.db_table):
                raise DatabaseError(f"duplicate column: {field.column}")
            return original_add_field(schema_editor, model, field)

        with monkeypatch.context() as patch:
            patch.setattr(schema_editor_class, "add_field", reject_duplicate_columns)
            executor = MigrationExecutor(connection)
            executor.migrate(MIGRATE_TO)

        assert added_fields == []
        assert set(OAUTH2_FIELD_NAMES) <= _column_names(connection, Resource._meta.db_table)

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_FROM)
        assert set(OAUTH2_FIELD_NAMES) <= _column_names(connection, Resource._meta.db_table)

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
    finally:
        recorder.record_unapplied(*RELEASE_BACKPORT_MIGRATION)
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)


def test_oauth2_fields_migration_adds_and_removes_columns_without_release_backport():
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest_migrations = executor.loader.graph.leaf_nodes()
    recorder = MigrationRecorder(connection)

    try:
        recorder.record_unapplied(*RELEASE_BACKPORT_MIGRATION)
        executor.migrate(MIGRATE_FROM)
        old_apps = executor.loader.project_state(MIGRATE_FROM).apps
        Resource = old_apps.get_model("core", "Resource")
        assert set(OAUTH2_FIELD_NAMES).isdisjoint(_column_names(connection, Resource._meta.db_table))

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
        assert set(OAUTH2_FIELD_NAMES) <= _column_names(connection, Resource._meta.db_table)

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_FROM)
        remaining_columns = set(OAUTH2_FIELD_NAMES) & _column_names(connection, Resource._meta.db_table)
        assert remaining_columns == set()
    finally:
        recorder.record_unapplied(*RELEASE_BACKPORT_MIGRATION)
        executor = MigrationExecutor(connection)
        executor.migrate(latest_migrations)
