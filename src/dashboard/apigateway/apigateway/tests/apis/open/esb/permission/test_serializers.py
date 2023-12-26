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
import datetime
import math

import pytest
import pytz

from apigateway.apis.open.esb.permission import serializers
from apigateway.apps.permission.constants import RENEWABLE_EXPIRE_DAYS
from apigateway.utils import time


class TestAppPermissionComponentSLZ:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "id": 1,
                    "name": "test",
                    "system_name": "test",
                    "system_id": 1,
                    "description": "desc",
                    "description_en": "desc_en",
                    "expires_in": 10,
                    "permission_level": "normal",
                    "permission_status": "pending",
                    "doc_link": "",
                    "board": "test",
                },
                {
                    "id": 1,
                    "name": "test",
                    "system_name": "test",
                    "system_id": 1,
                    "description": "desc",
                    "description_en": "desc_en",
                    "expires_in": 10,
                    "permission_level": "normal",
                    "permission_status": "pending",
                    "permission_action": "",
                    "doc_link": "",
                    "tag": "my-test",
                },
            ),
        ],
    )
    def test_to_representation(self, mocker, params, expected):
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BoardConfigManager.get_optional_display_label",
            return_value="my-test",
        )
        slz = serializers.AppPermissionComponentSLZ(params)
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
        slz = serializers.AppPermissionComponentSLZ()
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
        slz = serializers.AppPermissionComponentSLZ()
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
        slz = serializers.AppPermissionComponentSLZ()
        result = slz._need_to_apply_permission(permission_status)
        assert result == expected

    @pytest.mark.parametrize(
        "permission_status, expires_in, expected",
        [
            ("unlimited", -math.inf, False),
            ("unlimited", math.inf, False),
            ("pending", -math.inf, False),
            ("owned", 10, True),
            ("owned", time.to_seconds(RENEWABLE_EXPIRE_DAYS) + 100, False),
            ("owned", -10, False),
            ("need_apply", -math.inf, False),
        ],
    )
    def test_need_to_renew_permission(self, permission_status, expires_in, expected):
        slz = serializers.AppPermissionComponentSLZ()
        result = slz._need_to_renew_permission(permission_status, expires_in)
        assert result == expected


class TestAppPermissionApplySLZ:
    @pytest.mark.parametrize(
        "params, expected, will_error",
        [
            (
                {
                    "target_app_code": "test",
                    "component_ids": [1, 2, 3],
                },
                {
                    "target_app_code": "test",
                    "component_ids": [1, 2, 3],
                    "reason": "",
                    "expire_days": 180,
                },
                False,
            ),
            (
                {
                    "target_app_code": "test",
                    "component_ids": [1, 2, 3],
                    "expire_days": 10,
                },
                None,
                True,
            ),
        ],
    )
    def test_validate(self, mocker, params, expected, will_error):
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.serializers.ComponentIDValidator.__call__",
            return_value=None,
        )

        slz = serializers.AppPermissionApplySLZ(data=params, context={"system_id": 1})
        slz.is_valid()

        if will_error:
            assert slz.errors
        else:
            assert slz.validated_data == expected
            assert not slz.errors


class TestAppPermissionApplyRecordQuerySLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "target_app_code": "test",
                    "applied_by": "admin",
                    "applied_time_start": 1614665385,
                    "applied_time_end": 1614665385,
                    "apply_status": "pending",
                    "query": "test",
                },
                {
                    "target_app_code": "test",
                    "applied_by": "admin",
                    "applied_time_start": datetime.datetime.fromtimestamp(1614665385, tz=pytz.UTC),
                    "applied_time_end": datetime.datetime.fromtimestamp(1614665385, tz=pytz.UTC),
                    "apply_status": "pending",
                    "query": "test",
                },
            ),
        ],
    )
    def test_to_internal_value(self, mocker, data, expected):
        mocker.patch("apigateway.apis.open.esb.permission.serializers.BKAppCodeValidator.__call__", return_value=None)
        slz = serializers.AppPermissionApplyRecordQuerySLZ(data=data)
        slz.is_valid()
        assert slz.validated_data == expected
