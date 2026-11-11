import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

pytestmark = [pytest.mark.migration, pytest.mark.django_db(transaction=True)]

MIGRATE_FROM = [("skill", "0001_initial")]
MIGRATE_TO = [("skill", "0002_skillversion_changelog_json")]


def test_changelog_text_converted_to_entry_and_back():
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    alias = connection.alias
    try:
        executor.migrate(MIGRATE_FROM)
        old_apps = executor.loader.project_state(MIGRATE_FROM).apps
        metadata = (
            old_apps.get_model("skill", "SkillMetadata")
            .objects.using(alias)
            .create(type="platform", name="job-plan-run-and-log", display_name="作业", description="作业")
        )
        old_version = old_apps.get_model("skill", "SkillVersion")
        with_text = old_version.objects.using(alias).create(metadata=metadata, version="1.0.0", changelog="首个版本")
        empty = old_version.objects.using(alias).create(metadata=metadata, version="1.1.0")

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_TO)
        version = executor.loader.project_state(MIGRATE_TO).apps.get_model("skill", "SkillVersion")
        converted = version.objects.using(alias).get(pk=with_text.pk)
        assert converted.changelog == {
            "version": "1.0.0",
            "date": converted.created_time.date().isoformat(),
            "content": "首个版本",
        }
        assert version.objects.using(alias).get(pk=empty.pk).changelog == {}

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATE_FROM)
        reverted = executor.loader.project_state(MIGRATE_FROM).apps.get_model("skill", "SkillVersion")
        assert reverted.objects.using(alias).get(pk=with_text.pk).changelog == "首个版本"
        assert reverted.objects.using(alias).get(pk=empty.pk).changelog == ""
    finally:
        MigrationExecutor(connection).migrate(latest)
