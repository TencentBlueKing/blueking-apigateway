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

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum, MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.biz.mcp_server import MCPServerPermissionHandler
from apigateway.common.error_codes import error_codes
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestMCPServerPermissionHandler:
    def test_create_apply_should_only_dispatch_newly_created_applies(self, mocker, fake_gateway, fake_stage):
        mcp_server_1 = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        mcp_server_2 = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)

        unrelated_mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=unrelated_mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="admin",
            applied_time=now_datetime(),
        )

        mock_dispatch = mocker.patch.object(MCPServerPermissionHandler, "_create_itsm_tickets_for_applies")

        applies = MCPServerPermissionHandler.create_apply(
            bk_app_code="test-app",
            mcp_server_ids=[mcp_server_1.id, mcp_server_2.id],
            reason="for test",
            applied_by="tester",
        )

        apply_ids = sorted(applies.values_list("id", flat=True))
        assert len(apply_ids) == 2

        mock_dispatch.assert_called_once()
        dispatched_applies = mock_dispatch.call_args[0][0]
        dispatched_ids = sorted(dispatched_applies.values_list("id", flat=True))
        assert dispatched_ids == apply_ids

    def test_create_apply_allows_gateway_without_approvers(self, mocker, fake_gateway, fake_stage):
        MCPServer.objects.filter(gateway=fake_gateway).delete()
        fake_gateway.members.all().delete()
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        mock_dispatch = mocker.patch.object(MCPServerPermissionHandler, "_create_itsm_tickets_for_applies")

        applies = MCPServerPermissionHandler.create_apply(
            bk_app_code="test-app",
            mcp_server_ids=[mcp_server.id],
            reason="for test",
            applied_by="tester",
        )

        assert list(applies.values_list("mcp_server_id", flat=True)) == [mcp_server.id]
        mock_dispatch.assert_called_once()

    def test_create_apply_should_reject_partial_invalid_mcp_server_ids(self, mocker, fake_gateway, fake_stage):
        active_mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        inactive_mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.INACTIVE.value,
        )
        mock_dispatch = mocker.patch.object(MCPServerPermissionHandler, "_create_itsm_tickets_for_applies")

        with pytest.raises(error_codes.NOT_FOUND.__class__):
            MCPServerPermissionHandler.create_apply(
                bk_app_code="test-app",
                mcp_server_ids=[active_mcp_server.id, inactive_mcp_server.id],
                reason="for test",
                applied_by="tester",
            )

        assert not MCPServerAppPermissionApply.objects.filter(bk_app_code="test-app").exists()
        mock_dispatch.assert_not_called()


