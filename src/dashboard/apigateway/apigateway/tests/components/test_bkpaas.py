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

from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.components.bkauth import BkAuthAppNotFoundError
from apigateway.components.bkpaas import (
    REQ_PAAS_API_TIMEOUT,
    get_app_maintainers,
    get_paas_apps_by_username,
    get_paas_deploy_phases_framework,
    get_paas_deploy_phases_instance,
    get_paas_deployment_result,
    get_paas_offline_result,
    get_paas_repo_authorization,
    get_paas_repo_branch_info,
    get_paas_runtime_info,
    get_pass_deploy_streams_history_events,
    paas_app_module_offline,
    set_paas_stage_env,
)


def test_get_paas_repo_authorization__authorized(mocker):
    user_credentials = UserCredentials(credentials="bk-token", tenant_id="default")
    mocker.patch("apigateway.components.bkpaas.get_paas3_url_prefix", return_value="https://paas.example.com/prod")
    mock_gen_gateway_headers = mocker.patch(
        "apigateway.components.bkpaas.gen_gateway_headers",
        return_value={"X-Bkapi-Authorization": "authorization"},
    )
    mock_http_get = mocker.patch(
        "apigateway.components.bkpaas.http_get",
        return_value=(True, {"results": [{"fullname": "bkapps/demo"}]}),
    )

    result = get_paas_repo_authorization(user_credentials=user_credentials)

    assert result == {
        "authorized": True,
        "message": "",
        "address": "",
        "auth_docs": "",
    }
    mock_gen_gateway_headers.assert_called_once_with(user_credentials)
    mock_http_get.assert_called_once_with(
        "https://paas.example.com/prod/api/sourcectl/tc_git/repos/",
        {},
        headers={"X-Bkapi-Authorization": "authorization"},
        timeout=REQ_PAAS_API_TIMEOUT,
    )


def test_get_paas_repo_authorization__unauthorized(mocker):
    mocker.patch("apigateway.components.bkpaas.get_paas3_url_prefix", return_value="https://paas.example.com/prod")
    mocker.patch(
        "apigateway.components.bkpaas.gen_gateway_headers", return_value={"X-Bkapi-Authorization": "authorization"}
    )
    mocker.patch(
        "apigateway.components.bkpaas.http_get",
        return_value=(
            False,
            {
                "error": "status_code is 403, not 2xx!",
                "status_code": 403,
                "response_data": {
                    "message": "用户未关联 oauth 授权",
                    "address": "https://git.example.com/oauth/authorize",
                    "auth_docs": "http://docs.example.com/tc_git_oauth",
                },
            },
        ),
    )

    result = get_paas_repo_authorization()

    assert result == {
        "authorized": False,
        "message": "用户未关联 oauth 授权",
        "address": "https://git.example.com/oauth/authorize",
        "auth_docs": "http://docs.example.com/tc_git_oauth",
    }


def test_get_paas_repo_authorization__failed(mocker):
    mocker.patch("apigateway.components.bkpaas.get_paas3_url_prefix", return_value="https://paas.example.com/prod")
    mocker.patch(
        "apigateway.components.bkpaas.gen_gateway_headers", return_value={"X-Bkapi-Authorization": "authorization"}
    )
    mocker.patch("apigateway.components.bkpaas.http_get", return_value=(False, {"error": "request failed"}))

    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__):
        get_paas_repo_authorization()


def test_get_app_maintainers_returns_empty_when_bkauth_app_not_found(mocker):
    mocker.patch(
        "apigateway.components.bkpaas.get_tenant_id_for_app_developers",
        side_effect=BkAuthAppNotFoundError("app does not exist in bkauth, app_code=missing-app"),
    )
    mock_get_app = mocker.patch("apigateway.components.bkpaas._get_app_with_cache")

    assert get_app_maintainers("missing-app") == []
    mock_get_app.assert_not_called()


def test_get_app_maintainers_raises_when_bkauth_remote_error_not_app_not_found(mocker):
    mocker.patch(
        "apigateway.components.bkpaas.get_tenant_id_for_app_developers",
        side_effect=error_codes.REMOTE_REQUEST_ERROR.format(
            "request bkauth fail! "
            "Request=[http_get /api/v1/apps/demo request_id=request-id]"
            "error=status_code is 500, not 2xx! GET /api/v1/apps/demo, request_id=request-id"
        ),
    )
    mock_get_app = mocker.patch("apigateway.components.bkpaas._get_app_with_cache")

    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__):
        get_app_maintainers("demo")

    mock_get_app.assert_not_called()


