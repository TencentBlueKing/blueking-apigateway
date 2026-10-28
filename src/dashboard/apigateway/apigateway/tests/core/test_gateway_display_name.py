import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils.translation import override
from django_dynamic_fixture import G, N

from apigateway.core.gateway_name import validate_display_name, validate_display_name_en
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("value", [None, "", "  "])
def test_creation_defaults(value):
    assert validate_display_name(value, name="gateway-name") == "gateway-name"
    assert validate_display_name_en(value) is None


def test_fixture_and_localization():
    fixture = G(Gateway)
    assert fixture.display_name == fixture.name
    gateway = G(Gateway, display_name="默认  名称", display_name_en="English  Name")
    assert gateway.display_name == "默认  名称"
    assert gateway.display_name_en == "English  Name"
    with override("en"):
        assert gateway.display_name_i18n == "English  Name"
        gateway.display_name_en = None
        assert gateway.display_name_i18n == "默认  名称"
    with override("zh-cn"):
        assert gateway.display_name_i18n == "默认  名称"


@pytest.mark.parametrize("field", ["display_name", "display_name_en"])
def test_length_boundaries(field):
    gateway = G(Gateway, **{field: "A" * 64})
    setattr(gateway, field, "A" * 65)
    with pytest.raises(ValidationError) as exc:
        if field == "display_name":
            validate_display_name(
                gateway.display_name, name=gateway.name, gateways=Gateway.objects.exclude(pk=gateway.pk)
            )
        else:
            validate_display_name_en(gateway.display_name_en, gateways=Gateway.objects.exclude(pk=gateway.pk))
    assert field in exc.value.message_dict


@pytest.mark.parametrize("value", ["中文", "Name_1", "1Name", "Name!", "Name\nOther"])
def test_english_characters(value):
    with pytest.raises(ValidationError) as exc:
        validate_display_name_en(value, gateways=Gateway.objects.all())
    assert "display_name_en" in exc.value.message_dict


def test_english_allowed_characters():
    assert G(Gateway, display_name_en="Name 12- X").display_name_en == "Name 12- X"


@pytest.mark.parametrize(
    "existing,candidate,field",
    [
        ({"display_name": "Asset Hub"}, {"display_name": " ASSET HUB "}, "display_name"),
        ({"display_name_en": "English"}, {"display_name_en": "english"}, "display_name_en"),
    ],
)
def test_same_field_conflicts_are_global(existing, candidate, field):
    G(Gateway, tenant_id="other-tenant", status=0, is_public=False, is_deprecated=True, **existing)
    with pytest.raises(ValidationError) as exc:
        if field == "display_name":
            validate_display_name(candidate[field], name="candidate", gateways=Gateway.objects.all())
        else:
            validate_display_name_en(candidate[field], gateways=Gateway.objects.all())
    assert field in exc.value.message_dict


@pytest.mark.parametrize(
    "existing,candidate",
    [
        ({"display_name": "Shared"}, {"display_name_en": "Shared"}),
        ({"display_name_en": "Shared"}, {"display_name": "Shared"}),
        ({"name": "shared", "display_name": "Other"}, {"display_name": "SHARED"}),
        ({"name": "shared", "display_name": "Other"}, {"display_name_en": "SHARED"}),
        ({"display_name": "Shared"}, {"name": "shared", "display_name": "New Default"}),
        ({"display_name_en": "Shared"}, {"name": "shared", "display_name": "New Default"}),
    ],
)
def test_names_in_different_fields_are_independent(existing, candidate):
    G(Gateway, **existing)
    gateway = G(Gateway, **candidate)
    gateway.refresh_from_db()
    for field, value in candidate.items():
        assert getattr(gateway, field) == value


def test_cross_language_overlap_allowed_when_effective_names_differ():
    G(Gateway, display_name="Default One", display_name_en="English One")
    gateway = G(Gateway, display_name="English One", display_name_en="Default One")
    gateway.save()
    assert gateway.display_name == "English One"


def test_self_name_reuse_and_duplicate_english_fallback_are_allowed():
    gateway = G(Gateway, name="own-name", display_name="own-name", display_name_en="own-name")
    gateway.save()
    G(Gateway, display_name="Other Default", display_name_en="own-name-two")
    gateway.display_name = "own-name-two"
    gateway.save(update_fields=["display_name"])
    gateway.display_name_en = None
    gateway.save(update_fields=["display_name_en"])
    gateway.refresh_from_db()
    assert gateway.display_name_en is None
    with override("en"):
        assert gateway.display_name_i18n == "own-name-two"


def test_explicit_metadata_save_preserves_names(django_assert_num_queries):
    gateway = G(Gateway, display_name="Before", display_name_en="Before English")
    stale = Gateway.objects.get(pk=gateway.pk)
    gateway.display_name = "After"
    gateway.save(update_fields=["display_name"])
    stale.description = "metadata"
    with django_assert_num_queries(1):
        stale.save(update_fields=["description"])
    gateway.refresh_from_db()
    assert gateway.display_name == "After"
    assert gateway.description == "metadata"


