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
from apigateway.components.bkpaas import REQ_PAAS_API_TIMEOUT, get_paas_repo_authorization


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
        allow_status_codes={403},
    )


def test_get_paas_repo_authorization__unauthorized(mocker):
    mocker.patch("apigateway.components.bkpaas.get_paas3_url_prefix", return_value="https://paas.example.com/prod")
    mocker.patch(
        "apigateway.components.bkpaas.gen_gateway_headers", return_value={"X-Bkapi-Authorization": "authorization"}
    )
    mocker.patch(
        "apigateway.components.bkpaas.http_get",
        return_value=(
            True,
            {
                "message": "用户未关联 oauth 授权",
                "address": "https://git.example.com/oauth/authorize",
                "auth_docs": "http://docs.example.com/tc_git_oauth",
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
