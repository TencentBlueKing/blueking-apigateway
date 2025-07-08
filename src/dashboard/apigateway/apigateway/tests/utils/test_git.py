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

import pytest
import requests

from apigateway.utils.git import check_git_credentials


# 基础测试场景参数化
@pytest.mark.parametrize(
    "repo_url,username,token,expected_status,expected_call_count",
    [
        ("https://github.com/user/repo.git", "", "ghp_valid", True, 1),
        ("https://gitlab.com/user/repo.git", "user", "glpat_valid", True, 1),
        ("https://invalid.repo.com/repo.git", "", "token", False, 1),
    ],
    ids=["github_success", "gitlab_success", "invalid_domain"],
)
def test_basic_scenarios(mocker, repo_url, username, token, expected_status, expected_call_count):
    """通用测试模板覆盖基础场景"""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200 if expected_status else 404

    result = check_git_credentials(repo_url, username, token)

    assert result == expected_status
    assert mock_get.call_count == expected_call_count


@pytest.mark.parametrize(
    "exception",
    [
        requests.exceptions.Timeout(),
        requests.exceptions.ConnectionError(),
    ],
    ids=["timeout", "connection_error"],
)
def test_network_errors(mocker, exception):
    """测试网络异常场景"""
    mocker.patch("requests.get", side_effect=exception)

    result = check_git_credentials("https://github.com/user/repo.git", "", "token")

    assert result is False


def test_gitlab_personal_token_auth(mocker):
    """验证GitLab PAT认证格式（username固定为oauth2）"""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200

    check_git_credentials("https://gitlab.com/user/repo.git", "oauth2", "glpat_token")

    assert mock_get.call_args[1]["auth"] == ("oauth2", "glpat_token")


# 错误场景参数化
@pytest.mark.parametrize("status_code", [401, 403, 404, 500], ids=lambda x: f"status_{x}")
def test_error_status_codes(mocker, status_code):
    """测试各种错误状态码"""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = status_code

    result = check_git_credentials("https://github.com/user/repo.git", "", "token")

    assert result is False
