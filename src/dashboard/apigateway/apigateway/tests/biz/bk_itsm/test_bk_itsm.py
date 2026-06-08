# -*- coding: utf-8 -*-
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

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum, GrantTypeEnum
from apigateway.apps.permission.models import AppGatewayPermission, AppPermissionApply, AppPermissionRecord
from apigateway.biz.bk_itsm import ITSM_PERMISSION_APPROVAL_HANDLER, ItsmCallbackResultHandler
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestItsmCallbackResultHandler:
    def test_handle_gateway_callback_raise_when_callback_token_mismatch(self, fake_gateway):
        apply = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test-app",
            applied_by="admin",
            _resource_ids="",
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.PENDING.value,
            apply_record_id=1001,
            itsm_ticket_id="itsm-ticket-001",
            itsm_callback_token="cb-token-local",
        )

        with pytest.raises(Exception, match="invalid callback_token"):
            ItsmCallbackResultHandler().handle(
                ticket={
                    "id": "itsm-ticket-001",
                    "approve_result": True,
                    "form_data": {
                        "apply_record_id": apply.apply_record_id,
                        "grant_dimension": "gateway",
                    },
                },
                callback_token="cb-token-mismatch",
            )

    def test_handle_gateway_callback_raise_when_ticket_id_mismatch(self, fake_gateway):
        apply = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test-app",
            applied_by="admin",
            _resource_ids="",
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.PENDING.value,
            apply_record_id=1002,
            itsm_ticket_id="itsm-ticket-local",
            itsm_callback_token="cb-token-001",
        )

        with pytest.raises(Exception, match="ticket id mismatch"):
            ItsmCallbackResultHandler().handle(
                ticket={
                    "id": "itsm-ticket-callback",
                    "approve_result": True,
                    "form_data": {
                        "apply_record_id": apply.apply_record_id,
                        "grant_dimension": "gateway",
                    },
                },
                callback_token="cb-token-001",
            )

    def test_handle_gateway_callback_ignore_when_not_pending(self, mocker, fake_gateway):
        apply = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test-app",
            applied_by="admin",
            _resource_ids="",
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.APPROVED.value,
            apply_record_id=1003,
            itsm_ticket_id="itsm-ticket-003",
            itsm_callback_token="cb-token-003",
        )
        mock_get_manager = mocker.patch("apigateway.biz.bk_itsm.bk_itsm.PermissionDimensionManager.get_manager")

        ItsmCallbackResultHandler().handle(
            ticket={
                "id": "itsm-ticket-003",
                "approve_result": True,
                "form_data": {
                    "apply_record_id": apply.apply_record_id,
                    "grant_dimension": "gateway",
                },
            },
            callback_token="cb-token-003",
        )

        apply.refresh_from_db()
        assert apply.status == ApplyStatusEnum.APPROVED.value
        mock_get_manager.assert_not_called()

    def test_handle_gateway_callback_approved_grant_type_apply(self, fake_gateway):
        record = G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="test-app",
            applied_by="admin",
            applied_time=now_datetime(),
            _resource_ids="",
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.PENDING.value,
        )
        apply = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test-app",
            applied_by="admin",
            _resource_ids="",
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.PENDING.value,
            apply_record_id=record.id,
            itsm_ticket_id="itsm-ticket-004",
            itsm_callback_token="cb-token-004",
        )

        ItsmCallbackResultHandler().handle(
            ticket={
                "id": "itsm-ticket-004",
                "approve_result": True,
                "form_data": {
                    "apply_record_id": record.id,
                    "grant_dimension": "gateway",
                },
            },
            callback_token="cb-token-004",
        )

        permission = AppGatewayPermission.objects.get(gateway=fake_gateway, bk_app_code=apply.bk_app_code)
        assert permission.grant_type == GrantTypeEnum.APPLY.value
        assert not AppPermissionApply.objects.filter(id=apply.id).exists()

    def test_handle_mcp_callback_approved_updates_apply_and_sync_permissions(self, mocker, fake_gateway, fake_stage):
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        apply = G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="admin",
            applied_time=now_datetime(),
            itsm_ticket_id="itsm-mcp-001",
            itsm_callback_token="cb-mcp-001",
        )

        mock_save_permission = mocker.patch(
            "apigateway.biz.bk_itsm.bk_itsm.MCPServerAppPermission.objects.save_permission"
        )
        mock_sync_permissions = mocker.patch("apigateway.biz.bk_itsm.bk_itsm.MCPServerHandler.sync_permissions")

        ItsmCallbackResultHandler().handle(
            ticket={
                "id": "itsm-mcp-001",
                "approve_result": True,
                "form_data": {
                    "apply_record_id": apply.id,
                    "grant_dimension": "mcp_server",
                },
            },
            callback_token="cb-mcp-001",
        )

        apply.refresh_from_db()
        assert apply.status == MCPServerAppPermissionApplyStatusEnum.APPROVED.value
        assert apply.handled_by == ITSM_PERMISSION_APPROVAL_HANDLER
        assert apply.handled_time is not None
        mock_save_permission.assert_called_once_with(
            mcp_server_id=apply.mcp_server_id,
            bk_app_code=apply.bk_app_code,
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
            expire_days=None,
        )
        mock_sync_permissions.assert_called_once_with(apply.mcp_server_id)
