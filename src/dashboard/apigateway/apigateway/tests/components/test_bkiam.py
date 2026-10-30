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
    settings.BK_API_URL_TMPL = "https://{api_name}.example.com"


@pytest.fixture
def mock_headers(mocker):
    return mocker.patch(
        "apigateway.components.bkiam.gen_gateway_headers",
        side_effect=lambda **_kwargs: {"X-Bkapi-Authorization": "credentials"},
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

    assert bkiam.direct_auth(payload, tenant_id="tenant-a") is True
    assert bkiam.direct_auth(payload, tenant_id="tenant-a") is False
    assert mock_headers.call_args_list == [call(), call()]
    assert mock_post.call_args_list == [
        call(
            url=("https://bkiam.example.com/prod/api/v1/open/rbac/authorization/systems/bk_apigateway/auth/"),
            data=payload,
            headers={"X-Bkapi-Authorization": "credentials", "X-Bk-Tenant-Id": "tenant-a"},
            timeout=bkiam.REQUEST_TIMEOUT,
            request_session=None,
        ),
        call(
            url=("https://bkiam.example.com/prod/api/v1/open/rbac/authorization/systems/bk_apigateway/auth/"),
            data=payload,
            headers={"X-Bkapi-Authorization": "credentials", "X-Bk-Tenant-Id": "tenant-a"},
            timeout=bkiam.REQUEST_TIMEOUT,
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
            },
            tenant_id="tenant-a",
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
            },
            tenant_id="tenant-a",
        )


def test_direct_auth_malformed_success_json_raises(mocker, mock_headers):
    mocker.patch("apigateway.components.bkiam.http_post", side_effect=ValueError("invalid json"))

    with pytest.raises(ValueError, match="invalid json"):
        bkiam.direct_auth(
            {
                "subject": {"type": "user", "id": "alice"},
                "action_id": "manage_gateway",
                "resource": {"id": "42"},
            },
            tenant_id="tenant-a",
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

    bkiam.add_authorization([authorization], operator="admin", tenant_id="tenant-a")
    bkiam.revoke_authorization([revoke], operator="admin", tenant_id="tenant-a")

    common = {
        "url": ("https://bkiam.example.com/prod/api/v1/open/rbac/mgmt/systems/bk_apigateway/authorizations/"),
        "headers": {
            "X-Bkapi-Authorization": "credentials",
            "X-Bk-Tenant-Id": "tenant-a",
            "X-Bkiam-Operator": "admin",
        },
        "timeout": bkiam.REQUEST_TIMEOUT,
        "request_session": None,
    }
    mock_post.assert_called_once_with(data=[authorization], **common)
    mock_delete.assert_called_once_with(data=[revoke], **common)

    with pytest.raises(bkiam.BkIamParameterError, match="at most 20"):
        bkiam.add_authorization([authorization] * 21, operator="admin", tenant_id="tenant-a")

    oversized_resources = dict(authorization)
    oversized_resources["resources"] = [{"type": "gateway", "id": str(index)} for index in range(21)]
    with pytest.raises(bkiam.BkIamParameterError, match="resources per authorization"):
        bkiam.add_authorization([oversized_resources], operator="admin", tenant_id="tenant-a")


def _user_authorization(username: str) -> dict:
    return {
        "subject": {"type": "user", "id": username},
        "role_id": "administrator",
        "related_resource_type_id": "gateway",
        "resources": [{"type": "gateway", "id": "127"}],
        "expired_at": 1_800_000_000,
    }


def _missing_users_failure(*usernames: str):
    return (
        False,
        {
            "error": "status_code is 400, not 2xx!",
            "status_code": 400,
            "response_data": {
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "some subject not exists",
                    "data": {"missing_users": list(usernames)},
                }
            },
        },
    )


