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
import math
from unittest import mock

import pytest
from ddf import G
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import ValidationError

from apigateway.apis.open.permission import serializers
from apigateway.apps.permission.constants import RENEWABLE_EXPIRE_DAYS
from apigateway.apps.permission.models import AppGatewayPermission, AppPermissionApplyStatus
from apigateway.utils import time
from apigateway.utils.time import to_datetime_from_now


class TestAppPermissionResourceSLZ:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "id": 1,
                    "name": "test",
                    "api_name": "test",
                    "gateway_id": 1,
                    "description": "desc",
                    "expires_in": 10,
                    "permission_level": "normal",
                    "permission_status": "pending",
                    "doc_link": "",
                },
                {
                    "id": 1,
                    "name": "test",
                    "api_name": "test",
                    "gateway_id": 1,
                    "description": "desc",
                    "description_en": None,
                    "expires_in": 10,
                    "permission_level": "normal",
                    "permission_status": "pending",
                    "permission_action": "",
                    "doc_link": "",
                },
            ),
        ],
    )
    def test_to_representation(self, mocker, params, expected):
        slz = serializers.AppResourcePermissionOutputSLZ(
            params, context={"request": mock.MagicMock(gateway=mock.MagicMock(name="test"))}
        )
        assert slz.data == expected

    @pytest.mark.parametrize(
        "expires_in, expected",
        [
            (-math.inf, None),
            (math.inf, None),
            (0, 0),
            (10, 10),
            (-10, -10),
        ],
    )
    def test_get_expires_in(self, expires_in, expected):
        slz = serializers.AppResourcePermissionOutputSLZ()
        result = slz.get_expires_in({"expires_in": expires_in})
        assert result == expected

    @pytest.mark.parametrize(
        "obj, expected",
        [
            (
                {
                    "permission_status": "expired",
                    "expires_in": -10,
                },
                "apply",
            ),
            (
                {
                    "permission_status": "owned",
                    "expires_in": 10,
                },
                "renew",
            ),
            (
                {
                    "permission_status": "pending",
                    "expires_in": None,
                },
                "",
            ),
        ],
    )
    def test_get_permission_action(self, obj, expected):
        slz = serializers.AppResourcePermissionOutputSLZ()
        result = slz.get_permission_action(obj)
        assert result == expected

    @pytest.mark.parametrize(
        "permission_status, expected",
        [
            ("unlimited", False),
            ("pending", False),
            ("owned", False),
            ("rejected", True),
            ("need_apply", True),
            ("expired", True),
        ],
    )
    def test_need_to_apply_permission(self, permission_status, expected):
        slz = serializers.AppResourcePermissionOutputSLZ()
        result = slz._need_to_apply_permission(permission_status)
        assert result == expected

    @pytest.mark.parametrize(
        "permission_status, expires_in, expected",
        [
            ("unlimited", math.inf, False),
            ("unlimited", -math.inf, False),
            ("pending", -math.inf, False),
            ("owned", 10, True),
            ("owned", time.to_seconds(RENEWABLE_EXPIRE_DAYS) + 100, False),
            ("owned", -10, False),
            ("need_apply", -math.inf, False),
        ],
    )
    def test_need_to_renew_permission(self, permission_status, expires_in, expected):
        slz = serializers.AppResourcePermissionOutputSLZ()
        result = slz._need_to_renew_permission(permission_status, expires_in)
        assert result == expected


class TestPaaSAppPermissionApplySLZ:
    @pytest.mark.parametrize(
        "params, expected, will_error",
        [
            (
                {
                    "target_app_code": "test",
                    "resource_ids": [],
                    "grant_dimension": "api",
                },
                {
                    "target_app_code": "test",
                    "resource_ids": [],
                    "reason": "",
                    "expire_days": 180,
                    "grant_dimension": "api",
                },
                False,
            ),
            (
                {
                    "target_app_code": "test",
                    "resource_ids": [],
                    "expire_days": 10,
                    "grant_dimension": "api",
                },
                None,
                True,
            ),
            (
                {
                    "target_app_code": "test",
                    "resource_ids": [],
                    "grant_dimension": "resource",
                },
                None,
                True,
            ),
        ],
    )
    def test_validate(self, mocker, params, expected, will_error):
        mocker.patch(
            "apigateway.apis.open.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )

        slz = serializers.PaaSAppPermissionApplyInputSLZ(
            data=params, context={"request": mock.MagicMock(gateway=None)}
        )
        slz.is_valid()

        if will_error:
            assert slz.errors
        else:
            assert slz.validated_data == expected
            assert not slz.errors


class TestAppPermissionApplyV1SLZ:
    def test_validate_target_app_code(self, fake_request, fake_gateway):
        fake_request.gateway = fake_gateway
        fake_request.app = mock.MagicMock(app_code="test")

        slz = serializers.AppPermissionApplyV1InputSLZ(
            data={},
            context={
                "request": fake_request,
            },
        )

        with pytest.raises(drf_serializers.ValidationError):
            slz.validate_target_app_code("other")

        assert slz.validate_target_app_code("test") == "test"

    def test_validate_allow_apply(self, fake_request, fake_gateway):
        fake_request.gateway = fake_gateway

        bk_app_code = "app1"
        slz = serializers.AppPermissionApplyV1InputSLZ(
            data={},
            context={
                "request": fake_request,
            },
        )

        permission = G(
            AppGatewayPermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            expires=to_datetime_from_now(days=400),
        )

        with pytest.raises(drf_serializers.ValidationError):
            slz._validate_allow_apply(bk_app_code, "api")

        permission.expires = to_datetime_from_now(days=-1)
        permission.save()
        assert not slz._validate_allow_apply(bk_app_code, "api")

        bk_app_code = "app2"
        G(
            AppPermissionApplyStatus,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            grant_dimension="api",
            status="pending",
        )
        with pytest.raises(drf_serializers.ValidationError):
            slz._validate_allow_apply(bk_app_code, "api")


class TestRevokeAppPermissionSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "target_app_codes": ["app1", "app2"],
                    "grant_dimension": "api",
                },
                {
                    "target_app_codes": ["app1", "app2"],
                    "grant_dimension": "api",
                },
                None,
            ),
            (
                {
                    "target_app_codes": [],
                    "grant_dimension": "api",
                },
                None,
                ValidationError,
            ),
            (
                {
                    "target_app_codes": ["app1"],
                    "grant_dimension": "unknown",
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate(self, data, expected, expected_error):
        slz = serializers.RevokeAppPermissionInputSLZ(data=data)

        if expected_error:
            with pytest.raises(expected_error):
                slz.is_valid(raise_exception=True)
            return

        slz.is_valid(raise_exception=True)
        assert slz.validated_data == expected
