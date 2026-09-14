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
from unittest.mock import call

import pytest

from apigateway.components import bkiam


@pytest.fixture(autouse=True)
def _bkiam_settings(settings):
    settings.BK_IAM_V4_API_URL = "https://bkiam.example.com/prod"
    settings.BK_IAM_V4_SYSTEM_ID = "bk_apigateway"
    settings.BK_IAM_V4_CONNECT_TIMEOUT = 1.0
    settings.BK_IAM_V4_READ_TIMEOUT = 2.0


@pytest.fixture
def mock_headers(mocker):
    return mocker.patch(
        "apigateway.components.bkiam.gen_gateway_headers",
        side_effect=lambda: {"X-Bkapi-Authorization": "credentials"},
    )


def test_direct_auth_returns_explicit_decision_and_uses_gateway_contract(mocker, mock_headers):
    mock_post = mocker.patch(
        "apigateway.components.bkiam.http_post",
        side_effect=[
            (True, {"data": {"allowed": True}}),
            (True, {"data": {"allowed": False}}),
        ],
    )
    payload = {
        "subject": {"type": "user", "id": "alice"},
        "action_id": "manage_gateway",
        "resource": {"id": "42"},
    }

    assert bkiam.direct_auth(payload) is True
    assert bkiam.direct_auth(payload) is False
    assert mock_post.call_args_list == [
        call(
            url=("https://bkiam.example.com/prod/api/v1/open/rbac/authorization/systems/bk_apigateway/auth/"),
            data=payload,
            headers={"X-Bkapi-Authorization": "credentials"},
            timeout=(1.0, 2.0),
        ),
        call(
            url=("https://bkiam.example.com/prod/api/v1/open/rbac/authorization/systems/bk_apigateway/auth/"),
            data=payload,
            headers={"X-Bkapi-Authorization": "credentials"},
            timeout=(1.0, 2.0),
        ),
    ]


@pytest.mark.parametrize(
    ("status_code", "exception_type"),
    [
        (400, bkiam.BkIamParameterError),
        (401, bkiam.BkIamUnavailableError),
        (403, bkiam.BkIamUnavailableError),
        (404, bkiam.BkIamUnavailableError),
        (429, bkiam.BkIamUnavailableError),
        (500, bkiam.BkIamUnavailableError),
        (409, bkiam.BkIamError),
    ],
)
def test_http_error_classification(mocker, mock_headers, status_code, exception_type):
    mocker.patch(
        "apigateway.components.bkiam.http_post",
        return_value=(
            False,
            {
                "error": "request failed",
                "status_code": status_code,
                "response_data": {"message": "failure"},
            },
        ),
    )

    with pytest.raises(exception_type) as exc_info:
        bkiam.direct_auth(
            {
                "subject": {"type": "user", "id": "alice"},
                "action_id": "manage_gateway",
                "resource": {"id": "42"},
            }
        )

    assert exc_info.value.status_code == status_code
    assert exc_info.value.operation == "direct_auth"
    assert exc_info.value.response_data == {"message": "failure"}


def test_retrieve_system_classifies_404_as_not_found(mocker, mock_headers):
    mocker.patch(
        "apigateway.components.bkiam.http_get",
        return_value=(
            False,
            {
                "status_code": 404,
                "response_data": {"message": "not found"},
            },
        ),
    )

    with pytest.raises(bkiam.BkIamNotFoundError) as exc_info:
        bkiam.retrieve_system()

    assert exc_info.value.status_code == 404
    assert exc_info.value.operation == "retrieve_system"


@pytest.mark.parametrize(
    "response",
    [
        (False, {"error": "timeout"}),
        (True, []),
        (True, {}),
        (True, {"data": {}}),
        (True, {"data": {"allowed": "true"}}),
    ],
)
def test_direct_auth_malformed_or_transport_response_is_unavailable(mocker, mock_headers, response):
    mocker.patch("apigateway.components.bkiam.http_post", return_value=response)

    with pytest.raises(bkiam.BkIamUnavailableError):
        bkiam.direct_auth(
            {
                "subject": {"type": "user", "id": "alice"},
                "action_id": "manage_gateway",
                "resource": {"id": "42"},
            }
        )


