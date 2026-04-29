# -*- coding: utf-8 -*-

import pytest
from ddf import G

from apigateway.apps.bk_itsm.models import ItsmSystemConfig
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper

pytestmark = pytest.mark.django_db


class TestItsmPermissionApplyHelper:
    def test_extract_ticket_id(self):
        assert ItsmPermissionApplyHelper.extract_ticket_id({"id": "t-001"}) == "t-001"
        assert ItsmPermissionApplyHelper.extract_ticket_id({"ticket": {"id": "t-002"}}) == "t-002"
        assert ItsmPermissionApplyHelper.extract_ticket_id({"ticket_id": 1003}) == "1003"
        assert ItsmPermissionApplyHelper.extract_ticket_id({"data": {"id": "t-004"}}) == "t-004"
        assert ItsmPermissionApplyHelper.extract_ticket_id(None) == ""

    def test_create_permission_apply_ticket(self, mocker):
        config = G(
            ItsmSystemConfig,
            system_code="bk_apigateway",
            itsm_system_id="bk_apigateway",
            system_token="token-001",
            workflow_key="wf-001",
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
            reason="test-reason",
            expire_days=180,
            applied_by="admin",
            apply_record_id=123,
            approvers=["u1", "u2"],
        )

        _, kwargs = mock_create_ticket.call_args
        assert kwargs["workflow_key"] == "wf-001"
        assert kwargs["system_id"] == "bk_apigateway"
        assert kwargs["system_token"] == "token-001"
        assert kwargs["callback_token"] == "cb-token-123"
        assert kwargs["form_data"]["apply_record_id"] == 123
        assert kwargs["form_data"]["grant_dimension"] == "resource"
        assert kwargs["form_data"]["reason"] == "test-reason"
        assert kwargs["form_data"]["expire_days"] == 180
        assert kwargs["form_data"]["approvers"] == ["u1", "u2"]

    def test_is_ready_false_when_config_not_exists(self):
        helper = ItsmPermissionApplyHelper(system_code="not-exists")
        assert helper.is_ready() is False
