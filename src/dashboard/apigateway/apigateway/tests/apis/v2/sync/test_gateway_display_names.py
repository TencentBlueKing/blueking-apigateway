from unittest.mock import MagicMock

import pytest
from django.db import IntegrityError
from django.utils.translation import override, trans_real
from django_dynamic_fixture import G
from rest_framework.exceptions import ValidationError

from apigateway.apis.gateway_name import gateway_name_validation_errors
from apigateway.apis.open.gateway.serializers import GatewaySyncInputSLZ as V1GatewaySyncInputSLZ
from apigateway.apis.v2.sync.serializers import GatewaySyncInputSLZ as V2GatewaySyncInputSLZ
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Gateway
from apigateway.service.contexts import GatewayAuthContext


@pytest.fixture(params=["openapi.gateway.sync", "openapi.v2.sync.gateway.sync"])
def sync_view(request, mocker):
    mocker.patch(
        "apigateway.apis.open.gateway.views.OpenAPIGatewayRelatedAppPermission.has_permission", return_value=True
    )
    mocker.patch(
        "apigateway.apis.v2.permissions.OpenAPIV2GatewayRelatedAppPermission.has_permission", return_value=True
    )
    return request.param


def call_sync(request_view, sync_view, name, data, gateway=None):
    if gateway is not None:
        GatewayAuthContext().save(gateway.id, {"user_auth_type": "default"})
    return request_view(
        method="POST",
        view_name=sync_view,
        path_params={"gateway_name": name},
        data=data,
        gateway=gateway,
        app=MagicMock(app_code="foo"),
    )


@pytest.mark.parametrize("data", [{}, {"display_name": None}, {"display_name": " "}])
def test_sync_creation_defaults(request_view, sync_view, default_data_plane, unique_gateway_name, data):
    response = call_sync(request_view, sync_view, unique_gateway_name, data)
    assert response.status_code == 200, response.json()
    gateway = Gateway.objects.get(name=unique_gateway_name)
    assert gateway.display_name == unique_gateway_name
    assert gateway.display_name_en is None
    assert response.json()["data"]["display_name"] == unique_gateway_name


@pytest.mark.parametrize(
    "data,expected",
    [
        ({}, "Default"),
        ({"display_name": None}, "sync-gateway"),
        ({"display_name": " "}, "sync-gateway"),
        ({"display_name": " New Default "}, "New Default"),
    ],
)
def test_sync_update_omission_and_clear(request_view, sync_view, default_data_plane, data, expected):
    gateway = G(Gateway, name="sync-gateway", display_name="Default", display_name_en="English")
    response = call_sync(request_view, sync_view, gateway.name, data, gateway)
    assert response.status_code == 200, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name == expected
    assert gateway.display_name_en is None


def test_sync_english_and_localized_response(request_view, sync_view, default_data_plane):
    gateway = G(Gateway, name="sync-gateway", display_name="Default")
    with override("en"):
        response = call_sync(request_view, sync_view, gateway.name, {"display_name_en": " English  Name-2 "}, gateway)
    assert response.status_code == 200, response.json()
    assert response.json()["data"]["display_name"] == "English  Name-2"
    gateway.refresh_from_db()
    assert gateway.display_name == "Default"
    assert gateway.display_name_en == "English  Name-2"


@pytest.mark.parametrize("value", ["中文", "1Name", "Name_1", "A" * 65])
def test_sync_english_validation(request_view, sync_view, default_data_plane, value):
    gateway = G(Gateway, name="sync-gateway", display_name_en="Before")
    response = call_sync(
        request_view, sync_view, gateway.name, {"display_name_en": value, "description": "changed"}, gateway
    )
    assert response.status_code == 400, response.json()
    body = response.json()
    if "code" in body:
        assert body["result"] is False
        assert body["code"] == error_codes.INVALID_ARGUMENT.code.as_json(True)["code"]
    else:
        assert body["error"]["code"] == "INVALID_ARGUMENT"
    gateway.refresh_from_db()
    assert gateway.display_name_en == "Before"
    assert gateway.description != "changed"


def test_sync_fallback_conflict_rolls_back_before_side_effects(request_view, sync_view, default_data_plane, mocker):
    gateway = G(
        Gateway, name="sync-gateway", display_name="Shared", display_name_en="Own English", description="before"
    )
    G(Gateway, display_name="Other", display_name_en="Shared", tenant_id="other", is_public=False, status=0)
    auth = mocker.patch("apigateway.biz.gateway.gateway.GatewayHandler.save_auth_config")
    response = call_sync(
        request_view, sync_view, gateway.name, {"description": "changed", "maintainers": ["new-admin"]}, gateway
    )
    assert response.status_code == 400, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name_en == "Own English"
    assert gateway.description == "before"
    auth.assert_not_called()


