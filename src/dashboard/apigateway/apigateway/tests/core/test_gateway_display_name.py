import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import override
from django_dynamic_fixture import G, N

from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("value", [None, "", "  "])
def test_creation_defaults(value):
    gateway = G(Gateway, name="fixture_technical_name", display_name=value, display_name_en=value)
    gateway.refresh_from_db()
    assert gateway.display_name == gateway.name
    assert gateway.display_name_en is None


def test_fixture_and_localization():
    fixture = G(Gateway)
    assert fixture.display_name == fixture.name
    gateway = G(Gateway, display_name="  默认  名称  ", display_name_en=" English  Name ")
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
        gateway.save(update_fields=[field])
    assert field in exc.value.message_dict


@pytest.mark.parametrize("value", ["中文", "Name_1", "1Name", "Name!", "Name\nOther"])
def test_english_characters(value):
    with pytest.raises(ValidationError) as exc:
        N(Gateway, display_name_en=value).save()
    assert "display_name_en" in exc.value.message_dict


def test_english_allowed_characters():
    assert G(Gateway, display_name_en="Name 12- X").display_name_en == "Name 12- X"


@pytest.mark.parametrize(
    "existing,candidate,field",
    [
        ({"display_name": "Straße"}, {"display_name": " STRASSE "}, "display_name"),
        ({"display_name_en": "English"}, {"display_name_en": "english"}, "display_name_en"),
        ({"display_name": "English"}, {"display_name_en": "English"}, "display_name_en"),
        ({"display_name_en": "English"}, {"display_name": "English"}, "display_name"),
        ({"name": "technical"}, {"display_name": "TECHNICAL"}, "display_name"),
        ({"name": "technical"}, {"display_name_en": "TECHNICAL"}, "display_name_en"),
        ({"display_name": "Technical"}, {"name": "technical"}, "name"),
        ({"display_name_en": "Technical"}, {"name": "technical"}, "name"),
    ],
)
def test_global_conflicts(existing, candidate, field):
    G(Gateway, tenant_id="other-tenant", status=0, is_public=False, is_deprecated=True, **existing)
    with pytest.raises(ValidationError) as exc:
        N(Gateway, **candidate).save()
    assert field in exc.value.message_dict


def test_cross_language_overlap_allowed_when_effective_names_differ():
    G(Gateway, display_name="Default One", display_name_en="English One")
    gateway = G(Gateway, display_name="English One", display_name_en="Default One")
    gateway.save()
    assert gateway.display_name == "English One"


def test_self_name_reuse_and_english_fallback_conflict():
    gateway = G(Gateway, name="own-name", display_name="own-name", display_name_en="own-name")
    gateway.save()
    G(Gateway, display_name="Other Default", display_name_en="own-name-two")
    gateway.display_name = "own-name-two"
    gateway.save(update_fields=["display_name"])
    gateway.display_name_en = None
    with pytest.raises(ValidationError):
        gateway.save(update_fields=["display_name_en"])
    gateway.refresh_from_db()
    assert gateway.display_name_en == "own-name"


@pytest.mark.parametrize("fields", [None, ["description"]])
def test_stale_metadata_save_preserves_names(fields, django_assert_num_queries):
    gateway = G(Gateway, display_name="Before", display_name_en="Before English")
    stale = Gateway.objects.get(pk=gateway.pk)
    gateway.display_name = "After"
    gateway.save(update_fields=["display_name"])
    stale.description = "metadata"
    with django_assert_num_queries(1):
        stale.save(update_fields=fields)
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
    with pytest.raises(ValidationError):
        stale.save(update_fields=["display_name_en"])


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


def test_blank_default_name_resets_to_technical_name():
    gateway = G(Gateway, name="own-technical", display_name="Original", display_name_en="English")
    gateway.display_name = " "
    gateway.save(update_fields=["display_name"])
    gateway.refresh_from_db()
    assert gateway.display_name == "own-technical"
    assert gateway.display_name_en == "English"
