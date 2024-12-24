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
from django.db.models import Q
from django.test import TestCase

from apigateway.common.tenant.constants import TENANT_ID_OPERATION, TenantModeEnum
from apigateway.common.tenant.query import gateway_filter_by_app_tenant_id, gateway_filter_by_user_tenant_id


@pytest.mark.django_db
class TestGatewayFilterByUserTenantId(TestCase):
    def setUp(self):
        # Setup initial data for the tests
        self.queryset = MockQuerySet()

    def test_filter_by_operation_tenant(self):
        user_tenant_id = TENANT_ID_OPERATION
        filtered_queryset = gateway_filter_by_user_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            tenant_mode=TenantModeEnum.SINGLE.value, tenant_id=user_tenant_id
        )
        assert filtered_queryset.filter_condition == expected_filter

    def test_filter_by_single_tenant(self):
        user_tenant_id = "tenant_123"
        filtered_queryset = gateway_filter_by_user_tenant_id(self.queryset, user_tenant_id)
        expected_filter = {"tenant_mode": TenantModeEnum.SINGLE.value, "tenant_id": user_tenant_id}
        assert filtered_queryset.filter_condition == expected_filter


@pytest.mark.django_db
class TestGatewayFilterByAppTenantId(TestCase):
    def setUp(self):
        # Setup initial data for the tests
        self.queryset = MockQuerySet()

    def test_filter_by_app_tenant(self):
        app_tenant_id = "tenant_456"
        filtered_queryset = gateway_filter_by_app_tenant_id(self.queryset, app_tenant_id)
        expected_filter = Q(tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            tenant_mode=TenantModeEnum.SINGLE.value, tenant_id=app_tenant_id
        )
        assert filtered_queryset.filter_condition == expected_filter


class MockQuerySet:
    def __init__(self, filter_condition=None):
        self.filter_condition = filter_condition

    def filter(self, *args, **kwargs):
        if args:
            self.filter_condition = args[0]
        else:
            self.filter_condition = kwargs
        return self
