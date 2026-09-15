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

from apigateway.common.error_codes import error_codes
from apigateway.components import bkiam


@pytest.fixture(autouse=True)
def _bkiam_settings(settings):
    settings.BK_IAM_V4_API_URL = "https://bkiam.example.com/prod"


@pytest.fixture
def mock_headers(mocker):
    return mocker.patch(
        "apigateway.components.bkiam.gen_gateway_headers",
        side_effect=lambda: {"X-Bkapi-Authorization": "credentials"},
    )


def _patch_http(mocker, name, **kwargs):
    mock = mocker.patch(f"apigateway.components.bkiam.{name}", **kwargs)
    mock.__name__ = name
    return mock


def test_direct_auth_returns_explicit_decision_and_uses_gateway_contract(mocker, mock_headers):
    mock_post = _patch_http(
        mocker,
        "http_post",
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
            request_session=None,
        ),
        call(
            url=("https://bkiam.example.com/prod/api/v1/open/rbac/authorization/systems/bk_apigateway/auth/"),
            data=payload,
            headers={"X-Bkapi-Authorization": "credentials"},
            timeout=(1.0, 2.0),
            request_session=None,
        ),
    ]


def test_http_error_raises_remote_request_error(mocker, mock_headers):
    mock_post = _patch_http(
        mocker,
        "http_post",
        return_value=(
            False,
            {
                "error": "status_code is 500, not 2xx!",
                "status_code": 500,
                "response_data": {"message": "failure"},
            },
        ),
    )

    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__):
        bkiam.direct_auth(
            {
                "subject": {"type": "user", "id": "alice"},
                "action_id": "manage_gateway",
                "resource": {"id": "42"},
            }
        )


def test_retrieve_system_classifies_404_as_not_found(mocker, mock_headers):
    _patch_http(
        mocker,
        "http_get",
        return_value=(
            False,
            {
                "status_code": 404,
                "response_data": {"message": "not found"},
            },
        ),
    )

    with pytest.raises(bkiam.BkIamNotFoundError, match="does not exist"):
        bkiam.retrieve_system()


def test_direct_auth_transport_response_is_unavailable(mocker, mock_headers):
    mock_post = _patch_http(mocker, "http_post", return_value=(False, {"error": "timeout"}))

    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__):
        bkiam.direct_auth(
            {
                "subject": {"type": "user", "id": "alice"},
                "action_id": "manage_gateway",
                "resource": {"id": "42"},
            }
        )


def test_direct_auth_malformed_success_json_raises(mocker, mock_headers):
    mocker.patch("apigateway.components.bkiam.http_post", side_effect=ValueError("invalid json"))

    with pytest.raises(ValueError, match="invalid json"):
        bkiam.direct_auth(
            {
                "subject": {"type": "user", "id": "alice"},
                "action_id": "manage_gateway",
                "resource": {"id": "42"},
            }
        )


def test_authorization_writes_add_operator_and_enforce_batch_size(mocker, mock_headers):
    mock_post = mocker.patch("apigateway.components.bkiam.http_post", return_value=(True, {"data": None}))
    mock_delete = mocker.patch("apigateway.components.bkiam.http_delete", return_value=(True, {"data": None}))
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
        "request_session": None,
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
    mock_get = _patch_http(
        mocker,
        "http_get",
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
    mock_put = mocker.patch("apigateway.components.bkiam.http_put", return_value=(True, {"data": None}))

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
        {"data": None},
        {"code": 0, "message": "ok", "data": None},
    ],
)
def test_write_endpoints_ignore_success_data(mocker, mock_headers, response):
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
    mock_delete = mocker.patch("apigateway.components.bkiam.http_delete", return_value=(True, {"data": None}))

    bkiam.batch_delete_role_action("administrator", ["manage_gateway", "operate_gateway"])

    mock_delete.assert_called_once_with(
        url=(
            "https://bkiam.example.com/prod/api/v1/open/rbac/model/systems/bk_apigateway/roles/administrator/actions/"
        ),
        data=None,
        headers={"X-Bkapi-Authorization": "credentials"},
        timeout=(1.0, 2.0),
        request_session=None,
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

    assert bkiam.list_authorization_subject(payload) == {
        "count": 1,
        "results": [{"id": "alice", "expired_at": 1_800_000_000}],
    }
    mock_post.assert_called_once_with(
        url=(
            "https://bkiam.example.com/prod/api/v1/open/rbac/mgmt/systems/bk_apigateway/authorizations/query-subject/"
        ),
        data=payload,
        headers={"X-Bkapi-Authorization": "credentials"},
        timeout=(1.0, 2.0),
        request_session=None,
    )


def test_list_authorization_subject_rejects_non_user_subject(mocker, mock_headers):
    mocker.patch(
        "apigateway.components.bkiam.http_post",
        return_value=(
            True,
            {
                "data": {
                    "count": 1,
                    "results": [
                        {
                            "subject": {"type": "department", "id": "1"},
                            "expired_at": 1_800_000_000,
                        }
                    ],
                }
            },
        ),
    )

    with pytest.raises(ValueError, match="subject type must be user"):
        bkiam.list_authorization_subject(
            {
                "role_id": "administrator",
                "related_resource_type_id": "gateway",
                "resource": {"type": "gateway", "id": "42"},
                "page": 1,
                "page_size": 100,
            }
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
