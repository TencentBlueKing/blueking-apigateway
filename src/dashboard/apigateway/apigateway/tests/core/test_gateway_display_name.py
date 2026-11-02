import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import override
from django_dynamic_fixture import G

from apigateway.core.gateway_name import normalize_display_name, normalize_display_name_en
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("value", [None, "", "  "])
def test_creation_defaults(value):
    assert normalize_display_name(value, name="gateway-name") == "gateway-name"
    assert normalize_display_name_en(value) is None


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
            normalize_display_name(gateway.display_name, name=gateway.name)
        else:
            normalize_display_name_en(gateway.display_name_en)
    assert exc.value.code == "max_length"


@pytest.mark.parametrize("value", ["中文", "Name_1", "1Name", "Name!", "Name\nOther"])
def test_english_characters(value):
    with pytest.raises(ValidationError) as exc:
        normalize_display_name_en(value)
    assert exc.value.code == "invalid"


def test_english_allowed_characters():
    assert G(Gateway, display_name_en="Name 12- X").display_name_en == "Name 12- X"


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


@pytest.mark.parametrize("field", ["display_name", "display_name_en"])
def test_database_column_uniqueness(field):
    first = G(Gateway, **{field: "Unique Name"})
    second = G(Gateway)
    with pytest.raises(IntegrityError), transaction.atomic():
        Gateway.objects.filter(pk=second.pk).update(**{field: getattr(first, field)})
    assert Gateway.objects.filter(display_name_en=None).count() >= (2 if field == "display_name" else 1)


def test_blank_display_name_uses_name():
    assert normalize_display_name(" ", name="gateway-name") == "gateway-name"


def test_display_names_are_trimmed():
    assert normalize_display_name(" ", name="\t gateway-name \u3000") == "gateway-name"
    assert normalize_display_name("\t New  Name \u3000", name="gateway-name") == "New  Name"
    assert normalize_display_name_en(" English ") == "English"


@pytest.mark.parametrize("language,english", [("zh-cn", None), ("en", None), ("en", "English")])
def test_display_name_read_fallback(language, english):
    gateway = G(Gateway, display_name=None, display_name_en=english)
    with override(language):
        assert gateway.display_name_or_name == (english if language == "en" and english else gateway.name)
    gateway.refresh_from_db()
    assert gateway.display_name is None
