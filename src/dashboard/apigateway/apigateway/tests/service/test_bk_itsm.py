# -*- coding: utf-8 -*-
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

import argparse
import os

import pytest
from ddf import G

from apigateway.apps.bk_itsm.management.commands.register_to_itsm import Command as RegisterToItsmCommand
from apigateway.apps.bk_itsm.models import ItsmSystemConfig
from apigateway.apps.permission.constants import FormattedGrantDimensionEnum
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper

pytestmark = pytest.mark.django_db


class TestItsmPermissionApplyHelper:
    def test_create_permission_apply_ticket(self, mocker):
        config = G(
            ItsmSystemConfig,
            system_code="bk-apigateway",
            itsm_system_id="bk-apigateway",
            system_token="token-001",
            workflow_key_map={"gateway": "wf-001", "resource": "wf-001"},
            is_registered=True,
        )
        helper = ItsmPermissionApplyHelper(system_code=config.system_code)

        mock_create_ticket = mocker.patch("apigateway.service.bk_itsm.create_ticket", return_value={"id": "t-001"})
        mocker.patch.object(helper, "_build_callback_url", return_value="http://example.com/callback")
        mocker.patch.object(helper, "generate_callback_token", return_value="cb-token-123")

        helper.create_permission_apply_ticket(
            bk_app_code="bk-test",
            gateway_name="demo-gateway",
            grant_dimension="resource",
            apply_resource_names=["resource-a", "resource-b"],
            applied_by="admin",
            apply_record_id=123,
            approvers=["u1", "u2"],
        )

        _, kwargs = mock_create_ticket.call_args
        assert kwargs["workflow_key"] == "wf-001"
        assert kwargs["system_id"] == "bk-apigateway"
        assert kwargs["system_token"] == "token-001"
        assert kwargs["callback_token"] == "cb-token-123"
        assert kwargs["form_data"]["apply_record_id"] == 123
        assert kwargs["form_data"]["grant_dimension"] == "resource"
        assert kwargs["form_data"]["apply_resources"] == "resource-a, resource-b"
        assert kwargs["form_data"]["instance_approvers"] == ["u1", "u2"]
        assert kwargs["options"] == {
            "grant_dimension": [{"name": "resource", "key": "resource", "parent": None}],
        }
        assert "reason" not in kwargs["form_data"]
        assert "expire_days" not in kwargs["form_data"]

    def test_create_permission_apply_ticket_use_mcp_workflow_key(self, mocker):
        config = G(
            ItsmSystemConfig,
            system_code="bk-apigateway",
            itsm_system_id="bk-apigateway",
            system_token="token-001",
            workflow_key_map={"gateway": "wf-resource-001", "resource": "wf-resource-001", "mcp_server": "wf-mcp-001"},
            is_registered=True,
        )
        helper = ItsmPermissionApplyHelper(system_code=config.system_code)

        mock_create_ticket = mocker.patch("apigateway.service.bk_itsm.create_ticket", return_value={"id": "t-001"})
        mocker.patch.object(helper, "_build_callback_url", return_value="http://example.com/callback")
        mocker.patch.object(helper, "generate_callback_token", return_value="cb-token-123")

        helper.create_permission_apply_ticket(
            bk_app_code="bk-test",
            gateway_name="demo-gateway",
            grant_dimension="mcp_server",
            apply_resource_names=["mcp-a"],
            applied_by="admin",
            apply_record_id=123,
            approvers=["u1", "u2"],
        )

        _, kwargs = mock_create_ticket.call_args
        assert kwargs["workflow_key"] == "wf-mcp-001"
        assert kwargs["form_data"]["apply_resources"] == "mcp-a"

    def test_create_permission_apply_ticket_normalize_prefixed_workflow_key(self, mocker):
        config = G(
            ItsmSystemConfig,
            system_code="bk-apigateway",
            itsm_system_id="bk-apigateway",
            system_token="token-001",
            workflow_key_map={
                "gateway": "$Workflow20260507144500022801",
                "resource": "$Workflow20260507144500022801",
                "mcp_server": "$Workflow20260507120400022701",
            },
            is_registered=True,
        )
        helper = ItsmPermissionApplyHelper(system_code=config.system_code)

        mock_create_ticket = mocker.patch("apigateway.service.bk_itsm.create_ticket", return_value={"id": "t-001"})
        mocker.patch.object(helper, "_build_callback_url", return_value="http://example.com/callback")
        mocker.patch.object(helper, "generate_callback_token", return_value="cb-token-123")

        helper.create_permission_apply_ticket(
            bk_app_code="bk-test",
            gateway_name="demo-gateway",
            grant_dimension="resource",
            apply_resource_names=["resource-a"],
            applied_by="admin",
            apply_record_id=123,
            approvers=["u1", "u2"],
        )

        _, kwargs = mock_create_ticket.call_args
        assert kwargs["workflow_key"] == "20260507144500022801"

    def test_create_permission_apply_ticket_use_gateway_name_as_apply_resources(self, mocker):
        config = G(
            ItsmSystemConfig,
            system_code="bk-apigateway",
            itsm_system_id="bk-apigateway",
            system_token="token-001",
            workflow_key_map={"gateway": "wf-001", "resource": "wf-001", "mcp_server": "wf-mcp-001"},
            is_registered=True,
        )
        helper = ItsmPermissionApplyHelper(system_code=config.system_code)

        mock_create_ticket = mocker.patch("apigateway.service.bk_itsm.create_ticket", return_value={"id": "t-001"})
        mocker.patch.object(helper, "_build_callback_url", return_value="http://example.com/callback")
        mocker.patch.object(helper, "generate_callback_token", return_value="cb-token-123")

        helper.create_permission_apply_ticket(
            bk_app_code="bk-test",
            gateway_name="demo-gateway",
            grant_dimension="gateway",
            apply_resource_names=["resource-a", "resource-b"],
            applied_by="admin",
            apply_record_id=123,
            approvers=["u1", "u2"],
        )

        _, kwargs = mock_create_ticket.call_args
        assert kwargs["form_data"]["apply_resources"] == "demo-gateway"

    def test_create_permission_apply_ticket_raise_when_approvers_empty(self, mocker):
        config = G(
            ItsmSystemConfig,
            system_code="bk-apigateway",
            itsm_system_id="bk-apigateway",
            system_token="token-001",
            workflow_key_map={"gateway": "wf-001", "resource": "wf-001"},
            is_registered=True,
        )
        helper = ItsmPermissionApplyHelper(system_code=config.system_code)

        mock_create_ticket = mocker.patch("apigateway.service.bk_itsm.create_ticket", return_value={"id": "t-001"})
        mocker.patch.object(helper, "_build_callback_url", return_value="http://example.com/callback")

        with pytest.raises(Exception, match="ITSM approvers is required"):
            helper.create_permission_apply_ticket(
                bk_app_code="bk-test",
                gateway_name="demo-gateway",
                grant_dimension="resource",
                apply_resource_names=["resource-a"],
                applied_by="admin",
                apply_record_id=123,
                approvers=[],
            )

        mock_create_ticket.assert_not_called()

    def test_create_permission_apply_ticket_raise_when_applied_by_empty(self, mocker):
        config = G(
            ItsmSystemConfig,
            system_code="bk-apigateway",
            itsm_system_id="bk-apigateway",
            system_token="token-001",
            workflow_key_map={"gateway": "wf-001", "resource": "wf-001"},
            is_registered=True,
        )
        helper = ItsmPermissionApplyHelper(system_code=config.system_code)

        mock_create_ticket = mocker.patch("apigateway.service.bk_itsm.create_ticket", return_value={"id": "t-001"})
        mocker.patch.object(helper, "_build_callback_url", return_value="http://example.com/callback")

        with pytest.raises(Exception, match="ITSM applied_by is required"):
            helper.create_permission_apply_ticket(
                bk_app_code="bk-test",
                gateway_name="demo-gateway",
                grant_dimension="resource",
                apply_resource_names=["resource-a"],
                applied_by="  ",
                apply_record_id=123,
                approvers=["u1"],
            )

        mock_create_ticket.assert_not_called()

    def test_is_ready_false_when_config_not_exists(self):
        helper = ItsmPermissionApplyHelper(system_code="not-exists")
        assert helper.is_ready() is False

    def test_default_system_code_should_match_template_system_code(self):
        helper = ItsmPermissionApplyHelper()
        assert helper.system_code == "bk-apigateway"

    def test_register_to_itsm_default_template_file_should_exist(self):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args([])

        assert options.template_file.endswith("apps/bk_itsm/management/system_bk-apigateway.json")
        assert os.path.exists(options.template_file)

    def test_build_callback_url_uses_configured_path(self, settings):
        settings.BK_API_URL_TMPL = "https://bkapi.example.com/api/{api_name}"
        settings.BK_ITSM4_CALLBACK_PATH = "/stag/api/v2/inner/itsm/callback/"

        helper = ItsmPermissionApplyHelper()
        callback_url = helper._build_callback_url()

        assert callback_url == "https://bkapi.example.com/api/bk-apigateway/stag/api/v2/inner/itsm/callback/"

    def test_build_callback_url_fallback_to_callback_stage(self, settings):
        settings.BK_API_URL_TMPL = "https://bkapi.example.com/api/{api_name}"
        settings.BK_ITSM4_CALLBACK_PATH = "/gray/api/v2/inner/itsm/callback/"

        helper = ItsmPermissionApplyHelper()
        callback_url = helper._build_callback_url()

        assert callback_url == "https://bkapi.example.com/api/bk-apigateway/gray/api/v2/inner/itsm/callback/"

    def test_build_ticket_url_with_valid_template(self, settings):
        settings.BK_ITSM4_TICKET_URL_TEMPLATE = "http://itsm.example.com/ticket/{ticket_id}"

        url = ItsmPermissionApplyHelper.build_ticket_url("102025092210362600001802")
        assert url == "http://itsm.example.com/ticket/102025092210362600001802"

    def test_build_ticket_url_returns_empty_when_template_not_set(self, settings):
        settings.BK_ITSM4_TICKET_URL_TEMPLATE = ""

        url = ItsmPermissionApplyHelper.build_ticket_url("102025092210362600001802")
        assert url == ""

    def test_build_ticket_url_returns_empty_when_ticket_id_empty(self, settings):
        settings.BK_ITSM4_TICKET_URL_TEMPLATE = "http://itsm.example.com/ticket/{ticket_id}"

        assert ItsmPermissionApplyHelper.build_ticket_url("") == ""
        assert ItsmPermissionApplyHelper.build_ticket_url(None) == ""

    def test_build_ticket_title_for_gateway(self):
        title = ItsmPermissionApplyHelper._build_ticket_title(
            FormattedGrantDimensionEnum.GATEWAY.value, "demo-gateway", "bk-test", "demo-gateway"
        )
        assert title == "应用 [bk-test] 申请蓝鲸 API 网关 [demo-gateway] 权限"

    def test_build_ticket_title_for_mcp_server(self):
        title = ItsmPermissionApplyHelper._build_ticket_title(
            FormattedGrantDimensionEnum.MCP_SERVER.value, "demo-gateway", "bk-test", "mcp-a"
        )
        assert title == "应用 [bk-test] 申请蓝鲸 MCP [mcp-a] 权限"

    def test_build_apply_resources_display_for_gateway(self):
        helper = ItsmPermissionApplyHelper()
        result = helper._build_apply_resources_display(
            FormattedGrantDimensionEnum.GATEWAY.value, "demo-gateway", ["res-a", "res-b"]
        )
        assert result == "demo-gateway"

    def test_build_apply_resources_display_within_limit(self):
        helper = ItsmPermissionApplyHelper()
        result = helper._build_apply_resources_display(
            FormattedGrantDimensionEnum.RESOURCE.value, "demo-gateway", ["res-a", "res-b"]
        )
        assert result == "res-a, res-b"

    def test_build_apply_resources_display_truncated(self):
        helper = ItsmPermissionApplyHelper()
        result = helper._build_apply_resources_display(
            FormattedGrantDimensionEnum.RESOURCE.value,
            "demo-gateway",
            ["res-a", "res-b", "res-c", "res-d", "res-e", "res-f"],
            max_display=5,
        )
        assert result == "res-a, res-b, res-c, res-d, res-e 等 6 个资源"

    def test_build_apply_resources_display_fallback_to_gateway_when_empty(self):
        helper = ItsmPermissionApplyHelper()
        result = helper._build_apply_resources_display(FormattedGrantDimensionEnum.RESOURCE.value, "demo-gateway", [])
        assert result == "demo-gateway"

    def test_build_form_options_uses_enum(self):
        options = ItsmPermissionApplyHelper._build_form_options(FormattedGrantDimensionEnum.GATEWAY.value)
        assert options["grant_dimension"][0]["name"] == "gateway"
        assert options["grant_dimension"][0]["key"] == FormattedGrantDimensionEnum.GATEWAY.value

        options = ItsmPermissionApplyHelper._build_form_options(FormattedGrantDimensionEnum.MCP_SERVER.value)
        assert options["grant_dimension"][0]["name"] == "MCP Server"
        assert options["grant_dimension"][0]["key"] == FormattedGrantDimensionEnum.MCP_SERVER.value
