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
import datetime
import json

from ddf import G
from django.utils import timezone

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.metrics.models import StatisticsAppRequestByDay
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum, GrantTypeEnum
from apigateway.apps.permission.models import AppGatewayPermission, AppPermissionRecord, AppResourcePermission
from apigateway.apps.permission.tasks import (
    AppPermissionExpiringSoonAlerter,
    _get_actual_approver_from_itsm,
    async_fill_gateway_or_resource_itsm_approver,
    async_fill_mcp_server_itsm_approver,
    renew_app_resource_permission,
)
from apigateway.utils.time import NeverExpiresTime, now_datetime, to_datetime_from_now


class TestRenewAppResourcePermission:
    def test(self, fake_gateway, unique_id):
        bk_app_code = unique_id
        now = now_datetime()

        G(
            StatisticsAppRequestByDay,
            gateway_id=fake_gateway.id,
            bk_app_code=bk_app_code,
            resource_id=1,
            end_time=to_datetime_from_now(days=-3),
        )
        G(StatisticsAppRequestByDay, gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=2, end_time=now)
        G(StatisticsAppRequestByDay, gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=3, end_time=now)
        G(StatisticsAppRequestByDay, gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=4, end_time=now)
        G(StatisticsAppRequestByDay, gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=5, end_time=now)

        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=1,
            expires=to_datetime_from_now(days=3),
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=2,
            expires=to_datetime_from_now(days=-3),
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=3,
            expires=to_datetime_from_now(days=3),
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=4,
            expires=to_datetime_from_now(days=720),
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=5,
            expires=to_datetime_from_now(days=170),
        )

        renew_app_resource_permission()

        assert AppResourcePermission.objects.get(
            gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=1
        ).expires < to_datetime_from_now(days=4)
        assert (
            AppResourcePermission.objects.get(
                gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=2
            ).expires
            < now_datetime()
        )
        assert AppResourcePermission.objects.get(
            gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=3
        ).expires > to_datetime_from_now(days=179)
        assert AppResourcePermission.objects.get(
            gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=4
        ).expires > to_datetime_from_now(days=719)
        assert AppResourcePermission.objects.get(
            gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=5
        ).expires > to_datetime_from_now(days=179)


class TestAsyncFillItsmApprover:
    def test_get_actual_approver_returns_structured_result(self, mocker):
        mocker.patch(
            "apigateway.apps.permission.tasks.get_ticket_by_id",
            return_value=mocker.Mock(actual_approver="admin"),
        )

        assert _get_actual_approver_from_itsm("ticket-001") == "admin"

    def test_get_actual_approver_returns_empty_when_ticket_has_no_approver(self, mocker):
        mocker.patch(
            "apigateway.apps.permission.tasks.get_ticket_by_id",
            return_value=mocker.Mock(actual_approver=""),
        )

        assert _get_actual_approver_from_itsm("ticket-001") == ""

    def test_get_actual_approver_returns_empty_when_query_failed(self, mocker):
        mocker.patch("apigateway.apps.permission.tasks.get_ticket_by_id", side_effect=Exception("remote error"))

        assert _get_actual_approver_from_itsm("ticket-001") == ""

    def test_fill_gateway_permission_approver(self, mocker, fake_gateway, unique_id):
        record = G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code=unique_id,
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.APPROVED.value,
            handled_by="itsm",
        )
        permission = G(
            AppGatewayPermission,
            gateway=fake_gateway,
            bk_app_code=unique_id,
            grant_type=GrantTypeEnum.APPLY.value,
            handled_by="itsm",
        )
        mocker.patch("apigateway.apps.permission.tasks._get_actual_approver_from_itsm", return_value="admin")

        async_fill_gateway_or_resource_itsm_approver(GrantDimensionEnum.API.value, record.id, "ticket-001")

        record.refresh_from_db()
        permission.refresh_from_db()
        assert record.handled_by == "admin"
        assert permission.handled_by == "admin"

    def test_fill_resource_permission_approver(self, mocker, fake_gateway, unique_id):
        record = G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code=unique_id,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            status=ApplyStatusEnum.APPROVED.value,
            handled_by="itsm",
            _handled_resource_ids=json.dumps({ApplyStatusEnum.APPROVED.value: [1]}),
        )
        permission = G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=unique_id,
            resource_id=1,
            grant_type=GrantTypeEnum.APPLY.value,
            handled_by="itsm",
        )
        mocker.patch("apigateway.apps.permission.tasks._get_actual_approver_from_itsm", return_value="admin")

        async_fill_gateway_or_resource_itsm_approver(GrantDimensionEnum.RESOURCE.value, record.id, "ticket-001")

        record.refresh_from_db()
        permission.refresh_from_db()
        assert record.handled_by == "admin"
        assert permission.handled_by == "admin"

    def test_fill_mcp_permission_apply_approver(self, mocker, fake_gateway, fake_stage):
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        apply = G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            handled_by="itsm",
        )
        mocker.patch("apigateway.apps.permission.tasks._get_actual_approver_from_itsm", return_value="admin")

        async_fill_mcp_server_itsm_approver(apply.id, "ticket-001")

        apply.refresh_from_db()
        assert apply.handled_by == "admin"


