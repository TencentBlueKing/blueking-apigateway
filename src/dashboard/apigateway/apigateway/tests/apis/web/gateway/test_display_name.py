import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.translation import override
from django_dynamic_fixture import G

from apigateway.apis.gateway_name import validate_web_gateway_names
from apigateway.apis.open.gateway.serializers import GatewayUpdateStatusInputSLZ as OpenGatewayUpdateStatusInputSLZ
from apigateway.apis.web.gateway.serializers import GatewayUpdateInputSLZ, GatewayUpdateStatusInputSLZ
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
def test_keyword_search_excludes_english_display_name(request_view, keyword):
    gateway = G(Gateway, display_name="默认名", display_name_en="English", tenant_mode="single", tenant_id="default")
    user = _member(gateway)
    response = request_view(method="GET", view_name="gateways.list_create", data={"keyword": keyword}, user=user)
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]["results"]] == (
        [] if keyword == "English" else [gateway.pk]
    )


@pytest.mark.parametrize("field,value", [("display_name", "Taken"), ("display_name_en", "Taken")])
def test_technical_name_precheck_ignores_display_names(request_view, field, value):
    G(Gateway, **{field: value})
    response = request_view(method="GET", view_name="gateways.check_name_available", data={"name": "taken"})
    assert response.status_code == 200
    assert response.json()["data"] == {"is_available": True}


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
    assert response.status_code == expected, response.content
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


def test_preview_display_name_conflict_has_no_private_details(request_view):
    private = G(Gateway, name="private-technical", display_name="Shared", tenant_id="other")
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=_user(),
        data={"name": "new-technical", "display_name": "Shared"},
    )
    assert response.status_code == 200, response.json()
    data = response.json()["data"]
    assert data["is_available"] is False
    assert data["conflicts"] == [{"field": "display_name", "language": "default", "reason": "unique"}]
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


def test_preview_ignores_submitted_english_name(request_view):
    gateway = G(Gateway, display_name="Shared", display_name_en="Own English")
    user = _member(gateway)
    G(Gateway, display_name="Other", display_name_en="Shared")
    for extra in [
        {},
        {"display_name_en": None},
        {"display_name_en": "Shared"},
        {"display_name_en": "Bad_English"},
        {"display_name_en": "A" * 65},
    ]:
        response = request_view(
            method="POST",
            view_name="gateways.check_display_name_available",
            user=user,
            data={"gateway_id": gateway.pk, "name": "ignored-rename", "display_name": "Shared", **extra},
        )
        assert response.status_code == 200, response.json()
        assert response.json()["data"] == {"is_available": True, "conflicts": []}
    gateway.refresh_from_db()
    assert gateway.display_name_en == "Own English"


@pytest.mark.parametrize("data", [{"name": "candidate", "display_name": "A" * 65}])
def test_preview_format_errors_are_parameter_errors(request_view, data):
    response = request_view(method="POST", view_name="gateways.check_display_name_available", user=_user(), data=data)
    assert response.status_code == 400, response.json()
    assert response.json()["error"]["code"] == "INVALID_ARGUMENT"


@pytest.mark.parametrize("name", ["Uppercase", "under_score", "中文网关", "1gateway", "ab", "a" * 31])
def test_creation_preview_rejects_invalid_technical_names(request_view, name):
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=_user(),
        data={"name": name, "display_name": "Available Display"},
    )
    assert response.status_code == 400, response.json()
    assert response.json()["error"]["code"] == "INVALID_ARGUMENT"


def test_edit_preview_uses_persisted_name_instead_of_supplied_name(request_view):
    gateway = G(Gateway, name="existing-gateway", display_name="Own Display")
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=_member(gateway),
        data={"gateway_id": gateway.pk, "name": "Ignored_Invalid", "display_name": "Own Display"},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["data"] == {"is_available": True, "conflicts": []}


def test_all_gateway_updates_check_tenant(request_view, settings):
    settings.ENABLE_MULTI_TENANT_MODE = True
    gateway = G(Gateway, tenant_mode="single", tenant_id="other")
    user = _member(gateway)
    for payload, expected in [({"display_name": "Change"}, 403), ({"description": "Metadata"}, 403)]:
        response = request_view(
            method="PATCH",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": gateway.pk},
            data=payload,
            user=user,
        )
        assert response.status_code == expected, response.content


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
def test_web_database_error_uses_general_error_handler(request_view, mocker, column):
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
    assert response.status_code == 500, response.json()
    assert response.json()["error"]["code"] == "UNKNOWN"
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


