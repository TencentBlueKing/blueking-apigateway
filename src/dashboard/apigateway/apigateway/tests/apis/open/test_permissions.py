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

from apigateway.apis.open.permissions import (
    OpenAPIGatewayIdPermission,
    OpenAPIGatewayNamePermission,
    OpenAPIGatewayRelatedAppPermission,
    OpenAPIPermission,
)
from apigateway.utils.responses import OKJsonResponse

pytestmark = pytest.mark.django_db


class TestOpenAPIPermission:
    class APINameViewSet(viewsets.ViewSet):
        permission_classes = [OpenAPIPermission]

        def retrieve(self, request, api_name: str, *args, **kwargs):
            return OKJsonResponse()

    @pytest.mark.parametrize(
        "has_app, expected",
        [
            (False, False),
            (True, True),
        ],
    )
    def test_has_permission(
        self,
        fake_request,
        has_app,
        expected,
    ):
        permission = OpenAPIPermission()
        if has_app:
            fake_request.app = mock.MagicMock(app_code="test")

        view = self.APINameViewSet.as_view({"get": "retrieve"})
        assert permission.has_permission(fake_request, view) == expected


class TestOpenAPIGatewayIdPermission:
    class APINameViewSet(viewsets.ViewSet):
        permission_classes = [OpenAPIGatewayIdPermission]

        def retrieve(self, request, api_name: str, *args, **kwargs):
            return OKJsonResponse()

    @pytest.mark.parametrize(
        "with_fake_gateway, has_app, expected",
        [
            (True, False, False),
            (False, True, Http404),
            (True, True, True),
        ],
    )
    def test_has_permission(
        self,
        mocker,
        fake_request,
        fake_gateway,
        with_fake_gateway,
        has_app,
        expected,
    ):
        permission = OpenAPIGatewayIdPermission()

        mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway if with_fake_gateway else None)
        if has_app:
            fake_request.app = mock.MagicMock(app_code="test")

        view = self.APINameViewSet.as_view({"get": "retrieve"})
        if expected == Http404:
            with pytest.raises(Http404):
                permission.has_permission(fake_request, view)
            return

        assert permission.has_permission(fake_request, view) == expected

    def test_get_gateway_object(self, fake_gateway):
        permission = OpenAPIGatewayIdPermission()
        view = self.APINameViewSet.as_view({"get": "retrieve"})

        view.kwargs = {}
        result = permission.get_gateway_object(view)
        assert result is None

        view.kwargs = {"gateway_id": fake_gateway.id}
        result = permission.get_gateway_object(view)
        assert result == fake_gateway


class TestOpenAPIGatewayNamePermission:
    class APINameViewSet(viewsets.ViewSet):
        permission_classes = [OpenAPIGatewayNamePermission]

        def retrieve(self, request, api_name: str, *args, **kwargs):
            return OKJsonResponse()

    @pytest.mark.parametrize(
        "with_fake_gateway, has_app, expected",
        [
            (True, False, False),
            (False, True, Http404),
            (True, True, True),
        ],
    )
    def test_has_permission(
        self,
        mocker,
        fake_request,
        fake_gateway,
        with_fake_gateway,
        has_app,
        expected,
    ):
        permission = OpenAPIGatewayNamePermission()

        mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway if with_fake_gateway else None)
        if has_app:
            fake_request.app = mock.MagicMock(app_code="test")

        view = self.APINameViewSet.as_view({"get": "retrieve"})
        if expected == Http404:
            with pytest.raises(Http404):
                permission.has_permission(fake_request, view)
            return

        assert permission.has_permission(fake_request, view) == expected

    def test_get_gateway_object(self, fake_gateway):
        permission = OpenAPIGatewayNamePermission()
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


class TestOpenAPIGatewayRelatedAppPermission:
    class APINameViewSet(viewsets.ViewSet):
        permission_classes = [OpenAPIGatewayRelatedAppPermission]

        def retrieve(self, request, api_name: str, *args, **kwargs):
            return OKJsonResponse()

    @pytest.mark.parametrize(
        "with_fake_gateway, allow_gateway_not_exist, mock_allow_manage, expected",
        [
            (False, True, False, True),
            (False, False, False, Http404),
            (True, False, False, False),
            (True, False, True, True),
        ],
    )
    def test_has_permission(
        self,
        mocker,
        fake_request,
        fake_gateway,
        with_fake_gateway,
        allow_gateway_not_exist,
        mock_allow_manage,
        expected,
    ):
        permission = OpenAPIGatewayRelatedAppPermission()

        mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway if with_fake_gateway else None)
        mocker.patch(
            "apigateway.apis.open.permissions.GatewayRelatedApp.objects.filter",
            return_value=mocker.MagicMock(exists=mocker.MagicMock(return_value=mock_allow_manage)),
        )
        fake_request.app = mock.MagicMock(app_code="test")

        view = self.APINameViewSet.as_view({"get": "retrieve"})
        view.allow_gateway_not_exist = allow_gateway_not_exist

        if expected == Http404:
            with pytest.raises(Http404):
                permission.has_permission(fake_request, view)
            return

        assert permission.has_permission(fake_request, view) == expected

    def test_get_gateway_object(self, fake_gateway):
        permission = OpenAPIGatewayRelatedAppPermission()
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
