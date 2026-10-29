from unittest.mock import MagicMock

import pytest
from django.db import IntegrityError
from django.utils.translation import override, trans_real
from django_dynamic_fixture import G

from apigateway.apis.open.gateway.serializers import GatewaySyncInputSLZ as V1GatewaySyncInputSLZ
from apigateway.apis.v2.sync.serializers import GatewaySyncInputSLZ as V2GatewaySyncInputSLZ
from apigateway.common.error_codes import error_codes
from apigateway.common.exception_handler import custom_exception_handler
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


def test_sync_clear_english_allows_duplicate_fallback(request_view, sync_view, default_data_plane, mocker):
    gateway = G(
        Gateway, name="sync-gateway", display_name="Shared", display_name_en="Own English", description="before"
    )
    G(Gateway, display_name="Other", display_name_en="Shared", tenant_id="other", is_public=False, status=0)
    auth = mocker.patch("apigateway.biz.gateway.gateway.GatewayHandler.save_auth_config")
    response = call_sync(
        request_view, sync_view, gateway.name, {"description": "changed", "maintainers": ["new-admin"]}, gateway
    )
    assert response.status_code == 200, response.json()
    gateway.refresh_from_db()
    assert gateway.display_name_en is None
    assert gateway.description == "changed"
    auth.assert_called_once()


@pytest.mark.parametrize("column", ["display_name", "display_name_en"])
def test_sync_database_error_uses_general_error_handler(request_view, sync_view, default_data_plane, mocker, column):
    gateway = G(Gateway, name="sync-gateway")
    mocker.patch(
        "apigateway.biz.gateway.gateway.GatewaySaver.save",
        side_effect=IntegrityError(f"UNIQUE constraint failed: core_api.{column}"),
    )
    response = call_sync(request_view, sync_view, gateway.name, {}, gateway)
    assert response.status_code == 500, response.json()
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


@pytest.mark.parametrize("serializer", [V1GatewaySyncInputSLZ, V2GatewaySyncInputSLZ])
@pytest.mark.parametrize("column", ["display_name", "display_name_en"])
def test_queryset_conflict_uses_active_translation(monkeypatch, column, serializer):
    catalog = trans_real.DjangoTranslation("zh-cn")
    catalog._catalog["This display name is already in use."] = "展示名已被使用。"
    monkeypatch.setitem(trans_real._translations, "zh-cn", catalog)
    G(Gateway, **{column: "Taken"})
    slz = serializer(data={"name": "candidate", column: "Taken"})
    with override("zh-cn"):
        assert not slz.is_valid()
        assert str(slz.errors[column][0]) == "展示名已被使用。"


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
def test_database_errors_return_general_error(error):
    response = custom_exception_handler(error, {})
    assert response.status_code == 500
    assert str(error) not in str(response.data)


def test_sync_fallback_conflict_requires_explicit_available_display_name(request_view, sync_view, default_data_plane):
    G(Gateway, name="existing-gateway", display_name="foo-gateway")
    response = call_sync(request_view, sync_view, "foo-gateway", {})
    assert response.status_code == 400, response.json()
    assert not Gateway.objects.filter(name="foo-gateway").exists()
    response = call_sync(request_view, sync_view, "foo-gateway", {"display_name": "Other Display"})
    assert response.status_code == 200, response.json()
    assert Gateway.objects.get(name="foo-gateway").display_name == "Other Display"


@pytest.mark.parametrize("field", ["display_name", "display_name_en"])
def test_sync_queryset_conflict_precedes_save(request_view, sync_view, default_data_plane, mocker, field):
    gateway = G(Gateway, name="sync-gateway", display_name="Original")
    G(Gateway, **{field: "Taken"})
    save = mocker.patch("apigateway.biz.gateway.gateway.GatewaySaver.save")
    response = call_sync(request_view, sync_view, gateway.name, {field: "Taken"}, gateway)
    assert response.status_code == 400, response.json()
    save.assert_not_called()
    gateway.refresh_from_db()
    assert gateway.display_name == "Original"


@pytest.mark.parametrize("serializer", [V1GatewaySyncInputSLZ, V2GatewaySyncInputSLZ])
def test_sync_omitted_display_names_need_no_validation_queries(django_assert_num_queries, serializer):
    gateway = G(Gateway, name="sync-gateway", display_name="Current", display_name_en="English")
    slz = serializer(gateway, data={"name": gateway.name})
    with django_assert_num_queries(0):
        assert slz.is_valid(), slz.errors
    assert "display_name" not in slz.validated_data
    assert "display_name_en" not in slz.validated_data


@pytest.mark.parametrize("serializer", [V1GatewaySyncInputSLZ, V2GatewaySyncInputSLZ])
def test_sync_english_update_only_queries_english(django_assert_num_queries, serializer):
    gateway = G(Gateway, name="sync-gateway", display_name="Current")
    slz = serializer(gateway, data={"name": gateway.name, "display_name_en": " New English "})
    with django_assert_num_queries(1):
        assert slz.is_valid(), slz.errors
    assert "display_name" not in slz.validated_data
    assert slz.validated_data["display_name_en"] == "New English"


@pytest.mark.parametrize("serializer", [V1GatewaySyncInputSLZ, V2GatewaySyncInputSLZ])
@pytest.mark.parametrize("field", ["display_name", "display_name_en"])
def test_same_field_conflicts_are_global(serializer, field):
    G(Gateway, tenant_id="other-tenant", status=0, is_public=False, is_deprecated=True, **{field: "Asset Hub"})
    slz = serializer(data={"name": "candidate", field: " ASSET HUB "})
    assert not slz.is_valid()
    assert slz.errors[field][0].code == "unique"
