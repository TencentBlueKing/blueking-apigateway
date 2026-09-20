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
import requests
import responses

from apigateway.utils.git import check_git_credentials

REPO_URL = "https://git.example.com/repo.git"
PROBE_URL = "https://git.example.com/repo/info/refs?service=git-upload-pack"
ADVERTISEMENT = b"001e# service=git-upload-pack\n00000000"
CONTENT_TYPE = "application/x-git-upload-pack-advertisement"


@pytest.fixture
def git_response():
    response = requests.Response()
    response.status_code = 200
    response.url = PROBE_URL
    response.headers["Content-Type"] = CONTENT_TYPE
    response._content = ADVERTISEMENT
    return response


@pytest.mark.parametrize(
    "repo_url,username,token",
    [
        ("https://github.com/user/repo.git", "", "ghp_valid"),
        ("https://gitlab.com/user/repo.git", "user", "glpat_valid"),
    ],
)
def test_basic_scenarios(mocker, git_response, repo_url, username, token):
    mocker.patch("requests.Session.get", return_value=git_response)

    result = check_git_credentials(repo_url, username, token)

    assert result == (True, "")


@pytest.mark.parametrize(
    "exception_type",
    [
        requests.ConnectTimeout,
        requests.ReadTimeout,
        requests.Timeout,
        requests.ConnectionError,
        requests.exceptions.SSLError,
        requests.exceptions.InvalidURL,
        requests.exceptions.InvalidSchema,
        requests.exceptions.MissingSchema,
        requests.TooManyRedirects,
        requests.RequestException,
    ],
)
def test_network_errors(mocker, caplog, exception_type):
    repo_url = "https://secret-user:secret-password@git.example.com/private-repo.git?token=secret-query"
    username, token = "secret-user", "secret-password"
    mocker.patch("requests.Session.get", side_effect=exception_type(f"failed to request {repo_url}"))

    ok, message = check_git_credentials(repo_url, username, token)

    assert ok is False
    assert message == "无法连接 Git 服务，请检查仓库地址和网络连接，或稍后重试。"
    for secret in ("secret-user", "secret-password", "private-repo", "secret-query"):
        assert secret not in message + caplog.text


def test_gitlab_personal_token_auth(mocker, git_response):
    """验证GitLab PAT认证格式（username固定为oauth2）"""
    mock_get = mocker.patch("requests.Session.get", return_value=git_response)

    check_git_credentials("https://gitlab.com/user/repo.git", "oauth2", "glpat_token")

    assert mock_get.call_args[1]["auth"] == ("oauth2", "glpat_token")


@pytest.mark.parametrize(
    "repo_url,probe_url",
    [
        (REPO_URL, PROBE_URL),
        (f"{REPO_URL}.git", "https://git.example.com/repo.git/info/refs?service=git-upload-pack"),
        (f"{REPO_URL}?token=secret#fragment", PROBE_URL),
        (
            "https://git.example.com/repo;variant.git",
            "https://git.example.com/repo;variant/info/refs?service=git-upload-pack",
        ),
    ],
)
def test_probe_url(mocker, git_response, repo_url, probe_url):
    mock_get = mocker.patch("requests.Session.get", return_value=git_response)

    assert check_git_credentials(repo_url, "user", "token") == (True, "")
    mock_get.assert_called_once_with(probe_url, auth=("user", "token"), allow_redirects=False, timeout=10)


@pytest.mark.parametrize("status_code", [201, 204, 304, 400, 401, 403, 404, 429, 500, 502, 503])
def test_error_status_codes(mocker, git_response, status_code):
    git_response.status_code = status_code
    git_response._content = b""
    git_response.headers.clear()
    mocker.patch("requests.Session.get", return_value=git_response)

    ok, message = check_git_credentials("https://git.example.com/user/repo.git", "", "token")

    assert ok is False
    assert "git.example.com" in message
    assert f"HTTP {status_code}" in message


@pytest.mark.parametrize("status_code", [200, 204, 401, 503])
def test_redirect_response(mocker, status_code):
    mocker.patch("requests.sessions.get_netrc_auth", return_value=None)
    final_url = "https://final.example.com/private.git/info/refs?service=git-upload-pack"
    with responses.RequestsMock() as http:
        http.add(responses.GET, PROBE_URL, status=302, headers={"Location": final_url})
        http.add(
            responses.GET,
            final_url,
            status=status_code,
            body=ADVERTISEMENT if status_code == 200 else b"",
            content_type=CONTENT_TYPE,
        )

        ok, message = check_git_credentials(REPO_URL, "user", "token")

    if status_code == 200:
        assert (ok, message) == (True, "")
    else:
        assert ok is False
        assert "final.example.com" in message
        assert f"HTTP {status_code}" in message


