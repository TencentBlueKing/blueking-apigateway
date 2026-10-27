import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.translation import override
from django_dynamic_fixture import G

from apigateway.apis.web.gateway.serializers import GatewayUpdateInputSLZ
from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.core.models import Gateway
from apigateway.service.contexts import GatewayAuthContext
from apigateway.service.gateway_jwt import GatewayJWTHandler


def _user(username="ordinary", tenant_id="default"):
    user = get_user_model()(username=username, is_superuser=False, is_active=True)
    user.tenant_id = tenant_id
    return user


def _member(gateway, role=GatewayRoleEnum.ADMINISTRATOR.value):
    GatewayMember.objects.update_or_create(gateway=gateway, username="ordinary", defaults={"role": role})
    return _user()


@pytest.mark.parametrize(
    "value,expected", [(None, "web-display"), (" ", "web-display"), (" New Default ", "New Default")]
)
def test_create_default_and_ignore_english(request_view, default_data_plane, value, expected):
    response = request_view(
        method="POST",
        view_name="gateways.list_create",
        data={
            "name": "web-display",
            "display_name": value,
            "display_name_en": "Ignored English",
            "tenant_mode": "single",
            "tenant_id": "default",
        },
    )
    assert response.status_code == 201, response.json()
    gateway = Gateway.objects.get(name="web-display")
    assert gateway.display_name == expected
    assert gateway.display_name_en is None


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
@pytest.mark.parametrize(
    "payload,expected",
    [
        ({}, "Before"),
        ({"display_name": None}, "web-display"),
        ({"display_name": " "}, "web-display"),
        ({"display_name": " New Default "}, "New Default"),
    ],
)
def test_update_default_in_english_and_preserve_english(request_view, method, payload, expected):
    gateway = G(Gateway, name="web-display", display_name="Before", display_name_en="English")
    user = _member(gateway)
    with override("en"):
        response = request_view(
            method=method,
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": gateway.pk},
            data={**payload, "display_name_en": "Ignored English"},
            user=user,
        )
    assert response.status_code == 204, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name == expected
    assert gateway.display_name_en == "English"


@pytest.mark.parametrize("language,expected", [("en", "English"), ("zh-cn", "默认名")])
def test_list_and_detail_localized(request_view, language, expected):
    gateway = G(Gateway, display_name="默认名", display_name_en="English", tenant_mode="single", tenant_id="default")
    user = _member(gateway)
    GatewayJWTHandler.create_jwt(gateway)
    GatewayAuthContext().save(gateway.pk, {"user_auth_type": "default"})
    with override(language):
        response = request_view(method="GET", view_name="gateways.list_create", user=user)
        assert response.status_code == 200
        assert response.json()["data"]["results"][0]["display_name"] == expected
        response = request_view(
            method="GET",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": gateway.pk},
            user=user,
        )
        assert response.status_code == 200, response.json()
        assert response.json()["data"]["display_name"] == expected


@pytest.mark.parametrize("keyword", ["默认", "English"])
def test_keyword_matches_both_raw_names(request_view, keyword):
    gateway = G(Gateway, display_name="默认名", display_name_en="English", tenant_mode="single", tenant_id="default")
    user = _member(gateway)
    response = request_view(method="GET", view_name="gateways.list_create", data={"keyword": keyword}, user=user)
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]["results"]] == [gateway.pk]


@pytest.mark.parametrize("field,value", [("display_name", "Taken"), ("display_name_en", "Taken")])
def test_technical_name_precheck_reserves_display_names(request_view, field, value):
    G(Gateway, **{field: value})
    response = request_view(method="GET", view_name="gateways.check_name_available", data={"name": "taken"})
    assert response.status_code == 200
    assert response.json()["data"] == {"is_available": False}


@pytest.mark.parametrize(
    "role,expected", [(None, 403), (GatewayRoleEnum.OPERATOR.value, 403), (GatewayRoleEnum.ADMINISTRATOR.value, 200)]
)
def test_preview_checks_actual_manage_permission_before_excluding_self(request_view, role, expected):
    gateway = G(Gateway, display_name="Own")
    if role:
        _member(gateway, role)
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=_user(),
        data={"gateway_id": gateway.pk, "display_name": "Own"},
    )
    assert response.status_code == expected, response.json()
    if expected == 200:
        assert response.json()["data"] == {"is_available": True, "conflicts": []}


