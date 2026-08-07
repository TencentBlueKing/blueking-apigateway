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

from io import StringIO

import pytest
from ddf import G
from django.core.management import call_command

from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import GrantDimensionEnum
from apigateway.apps.permission.management.commands.backfill_itsm_approver import ITSM_HANDLED_BY_PLACEHOLDER
from apigateway.apps.permission.models import AppPermissionRecord

pytestmark = pytest.mark.django_db

COMMAND_NAME = "backfill_itsm_approver"


def test_dry_run_does_not_backfill(fake_gateway, unique_id, mocker):
    record = G(
        AppPermissionRecord,
        gateway=fake_gateway,
        bk_app_code=unique_id,
        grant_dimension=GrantDimensionEnum.API.value,
        handled_by=ITSM_HANDLED_BY_PLACEHOLDER,
        itsm_ticket_id="ticket-001",
    )
    backfill = mocker.patch(
        "apigateway.apps.permission.management.commands.backfill_itsm_approver."
        "async_fill_gateway_or_resource_itsm_approver"
    )

    output = StringIO()
    call_command(COMMAND_NAME, type="gateway", dry_run=True, stdout=output)

    assert f"gateway record_id={record.id}" in output.getvalue()
    assert (
        "mode=dry-run gateway_total=1 gateway_success=0 gateway_failed=0 "
        "mcp_total=0 mcp_success=0 mcp_failed=0" in output.getvalue()
    )
    backfill.assert_not_called()


def test_default_backfills_gateway_and_mcp(fake_gateway, fake_stage, unique_id, mocker):
    record = G(
        AppPermissionRecord,
        gateway=fake_gateway,
        bk_app_code=unique_id,
        grant_dimension=GrantDimensionEnum.RESOURCE.value,
        handled_by=ITSM_HANDLED_BY_PLACEHOLDER,
        itsm_ticket_id="ticket-gateway",
    )
    mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
    apply = G(
        MCPServerAppPermissionApply,
        mcp_server=mcp_server,
        bk_app_code=unique_id,
        handled_by=ITSM_HANDLED_BY_PLACEHOLDER,
        itsm_ticket_id="ticket-mcp",
    )
    # already backfilled, should be skipped without --force
    G(
        AppPermissionRecord,
        gateway=fake_gateway,
        bk_app_code=f"{unique_id}-done",
        grant_dimension=GrantDimensionEnum.API.value,
        handled_by="admin",
        itsm_ticket_id="ticket-done",
    )

    def _fill_gateway(grant_dimension, record_id, ticket_id):
        AppPermissionRecord.objects.filter(id=record_id).update(handled_by="admin")

    def _fill_mcp(apply_id, ticket_id):
        MCPServerAppPermissionApply.objects.filter(id=apply_id).update(handled_by="admin")

    gateway_backfill = mocker.patch(
        "apigateway.apps.permission.management.commands.backfill_itsm_approver."
        "async_fill_gateway_or_resource_itsm_approver",
        side_effect=_fill_gateway,
    )
    mcp_backfill = mocker.patch(
        "apigateway.apps.permission.management.commands.backfill_itsm_approver.async_fill_mcp_server_itsm_approver",
        side_effect=_fill_mcp,
    )

    output = StringIO()
    call_command(COMMAND_NAME, stdout=output)

    assert (
        "mode=backfill gateway_total=1 gateway_success=1 gateway_failed=0 "
        "mcp_total=1 mcp_success=1 mcp_failed=0" in output.getvalue()
    )
    gateway_backfill.assert_called_once_with(record.grant_dimension, record.id, "ticket-gateway")
    mcp_backfill.assert_called_once_with(apply.id, "ticket-mcp")
    record.refresh_from_db()
    apply.refresh_from_db()
    assert record.handled_by == "admin"
    assert apply.handled_by == "admin"


def test_mcp_apply_id_only_backfills_mcp(fake_gateway, fake_stage, unique_id, mocker):
    G(
        AppPermissionRecord,
        gateway=fake_gateway,
        bk_app_code=unique_id,
        grant_dimension=GrantDimensionEnum.API.value,
        handled_by=ITSM_HANDLED_BY_PLACEHOLDER,
        itsm_ticket_id="ticket-gateway",
    )
    mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
    apply = G(
        MCPServerAppPermissionApply,
        mcp_server=mcp_server,
        bk_app_code=unique_id,
        handled_by=ITSM_HANDLED_BY_PLACEHOLDER,
        itsm_ticket_id="ticket-mcp",
    )

    gateway_backfill = mocker.patch(
        "apigateway.apps.permission.management.commands.backfill_itsm_approver."
        "async_fill_gateway_or_resource_itsm_approver"
    )
    mcp_backfill = mocker.patch(
        "apigateway.apps.permission.management.commands.backfill_itsm_approver.async_fill_mcp_server_itsm_approver",
        side_effect=lambda apply_id, ticket_id: MCPServerAppPermissionApply.objects.filter(id=apply_id).update(
            handled_by="admin"
        ),
    )

    output = StringIO()
    call_command(COMMAND_NAME, mcp_apply_id=apply.id, stdout=output)

    assert (
        "mode=backfill gateway_total=0 gateway_success=0 gateway_failed=0 "
        "mcp_total=1 mcp_success=1 mcp_failed=0" in output.getvalue()
    )
    gateway_backfill.assert_not_called()
    mcp_backfill.assert_called_once_with(apply.id, "ticket-mcp")


def test_backfill_failure_is_counted_and_continues(fake_gateway, unique_id, mocker):
    record1 = G(
        AppPermissionRecord,
        gateway=fake_gateway,
        bk_app_code=f"{unique_id}-1",
        grant_dimension=GrantDimensionEnum.API.value,
        handled_by=ITSM_HANDLED_BY_PLACEHOLDER,
        itsm_ticket_id="ticket-1",
    )
    record2 = G(
        AppPermissionRecord,
        gateway=fake_gateway,
        bk_app_code=f"{unique_id}-2",
        grant_dimension=GrantDimensionEnum.API.value,
        handled_by=ITSM_HANDLED_BY_PLACEHOLDER,
        itsm_ticket_id="ticket-2",
    )

    def _side_effect(grant_dimension, record_id, ticket_id):
        if record_id == record1.id:
            raise RuntimeError("itsm down")
        AppPermissionRecord.objects.filter(id=record_id).update(handled_by="admin")

    backfill = mocker.patch(
        "apigateway.apps.permission.management.commands.backfill_itsm_approver."
        "async_fill_gateway_or_resource_itsm_approver",
        side_effect=_side_effect,
    )

    output = StringIO()
    err = StringIO()
    call_command(COMMAND_NAME, type="gateway", stdout=output, stderr=err)

    assert (
        "mode=backfill gateway_total=2 gateway_success=1 gateway_failed=1 "
        "mcp_total=0 mcp_success=0 mcp_failed=0" in output.getvalue()
    )
    assert f"gateway backfill failed record_id={record1.id}" in err.getvalue()
    assert backfill.call_count == 2
    record2.refresh_from_db()
    assert record2.handled_by == "admin"