class TestGetPaaSAppsByUsername:
    def test_get_paas_apps_by_username_sends_tenant_header(self, mocker):
        mocker.patch("apigateway.components.bkpaas.get_paas3_url_prefix", return_value="https://paas.example.com/prod")
        mocker.patch("apigateway.components.bkpaas.gen_gateway_headers", return_value={"X-Gateway": "1"})
        mock_http_get = mocker.patch(
            "apigateway.components.bkpaas.http_get",
            return_value=(True, [{"code": "app-001", "name": "App 001"}]),
        )

        result = get_paas_apps_by_username("alice", "tenant-a")

        assert result == [{"code": "app-001", "name": "App 001"}]
        mock_http_get.assert_called_once()
        _, data = mock_http_get.call_args.args[:2]
        assert data == {"username": "alice"}
        assert mock_http_get.call_args.kwargs["headers"] == {
            "X-Gateway": "1",
            "X-Bk-Tenant-Id": "tenant-a",
        }


@pytest.mark.parametrize(
    "call_paas_api",
    [
        pytest.param(lambda: paas_app_module_offline("demo", "default", "prod"), id="offline"),
        pytest.param(
            lambda: set_paas_stage_env("demo", "default", "prod", {"RELEASE_VERSION": "1.0.0"}),
            id="set-stage-env",
        ),
        pytest.param(
            lambda: get_paas_deploy_phases_framework("demo", "default", "prod"),
            id="deploy-phases-framework",
        ),
        pytest.param(
            lambda: get_paas_deploy_phases_instance("demo", "default", "prod", "deploy-id"),
            id="deploy-phases-instance",
        ),
        pytest.param(
            lambda: get_pass_deploy_streams_history_events("deploy-id"),
            id="deploy-stream-events",
        ),
        pytest.param(
            lambda: get_paas_deployment_result("demo", "default", "deploy-id"),
            id="deployment-result",
        ),
        pytest.param(
            lambda: get_paas_offline_result("demo", "default", "deploy-id"),
            id="offline-result",
        ),
        pytest.param(lambda: get_paas_runtime_info("demo", "default"), id="runtime-info"),
        pytest.param(lambda: get_paas_repo_branch_info("demo", "default"), id="repo-branch-info"),
    ],
)
def test_paas_api_failure_raises_readable_remote_request_error(mocker, call_paas_api):
    detail = "无法获取源码信息: AccessToken无权限访问该仓库"
    failed_response = {
        "error": r"status_code is 400, resp.body=b'{\"detail\":\"\xe6\x97\xa0\xe6\xb3\x95\"}'",
        "status_code": 400,
        "response_data": {
            "code": "CANNOT_GET_REPO",
            "detail": detail,
        },
    }
    mocker.patch("apigateway.components.bkpaas.get_paas3_url_prefix", return_value="https://paas.example.com/prod")
    mocker.patch("apigateway.components.bkpaas.gen_gateway_headers", return_value={"X-Gateway": "1"})
    mocker.patch("apigateway.components.bkpaas.http_get", return_value=(False, failed_response))
    mocker.patch("apigateway.components.bkpaas.http_post", return_value=(False, failed_response))

    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__) as exc_info:
        call_paas_api()

    message = str(exc_info.value.code.message)
    assert detail in message
    assert r"\xe6\x97\xa0" not in message


def test_paas_api_failure_falls_back_to_transport_error(mocker):
    transport_error = "request timed out"
    mocker.patch("apigateway.components.bkpaas.get_paas3_url_prefix", return_value="https://paas.example.com/prod")
    mocker.patch("apigateway.components.bkpaas.gen_gateway_headers", return_value={"X-Gateway": "1"})
    mocker.patch(
        "apigateway.components.bkpaas.http_post",
        return_value=(False, {"error": transport_error}),
    )

    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__) as exc_info:
        paas_app_module_offline("demo", "default", "prod")

    assert transport_error in str(exc_info.value.code.message)
