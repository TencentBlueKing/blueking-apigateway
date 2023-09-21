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
from ddf import G

from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionApply,
    AppPermissionApplyStatus,
    AppResourcePermission,
)
from apigateway.biz.permission import (
    APIPermissionDimensionManager,
    PermissionDimensionManager,
    ResourcePermissionDimensionManager,
    ResourcePermissionHandler,
)
from apigateway.core.models import Resource

pytestmark = pytest.mark.django_db


class TestResourcePermissionHandler:
    def test_grant_or_renewal_expire_soon(self, fake_gateway, fake_resource):
        data = [
            {
                "gateway": fake_gateway,
                "resource_id": fake_resource.id,
                "bk_app_code": "test",
            },
        ]
        for test in data:
            handler = ResourcePermissionHandler()
            handler.grant_or_renewal_expire_soon(test["gateway"], test["resource_id"], test["bk_app_code"], 1, 300)
            app_resource_permission = AppResourcePermission.objects.get_permission_or_none(
                gateway=test["gateway"],
                resource_id=test["resource_id"],
                bk_app_code=test["bk_app_code"],
            )
            assert not app_resource_permission.has_expired


class TestPermissionDimensionManager:
    @pytest.mark.parametrize(
        "grant_dimension, expected",
        [
            ("api", APIPermissionDimensionManager),
            ("resource", ResourcePermissionDimensionManager),
        ],
    )
    def test_get_manager(self, grant_dimension, expected):
        manager = PermissionDimensionManager.get_manager(grant_dimension)
        assert isinstance(manager, expected)


class TestAPIPermissionDimensionManager:
    def _make_fake_apply(self, fake_gateway):
        return G(
            AppPermissionApply,
            bk_app_code="test",
            gateway=fake_gateway,
            _resource_ids="",
            grant_dimension="api",
            status=ApplyStatusEnum.PENDING.value,
        )

    def _make_fake_apply_status(self, fake_apply):
        return G(
            AppPermissionApplyStatus,
            apply=fake_apply,
            bk_app_code=fake_apply.bk_app_code,
            gateway=fake_apply.gateway,
            resource=None,
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.PENDING.value,
        )

    def test_handle_permission_apply_approved(self, fake_gateway):
        # 审批同意
        apply = self._make_fake_apply(fake_gateway)
        self._make_fake_apply_status(apply)
        record = APIPermissionDimensionManager().handle_permission_apply(
            gateway=apply.gateway,
            apply=apply,
            status=ApplyStatusEnum.APPROVED.value,
            comment="",
            handled_by="admin",
            part_resource_ids=None,
        )
        assert record.id
        assert AppGatewayPermission.objects.filter(gateway=fake_gateway, bk_app_code=apply.bk_app_code).count() == 1
        assert AppPermissionApplyStatus.objects.filter(gateway=fake_gateway).count() == 0

    def test_handle_permission_apply_rejected(self, fake_gateway):
        # 审批拒绝
        apply = self._make_fake_apply(fake_gateway)
        self._make_fake_apply_status(apply)

        record = APIPermissionDimensionManager().handle_permission_apply(
            gateway=fake_gateway,
            apply=apply,
            status=ApplyStatusEnum.REJECTED.value,
            comment="",
            handled_by="admin",
            part_resource_ids=None,
        )
        assert record.id
        assert AppGatewayPermission.objects.filter(gateway=fake_gateway, bk_app_code=apply.bk_app_code).count() == 0
        assert AppPermissionApplyStatus.objects.filter(gateway=fake_gateway).count() == 0

    def test_save_permission_apply_status(self, fake_gateway):
        apply = self._make_fake_apply(fake_gateway)

        # 新建
        manager = APIPermissionDimensionManager()
        manager.save_permission_apply_status(
            bk_app_code=apply.bk_app_code,
            gateway=fake_gateway,
            apply=apply,
            status=ApplyStatusEnum.PENDING.value,
        )

        assert (
            AppPermissionApplyStatus.objects.filter(
                bk_app_code=apply.bk_app_code,
                apply=apply,
                status=ApplyStatusEnum.PENDING.value,
                gateway=fake_gateway,
                resource=None,
            ).count()
            == 1
        )

        # 更新
        manager.save_permission_apply_status(
            bk_app_code=apply.bk_app_code,
            gateway=fake_gateway,
            apply=apply,
            status=ApplyStatusEnum.REJECTED.value,
        )

        assert (
            AppPermissionApplyStatus.objects.filter(
                bk_app_code=apply.bk_app_code,
                apply=apply,
                status=ApplyStatusEnum.REJECTED.value,
                gateway=fake_gateway,
                resource=None,
            ).count()
            == 1
        )

    def test_allow_apply_permission(self, mocker, fake_gateway):
        manager = APIPermissionDimensionManager()
        target_app_code = "test"

        # 权限申请中
        record = G(
            AppPermissionApplyStatus,
            gateway=fake_gateway,
            bk_app_code=target_app_code,
            grant_dimension="api",
            status="pending",
        )
        result, _ = manager.allow_apply_permission(fake_gateway.id, target_app_code)
        assert result is False

        record.delete()

        # 无权限申请
        result, _ = manager.allow_apply_permission(fake_gateway.id, target_app_code)
        assert result is True

        # 已拥有权限，权限永久有效
        G(AppGatewayPermission, gateway=fake_gateway, bk_app_code=target_app_code, expires=None)
        result, _ = manager.allow_apply_permission(fake_gateway.id, target_app_code)
        assert result is False

        # 已拥有权限，权限将过期
        mocker.patch(
            "apigateway.apps.permission.models.AppGatewayPermission.allow_apply_permission",
            new_callable=mock.PropertyMock(return_value=True),
        )
        result, _ = manager.allow_apply_permission(fake_gateway, target_app_code)
        assert result is True


