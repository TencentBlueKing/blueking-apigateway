from unittest import mock

import pytest
from ddf import G
from django.http import Http404
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apigateway.apis.v2.permissions import OpenAPIV2GatewayNamePermission, OpenAPIV2Permission
from apigateway.core.models import Gateway


@pytest.mark.parametrize("permission_class", [OpenAPIV2Permission, OpenAPIV2GatewayNamePermission])
def test_openapi_permission_sets_tenant_id_in_multi_tenant_mode(settings, permission_class):
    settings.ENABLE_MULTI_TENANT_MODE = True
    gateway = G(Gateway, name="tenant-gateway")
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
