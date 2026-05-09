# -*- coding: utf-8 -*-

from apigateway.components.bkitsm import _call_bkitsm_api, create_system_workflow, create_ticket


def test_call_bkitsm_api_with_operation_tenant_headers(settings, mocker):
    settings.BK_ITSM4_URL_PREFIX = "http://bk-itsm4.example.com/prod"

    mock_gen_headers = mocker.patch(
        "apigateway.components.bkitsm.gen_gateway_headers",
        return_value={"Content-Type": "application/json"},
    )
    mock_request = mocker.patch("apigateway.components.bkitsm.do_blueking_http_request", return_value={"ok": True})

    _call_bkitsm_api(mocker.Mock(), "/api/v1/demo/", {"k": "v"})

    mock_gen_headers.assert_called_once_with(with_operation_tenant_headers=True)
    mock_request.assert_called_once()


def test_create_system_workflow_with_system_token(settings, mocker):
    settings.BK_ITSM4_URL_PREFIX = "http://bk-itsm4.example.com/prod"
    settings.BK_ITSM4_API_TIMEOUT = 30

    mock_call = mocker.patch("apigateway.components.bkitsm._call_bkitsm_api", return_value={"key": "wf-001"})

    create_system_workflow(
        system_id="bk_apigateway",
        name="网关权限申请",
        form_schema={"type": "object", "properties": {}},
        portal_id="DEFAULT",
        predefined_approver={"type": "Variable", "id": ["approvers"]},
        system_token="token-001",
    )

    _, kwargs = mock_call.call_args
    assert kwargs["more_headers"] == {"SYSTEM-TOKEN": "token-001"}


def test_create_ticket_prefers_system_token(settings, mocker):
    settings.BK_ITSM4_URL_PREFIX = "http://bk-itsm4.example.com/prod"
    settings.BK_ITSM4_API_TIMEOUT = 30
    settings.BK_ITSM4_SYSTEM_TOKEN = "fallback-token"

    mock_call = mocker.patch("apigateway.components.bkitsm._call_bkitsm_api", return_value={"id": "t-001"})

    create_ticket(
        workflow_key="wf-001",
        form_data={"ticket__title": "test"},
        system_id="bk_apigateway",
        system_token="explicit-token",
    )

    _, kwargs = mock_call.call_args
    assert kwargs["more_headers"] == {"SYSTEM-TOKEN": "explicit-token"}


def test_create_ticket_fallback_to_global_token(settings, mocker):
    settings.BK_ITSM4_URL_PREFIX = "http://bk-itsm4.example.com/prod"
    settings.BK_ITSM4_API_TIMEOUT = 30
    settings.BK_ITSM4_SYSTEM_TOKEN = "fallback-token"

    mock_call = mocker.patch("apigateway.components.bkitsm._call_bkitsm_api", return_value={"id": "t-001"})

    create_ticket(
        workflow_key="wf-001",
        form_data={"ticket__title": "test"},
        system_id="bk_apigateway",
    )

    _, kwargs = mock_call.call_args
    assert kwargs["more_headers"] == {"SYSTEM-TOKEN": "fallback-token"}