def test_missing_redirect_location(mocker, git_response):
    git_response.status_code = 302
    mocker.patch("requests.Session.get", return_value=git_response)

    ok, message = check_git_credentials("https://git.example.com/repo.git", "user", "token")

    assert ok is False
    assert "Git 服务重定向异常" in message
    assert "HTTP 302" in message


def test_only_one_redirect():
    redirected_url = "https://git.example.com/moved/info/refs"
    with responses.RequestsMock() as http:
        http.add(responses.GET, PROBE_URL, status=302, headers={"Location": redirected_url})
        http.add(responses.GET, redirected_url, status=307, headers={"Location": "/another/location"})

        ok, message = check_git_credentials(REPO_URL, "user", "token")

        assert len(http.calls) == 2
        assert ok is False
        assert "HTTP 307" in message
        assert "Git 服务重定向异常" in message


@pytest.mark.parametrize(
    "location,final_url,keeps_auth",
    [
        ("/moved/info/refs", "https://git.example.com/moved/info/refs", True),
        ("https://other.example.com/refs", "https://other.example.com/refs", False),
        ("http://git.example.com/refs", "http://git.example.com/refs", False),
        ("https://git.example.com:8443/refs", "https://git.example.com:8443/refs", False),
    ],
)
def test_redirect_credentials(mocker, location, final_url, keeps_auth):
    mocker.patch("requests.sessions.get_netrc_auth", return_value=None)
    with responses.RequestsMock() as http:
        http.add(responses.GET, PROBE_URL, status=302, headers={"Location": location})
        http.add(responses.GET, final_url, body=ADVERTISEMENT, content_type=CONTENT_TYPE)

        assert check_git_credentials(REPO_URL, "user", "token") == (True, "")
        assert "Authorization" in http.calls[0].request.headers
        assert ("Authorization" in http.calls[1].request.headers) is keeps_auth


@pytest.mark.parametrize(
    "content_type,body",
    [
        ("text/html", b"<html>secret login page</html>"),
        (CONTENT_TYPE, b"<html>secret login page</html>"),
        (CONTENT_TYPE, b""),
        ("", b""),
        ("application/x-git-receive-pack-advertisement", ADVERTISEMENT),
    ],
)
def test_invalid_git_response(mocker, git_response, content_type, body):
    git_response.headers["Content-Type"] = content_type
    git_response._content = body
    mocker.patch("requests.Session.get", return_value=git_response)

    ok, message = check_git_credentials(REPO_URL, "user", "token")

    assert ok is False
    assert "HTTP 200" in message
    assert "响应不是 Git Smart HTTP 格式" in message
    assert "secret" not in message


def test_service_announcement_without_newline(mocker, git_response):
    git_response._content = b"001d# service=git-upload-pack00000000"
    git_response.headers["Content-Type"] = f"{CONTENT_TYPE}; charset=utf-8"
    mocker.patch("requests.Session.get", return_value=git_response)

    assert check_git_credentials(REPO_URL, "user", "token") == (True, "")


@pytest.mark.parametrize(
    "repo_url",
    [
        "https://[invalid/secret-path.git",
        "https://secret-user:secret-password@git.example.com／invalid/secret-path.git",
    ],
)
def test_invalid_repository_url(mocker, repo_url):
    mock_get = mocker.patch("requests.Session.get")

    ok, message = check_git_credentials(repo_url, "secret-user", "secret-password")

    assert ok is False
    assert message == "无法连接 Git 服务，请检查仓库地址和网络连接，或稍后重试。"
    assert "secret" not in message
    mock_get.assert_not_called()


@pytest.mark.parametrize(
    "location,expected_message",
    [("https://[invalid/secret-path", "无法连接 Git 服务"), (PROBE_URL, "HTTP 302")],
)
def test_invalid_or_looping_redirect(location, expected_message):
    with responses.RequestsMock() as http:
        http.add(responses.GET, PROBE_URL, status=302, headers={"Location": location})

        ok, message = check_git_credentials(REPO_URL, "secret-user", "secret-password")

    assert ok is False
    assert expected_message in message
    assert "secret" not in message