class TestResourcePermissionDimensionManager:
    def _make_fake_apply(self, fake_gateway):
        r1 = G(Resource, gateway=fake_gateway)
        r2 = G(Resource, gateway=fake_gateway)

        return G(
            AppPermissionApply,
            bk_app_code="test",
            gateway=fake_gateway,
            _resource_ids=f"{r1.id};{r2.id}",
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            status=ApplyStatusEnum.PENDING.value,
        )

    def _make_fake_apply_status(self, fake_apply):
        for resource in Resource.objects.filter(id__in=fake_apply.resource_ids):
            G(
                AppPermissionApplyStatus,
                apply=fake_apply,
                bk_app_code=fake_apply.bk_app_code,
                gateway=fake_apply.gateway,
                resource=resource,
                grant_dimension=GrantDimensionEnum.RESOURCE.value,
                status=ApplyStatusEnum.PENDING.value,
            )

    def test_handle_permission_apply_approved(self, fake_gateway):
        # 审批同意，全部同意
        apply = self._make_fake_apply(fake_gateway)
        self._make_fake_apply_status(apply)

        record = ResourcePermissionDimensionManager().handle_permission_apply(
            gateway=fake_gateway,
            apply=apply,
            status=ApplyStatusEnum.APPROVED.value,
            comment="",
            handled_by="admin",
            part_resource_ids=None,
        )
        assert record.id
        assert AppResourcePermission.objects.filter(gateway=fake_gateway, bk_app_code=apply.bk_app_code).count() == 2
        assert (
            AppPermissionApplyStatus.objects.filter(gateway=fake_gateway, bk_app_code=apply.bk_app_code).count() == 0
        )

    def test_handle_permission_apply_rejected(self, fake_gateway):
        # 审批拒绝，全部拒绝
        apply = self._make_fake_apply(fake_gateway)
        self._make_fake_apply_status(apply)

        record = ResourcePermissionDimensionManager().handle_permission_apply(
            gateway=fake_gateway,
            apply=apply,
            status=ApplyStatusEnum.REJECTED.value,
            comment="",
            handled_by="admin",
            part_resource_ids=None,
        )
        assert record.id
        assert AppResourcePermission.objects.filter(gateway=fake_gateway, bk_app_code=apply.bk_app_code).count() == 0
        assert (
            AppPermissionApplyStatus.objects.filter(
                gateway=fake_gateway,
                bk_app_code=apply.bk_app_code,
                apply=None,
            ).count()
            == 2
        )

    def test_handle_permission_apply_partial_approved(self, fake_gateway):
        # 部分审批
        apply = self._make_fake_apply(fake_gateway)
        self._make_fake_apply_status(apply)

        record = ResourcePermissionDimensionManager().handle_permission_apply(
            gateway=fake_gateway,
            apply=apply,
            status=ApplyStatusEnum.PARTIAL_APPROVED.value,
            comment="",
            handled_by="admin",
            part_resource_ids=apply.resource_ids[:1],
        )
        assert record.id
        assert AppResourcePermission.objects.filter(gateway=fake_gateway, bk_app_code=apply.bk_app_code).count() == 1
        assert (
            AppPermissionApplyStatus.objects.filter(gateway=fake_gateway, bk_app_code=apply.bk_app_code).count() == 1
        )

    def test_save_permission_apply_status(self, fake_gateway):
        apply = self._make_fake_apply(fake_gateway)

        # 新建
        manager = ResourcePermissionDimensionManager()
        manager.save_permission_apply_status(
            bk_app_code=apply.bk_app_code,
            gateway=fake_gateway,
            apply=apply,
            status=ApplyStatusEnum.PENDING.value,
            resources=Resource.objects.filter(id__in=apply.resource_ids),
        )

        assert (
            AppPermissionApplyStatus.objects.filter(
                bk_app_code=apply.bk_app_code,
                apply=apply,
                status=ApplyStatusEnum.PENDING.value,
                gateway=fake_gateway,
            ).count()
            == 2
        )

        # 更新
        manager.save_permission_apply_status(
            bk_app_code=apply.bk_app_code,
            gateway=fake_gateway,
            apply=apply,
            status=ApplyStatusEnum.REJECTED.value,
            resources=Resource.objects.filter(id__in=apply.resource_ids),
        )

        assert (
            AppPermissionApplyStatus.objects.filter(
                bk_app_code=apply.bk_app_code,
                apply=apply,
                status=ApplyStatusEnum.REJECTED.value,
                gateway=fake_gateway,
            ).count()
            == 2
        )

    def test_allow_apply_permission(self, fake_gateway):
        manager = ResourcePermissionDimensionManager()
        result, _ = manager.allow_apply_permission(fake_gateway.id, "test")
        assert not result
