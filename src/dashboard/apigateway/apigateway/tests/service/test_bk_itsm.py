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

import argparse
import json
import os

import pytest
from ddf import G

from apigateway.apps.bk_itsm.management.commands.register_to_itsm import Command as RegisterToItsmCommand
from apigateway.apps.bk_itsm.models import ItsmSystemConfig
from apigateway.apps.permission.constants import FormattedGrantDimensionEnum
from apigateway.components.bkitsm import ItsmFormModelUpdateResult, ItsmWorkflowList
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
            apply_reason="  need access for daily ops  ",
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
        assert kwargs["form_data"]["apply_reason"] == "need access for daily ops"
        assert kwargs["form_data"]["instance_approvers"] == ["u1", "u2"]
        assert kwargs["options"] == {
            "grant_dimension": [{"name": "resource", "key": "resource", "parent": None}],
        }
        assert "reason" not in kwargs["form_data"]
        assert "expire_days" not in kwargs["form_data"]

    def test_create_permission_apply_ticket_normalizes_none_apply_reason(self, mocker):
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

        helper.create_permission_apply_ticket(
            bk_app_code="bk-test",
            gateway_name="demo-gateway",
            grant_dimension="resource",
            apply_resource_names=["resource-a"],
            applied_by="admin",
            apply_record_id=123,
            apply_reason=None,
            approvers=["u1"],
        )

        _, kwargs = mock_create_ticket.call_args
        assert kwargs["form_data"]["apply_reason"] == ""

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
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args([])
        with open(options.template_file, encoding="utf-8") as fp:
            template = json.load(fp)

        helper = ItsmPermissionApplyHelper()
        assert helper.system_code == template["system"]["code"]

    def test_register_to_itsm_default_template_file_should_exist(self):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args([])

        assert options.template_file.endswith("apps/bk_itsm/management/system_bk-apigateway.json")
        assert os.path.exists(options.template_file)

    def test_register_to_itsm_form_model_update_options(self):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args(["--update-form-model", "--form-model-key", "fm-001"])

        assert options.update_form_model is True
        assert options.form_model_key == "fm-001"

    def test_register_to_itsm_form_model_key_requires_update_form_model(self):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args(["--form-model-key", "fm-001"])

        with pytest.raises(RuntimeError, match="--form-model-key requires --update-form-model"):
            RegisterToItsmCommand().handle(**vars(options))

    def test_register_to_itsm_update_form_model_fails_when_workflow_list_query_failed(self, mocker):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args(["--update-form-model"])

        mocker.patch(
            "apigateway.apps.bk_itsm.management.commands.register_to_itsm.system_workflow_list",
            side_effect=Exception("ITSM 503"),
        )
        mock_system_migrate = mocker.patch(
            "apigateway.apps.bk_itsm.management.commands.register_to_itsm.system_migrate"
        )

        with pytest.raises(RuntimeError, match="failed to query system_workflow_list"):
            RegisterToItsmCommand().handle(**vars(options))

        mock_system_migrate.assert_not_called()

    def test_register_to_itsm_build_form_model_update_payload(self):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args([])

        with open(options.template_file, encoding="utf-8") as fp:
            template = json.load(fp)

        payload = RegisterToItsmCommand._build_form_model_update_payload("bk-apigateway-20260804", template)

        assert payload["key"] == "20260804110000000101"
        assert payload["name"] == "bk-apigateway-20260804"
        assert payload["app_id"] == "core"
        assert payload["system_id"] == "bk-apigateway-20260804"
        assert payload["meta"]["fields"]["apply_reason"]["type"] == "textarea"
        assert "styleCode" not in payload["meta"]

    def test_register_to_itsm_update_form_model_when_system_registered(self, mocker):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args(["--update-form-model"])

        with open(options.template_file, encoding="utf-8") as fp:
            template = json.load(fp)

        field_keys = set(template["form_models"][0]["meta"]["fields"].keys())
        remote_properties = {key: {} for key in field_keys}
        command = RegisterToItsmCommand()
        mocker.patch.object(
            command,
            "_get_system_workflow_list",
            return_value=ItsmWorkflowList.from_response(
                {
                    "count": 1,
                    "results": [{"form_schema": {"properties": remote_properties}}],
                }
            ),
        )
        mocker.patch.object(command, "_ensure_config_from_template")
        mock_update_form_model = mocker.patch(
            "apigateway.apps.bk_itsm.management.commands.register_to_itsm.update_form_model",
            return_value=ItsmFormModelUpdateResult(meta={"fields": {key: {} for key in field_keys}}),
        )
        mock_system_migrate = mocker.patch(
            "apigateway.apps.bk_itsm.management.commands.register_to_itsm.system_migrate"
        )

        command.handle(**vars(options))

        mock_system_migrate.assert_not_called()
        mock_update_form_model.assert_called_once()
        assert mock_update_form_model.call_args.kwargs["key"] == "20260804110000000101"
        assert "apply_reason" in mock_update_form_model.call_args.kwargs["meta"]["fields"]

    def test_register_to_itsm_update_form_model_does_not_require_workflow_schema_updated(self, mocker):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args(["--update-form-model"])

        with open(options.template_file, encoding="utf-8") as fp:
            template = json.load(fp)

        field_keys = set(template["form_models"][0]["meta"]["fields"].keys())
        remote_properties = {"ticket_info_group": {}, "ticket_handle_group": {}}
        command = RegisterToItsmCommand()
        mocker.patch.object(
            command,
            "_get_system_workflow_list",
            return_value=ItsmWorkflowList.from_response(
                {
                    "count": 1,
                    "results": [{"form_schema": {"properties": remote_properties}}],
                }
            ),
        )
        mock_ensure_config = mocker.patch.object(command, "_ensure_config_from_template")
        mocker.patch(
            "apigateway.apps.bk_itsm.management.commands.register_to_itsm.update_form_model",
            return_value=ItsmFormModelUpdateResult(meta={"fields": {key: {} for key in field_keys}}),
        )
        mock_system_migrate = mocker.patch(
            "apigateway.apps.bk_itsm.management.commands.register_to_itsm.system_migrate"
        )

        command.handle(**vars(options))

        mock_system_migrate.assert_not_called()
        mock_ensure_config.assert_called_once()

    def test_register_to_itsm_default_template_contains_apply_reason_and_style(self):
        parser = argparse.ArgumentParser()
        RegisterToItsmCommand().add_arguments(parser)
        options = parser.parse_args([])

        with open(options.template_file, encoding="utf-8") as fp:
            template = json.load(fp)

        form_model_meta = template["form_models"][0]["meta"]
        assert form_model_meta["fields"]["apply_reason"]["type"] == "textarea"
        for translation in form_model_meta["fields"]["apply_reason"]["meta"]["translations"].values():
            assert translation["name_en"] == "Apply Reason"
            assert translation["name_zh_hans"] == "申请理由"
        assert form_model_meta["fields_order"] == [
            "gateway_name",
            "grant_dimension",
            "bk_app_code",
            "apply_record_id",
            "apply_resources",
            "apply_reason",
            "instance_approvers",
        ]

        for workflow_item in template["workflows"]:
            version = workflow_item["version"]
            submit_activity = next(
                activity for activity in version["activities"].values() if activity["type"] == "SUBMIT"
            )
            assert submit_activity["meta"]["fields"]["apply_reason"] == {"state": "readonly", "required": False}

            form_canvas_data = version["form_canvas_data"]
            assert form_canvas_data["jsonschema"]["properties"]["apply_reason"]["maxLength"] == 512

            def iter_layout_fields(layout):
                for row in layout:
                    for field in row["list"]:
                        yield field
                        yield from iter_layout_fields(field.get("list", []))

            layout = form_canvas_data["form_data"]["layout"]
            assert [field["key"] for row in layout for field in row["list"]] == [
                "ticket_info_group",
                "ticket_handle_group",
            ]
            assert [field["key"] for field in layout[0]["list"][0]["list"][0]["list"]] == [
                "ticket__title",
                "gateway_name",
            ]
            layout_fields = list(iter_layout_fields(layout))
            assert "apply_reason" in {field["key"] for field in layout_fields}
            apply_reason_layout = next(field for field in layout_fields if field["key"] == "apply_reason")
            for translation in apply_reason_layout["translations"].values():
                assert translation["name_en"] == "Apply Reason"
                assert translation["name_zh_hans"] == "申请理由"
            assert apply_reason_layout["verification"]["wordLimit"]["value"]["max"] == 512
            assert ".reason" in form_canvas_data["form_data"]["styleCode"]
            assert form_canvas_data["form_data"]["classList"] == [
                "header",
                "gateway",
                "scope",
                "target",
                "app",
                "reason",
                "ticket",
                "approver",
            ]

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