def test_preview_rejects_cross_tenant_even_for_member(request_view, settings):
    settings.ENABLE_MULTI_TENANT_MODE = True
    gateway = G(Gateway, tenant_mode="single", tenant_id="other")
    user = _member(gateway)
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=user,
        data={"gateway_id": gateway.pk, "display_name": "Own"},
    )
    assert response.status_code == 403, response.json()


def test_preview_fallback_conflict_has_no_private_details(request_view):
    private = G(Gateway, name="private-technical", display_name="Other", display_name_en="Shared", tenant_id="other")
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=_user(),
        data={"name": "new-technical", "display_name": "Shared"},
    )
    assert response.status_code == 200, response.json()
    data = response.json()["data"]
    assert data["is_available"] is False
    assert {"field": "display_name", "language": "en", "reason": "english_fallback_conflict"} in data["conflicts"]
    assert private.name not in str(data)


@pytest.mark.parametrize("length", [64, 65])
def test_default_name_length_on_create_and_update(request_view, default_data_plane, length):
    response = request_view(
        method="POST",
        view_name="gateways.list_create",
        data={"name": "web-display", "display_name": "A" * length, "tenant_mode": "single", "tenant_id": "default"},
    )
    assert response.status_code == (201 if length == 64 else 400), response.json()
    gateway = G(Gateway, name="another-web", display_name="Before")
    response = request_view(
        method="PATCH",
        view_name="gateways.retrieve_update_destroy",
        path_params={"gateway_id": gateway.pk},
        data={"display_name": "B" * length},
        user=_member(gateway),
    )
    assert response.status_code == (204 if length == 64 else 400), response.json()


def test_preview_preserves_english_unless_explicitly_cleared(request_view):
    gateway = G(Gateway, display_name="Shared", display_name_en="Own English")
    user = _member(gateway)
    G(Gateway, display_name="Other", display_name_en="Shared")
    for extra, expected in [({}, True), ({"display_name_en": None}, False)]:
        response = request_view(
            method="POST",
            view_name="gateways.check_display_name_available",
            user=user,
            data={"gateway_id": gateway.pk, "name": "ignored-rename", "display_name": "Shared", **extra},
        )
        assert response.status_code == 200, response.json()
        assert response.json()["data"]["is_available"] is expected
    gateway.refresh_from_db()
    assert gateway.display_name_en == "Own English"


@pytest.mark.parametrize(
    "data", [{"name": "candidate", "display_name_en": "Bad_English"}, {"name": "candidate", "display_name": "A" * 65}]
)
def test_preview_format_errors_are_parameter_errors(request_view, data):
    response = request_view(method="POST", view_name="gateways.check_display_name_available", user=_user(), data=data)
    assert response.status_code == 400, response.json()
    assert response.json()["error"]["code"] == "INVALID_ARGUMENT"


def test_name_update_tenant_check_does_not_expand_to_metadata_updates(request_view, settings):
    settings.ENABLE_MULTI_TENANT_MODE = True
    gateway = G(Gateway, tenant_mode="single", tenant_id="other")
    user = _member(gateway)
    for payload, expected in [({"display_name": "Change"}, 403), ({"description": "Metadata"}, 204)]:
        response = request_view(
            method="PATCH",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": gateway.pk},
            data=payload,
            user=user,
        )
        assert response.status_code == expected, response.json()


def test_name_conflict_precedes_programmable_paas_creation(request_view, mocker):
    G(Gateway, display_name="Taken")
    occupied = mocker.patch("apigateway.apis.web.gateway.validators.is_app_code_occupied", return_value=False)
    paas = mocker.patch("apigateway.apis.web.gateway.views.create_paas_app")
    response = request_view(
        method="POST",
        view_name="gateways.list_create",
        data={
            "name": "prog-name",
            "display_name": "Taken",
            "kind": 1,
            "tenant_mode": "single",
            "tenant_id": "default",
        },
    )
    assert response.status_code == 400, response.json()
    occupied.assert_called_once()
    paas.assert_not_called()


