#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from ddf import G
from django.db.models import Q

from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission
from apigateway.common.tenant.constants import TENANT_ID_OPERATION, TenantModeEnum
from apigateway.common.tenant.query import (
    gateway_filter_by_app_tenant_id,
    gateway_filter_by_maintainer_tenant_id,
    gateway_mcp_server_filter_by_user_tenant_id,
    gateway_related_filter_by_maintainer_tenant_id,
    gateway_related_filter_by_user_tenant_id,
    mcp_server_related_filter_by_maintainer_tenant_id,
    mcp_server_related_filter_by_user_tenant_id,
)
from apigateway.core.models import Gateway, Stage


@pytest.mark.no_meta_schema
class TestGatewayFilterByMaintainerTenantId:
    def setup_method(self):
        # Setup initial data for the tests
        self.queryset = MockQuerySet()

    def test_filter_by_operation_tenant(self):
        user_tenant_id = TENANT_ID_OPERATION
        filtered_queryset = gateway_filter_by_maintainer_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            tenant_mode=TenantModeEnum.SINGLE.value, tenant_id=user_tenant_id
        )
        assert filtered_queryset.filter_condition == expected_filter

    def test_filter_by_single_tenant(self):
        user_tenant_id = "tenant_123"
        filtered_queryset = gateway_filter_by_maintainer_tenant_id(self.queryset, user_tenant_id)
        expected_filter = {"tenant_mode": TenantModeEnum.SINGLE.value, "tenant_id": user_tenant_id}
        assert filtered_queryset.filter_condition == expected_filter


@pytest.mark.no_meta_schema
class TestGatewayRelatedFilterByMaintainerTenantId:
    def setup_method(self):
        self.queryset = MockQuerySet()

    def test_filter_by_operation_tenant(self):
        user_tenant_id = TENANT_ID_OPERATION
        filtered_queryset = gateway_related_filter_by_maintainer_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            gateway__tenant_mode=TenantModeEnum.SINGLE.value,
            gateway__tenant_id=user_tenant_id,
        )
        assert filtered_queryset.filter_condition == expected_filter

    def test_filter_by_single_tenant(self):
        user_tenant_id = "tenant_123"
        filtered_queryset = gateway_related_filter_by_maintainer_tenant_id(self.queryset, user_tenant_id)
        expected_filter = {
            "gateway__tenant_mode": TenantModeEnum.SINGLE.value,
            "gateway__tenant_id": user_tenant_id,
        }
        assert filtered_queryset.filter_condition == expected_filter


@pytest.mark.no_meta_schema
class TestGatewayRelatedFilterByUserTenantId:
    def setup_method(self):
        self.queryset = MockQuerySet()

    def test_filter_by_operation_tenant(self):
        user_tenant_id = TENANT_ID_OPERATION
        filtered_queryset = gateway_related_filter_by_user_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            gateway__tenant_mode=TenantModeEnum.SINGLE.value,
            gateway__tenant_id=user_tenant_id,
        )
        assert filtered_queryset.filter_condition == expected_filter

    def test_filter_by_single_tenant(self):
        user_tenant_id = "tenant_123"
        filtered_queryset = gateway_related_filter_by_user_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            gateway__tenant_mode=TenantModeEnum.SINGLE.value,
            gateway__tenant_id=user_tenant_id,
        )
        assert filtered_queryset.filter_condition == expected_filter


@pytest.mark.no_meta_schema
class TestMCPServerRelatedFilterByMaintainerTenantId:
    def setup_method(self):
        self.queryset = MockQuerySet()

    def test_filter_by_operation_tenant(self):
        user_tenant_id = TENANT_ID_OPERATION
        filtered_queryset = mcp_server_related_filter_by_maintainer_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(mcp_server__gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            mcp_server__gateway__tenant_mode=TenantModeEnum.SINGLE.value,
            mcp_server__gateway__tenant_id=user_tenant_id,
        )
        assert filtered_queryset.filter_condition == expected_filter

    def test_filter_by_single_tenant(self):
        user_tenant_id = "tenant_123"
        filtered_queryset = mcp_server_related_filter_by_maintainer_tenant_id(self.queryset, user_tenant_id)
        expected_filter = {
            "mcp_server__gateway__tenant_mode": TenantModeEnum.SINGLE.value,
            "mcp_server__gateway__tenant_id": user_tenant_id,
        }
        assert filtered_queryset.filter_condition == expected_filter