def test_partial_name_save_uses_current_sibling_values():
    gateway = G(Gateway, display_name="Before", display_name_en="Before English")
    stale = Gateway.objects.get(pk=gateway.pk)
    gateway.display_name = "Current"
    gateway.save(update_fields=["display_name"])
    G(Gateway, display_name="Other", display_name_en="Current")
    stale.display_name_en = None
    stale.save(update_fields=["display_name_en"])
    gateway.refresh_from_db()
    assert gateway.display_name == "Current"
    assert gateway.display_name_en is None


def test_deferred_metadata_save_and_empty_update_fields(django_assert_num_queries):
    gateway = G(Gateway)
    deferred = Gateway.objects.only("id", "description").get(pk=gateway.pk)
    deferred.description = "new"
    with django_assert_num_queries(1):
        deferred.save()
    with django_assert_num_queries(0):
        deferred.save(update_fields=[])
    gateway.refresh_from_db()
    assert gateway.description == "new"


def test_refresh_allows_later_name_change():
    gateway = G(Gateway, display_name="Initial")
    gateway.refresh_from_db()
    gateway.display_name = "Updated"
    gateway.save()
    gateway.refresh_from_db()
    assert gateway.display_name == "Updated"


@pytest.mark.parametrize("field", ["display_name", "display_name_en"])
def test_database_column_uniqueness(field):
    first = G(Gateway, **{field: "Unique Name"})
    second = G(Gateway)
    with pytest.raises(IntegrityError), transaction.atomic():
        Gateway.objects.filter(pk=second.pk).update(**{field: getattr(first, field)})
    assert Gateway.objects.filter(display_name_en=None).count() >= (2 if field == "display_name" else 1)


def test_explicit_deferred_name_save():
    gateway = G(Gateway, display_name="Explicit Deferred")
    deferred = Gateway.objects.only("id", "description").get(pk=gateway.pk)
    deferred.save(update_fields=["display_name"])
    gateway.refresh_from_db()
    assert gateway.display_name == "Explicit Deferred"


def test_explicit_names_are_not_suppressed_on_stale_instance():
    gateway = G(Gateway, display_name="Original")
    stale = Gateway.objects.get(pk=gateway.pk)
    gateway.display_name = "Changed"
    gateway.save(update_fields=["display_name"])
    stale.save(update_fields=["display_name"])
    gateway.refresh_from_db()
    assert gateway.display_name == "Original"


def test_partial_refresh_preserves_pending_name_change():
    gateway = G(Gateway, display_name="Original")
    gateway.display_name = "Pending"
    gateway.refresh_from_db(fields=["description"])
    gateway.save()
    gateway.refresh_from_db()
    assert gateway.display_name == "Pending"


def test_named_fields_omitted_by_update_fields_are_not_written():
    gateway = G(Gateway, display_name="Original")
    gateway.display_name = "Pending"
    gateway.description = "metadata"
    gateway.save(update_fields=["description"])
    gateway.save()
    gateway.refresh_from_db()
    assert gateway.display_name == "Pending"


def test_blank_display_name_uses_name():
    assert validate_display_name(" ", name="gateway-name") == "gateway-name"


def test_manually_constructed_primary_key_can_insert():
    gateway = N(Gateway, id=987654, name="manual-primary-key")
    gateway.save()
    assert Gateway.objects.get(pk=987654).display_name == "manual-primary-key"


def test_positional_save_arguments_preserve_explicit_update_fields():
    gateway = G(Gateway, display_name="Before")
    gateway.display_name = "After"
    gateway.description = "Must not be written"
    gateway.save(False, False, None, ["display_name"])
    gateway.refresh_from_db()
    assert gateway.display_name == "After"
    assert gateway.description != "Must not be written"


def test_lower_comparison_does_not_expand_german_sharp_s():
    G(Gateway, name="existing", display_name="Straße")
    assert validate_display_name("STRASSE", name="candidate", gateways=Gateway.objects.all()) == "STRASSE"


@pytest.mark.parametrize("display_name,expected_rows", [("TAKEN", 1), ("Unrelated %", 0), ("Unrelated _", 0)])
def test_display_name_lookup_reads_at_most_one_row(display_name, expected_rows):
    Gateway.objects.bulk_create(
        [Gateway(name=f"unrelated-{i}", display_name=f"Unrelated {i}", status=1) for i in range(100)]
    )
    G(Gateway, name="taken-gateway", display_name="Taken")
    with CaptureQueriesContext(connection) as queries:
        try:
            validate_display_name(display_name, name="candidate", gateways=Gateway.objects.all())
        except ValidationError:
            assert expected_rows == 1
        else:
            assert expected_rows == 0
    assert len(queries) == 1
    # Verify the DB result size, not just the number of SQL statements.
    with connection.cursor() as cursor:
        cursor.execute(queries[0]["sql"])
        assert len(cursor.fetchall()) == expected_rows


def test_display_names_are_trimmed():
    assert validate_display_name(" ", name="\t gateway-name \u3000") == "gateway-name"
    assert validate_display_name("\t New  Name \u3000", name="gateway-name") == "New  Name"
    assert validate_display_name_en(" English ") == "English"


def test_implicit_model_save_keeps_django_insert_fallback():
    gateway = G(Gateway, name="recreated")
    Gateway.objects.filter(pk=gateway.pk).delete()
    gateway.description = "recreated after deletion"
    gateway.save()
    assert Gateway.objects.get(pk=gateway.pk).description == gateway.description
