#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

import pytest
from ddf import G

from apigateway.apps.permission.constants import RENEWABLE_EXPIRE_DAYS
from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.utils.time import now_datetime


class TestAppGatewayPermission:
    @pytest.mark.parametrize(
        "timedelta, expected",
        [
            (-10, True),
            (0, True),
            (RENEWABLE_EXPIRE_DAYS * 86400 - 1, True),
            (RENEWABLE_EXPIRE_DAYS * 86400 + 1, False),
        ],
    )
    def test_allow_apply_permission(self, timedelta, expected, fake_gateway):
        expires = now_datetime() + datetime.timedelta(seconds=timedelta)
        perm = G(AppGatewayPermission, gateway=fake_gateway, bk_app_code="test", expires=expires)
        assert perm.allow_apply_permission is expected

    def test_allow_apply_permission_no_expires(self, fake_gateway):
        perm = G(AppGatewayPermission, gateway=fake_gateway, bk_app_code="test", expires=None)
        assert perm.allow_apply_permission is False


class TestAppResourcePermission:
    @pytest.mark.parametrize(
        "timedelta, expected",
        [
            (-10, True),
            (0, True),
            (295, True),
            (305, False),
            (3153600000, False),
        ],
    )
    def test_will_expired_in(self, timedelta, expected):
        expires = now_datetime() + datetime.timedelta(seconds=timedelta)
        permission = G(AppResourcePermission, expires=expires)
        assert permission.will_expired_in(seconds=300) is expected

    @pytest.mark.parametrize(
        "timedelta, expected",
        [
            (-10, True),
            (0, True),
            (RENEWABLE_EXPIRE_DAYS * 86400 - 1, True),
            (RENEWABLE_EXPIRE_DAYS * 86400 + 1, False),
        ],
    )
    def test_allow_apply_permission(self, timedelta, expected, fake_gateway):
        expires = now_datetime() + datetime.timedelta(seconds=timedelta)
        perm = G(AppResourcePermission, gateway=fake_gateway, bk_app_code="test", expires=expires)
        assert perm.allow_apply_permission is expected

    def test_allow_apply_permission_no_expires(self, fake_gateway):
        perm = G(AppResourcePermission, gateway=fake_gateway, bk_app_code="test", expires=None)
        assert perm.allow_apply_permission is False
