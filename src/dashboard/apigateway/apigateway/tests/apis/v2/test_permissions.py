from unittest import mock

import pytest
from ddf import G
from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apigateway.apis.v2.permissions import OpenAPIV2GatewayNamePermission, OpenAPIV2Permission
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.models import Gateway


@pytest.mark.parametrize("permission_class", [OpenAPIV2Permission, OpenAPIV2GatewayNamePermission])
def test_openapi_permission_sets_tenant_id_in_multi_tenant_mode(settings, permission_class):
    settings.ENABLE_MULTI_TENANT_MODE = True
    gateway = G(Gateway, name="tenant-gateway", tenant_mode=TenantModeEnum.GLOBAL.value, tenant_id="")
    request = Request(
        APIRequestFactory().get(
            "/",
            HTTP_X_BK_TENANT_ID="tenant-a",
        )
    )
    request.app = mock.MagicMock(app_code="bk_auth")
    view = mock.MagicMock(kwargs={"gateway_name": gateway.name})

    assert permission_class().has_permission(request, view) is True
    assert request.tenant_id == "tenant-a"


def test_openapi_gateway_name_permission_sets_tenant_id_before_gateway_lookup(settings):
    settings.ENABLE_MULTI_TENANT_MODE = True
    request = Request(
        APIRequestFactory().get(
            "/",
            HTTP_X_BK_TENANT_ID="tenant-b",
        )
    )
    request.app = mock.MagicMock(app_code="bk_auth")
    view = mock.MagicMock(kwargs={"gateway_name": "missing-gateway"})

    permission = OpenAPIV2GatewayNamePermission()
    with pytest.raises(Http404):
        permission.has_permission(request, view)

    assert request.tenant_id == "tenant-b"


@pytest.mark.parametrize(
    ("gateway_tenant_mode", "gateway_tenant_id"),
    [
        (TenantModeEnum.GLOBAL.value, ""),
        (TenantModeEnum.SINGLE.value, "tenant-a"),
    ],
)
def test_openapi_gateway_name_permission_allows_visible_gateway(
    settings,
    gateway_tenant_mode,
    gateway_tenant_id,
):
    settings.ENABLE_MULTI_TENANT_MODE = True
    gateway = G(
        Gateway,
        name="visible-gateway",
        tenant_mode=gateway_tenant_mode,
        tenant_id=gateway_tenant_id,
    )
    request = Request(APIRequestFactory().get("/", HTTP_X_BK_TENANT_ID="tenant-a"))
    request.app = mock.MagicMock(app_code="bk_auth")
    view = mock.MagicMock(kwargs={"gateway_name": gateway.name})

    assert OpenAPIV2GatewayNamePermission().has_permission(request, view) is True
    assert request.gateway == gateway


def test_openapi_gateway_name_permission_hides_cross_tenant_gateway(settings):
    settings.ENABLE_MULTI_TENANT_MODE = True
    gateway = G(
        Gateway,
        name="cross-tenant-gateway",
        tenant_mode=TenantModeEnum.SINGLE.value,
        tenant_id="tenant-b",
    )
    request = Request(APIRequestFactory().get("/", HTTP_X_BK_TENANT_ID="tenant-a"))
    request.app = mock.MagicMock(app_code="bk_auth")
    view = mock.MagicMock(kwargs={"gateway_name": gateway.name})

    with pytest.raises(Http404):
        OpenAPIV2GatewayNamePermission().has_permission(request, view)


def test_openapi_gateway_name_permission_requires_tenant_header(settings):
    settings.ENABLE_MULTI_TENANT_MODE = True
    gateway = G(Gateway, name="tenant-gateway", tenant_mode=TenantModeEnum.GLOBAL.value, tenant_id="")
    request = Request(APIRequestFactory().get("/"))
    request.app = mock.MagicMock(app_code="bk_auth")
    view = mock.MagicMock(kwargs={"gateway_name": gateway.name})

    with pytest.raises(ValidationError, match="tenant_id is required in multi-tenant mode"):
        OpenAPIV2GatewayNamePermission().has_permission(request, view)


def test_openapi_gateway_name_permission_keeps_single_tenant_mode_behavior(settings):
    settings.ENABLE_MULTI_TENANT_MODE = False
    gateway = G(
        Gateway,
        name="single-tenant-mode-gateway",
        tenant_mode=TenantModeEnum.SINGLE.value,
        tenant_id="another-tenant",
    )
    request = Request(APIRequestFactory().get("/"))
    request.app = mock.MagicMock(app_code="bk_auth")
    view = mock.MagicMock(kwargs={"gateway_name": gateway.name})

    assert OpenAPIV2GatewayNamePermission().has_permission(request, view) is True
    assert request.gateway == gateway