def test_add_authorization_retries_once_without_missing_users(mocker, mock_headers, caplog):
    kept = _user_authorization("alice")
    missing = _user_authorization("jsorwan")
    mock_post = mocker.patch(
        "apigateway.components.bkiam.http_post",
        side_effect=[
            _missing_users_failure("jsorwan", "lorryxywu"),
            (True, {"data": None}),
        ],
    )
    caplog.set_level("WARNING", logger="apigateway.components.bkiam")

    assert bkiam.add_authorization([kept, missing], operator="admin", tenant_id="tenant-a") is None

    assert [item.kwargs["data"] for item in mock_post.call_args_list] == [[kept, missing], [kept]]
    assert "missing_users=['jsorwan', 'lorryxywu']" in caplog.text
    assert mock_post.call_count == 2


def test_add_authorization_retry_failure_is_logged(mocker, mock_headers, caplog):
    kept = _user_authorization("alice")
    missing = _user_authorization("jsorwan")
    mock_post = mocker.patch(
        "apigateway.components.bkiam.http_post",
        side_effect=[
            _missing_users_failure("jsorwan"),
            (False, {"error": "status_code is 500, not 2xx!", "status_code": 500}),
        ],
    )
    caplog.set_level("ERROR", logger="apigateway.components.bkiam")

    assert bkiam.add_authorization([kept, missing], operator="admin", tenant_id="tenant-a") is None

    assert mock_post.call_count == 2
    assert mock_post.call_args_list[1].kwargs["data"] == [kept]
    assert "bkiam authorizations failed" in caplog.text
    assert "status_code is 500" in caplog.text


def test_add_authorization_skips_retry_when_every_subject_is_missing(mocker, mock_headers, caplog):
    missing = _user_authorization("jsorwan")
    mock_post = mocker.patch(
        "apigateway.components.bkiam.http_post",
        return_value=_missing_users_failure("jsorwan"),
    )
    caplog.set_level("ERROR", logger="apigateway.components.bkiam")

    assert bkiam.add_authorization([missing], operator="admin", tenant_id="tenant-a") is None

    mock_post.assert_called_once()
    assert "bkiam authorizations failed" in caplog.text
    assert "status_code is 400" in caplog.text


def test_add_authorization_without_missing_users_logs_and_returns(mocker, mock_headers, caplog):
    mock_post = mocker.patch(
        "apigateway.components.bkiam.http_post",
        return_value=(False, {"error": "status_code is 500, not 2xx!", "status_code": 500}),
    )
    caplog.set_level("ERROR", logger="apigateway.components.bkiam")

    assert bkiam.add_authorization([_user_authorization("alice")], operator="admin", tenant_id="tenant-a") is None

    mock_post.assert_called_once()
    assert "bkiam authorizations failed" in caplog.text
    assert "status_code is 500" in caplog.text


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
    assert bkiam.list_resource_type(page=2, page_size=50)["count"] == 1
    assert bkiam.batch_create_resource_type([{"id": "gateway", "name": "网关"}]) == ["gateway"]
    bkiam.update_resource_type("gateway", {"name": "网关"})
    assert bkiam.list_action(page=2, page_size=50)["results"][0]["id"] == "manage_gateway"
    assert bkiam.batch_create_action(
        [{"id": "manage_gateway", "name": "管理网关", "resource_type_id": "gateway"}]
    ) == ["manage_gateway"]
    bkiam.update_action("manage_gateway", {"name": "管理网关"})
    assert bkiam.list_role(page=2, page_size=50)["results"][0]["id"] == "administrator"
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
    assert [item.kwargs["data"] for item in mock_get.call_args_list] == [
        {},
        {"page": 2, "page_size": 50},
        {"page": 2, "page_size": 50},
        {"page": 2, "page_size": 50},
    ]
    assert mock_post.call_count == 5
    assert mock_put.call_count == 4
    assert mock_headers.call_args_list == [call()] * 13