class TestAppPermissionExpiringSoonAlerter:
    def test_get_permissions_expiring_soon(self, fake_resource_ctx, unique_id):
        now = timezone.now()
        fake_gateway = fake_resource_ctx[0].gateway

        G(AppGatewayPermission, gateway=fake_gateway, expires=now + datetime.timedelta(days=20), bk_app_code=unique_id)

        resource1 = fake_resource_ctx[0]
        resource2 = fake_resource_ctx[1]
        resource3 = fake_resource_ctx[2]
        resource4 = fake_resource_ctx[3]
        resource5 = fake_resource_ctx[4]

        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource1.id,
            expires=now + datetime.timedelta(days=10),
            bk_app_code=unique_id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource2.id,
            expires=now + datetime.timedelta(days=70),
            bk_app_code=unique_id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource3.id,
            expires=now + datetime.timedelta(days=15),
            bk_app_code="test2",
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource4.id,
            expires=now + datetime.timedelta(days=15),
            bk_app_code="test2",
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource5.id,
            expires=now + datetime.timedelta(days=15),
            bk_app_code="test2",
        )

        alerter = AppPermissionExpiringSoonAlerter(30, [])
        result = alerter._get_permissions_expiring_soon()
        assert len(result[unique_id]) == 2
        assert len(result["test2"]) == 1

    def test_filter_permissions(self, fake_resource_ctx, unique_id):
        now = timezone.now()
        fake_gateway = fake_resource_ctx[0].gateway

        resource1 = fake_resource_ctx[0]
        resource2 = fake_resource_ctx[1]
        resource3 = fake_resource_ctx[2]

        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource1.id,
            expires=now + datetime.timedelta(hours=24 * 1 + 1),
            bk_app_code=unique_id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource2.id,
            expires=now + datetime.timedelta(hours=24 * 3 + 2),
            bk_app_code=unique_id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource3.id,
            expires=now + datetime.timedelta(hours=24 * 7 + 1),
            bk_app_code=unique_id,
        )

        alerter = AppPermissionExpiringSoonAlerter(30, [1, 3])

        permissions = alerter._get_permissions_expiring_soon()
        assert len(permissions[unique_id]) == 3

        result = alerter._filter_permissions(permissions)
        assert len(result[unique_id]) == 2

        fake_gateway.status = 0
        fake_gateway.save()

        result = alerter._filter_permissions(permissions)
        assert len(result.get(unique_id, [])) == 0

    def test_complete_permissions(self, fake_resource_ctx, unique_id):
        now = timezone.now()
        fake_gateway = fake_resource_ctx[0].gateway

        resource1 = fake_resource_ctx[0]
        resource2 = fake_resource_ctx[1]
        resource3 = fake_resource_ctx[2]

        G(
            AppResourcePermission,
            gateway=fake_gateway,
            expires=now + datetime.timedelta(days=1),
            bk_app_code=unique_id,
            resource_id=resource1.id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            expires=now + datetime.timedelta(days=2),
            bk_app_code=unique_id,
            resource_id=resource2.id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            expires=now + datetime.timedelta(days=3),
            bk_app_code=unique_id,
            resource_id=resource3.id,
        )

        alerter = AppPermissionExpiringSoonAlerter(30, [])

        permissions = alerter._get_permissions_expiring_soon()
        alerter._complete_permissions(permissions)
        assert permissions[unique_id][0]["gateway_name"] == fake_gateway.name

    def test_get_permissions_expiring_soon_skip_when_gateway_perm_is_forever(self, fake_resource_ctx, unique_id):
        """应用拥有永久网关维度权限时，对应的资源维度权限过期告警应被忽略"""
        now = timezone.now()
        fake_gateway = fake_resource_ctx[0].gateway
        resource1 = fake_resource_ctx[0]

        G(
            AppGatewayPermission,
            gateway=fake_gateway,
            bk_app_code=unique_id,
            expires=NeverExpiresTime.time,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource1.id,
            expires=now + datetime.timedelta(days=10),
            bk_app_code=unique_id,
        )

        alerter = AppPermissionExpiringSoonAlerter(30, [])
        result = alerter._get_permissions_expiring_soon()

        assert len(result[unique_id]) == 0

    def test_get_permissions_expiring_soon_alert_when_no_forever_gateway_perm(self, fake_resource_ctx, unique_id):
        """应用没有永久网关维度权限时，资源维度权限过期告警应正常触发"""
        now = timezone.now()
        fake_gateway = fake_resource_ctx[0].gateway
        resource1 = fake_resource_ctx[0]

        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource1.id,
            expires=now + datetime.timedelta(days=10),
            bk_app_code=unique_id,
        )

        alerter = AppPermissionExpiringSoonAlerter(30, [])
        result = alerter._get_permissions_expiring_soon()

        assert len(result[unique_id]) == 1

    def test_send_alert_skip_failed_app(self, mocker):
        alerter = AppPermissionExpiringSoonAlerter(30, [])
        permissions = {
            "missing-app": [{"gateway_name": "gateway", "grant_dimension": 1, "resource_name": "resource"}],
            "valid-app": [{"gateway_name": "gateway", "grant_dimension": 1, "resource_name": "resource"}],
        }

        mocker.patch(
            "apigateway.apps.permission.tasks.get_app_maintainers",
            side_effect=[Exception("not found"), ["maintainer"]],
        )
        get_tenant_id = mocker.patch(
            "apigateway.apps.permission.tasks.get_tenant_id_for_app_developers",
            return_value="tenant-1",
        )
        mocker.patch("apigateway.apps.permission.tasks.render_to_string", return_value="mail-content")
        mocker.patch("apigateway.apps.permission.tasks.read_file", return_value=b"logo")
        send_mail = mocker.patch("apigateway.apps.permission.tasks.cmsi_component.send_mail")
        log_exception = mocker.patch("apigateway.apps.permission.tasks.logger.exception")

        alerter._send_alert(permissions)

        log_exception.assert_called_once_with(
            "failed to send app permission expiring soon alert for bk_app_code=%s",
            "missing-app",
        )
        get_tenant_id.assert_called_once_with("valid-app")
        send_mail.assert_called_once()