def test_default_change_may_match_another_english_name(request_view):
    gateway = G(Gateway, display_name="Before")
    G(Gateway, display_name="Other", display_name_en="Taken", tenant_id="other", status=0, is_public=False)
    response = request_view(
        method="PATCH",
        view_name="gateways.retrieve_update_destroy",
        path_params={"gateway_id": gateway.pk},
        data={"display_name": "Taken", "description": "changed"},
        user=_member(gateway),
    )
    assert response.status_code == 204, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name == "Taken"
    assert gateway.description == "changed"


def test_display_name_preview_does_not_check_technical_name_availability(request_view):
    G(Gateway, name="existing-name", display_name="Other")
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=_user(),
        data={"name": "existing-name", "display_name": "Available"},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["data"] == {"is_available": True, "conflicts": []}


def test_create_fallback_conflict_requires_explicit_available_display_name(request_view, default_data_plane):
    G(Gateway, name="existing-gateway", display_name="foo-gateway")
    payload = {"name": "foo-gateway", "tenant_mode": "single", "tenant_id": "default"}
    response = request_view(method="POST", view_name="gateways.list_create", data=payload)
    assert response.status_code == 400, response.json()
    assert not Gateway.objects.filter(name="foo-gateway").exists()
    response = request_view(
        method="POST", view_name="gateways.list_create", data={**payload, "display_name": "Other Display"}
    )
    assert response.status_code == 201, response.json()
    assert Gateway.objects.get(name="foo-gateway").display_name == "Other Display"


@pytest.mark.parametrize("serializer", [GatewayUpdateStatusInputSLZ, OpenGatewayUpdateStatusInputSLZ])
def test_status_update_preserves_current_names(serializer):
    gateway = G(Gateway, display_name="Original", display_name_en="Original English")
    stale = Gateway.objects.get(pk=gateway.pk)
    Gateway.objects.filter(pk=gateway.pk).update(display_name="Current", display_name_en="Current English")
    slz = serializer(stale, data={"status": 0})
    assert slz.is_valid(), slz.errors
    slz.save(updated_by="ordinary")
    gateway.refresh_from_db()
    assert gateway.display_name == "Current"
    assert gateway.display_name_en == "Current English"
    assert gateway.status == 0
    assert gateway.updated_by == "ordinary"


def test_web_queryset_conflict_precedes_save(request_view, mocker):
    gateway = G(Gateway, display_name="Original")
    user = _member(gateway)
    G(Gateway, display_name="Taken")
    save = mocker.patch("apigateway.core.models.Gateway.save")
    response = request_view(
        method="PATCH",
        view_name="gateways.retrieve_update_destroy",
        path_params={"gateway_id": gateway.pk},
        data={"display_name": "Taken"},
        user=user,
    )
    assert response.status_code == 400, response.json()
    save.assert_not_called()
    gateway.refresh_from_db()
    assert gateway.display_name == "Original"


def test_web_display_name_update_only_queries_its_uniqueness(django_assert_num_queries):
    gateway = G(Gateway, display_name="Current", display_name_en="English")
    data = {"display_name": " New Display "}
    with django_assert_num_queries(1):
        validate_web_gateway_names(data, gateway)
    assert data == {"display_name": "New Display"}


def test_preview_reports_only_display_name_conflict(request_view):
    G(Gateway, display_name="Taken Display", display_name_en="Taken English")
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=_user(),
        data={"name": "candidate", "display_name": "Taken Display", "display_name_en": "Taken English"},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["data"] == {
        "is_available": False,
        "conflicts": [
            {"field": "display_name", "language": "default", "reason": "unique"},
        ],
    }


def test_preview_does_not_validate_stored_english_name(request_view):
    gateway = G(Gateway, display_name="Own Display", display_name_en="Legacy_English")
    response = request_view(
        method="POST",
        view_name="gateways.check_display_name_available",
        user=_member(gateway),
        data={"gateway_id": gateway.pk, "display_name": "Own Display"},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["data"] == {"is_available": True, "conflicts": []}
