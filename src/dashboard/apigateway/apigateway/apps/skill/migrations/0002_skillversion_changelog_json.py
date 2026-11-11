from django.db import migrations, models


# MySQL 不能把非 JSON 文本原地改成 JSON 列，所以新建列、搬数据、再换名
def text_to_entry(apps, schema_editor):
    SkillVersion = apps.get_model("skill", "SkillVersion")
    versions = SkillVersion.objects.using(schema_editor.connection.alias).exclude(changelog="")
    for version in versions:
        version.changelog_entry = {
            "version": version.version,
            "date": version.created_time.date().isoformat() if version.created_time else "",
            "content": version.changelog,
        }
        version.save(update_fields=["changelog_entry"])


def entry_to_text(apps, schema_editor):
    SkillVersion = apps.get_model("skill", "SkillVersion")
    for version in SkillVersion.objects.using(schema_editor.connection.alias).all():
        if not version.changelog_entry:
            continue
        version.changelog = version.changelog_entry.get("content", "")
        version.save(update_fields=["changelog"])


class Migration(migrations.Migration):
    dependencies = [("skill", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="skillversion",
            name="changelog_entry",
            field=models.JSONField(blank=True, default=dict, help_text="版本说明：version、date、content"),
        ),
        migrations.RunPython(text_to_entry, entry_to_text),
        migrations.RemoveField(model_name="skillversion", name="changelog"),
        migrations.RenameField(model_name="skillversion", old_name="changelog_entry", new_name="changelog"),
    ]
