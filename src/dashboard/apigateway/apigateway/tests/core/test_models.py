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
import pytest
from django_dynamic_fixture import G

from apigateway.biz.resource import ResourceHandler
from apigateway.core import models
from apigateway.core.constants import GatewayStatusEnum

pytestmark = pytest.mark.django_db


class TestAPI:
    @pytest.mark.parametrize(
        "status, is_public, expected",
        [
            (GatewayStatusEnum.ACTIVE.value, True, True),
            (GatewayStatusEnum.INACTIVE.value, True, False),
            (GatewayStatusEnum.ACTIVE.value, False, False),
            (GatewayStatusEnum.INACTIVE.value, False, False),
        ],
    )
    def test_is_active_and_public(self, status, is_public, expected):
        gateway = G(models.Gateway, status=status, is_public=is_public)
        assert gateway.is_active_and_public == expected


class TestResource:
    def test_snapshot(self, fake_resource):
        snapshot = ResourceHandler.snapshot(fake_resource, as_dict=True)
        assert snapshot
        assert isinstance(snapshot, dict)
