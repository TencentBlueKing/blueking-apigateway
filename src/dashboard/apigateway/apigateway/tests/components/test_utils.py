#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

from unittest.mock import Mock, patch

import pytest

from apigateway.common.error_codes import error_codes
from apigateway.components.utils import _remove_sensitive_info, do_legacy_blueking_http_request


def test_remove_sensitive_info():
    info = {
        "bk_token": "1234567890",
        "bk_app_secret": "abcdef123456",
        "app_secret": "secret123456",
        "other_key": "value",
    }
    expected_result = {
        "bk_token": "123456******",
        "bk_app_secret": "abcdef******",
        "app_secret": "secret******",
        "other_key": "value",
    }
    assert _remove_sensitive_info(info) == str(expected_result)
    assert _remove_sensitive_info(None) == ""


@pytest.fixture
def mock_local():
    with patch("apigateway.components.utils.local") as mock_local:
        mock_local.request_id = "test_request_id"
        yield mock_local


def test_do_legacy_blueking_http_request_success(mock_local):
    http_func = Mock(return_value=(True, {"code": 0, "data": "success"}))
    http_func.__name__ = "test_func"
    result = do_legacy_blueking_http_request("test_component", http_func, "http://test.url")
    assert result == "success"


def test_do_legacy_blueking_http_request_failure(mock_local):
    http_func = Mock(return_value=(False, {"error": "test_error"}))
    http_func.__name__ = "test_func"
    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__):
        do_legacy_blueking_http_request("test_component", http_func, "http://test.url")


def test_do_legacy_blueking_http_request_error_code(mock_local):
    http_func = Mock(return_value=(True, {"code": 1, "message": "test_message"}))
    http_func.__name__ = "test_func"
    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__):
        do_legacy_blueking_http_request("test_component", http_func, "http://test.url")
