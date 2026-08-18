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
from pydantic import ValidationError

from apigateway.common.error_codes import error_codes
from apigateway.components.bkitsm import (
    ItsmFormModelUpdateResult,
    ItsmTicketItem,
    ItsmTicketSearchResult,
    ItsmWorkflowList,
    _call_bkitsm_api,
    create_ticket,
    get_ticket_by_id,
    system_workflow_list,
    update_form_model,
)


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


def test_itsm_workflow_list_requires_results_shape():
    workflow_list = ItsmWorkflowList.from_response({"count": 1, "results": [{"form_schema": {"properties": {}}}]})

    assert len(workflow_list.workflows) == 1

    with pytest.raises(ValidationError):
        ItsmWorkflowList.from_response({"count": 1, "data": []})

    with pytest.raises(ValidationError):
        ItsmWorkflowList.from_response({"count": 1, "results": ["invalid"]})


def test_system_workflow_list_returns_empty_when_system_not_found(settings, mocker):
    settings.BK_ITSM4_URL_PREFIX = "http://bk-itsm4.example.com/prod"
    settings.BK_ITSM4_API_TIMEOUT = 30
    settings.BK_ITSM4_SYSTEM_TOKEN = ""

    mock_http_get = mocker.patch(
        "apigateway.components.bkitsm.http_get",
        return_value=(
            False,
            {
                "error": "status_code is 400, not 2xx!",
                "status_code": 400,
                "response_data": {
                    "result": False,
                    "code": "40000",
                    "message": "message text should not be parsed",
                    "data": {"detail": "message text should not be parsed"},
                },
            },
        ),
    )
    mock_http_get.__name__ = "http_get"

    result = system_workflow_list(system_id="bk-apigateway")

    assert result.is_registered is False
    assert result.count == 0
    assert result.workflows == []
    assert "ignored_error_status_codes" not in mock_http_get.call_args.kwargs


@pytest.mark.parametrize(
    "status_code, code",
    [
        (400, "40001"),
        (500, "40000"),
    ],
)
def test_system_workflow_list_keeps_unexpected_remote_error(settings, mocker, status_code, code):
    settings.BK_ITSM4_URL_PREFIX = "http://bk-itsm4.example.com/prod"
    settings.BK_ITSM4_API_TIMEOUT = 30
    settings.BK_ITSM4_SYSTEM_TOKEN = ""

    mock_http_get = mocker.patch(
        "apigateway.components.bkitsm.http_get",
        return_value=(
            False,
            {
                "error": f"status_code is {status_code}, not 2xx!",
                "status_code": status_code,
                "response_data": {"result": False, "code": code, "message": "remote error"},
            },
        ),
    )
    mock_http_get.__name__ = "http_get"

    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__):
        system_workflow_list(system_id="bk-apigateway")


def test_itsm_form_model_update_result_extract_updated_fields():
    result = ItsmFormModelUpdateResult.from_response({"meta": {"fields": {"apply_reason": {}, "gateway_name": {}}}})

    assert result.updated_field_keys == frozenset({"apply_reason", "gateway_name"})


def test_itsm_ticket_item_prefers_first_history_user():
    detail = ItsmTicketItem.model_validate(
        {
            "id": "t-001",
            "history_processors": [
                {"id": "admin", "type": "user", "display": "管理员(admin)"},
                {"id": "neoling", "type": "user", "display": "neoling"},
            ],
        }
    )

    assert detail.actual_approver == "admin"


def test_itsm_ticket_item_returns_empty_without_history_user():
    detail = ItsmTicketItem.model_validate(
        {
            "id": "t-001",
            "history_processors": [
                {"id": "group-a", "type": "group", "display": "group-a"},
            ],
        }
    )

    assert detail.actual_approver == ""


def test_itsm_ticket_item_requires_processors_list():
    with pytest.raises(ValidationError):
        ItsmTicketItem.model_validate(
            {
                "id": "t-001",
                "history_processors": {"id": "admin", "type": "user"},
            }
        )


def test_itsm_ticket_search_result_extract_actual_approver():
    result = ItsmTicketSearchResult.from_response(
        {
            "results": [
                {
                    "id": "t-001",
                    "history_processors": [
                        {"id": "admin", "type": "user", "display": "管理员(admin)"},
                        {"id": "neoling", "type": "user", "display": "neoling"},
                    ],
                }
            ],
            "page": 1,
            "page_size": 10,
            "count": 1,
        }
    )

    assert result.actual_approver == "admin"


def test_itsm_ticket_search_result_requires_results_list():
    with pytest.raises(ValidationError):
        ItsmTicketSearchResult.from_response({"results": {}, "count": 1})


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


def test_update_form_model_fallback_to_global_token(settings, mocker):
    settings.BK_ITSM4_URL_PREFIX = "http://bk-itsm4.example.com/prod"
    settings.BK_ITSM4_API_TIMEOUT = 30
    settings.BK_ITSM4_SYSTEM_TOKEN = "fallback-token"

    mock_call = mocker.patch(
        "apigateway.components.bkitsm._call_bkitsm_api",
        return_value={"meta": {"fields": {"apply_reason": {}}}},
    )

    result = update_form_model(
        key="fm-001",
        name="bk-apigateway",
        meta={"fields": {}},
        system_id="bk-apigateway",
    )

    _, kwargs = mock_call.call_args
    assert kwargs["more_headers"] == {"SYSTEM-TOKEN": "fallback-token"}
    assert result.updated_field_keys == frozenset({"apply_reason"})


def test_get_ticket_by_id(settings, mocker):
    settings.BK_ITSM4_URL_PREFIX = "http://bk-itsm4.example.com/prod"
    settings.BK_ITSM4_API_TIMEOUT = 30
    settings.BK_ITSM4_QUERY_OPERATOR = "admin"

    mock_call = mocker.patch(
        "apigateway.components.bkitsm._call_bkitsm_api",
        return_value={
            "results": [{"id": "t-001", "history_processors": [{"id": "admin", "type": "user"}]}],
            "count": 1,
        },
    )

    result = get_ticket_by_id("t-001")

    args, kwargs = mock_call.call_args
    assert args[1] == "/api/v1/ticket_search/full_text_search/"
    assert args[2] == {
        "page": 1,
        "page_size": 1,
        "id__in": "t-001",
        "operator": "admin",
        "group_key": "all",
    }
    assert kwargs["timeout"] == 30
    assert result.actual_approver == "admin"
    assert result.count == 1
