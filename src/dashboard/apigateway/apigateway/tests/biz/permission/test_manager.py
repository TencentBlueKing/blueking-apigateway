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

from unittest import mock

import pytest
from ddf import G

from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionApply,
    AppPermissionApplyStatus,
    AppPermissionRecord,
    AppResourcePermission,
)
from apigateway.biz.permission import (
    GatewayPermissionDimensionManager,
    PermissionDimensionManager,
    ResourcePermissionDimensionManager,
)
from apigateway.core.models import Resource

pytestmark = pytest.mark.django_db


class TestPermissionDimensionManager:
    @pytest.mark.parametrize(
        "grant_dimension, expected",
        [
            ("api", GatewayPermissionDimensionManager),
            ("resource", ResourcePermissionDimensionManager),
        ],
    )
    def test_get_manager(self, grant_dimension, expected):
        manager = PermissionDimensionManager.get_manager(grant_dimension)
        assert isinstance(manager, expected)


class TestGatewayPermissionDimensionManager:
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
        record = GatewayPermissionDimensionManager().handle_permission_apply(
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

        record = GatewayPermissionDimensionManager().handle_permission_apply(
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
        manager = GatewayPermissionDimensionManager()
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
        manager = GatewayPermissionDimensionManager()
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

    def test_create_apply_record(self, fake_gateway, fake_resource):
        manager = GatewayPermissionDimensionManager()
        record = manager.create_apply_record(
            "test",
            fake_gateway,
            [fake_resource.id],
            GrantDimensionEnum.API.value,
            "",
            180,
            "admin",
        )

        assert AppPermissionRecord.objects.filter(id=record.id).exists()
        assert AppPermissionApply.objects.filter(apply_record_id=record.id).exists()
        assert AppPermissionApplyStatus.objects.filter(gateway=fake_gateway).exists()


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

    def test_allow_apply_permission(self, mocker, fake_gateway):
        manager = ResourcePermissionDimensionManager()
        target_app_code = "test"

        # resource_ids 为空
        result, _ = manager.allow_apply_permission(fake_gateway.id, target_app_code, [])
        assert result is True

        result, _ = manager.allow_apply_permission(fake_gateway.id, target_app_code, None)
        assert result is True

        resource = G(Resource, gateway=fake_gateway)

        # 权限申请中
        G(
            AppPermissionApplyStatus,
            gateway=fake_gateway,
            bk_app_code=target_app_code,
            resource=resource,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            status=ApplyStatusEnum.PENDING.value,
        )
        result, reason = manager.allow_apply_permission(fake_gateway.id, target_app_code, [resource.id])
        assert result is False
        assert resource.name in reason

        AppPermissionApplyStatus.objects.filter(gateway=fake_gateway, bk_app_code=target_app_code).delete()

        # 无权限申请
        result, _ = manager.allow_apply_permission(fake_gateway.id, target_app_code, [resource.id])
        assert result is True

        # 已拥有权限，权限永久有效
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=target_app_code,
            resource_id=resource.id,
            expires=None,
        )
        result, reason = manager.allow_apply_permission(fake_gateway.id, target_app_code, [resource.id])
        assert result is False
        assert resource.name in reason

        # 已拥有权限，权限将过期
        mocker.patch(
            "apigateway.apps.permission.models.AppResourcePermission.allow_apply_permission",
            new_callable=mock.PropertyMock(return_value=True),
        )
        result, _ = manager.allow_apply_permission(fake_gateway.id, target_app_code, [resource.id])
        assert result is True

    def test_create_apply_record(self, fake_gateway, fake_resource):
        manager = ResourcePermissionDimensionManager()
        record = manager.create_apply_record(
            "test",
            fake_gateway,
            [fake_resource.id],
            GrantDimensionEnum.API.value,
            "",
            180,
            "admin",
        )

        assert AppPermissionRecord.objects.filter(id=record.id).exists()
        assert AppPermissionApply.objects.filter(apply_record_id=record.id).exists()
        assert AppPermissionApplyStatus.objects.filter(gateway=fake_gateway).exists()


class TestPermissionDimensionManagerItsmIntegration:
    def test_build_itsm_ticket_apply_resources_for_gateway(self, fake_gateway):
        itsm_grant_dimension, resource_names = PermissionDimensionManager._build_itsm_ticket_apply_resources(
            grant_dimension=GrantDimensionEnum.API.value,
            gateway=fake_gateway,
            resource_ids=[],
        )

        assert itsm_grant_dimension == "gateway"
        assert resource_names == [fake_gateway.name]

    def test_create_apply_record_with_itsm_ticket(self, settings, mocker, fake_gateway, fake_resource):
        settings.BK_ITSM4_PERMISSION_APPLY_ENABLED = True

        helper = mocker.MagicMock()
        helper.is_ready.return_value = True
        helper.generate_callback_token.return_value = "cb-token-001"
        helper.create_permission_apply_ticket.return_value = {"ticket": {"id": "ticket-001"}}
        helper.extract_ticket_id.return_value = "ticket-001"
        mocker.patch("apigateway.biz.permission.manager.ItsmPermissionApplyHelper", return_value=helper)

        manager = GatewayPermissionDimensionManager()
        record = manager.create_apply_record(
            "test-app",
            fake_gateway,
            [fake_resource.id],
            GrantDimensionEnum.API.value,
            "reason",
            180,
            "admin",
        )

        record.refresh_from_db()
        apply = AppPermissionApply.objects.get(apply_record_id=record.id)

        assert record.itsm_ticket_id == "ticket-001"
        assert apply.itsm_ticket_id == "ticket-001"
        assert apply.itsm_callback_token == "cb-token-001"
        helper.create_permission_apply_ticket.assert_called_once()
        assert helper.create_permission_apply_ticket.call_args.kwargs["callback_token"] == "cb-token-001"

    def test_create_apply_record_with_itsm_not_ready(self, settings, mocker, fake_gateway, fake_resource):
        settings.BK_ITSM4_PERMISSION_APPLY_ENABLED = True

        helper = mocker.MagicMock()
        helper.is_ready.return_value = False
        mocker.patch("apigateway.biz.permission.manager.ItsmPermissionApplyHelper", return_value=helper)

        manager = GatewayPermissionDimensionManager()
        record = manager.create_apply_record(
            "test-app",
            fake_gateway,
            [fake_resource.id],
            GrantDimensionEnum.API.value,
            "reason",
            180,
            "admin",
        )

        record.refresh_from_db()
        assert record.itsm_ticket_id == ""
        helper.create_permission_apply_ticket.assert_not_called()

    def test_create_apply_record_persists_callback_token_before_ticket_id(
        self, settings, mocker, fake_gateway, fake_resource
    ):
        settings.BK_ITSM4_PERMISSION_APPLY_ENABLED = True

        helper = mocker.MagicMock()
        helper.is_ready.return_value = True
        helper.generate_callback_token.return_value = "cb-token-001"
        helper.create_permission_apply_ticket.return_value = {"ticket": {}}
        helper.extract_ticket_id.return_value = ""
        mocker.patch("apigateway.biz.permission.manager.ItsmPermissionApplyHelper", return_value=helper)

        manager = GatewayPermissionDimensionManager()
        record = manager.create_apply_record(
            "test-app",
            fake_gateway,
            [fake_resource.id],
            GrantDimensionEnum.API.value,
            "reason",
            180,
            "admin",
        )

        record.refresh_from_db()
        apply = AppPermissionApply.objects.get(apply_record_id=record.id)

        assert record.itsm_ticket_id == ""
        assert apply.itsm_ticket_id == ""
        assert apply.itsm_callback_token == "cb-token-001"