@pytest.mark.parametrize("column", ["display_name", "display_name_en"])
def test_sync_known_index_race_maps_to_parameter_error(request_view, sync_view, default_data_plane, mocker, column):
    gateway = G(Gateway, name="sync-gateway")
    mocker.patch(
        "apigateway.biz.gateway.gateway.GatewaySaver.save",
        side_effect=IntegrityError(f"UNIQUE constraint failed: core_api.{column}"),
    )
    response = call_sync(request_view, sync_view, gateway.name, {}, gateway)
    assert response.status_code == 400, response.json()
    assert "UNIQUE constraint" not in str(response.json())


@pytest.mark.parametrize("field", ["display_name", "display_name_en"])
@pytest.mark.parametrize("length", [64, 65])
def test_sync_display_name_length(request_view, sync_view, default_data_plane, field, length):
    gateway = G(Gateway, name="sync-gateway")
    response = call_sync(request_view, sync_view, gateway.name, {field: "A" * length}, gateway)
    assert response.status_code == (200 if length == 64 else 400), response.json()
    gateway.refresh_from_db()
    if length == 64:
        assert getattr(gateway, field) == "A" * 64


@pytest.mark.parametrize("english", [None, "", "  "])
def test_sync_explicit_english_clear(request_view, sync_view, default_data_plane, english):
    gateway = G(Gateway, name="sync-gateway", display_name_en="Before English")
    response = call_sync(request_view, sync_view, gateway.name, {"display_name_en": english}, gateway)
    assert response.status_code == 200, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name_en is None


def test_sync_self_name_reuse(request_view, sync_view, default_data_plane):
    gateway = G(Gateway, name="sync-gateway")
    response = call_sync(
        request_view, sync_view, gateway.name, {"display_name": gateway.name, "display_name_en": gateway.name}, gateway
    )
    assert response.status_code == 200, response.json()


@pytest.mark.parametrize("serializer", [V1GatewaySyncInputSLZ, V2GatewaySyncInputSLZ])
def test_sync_serializer_preserves_default_omission(serializer):
    gateway = G(Gateway, name="sync-gateway", display_name="Current", display_name_en="English")
    slz = serializer(gateway, data={"name": gateway.name})
    assert slz.is_valid(), slz.errors
    assert "display_name" not in slz.validated_data
    assert "display_name_en" not in slz.validated_data


@pytest.mark.parametrize(
    "key",
    [
        "core_api.display_name",
        "core_api.display_name_en",
        "core_api_display_name_1234abcd_uniq",
        "core_api.core_api_display_name_en_1234abcd_uniq",
    ],
)
def test_mysql_display_name_unique_error_is_sanitized(key):
    with pytest.raises(ValidationError) as exc, gateway_name_validation_errors():
        raise IntegrityError(1062, f"Duplicate entry 'private-value' for key '{key}'")
    assert "private-value" not in str(exc.value)
    assert "already in use" in str(exc.value)


@pytest.mark.parametrize("column", ["display_name", "display_name_en"])
def test_index_conflict_uses_active_translation(monkeypatch, column):
    catalog = trans_real.DjangoTranslation("zh-cn")
    catalog._catalog["This display name is already in use."] = "展示名已被使用。"
    monkeypatch.setitem(trans_real._translations, "zh-cn", catalog)
    with override("zh-cn"), pytest.raises(ValidationError) as exc, gateway_name_validation_errors():
        raise IntegrityError(f"UNIQUE constraint failed: core_api.{column}")
    assert str(exc.value.detail[column]) == "展示名已被使用。"


@pytest.mark.parametrize(
    "error",
    [
        IntegrityError("UNIQUE constraint failed: core_api.name"),
        IntegrityError("NOT NULL constraint failed: core_api.display_name"),
        IntegrityError(1062, "Duplicate entry 'value' for key 'another_table.display_name'"),
        IntegrityError(1062, "Duplicate entry 'value' for key 'display_name'"),
        IntegrityError(1062, "Duplicate entry 'value' for key 'core_api.name'"),
    ],
)
def test_unrelated_database_errors_propagate(error):
    with pytest.raises(IntegrityError) as exc, gateway_name_validation_errors():
        raise error
    assert exc.value is error