def test_direct_auth_malformed_success_json_is_unavailable(mocker, mock_headers):
    mocker.patch("apigateway.components.bkiam.http_post", side_effect=ValueError("invalid json"))

    with pytest.raises(bkiam.BkIamUnavailableError, match="malformed JSON"):
        bkiam.direct_auth(
            {
                "subject": {"type": "user", "id": "alice"},
                "action_id": "manage_gateway",
                "resource": {"id": "42"},
            }
        )


def test_authorization_writes_add_operator_and_enforce_batch_size(mocker, mock_headers):
    mock_post = mocker.patch("apigateway.components.bkiam.http_post", return_value=(True, {}))
    mock_delete = mocker.patch("apigateway.components.bkiam.http_delete", return_value=(True, {}))
    authorization = {
        "subject": {"type": "user", "id": "alice"},
        "role_id": "administrator",
        "related_resource_type_id": "gateway",
        "resources": [{"type": "gateway", "id": "42"}],
        "expired_at": 1_800_000_000,
    }
    revoke = {key: value for key, value in authorization.items() if key != "expired_at"}

    bkiam.add_authorization([authorization], operator="admin")
    bkiam.revoke_authorization([revoke], operator="admin")

    common = {
        "url": ("https://bkiam.example.com/prod/api/v1/open/rbac/mgmt/systems/bk_apigateway/authorizations/"),
        "headers": {
            "X-Bkapi-Authorization": "credentials",
            "X-Bkiam-Operator": "admin",
        },
        "timeout": (1.0, 2.0),
    }
    mock_post.assert_called_once_with(data=[authorization], **common)
    mock_delete.assert_called_once_with(data=[revoke], **common)

    with pytest.raises(bkiam.BkIamParameterError, match="at most 20"):
        bkiam.add_authorization([authorization] * 21, operator="admin")

    oversized_resources = dict(authorization)
    oversized_resources["resources"] = [{"type": "gateway", "id": str(index)} for index in range(21)]
    with pytest.raises(bkiam.BkIamParameterError, match="resources per authorization"):
        bkiam.add_authorization([oversized_resources], operator="admin")


def test_model_endpoints_use_exact_paths_and_return_data(mocker, mock_headers):
    mock_get = mocker.patch(
        "apigateway.components.bkiam.http_get",
        side_effect=[
            (True, {"data": {"id": "bk_apigateway"}}),
            (True, {"data": {"count": 1, "results": [{"id": "gateway"}]}}),
            (True, {"data": {"count": 1, "results": [{"id": "manage_gateway"}]}}),
            (True, {"data": {"count": 1, "results": [{"id": "administrator"}]}}),
        ],
    )
    mock_post = mocker.patch(
        "apigateway.components.bkiam.http_post",
        side_effect=[
            (True, {"data": {"id": "bk_apigateway"}}),
            (True, {"data": ["gateway"]}),
            (True, {"data": ["manage_gateway"]}),
            (True, {"data": ["administrator"]}),
            (True, {"data": ["manage_gateway"]}),
        ],
    )
    mock_put = mocker.patch("apigateway.components.bkiam.http_put", return_value=(True, {}))

    assert bkiam.retrieve_system() == {"id": "bk_apigateway"}
    assert bkiam.create_system({"id": "bk_apigateway", "name": "API 网关", "clients": ["bk_apigateway"]}) == {
        "id": "bk_apigateway"
    }
    bkiam.update_system({"managers": ["admin"]})
    assert bkiam.list_resource_type()["count"] == 1
    assert bkiam.batch_create_resource_type([{"id": "gateway", "name": "网关"}]) == ["gateway"]
    bkiam.update_resource_type("gateway", {"name": "网关"})
    assert bkiam.list_action()["results"][0]["id"] == "manage_gateway"
    assert bkiam.batch_create_action(
        [{"id": "manage_gateway", "name": "管理网关", "resource_type_id": "gateway"}]
    ) == ["manage_gateway"]
    bkiam.update_action("manage_gateway", {"name": "管理网关"})
    assert bkiam.list_role()["results"][0]["id"] == "administrator"
    assert bkiam.batch_create_role(
        [
            {
                "id": "administrator",
                "name": "管理员",
                "actions": [{"id": "manage_gateway", "resource_type_id": "gateway"}],
            }
        ]
    ) == ["administrator"]
    bkiam.update_role("administrator", {"name": "管理员"})
    assert bkiam.batch_create_role_action(
        "administrator",
        [{"id": "manage_gateway", "resource_type_id": "gateway"}],
    ) == ["manage_gateway"]

    called_urls = [item.kwargs["url"] for item in mock_get.call_args_list]
    assert called_urls == [
        "https://bkiam.example.com/prod/api/v1/open/rbac/model/systems/bk_apigateway/",
        ("https://bkiam.example.com/prod/api/v1/open/rbac/model/systems/bk_apigateway/resource-types/"),
        "https://bkiam.example.com/prod/api/v1/open/rbac/model/systems/bk_apigateway/actions/",
        "https://bkiam.example.com/prod/api/v1/open/rbac/model/systems/bk_apigateway/roles/",
    ]
    assert mock_post.call_count == 5
    assert mock_put.call_count == 4


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"code": 0, "message": "ok"},
    ],
)
def test_write_endpoints_accept_success_without_data(mocker, mock_headers, response):
    mocker.patch("apigateway.components.bkiam.http_put", return_value=(True, response))
    mocker.patch("apigateway.components.bkiam.http_post", return_value=(True, response))
    mocker.patch("apigateway.components.bkiam.http_delete", return_value=(True, response))
    authorization = {
        "subject": {"type": "user", "id": "alice"},
        "role_id": "administrator",
        "related_resource_type_id": "gateway",
        "resources": [{"type": "gateway", "id": "42"}],
        "expired_at": 1_800_000_000,
    }
    revoke = {key: value for key, value in authorization.items() if key != "expired_at"}

    assert bkiam.update_system({"managers": ["admin"]}) is None
    assert bkiam.add_authorization([authorization], operator="admin") is None
    assert bkiam.revoke_authorization([revoke], operator="admin") is None


