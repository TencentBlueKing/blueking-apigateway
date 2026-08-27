import json
from datetime import timedelta

from django.db import migrations, transaction
from django.utils import timezone

BATCH_SIZE = 1000
MEMBER_EXPIRE_DAYS = 365
MAX_USERNAME_LENGTH = 64
ADMINISTRATOR_ROLE = "administrator"
MIGRATION_OPERATOR = "system"


def _report(event, **data):
    print(
        json.dumps(
            {
                "event": event,
                **data,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _parse_maintainers(raw_maintainers):
    if not raw_maintainers:
        return []

    # Keep this aligned with the historical Gateway.maintainers behavior at
    # migration creation time. Do not normalize usernames here, as doing so
    # could grant a user who did not match the legacy permission check.
    usernames = raw_maintainers.rstrip(";,").split(";")
    return list(dict.fromkeys(username for username in usernames if username))


def _flush_members(member_model, members, db_alias):
    if not members:
        return 0, 0

    gateway_ids = {member.gateway_id for member in members}
    with transaction.atomic(using=db_alias):
        existing_pairs = set(
            member_model.objects.using(db_alias)
            .filter(gateway_id__in=gateway_ids)
            .values_list("gateway_id", "username")
        )
        members_to_create = [
            member for member in members if (member.gateway_id, member.username) not in existing_pairs
        ]
        member_model.objects.using(db_alias).bulk_create(members_to_create, batch_size=BATCH_SIZE)

    return len(members_to_create), len(members) - len(members_to_create)


def backfill_gateway_members(apps, schema_editor):
    Gateway = apps.get_model("core", "Gateway")
    GatewayMember = apps.get_model("core", "GatewayMember")
    db_alias = schema_editor.connection.alias
    expires = timezone.now() + timedelta(days=MEMBER_EXPIRE_DAYS)

    scanned_count = 0
    created_count = 0
    existing_count = 0
    empty_count = 0
    invalid_count = 0
    pending = []

    gateways = (
        Gateway.objects.using(db_alias)
        .only("id", "name", "_maintainers")
        .order_by("id")
        .iterator(chunk_size=BATCH_SIZE)
    )
    for gateway in gateways:
        scanned_count += 1
        usernames = _parse_maintainers(gateway._maintainers)
        if not usernames:
            empty_count += 1
            _report(
                "gateway_member_migration.empty_maintainers",
                gateway_id=gateway.id,
                gateway_name=gateway.name,
            )
            continue

        for username in usernames:
            if len(username) > MAX_USERNAME_LENGTH:
                invalid_count += 1
                _report(
                    "gateway_member_migration.invalid_maintainer",
                    gateway_id=gateway.id,
                    gateway_name=gateway.name,
                    reason=f"username exceeds {MAX_USERNAME_LENGTH} characters",
                    username=username,
                )
                continue

            pending.append(
                GatewayMember(
                    gateway_id=gateway.id,
                    username=username,
                    role=ADMINISTRATOR_ROLE,
                    expires=expires,
                    created_by=MIGRATION_OPERATOR,
                    updated_by=MIGRATION_OPERATOR,
                )
            )
            if len(pending) == BATCH_SIZE:
                created, existing = _flush_members(GatewayMember, pending, db_alias)
                created_count += created
                existing_count += existing
                pending.clear()

    if pending:
        created, existing = _flush_members(GatewayMember, pending, db_alias)
        created_count += created
        existing_count += existing

    _report(
        "gateway_member_migration.summary",
        created=created_count,
        empty=empty_count,
        existing=existing_count,
        invalid=invalid_count,
        scanned=scanned_count,
    )
    if invalid_count:
        raise RuntimeError(f"failed to migrate {invalid_count} invalid gateway maintainers")


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("core", "0057_gateway_member"),
    ]

    operations = [
        migrations.RunPython(
            backfill_gateway_members,
            migrations.RunPython.noop,
            atomic=False,
        ),
    ]
