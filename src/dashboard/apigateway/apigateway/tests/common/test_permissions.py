# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
from unittest import mock

import pytest
from django.http import Http404
from rest_framework import viewsets

from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.utils.responses import OKJsonResponse

pytestmark = pytest.mark.django_db


class TestGatewayRelatedAppPermission:
    class APINameViewSet(viewsets.ViewSet):
        permission_classes = [GatewayRelatedAppPermission]

        def retrieve(self, request, api_name: str, *args, **kwargs):
            return OKJsonResponse()

    @pytest.mark.parametrize(
        "mock_gateway, allow_api_not_exist, api_permission_exempt, mock_allow_manage, expected",
        [
            (None, True, False, False, True),
            (None, False, False, False, Http404),
            ("gateway", False, True, False, True),
            ("gateway", False, False, False, False),
            ("gateway", False, False, True, True),
        ],
    )
    def test_has_permission(
        self,
        fake_request,
        fake_gateway,
        mocker,
        mock_gateway,
        allow_api_not_exist,
        api_permission_exempt,
        mock_allow_manage,
        expected,
    ):
        permission = GatewayRelatedAppPermission()

        mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway if mock_gateway else None)
        mocker.patch(
            "apigateway.common.permissions.permissions.APIRelatedApp.objects.filter",
            return_value=mocker.MagicMock(exists=mocker.MagicMock(return_value=mock_allow_manage)),
        )
        fake_request.app = mock.MagicMock(app_code="test")

        view = self.APINameViewSet.as_view({"get": "retrieve"})
        view.allow_api_not_exist = allow_api_not_exist
        view.api_permission_exempt = api_permission_exempt

        if expected == Http404:
            with pytest.raises(Http404):
                permission.has_permission(fake_request, view)
            return

        assert permission.has_permission(fake_request, view) == expected

    def test_get_api_object(self, fake_gateway):
        permission = GatewayRelatedAppPermission()
        view = self.APINameViewSet.as_view({"get": "retrieve"})

        view.kwargs = {}
        result = permission.get_gateway_object(view)
        assert result is None

        view.kwargs = {"gateway_name": "not-exist"}
        result = permission.get_gateway_object(view)
        assert result is None

        view.kwargs = {"gateway_name": fake_gateway.name}
        result = permission.get_gateway_object(view)
        assert result == fake_gateway