class TestMCPServerPermissionHandlerItsm:
    def test_create_itsm_tickets_for_applies(self, mocker, fake_gateway, fake_stage):
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        apply = G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="admin",
            applied_time=now_datetime(),
            itsm_ticket_id="",
        )

        helper = mocker.MagicMock()
        helper.is_ready.return_value = True
        helper.generate_callback_token.return_value = "cb-token-mcp-001"
        helper.create_permission_apply_ticket.return_value = {"id": "itsm-001"}
        helper.extract_ticket_id.return_value = "itsm-001"
        mocker.patch("apigateway.biz.mcp_server.permission.ItsmPermissionApplyHelper", return_value=helper)

        MCPServerPermissionHandler._create_itsm_tickets_for_applies(
            MCPServerAppPermissionApply.objects.filter(id=apply.id)
        )

        apply.refresh_from_db()
        assert apply.itsm_ticket_id == "itsm-001"
        helper.create_permission_apply_ticket.assert_called_once()
        assert helper.create_permission_apply_ticket.call_args.kwargs["apply_reason"] == apply.reason

    def test_create_itsm_tickets_for_applies_when_not_ready(self, mocker, fake_gateway, fake_stage, caplog):
        caplog.set_level("WARNING", logger="apigateway.biz.mcp_server.permission")
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        apply = G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="admin",
            applied_time=now_datetime(),
            itsm_ticket_id="",
        )

        helper = mocker.MagicMock()
        helper.is_ready.return_value = False
        mocker.patch("apigateway.biz.mcp_server.permission.ItsmPermissionApplyHelper", return_value=helper)

        MCPServerPermissionHandler._create_itsm_tickets_for_applies(
            MCPServerAppPermissionApply.objects.filter(id=apply.id)
        )

        apply.refresh_from_db()
        assert apply.itsm_ticket_id == ""
        helper.create_permission_apply_ticket.assert_not_called()
        assert "Skip creating ITSM tickets for mcp server applies" in caplog.text
        assert "apply_count=1" in caplog.text

    def test_create_itsm_tickets_persists_callback_token_before_ticket_id(self, mocker, fake_gateway, fake_stage):
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        apply = G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="admin",
            applied_time=now_datetime(),
            itsm_ticket_id="",
            itsm_callback_token="",
        )

        helper = mocker.MagicMock()
        helper.is_ready.return_value = True
        helper.generate_callback_token.return_value = "cb-token-mcp-001"
        helper.create_permission_apply_ticket.return_value = {"ticket": {}}
        helper.extract_ticket_id.return_value = ""
        mocker.patch("apigateway.biz.mcp_server.permission.ItsmPermissionApplyHelper", return_value=helper)

        MCPServerPermissionHandler._create_itsm_tickets_for_applies(
            MCPServerAppPermissionApply.objects.filter(id=apply.id)
        )

        apply.refresh_from_db()
        assert apply.itsm_ticket_id == ""
        assert apply.itsm_callback_token == "cb-token-mcp-001"

    def test_save_permission_updates_grant_type_for_existing_record(self, fake_gateway, fake_stage):
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        MCPServerAppPermission.objects.save_permission(
            mcp_server_id=mcp_server.id,
            bk_app_code="test-app",
            grant_type=GrantTypeEnum.APPLY.value,
            expire_days=30,
        )
        MCPServerAppPermission.objects.save_permission(
            mcp_server_id=mcp_server.id,
            bk_app_code="test-app",
            grant_type=GrantTypeEnum.SYNC.value,
            expire_days=None,
        )

        permission = MCPServerAppPermission.objects.get(mcp_server_id=mcp_server.id, bk_app_code="test-app")
        assert permission.grant_type == GrantTypeEnum.SYNC.value

    def test_save_permission_with_operator_new_record(self, fake_gateway, fake_stage):
        """测试 save_permission 带 operator 参数创建新记录"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        MCPServerAppPermission.objects.save_permission(
            mcp_server_id=mcp_server.id,
            bk_app_code="test-app",
            grant_type=GrantTypeEnum.INITIALIZE.value,
            expire_days=None,
            operator="admin_user",
        )

        permission = MCPServerAppPermission.objects.get(mcp_server_id=mcp_server.id, bk_app_code="test-app")
        assert permission.created_by == "admin_user"
        assert permission.updated_by == "admin_user"

    def test_save_permission_with_operator_existing_record(self, fake_gateway, fake_stage):
        """测试 save_permission 带 operator 参数更新已有记录"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        MCPServerAppPermission.objects.save_permission(
            mcp_server_id=mcp_server.id,
            bk_app_code="test-app",
            grant_type=GrantTypeEnum.APPLY.value,
            expire_days=None,
            operator="first_user",
        )

        MCPServerAppPermission.objects.save_permission(
            mcp_server_id=mcp_server.id,
            bk_app_code="test-app",
            grant_type=GrantTypeEnum.INITIALIZE.value,
            expire_days=None,
            operator="second_user",
        )

        permission = MCPServerAppPermission.objects.get(mcp_server_id=mcp_server.id, bk_app_code="test-app")
        # created_by 保持首次写入的值，不会被覆盖
        assert permission.created_by == "first_user"
        # updated_by 应更新为新 operator
        assert permission.updated_by == "second_user"

    def test_save_permission_without_operator(self, fake_gateway, fake_stage):
        """测试 save_permission 不带 operator 参数"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        MCPServerAppPermission.objects.save_permission(
            mcp_server_id=mcp_server.id,
            bk_app_code="test-app",
            grant_type=GrantTypeEnum.INITIALIZE.value,
            expire_days=None,
        )

        permission = MCPServerAppPermission.objects.get(mcp_server_id=mcp_server.id, bk_app_code="test-app")
        assert permission.created_by is None
        assert permission.updated_by is None
