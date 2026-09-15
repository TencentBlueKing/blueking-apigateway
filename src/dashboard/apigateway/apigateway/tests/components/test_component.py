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

from apigateway.components.component import BaseComponent


def test_subclass_response_parser_is_used(mocker):
    # Edition-specific clients inherit the shared request path and override the response format.
    class EditionComponent(BaseComponent):
        HOST = "https://example.com"

        def parse_response(self, http_ok, resp):
            return http_ok, "", resp["payload"]

    http_get = mocker.Mock(return_value=(True, {"payload": {"name": "sdk"}}))
    params = {"package_name": "sdk"}

    result = EditionComponent()._call_api(http_get, "/package/info", params, timeout=10)

    assert result == (True, "", {"name": "sdk"})
    http_get.assert_called_once_with("https://example.com/package/info", params, timeout=10)