def test_delete_role_actions_uses_ids_query_parameter(mocker, mock_headers):
    mock_delete = mocker.patch("apigateway.components.bkiam.http_delete", return_value=(True, {}))

    bkiam.batch_delete_role_action("administrator", ["manage_gateway", "operate_gateway"])

    mock_delete.assert_called_once_with(
        url=(
            "https://bkiam.example.com/prod/api/v1/open/rbac/model/systems/bk_apigateway/roles/administrator/actions/"
        ),
        data=None,
        headers={"X-Bkapi-Authorization": "credentials"},
        timeout=(1.0, 2.0),
        params={"ids": "manage_gateway,operate_gateway"},
    )


def test_list_authorization_subject_returns_validated_page(mocker, mock_headers):
    mock_post = mocker.patch(
        "apigateway.components.bkiam.http_post",
        return_value=(
            True,
            {
                "data": {
                    "count": 1,
                    "results": [
                        {
                            "subject": {"type": "user", "id": "alice"},
                            "expired_at": 1_800_000_000,
                        }
                    ],
                }
            },
        ),
    )
    payload = {
        "role_id": "administrator",
        "related_resource_type_id": "gateway",
        "resource": {"type": "gateway", "id": "42"},
        "page": 2,
        "page_size": 100,
    }

    assert bkiam.list_authorization_subject(payload)["count"] == 1
    mock_post.assert_called_once_with(
        url=(
            "https://bkiam.example.com/prod/api/v1/open/rbac/mgmt/systems/bk_apigateway/authorizations/query-subject/"
        ),
        data=payload,
        headers={"X-Bkapi-Authorization": "credentials"},
        timeout=(1.0, 2.0),
    )


@pytest.mark.parametrize(
    ("page", "page_size"),
    [
        (0, 100),
        (1, 0),
        (1, 101),
    ],
)
def test_list_endpoints_reject_invalid_pagination(mocker, mock_headers, page, page_size):
    http_get = mocker.patch("apigateway.components.bkiam.http_get")

    with pytest.raises(bkiam.BkIamParameterError, match="page_size between"):
        bkiam.list_role(page=page, page_size=page_size)

    http_get.assert_not_called()
