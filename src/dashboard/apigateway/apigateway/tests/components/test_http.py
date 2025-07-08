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

from unittest.mock import patch

import pytest
import requests

from apigateway.components.http import _enrich_header, _http_request


@pytest.fixture
def mock_session():
    with patch("apigateway.components.http.session") as mock_session:
        yield mock_session


def test_http_request_get(mock_session):
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = b'{"key": "value"}'
    mock_session.get.return_value = mock_response

    success, response = _http_request(
        method="GET",
        url="http://example.com",
        headers={"X-Request-Id": "test-request-id"},
        data={"param": "value"},
        timeout=5,
    )

    assert success is True
    assert response == {"key": "value"}


def test_http_request_post(mock_session):
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = b'{"key": "value"}'
    mock_session.post.return_value = mock_response

    success, response = _http_request(
        method="POST",
        url="http://example.com",
        headers={"X-Request-Id": "test-request-id"},
        data={"param": "value"},
        timeout=5,
    )

    assert success is True
    assert response == {"key": "value"}


def test_http_request_error(mock_session):
    mock_session.get.side_effect = requests.exceptions.RequestException("Test exception")

    success, response = _http_request(
        method="GET",
        url="http://example.com",
        headers={"X-Request-Id": "test-request-id"},
        data={"param": "value"},
        timeout=5,
    )

    assert success is False
    assert "error" in response


def test_enrich_header():
    # Test when headers are None
    headers = _enrich_header()
    assert "Content-Type" in headers
    assert headers["Content-Type"] == "application/json"
    assert "X-Request-Id" in headers
    assert len(headers["X-Request-Id"]) == 32

    # Test when headers are provided without X-Request-Id
    headers = _enrich_header({"Content-Type": "application/xml"})
    assert headers["Content-Type"] == "application/xml"
    assert "X-Request-Id" in headers
    assert len(headers["X-Request-Id"]) == 32

    # Test when headers are provided with X-Request-Id
    headers = _enrich_header({"Content-Type": "application/xml", "X-Request-Id": "test-id"})
    assert headers["Content-Type"] == "application/xml"
    assert headers["X-Request-Id"] == "test-id"