@pytest.mark.no_meta_schema
class TestMCPServerRelatedFilterByUserTenantId:
    def setup_method(self):
        self.queryset = MockQuerySet()

    def test_filter_by_operation_tenant(self):
        user_tenant_id = TENANT_ID_OPERATION
        filtered_queryset = mcp_server_related_filter_by_user_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(mcp_server__gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            mcp_server__gateway__tenant_mode=TenantModeEnum.SINGLE.value,
            mcp_server__gateway__tenant_id=user_tenant_id,
        )
        assert filtered_queryset.filter_condition == expected_filter

    def test_filter_by_single_tenant(self):
        user_tenant_id = "tenant_123"
        filtered_queryset = mcp_server_related_filter_by_user_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(mcp_server__gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            mcp_server__gateway__tenant_mode=TenantModeEnum.SINGLE.value,
            mcp_server__gateway__tenant_id=user_tenant_id,
        )
        assert filtered_queryset.filter_condition == expected_filter


@pytest.mark.no_meta_schema
class TestGatewayMCPServerFilterByUserTenantId:
    def setup_method(self):
        self.queryset = MockQuerySet()

    def test_filter_by_operation_tenant(self):
        user_tenant_id = TENANT_ID_OPERATION
        filtered_queryset = gateway_mcp_server_filter_by_user_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            gateway__tenant_mode=TenantModeEnum.SINGLE.value,
            gateway__tenant_id=user_tenant_id,
        )
        assert filtered_queryset.filter_condition == expected_filter

    def test_filter_by_single_tenant(self):
        user_tenant_id = "tenant_123"
        filtered_queryset = gateway_mcp_server_filter_by_user_tenant_id(self.queryset, user_tenant_id)
        expected_filter = Q(gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
            gateway__tenant_mode=TenantModeEnum.SINGLE.value,
            gateway__tenant_id=user_tenant_id,
        )
        assert filtered_queryset.filter_condition == expected_filter


@pytest.mark.no_meta_schema
class TestGatewayFilterByAppTenantId:
    def setup_method(self):
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "filter_function, tenant_id, include_global",
    [
        (gateway_filter_by_maintainer_tenant_id, TENANT_ID_OPERATION, True),
        (gateway_filter_by_maintainer_tenant_id, "tenant-a", False),
        (gateway_filter_by_app_tenant_id, "tenant-a", True),
    ],
)
def test_gateway_filters_isolate_real_rows(filter_function, tenant_id, include_global):
    own = G(Gateway, tenant_mode="single", tenant_id=tenant_id)
    global_gateway = G(Gateway, tenant_mode="global", tenant_id="")
    G(Gateway, tenant_mode="single", tenant_id="other-tenant")
    expected = {own.id, global_gateway.id} if include_global else {own.id}
    assert set(filter_function(Gateway.objects.all(), tenant_id).values_list("id", flat=True)) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "filter_function, through_mcp, include_global",
    [
        (gateway_related_filter_by_maintainer_tenant_id, False, False),
        (gateway_related_filter_by_user_tenant_id, False, True),
        (mcp_server_related_filter_by_maintainer_tenant_id, True, False),
        (mcp_server_related_filter_by_user_tenant_id, True, True),
        (gateway_mcp_server_filter_by_user_tenant_id, False, True),
    ],
)
def test_related_filters_isolate_real_rows(filter_function, through_mcp, include_global):
    rows = []
    for mode, tenant in [("single", "tenant-a"), ("global", ""), ("single", "tenant-b")]:
        gateway = G(Gateway, tenant_mode=mode, tenant_id=tenant)
        stage = G(Stage, gateway=gateway)
        if through_mcp or filter_function is gateway_mcp_server_filter_by_user_tenant_id:
            server = G(MCPServer, gateway=gateway, stage=stage)
            row = G(MCPServerAppPermission, mcp_server=server) if through_mcp else server
        else:
            row = stage
        rows.append(row)
    expected = {rows[0].pk, rows[1].pk} if include_global else {rows[0].pk}
    queryset = type(rows[0]).objects.all()
    assert set(filter_function(queryset, "tenant-a").values_list("pk", flat=True)) == expected
