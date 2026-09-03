# -*- coding: utf-8 -*-
from unittest import mock

import pytest
from rest_framework import viewsets

from apigateway.apis.permissions import GatewayApprovalPermission, GatewayPermission
from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.utils.responses import OKJsonResponse

pytestmark = pytest.mark.django_db


class _GatewayViewSet(viewsets.ViewSet):
    def retrieve(self, request, gateway_id: int, *args, **kwargs):
        return OKJsonResponse()


@pytest.mark.parametrize(
    "permission_class, username, expected",
    [
        (GatewayPermission, "admin", True),
        (GatewayPermission, "operator", False),
        (GatewayApprovalPermission, "admin", True),
        (GatewayApprovalPermission, "operator", True),
        (GatewayApprovalPermission, "guest", False),
    ],
)
def test_gateway_permissions_by_role(mocker, fake_request, fake_gateway, permission_class, username, expected):
    GatewayMember.objects.update_or_create(
        gateway=fake_gateway,
        username="operator",
        defaults={"role": GatewayRoleEnum.OPERATOR.value},
    )
    permission = permission_class()
    mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway)
    fake_request.user = mock.MagicMock(username=username)

    view = _GatewayViewSet.as_view({"get": "retrieve"})

    assert permission.has_permission(fake_request, view) == expected
