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
from apigateway.components.bkauth import BkAuthAppNotFoundError, get_app_info


def test_get_app_info_raises_app_not_found_for_bkauth_404(mocker, settings):
    settings.BK_AUTH_API_URL = "http://bkauth"
    mock_http_get = mocker.patch(
        "apigateway.components.bkauth.http_get",
        return_value=(
            False,
            {
                "error": "status_code is 404, not 2xx!",
                "status_code": 404,
                "response_data": {
                    "code": 1903404,
                    "message": "message text should not be parsed",
                    "data": {},
                },
            },
        ),
    )

    mock_http_get.__name__ = "http_get"

    with pytest.raises(BkAuthAppNotFoundError):
        get_app_info("subscription")

    mock_http_get.assert_called_once()
    assert "ignored_error_status_codes" not in mock_http_get.call_args.kwargs


@pytest.mark.parametrize(
    "status_code, code",
    [
        (404, 1903400),
        (500, 1903404),
    ],
)
def test_get_app_info_keeps_remote_error_for_non_get_app_info_not_found(mocker, settings, status_code, code):
    settings.BK_AUTH_API_URL = "http://bkauth"
    mock_http_get = mocker.patch(
        "apigateway.components.bkauth.http_get",
        return_value=(
            False,
            {
                "error": f"status_code is {status_code}, not 2xx!",
                "status_code": status_code,
                "response_data": {
                    "code": code,
                    "message": "remote error",
                    "data": {},
                },
            },
        ),
    )
    mock_http_get.__name__ = "http_get"

    with pytest.raises(error_codes.REMOTE_REQUEST_ERROR.__class__):
        get_app_info("subscription")