@pytest.mark.parametrize(
    "response",
    [
        {},
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
    assert bkiam.add_authorization([authorization], operator="admin", tenant_id="tenant-a") is None
    assert bkiam.revoke_authorization([revoke], operator="admin", tenant_id="tenant-a") is None


def test_delete_role_actions_uses_ids_query_parameter(mocker, mock_headers):
    mock_delete = mocker.patch("apigateway.components.bkiam.http_delete", return_value=(True, {"data": None}))

    bkiam.batch_delete_role_action("administrator", ["manage_gateway", "operate_gateway"])

    mock_delete.assert_called_once_with(
        url=(
            "https://bkiam.example.com/prod/api/v1/open/rbac/model/systems/bk_apigateway/roles/administrator/actions/"
        ),
        data=None,
        headers={"X-Bkapi-Authorization": "credentials", "X-Bk-Tenant-Id": "system"},
        timeout=bkiam.REQUEST_TIMEOUT,
        request_session=None,
        params={"ids": "manage_gateway,operate_gateway"},
    )


def test_list_authorization_subject_returns_page(mocker, mock_headers):
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

    assert bkiam.list_authorization_subject(payload, tenant_id="tenant-a") == {
        "count": 1,
        "results": [{"id": "alice", "expired_at": 1_800_000_000}],
    }
    mock_post.assert_called_once_with(
        url=(
            "https://bkiam.example.com/prod/api/v1/open/rbac/mgmt/systems/bk_apigateway/authorizations/query-subject/"
        ),
        data=payload,
        headers={"X-Bkapi-Authorization": "credentials", "X-Bk-Tenant-Id": "tenant-a"},
        timeout=bkiam.REQUEST_TIMEOUT,
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
            },
            tenant_id="tenant-a",
        )


def _authorization_subject_response(count, results):
    return (True, {"data": {"count": count, "results": results}})


def _authorization_subject_raw(username):
    return {"subject": {"type": "user", "id": username}, "expired_at": 1_800_000_000}


def test_iter_authorization_subjects_pages_until_count(mocker, mock_headers):
    mock_post = _patch_http(
        mocker,
        "http_post",
        side_effect=[
            _authorization_subject_response(
                3,
                [_authorization_subject_raw("a"), _authorization_subject_raw("b")],
            ),
            _authorization_subject_response(3, [_authorization_subject_raw("c")]),
        ],
    )
    payload = {
        "role_id": "administrator",
        "related_resource_type_id": "gateway",
        "resource": {"type": "gateway", "id": "42"},
        "page_size": 2,
    }

    assert list(bkiam.iter_authorization_subjects(payload, tenant_id="tenant-a")) == [
        {"id": "a", "expired_at": 1_800_000_000},
        {"id": "b", "expired_at": 1_800_000_000},
        {"id": "c", "expired_at": 1_800_000_000},
    ]
    assert [call.kwargs["data"]["page"] for call in mock_post.call_args_list] == [1, 2]
    assert all(call.kwargs["headers"]["X-Bk-Tenant-Id"] == "tenant-a" for call in mock_post.call_args_list)


def test_iter_authorization_subjects_stops_on_empty_page_when_count_shrinks(mocker, mock_headers):
    mock_post = _patch_http(
        mocker,
        "http_post",
        side_effect=[
            _authorization_subject_response(3, [_authorization_subject_raw("a")]),
            _authorization_subject_response(1, []),
        ],
    )
    payload = {
        "role_id": "administrator",
        "related_resource_type_id": "gateway",
        "resource": {"type": "gateway", "id": "42"},
        "page_size": 1,
    }

    assert list(bkiam.iter_authorization_subjects(payload, tenant_id="tenant-a")) == [
        {"id": "a", "expired_at": 1_800_000_000},
    ]
    assert [call.kwargs["data"]["page"] for call in mock_post.call_args_list] == [1, 2]


def test_iter_authorization_subjects_uses_first_count_as_upper_bound(mocker, mock_headers):
    mock_post = _patch_http(
        mocker,
        "http_post",
        side_effect=[
            _authorization_subject_response(2, [_authorization_subject_raw("a")]),
            _authorization_subject_response(
                3,
                [_authorization_subject_raw("b"), _authorization_subject_raw("c")],
            ),
        ],
    )
    payload = {
        "role_id": "administrator",
        "related_resource_type_id": "gateway",
        "resource": {"type": "gateway", "id": "42"},
        "page_size": 1,
    }

    assert list(bkiam.iter_authorization_subjects(payload, tenant_id="tenant-a")) == [
        {"id": "a", "expired_at": 1_800_000_000},
        {"id": "b", "expired_at": 1_800_000_000},
    ]
    assert [call.kwargs["data"]["page"] for call in mock_post.call_args_list] == [1, 2]