def test_explicit_stale_default_input_is_not_suppressed():
    gateway = G(Gateway, display_name="Original", display_name_en="English")
    stale = Gateway.objects.get(pk=gateway.pk)
    gateway.display_name = "Current"
    gateway.save(update_fields=["display_name"])
    slz = GatewayUpdateInputSLZ(stale, data={"display_name": "Original"}, partial=True)
    assert slz.is_valid(), slz.errors
    slz.save()
    gateway.refresh_from_db()
    assert gateway.display_name == "Original"
    assert gateway.display_name_en == "English"


def test_omitted_default_preserves_current_database_value():
    gateway = G(Gateway, display_name="Original")
    stale = Gateway.objects.get(pk=gateway.pk)
    gateway.display_name = "Current"
    gateway.save(update_fields=["display_name"])
    slz = GatewayUpdateInputSLZ(stale, data={"description": "Metadata"}, partial=True)
    assert slz.is_valid(), slz.errors
    slz.save()
    gateway.refresh_from_db()
    assert gateway.display_name == "Current"


@pytest.mark.parametrize("column", ["display_name", "display_name_en"])
def test_web_known_index_race_is_sanitized(request_view, mocker, column):
    gateway = G(Gateway)
    user = _member(gateway)
    mocker.patch(
        "apigateway.core.models.Gateway.save",
        side_effect=IntegrityError(f"UNIQUE constraint failed: core_api.{column}"),
    )
    response = request_view(
        method="PATCH",
        view_name="gateways.retrieve_update_destroy",
        path_params={"gateway_id": gateway.pk},
        data={"display_name": "New"},
        user=user,
    )
    assert response.status_code == 400, response.json()
    assert response.json()["error"]["code"] == "INVALID_ARGUMENT"
    assert "UNIQUE constraint" not in str(response.json())


def test_web_unrelated_database_error_is_not_a_naming_error(request_view, mocker):
    gateway = G(Gateway)
    user = _member(gateway)
    mocker.patch("apigateway.core.models.Gateway.save", side_effect=IntegrityError("unrelated database failure"))
    response = request_view(
        method="PATCH",
        view_name="gateways.retrieve_update_destroy",
        path_params={"gateway_id": gateway.pk},
        data={"display_name": "New"},
        user=user,
    )
    assert response.status_code == 500, response.json()
    assert response.json()["error"]["code"] == "UNKNOWN"


def test_web_update_rolls_back_name_if_later_binding_update_fails(request_view, mocker):
    gateway = G(Gateway, display_name="Before")
    user = _member(gateway)
    mocker.patch(
        "apigateway.apis.web.gateway.views.GatewayAppBindingHandler.update_gateway_app_bindings",
        side_effect=RuntimeError("binding failure"),
    )
    response = request_view(
        method="PATCH",
        view_name="gateways.retrieve_update_destroy",
        path_params={"gateway_id": gateway.pk},
        data={"display_name": "After", "bk_app_codes": ["app"]},
        user=user,
    )
    assert response.status_code == 500, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name == "Before"


@pytest.mark.parametrize("role", [None, GatewayRoleEnum.OPERATOR.value])
def test_name_update_requires_real_management_role(request_view, role):
    gateway = G(Gateway, display_name="Before")
    if role is not None:
        _member(gateway, role)
    response = request_view(
        method="PATCH",
        view_name="gateways.retrieve_update_destroy",
        path_params={"gateway_id": gateway.pk},
        data={"display_name": "After"},
        user=_user(),
    )
    assert response.status_code == 403, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name == "Before"


def test_default_change_checks_english_fallback_globally(request_view):
    gateway = G(Gateway, display_name="Before")
    G(Gateway, display_name="Other", display_name_en="Taken", tenant_id="other", status=0, is_public=False)
    response = request_view(
        method="PATCH",
        view_name="gateways.retrieve_update_destroy",
        path_params={"gateway_id": gateway.pk},
        data={"display_name": "Taken", "description": "changed"},
        user=_member(gateway),
    )
    assert response.status_code == 400, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name == "Before"
    assert gateway.description != "changed"
