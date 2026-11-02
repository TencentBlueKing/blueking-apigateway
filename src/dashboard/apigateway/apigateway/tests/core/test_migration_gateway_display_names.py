import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor

pytestmark = [pytest.mark.migration, pytest.mark.django_db(transaction=True)]

MIGRATE_FROM = [("core", "0056_releasedresource_oauth2_scope_fields")]
MIGRATE_TO = [("core", "0057_gateway_display_names")]


def test_display_names_migration_backfills_and_indexes():
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    alias = connection.alias
    try:
        executor.migrate(MIGRATE_FROM)
        old_gateway = executor.loader.project_state(MIGRATE_FROM).apps.get_model("core", "Gateway")
        ids = [
            old_gateway.objects.using(alias).create(name=name, status=1, tenant_mode="single", tenant_id="").pk
            for name in ("legacy-one", "legacy-two", "legacy-three")
        ]
        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
        gateway = executor.loader.project_state(MIGRATE_TO).apps.get_model("core", "Gateway")
        rows = gateway.objects.using(alias).filter(pk__in=ids).order_by("pk")
        assert list(rows.values_list("display_name", "display_name_en")) == [
            ("legacy-one", None),
            ("legacy-two", None),
            ("legacy-three", None),
        ]
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, gateway._meta.db_table)
        unique_columns = {tuple(value["columns"]) for value in constraints.values() if value["unique"]}
        assert ("display_name",) in unique_columns
        assert ("display_name_en",) in unique_columns
        with pytest.raises(IntegrityError), transaction.atomic(using=alias):
            rows.filter(pk=ids[1]).update(display_name="legacy-one")
        rows.filter(pk__in=ids[:2]).update(display_name=None)
        assert rows.filter(display_name=None).count() == 2
        rows.filter(pk=ids[0]).update(display_name_en="Unique English")
        with pytest.raises(IntegrityError), transaction.atomic(using=alias):
            rows.filter(pk=ids[1]).update(display_name_en="Unique English")
    finally:
        MigrationExecutor(connection).migrate(latest)
