# -*- coding: utf-8 -*-
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

from components.bk.apisv2.cc.toolkit import configs
from components.bk.apisv2.cc.toolkit.tools import CCClient


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_cc_jwt_enabled(mocker, enabled, method):
    mocker.patch.object(configs, "JWT_ENABLED", enabled)
    component = mocker.MagicMock()
    component.current_user.username = "test-user"
    component.request.app_code = "test-app"
    component.outgoing.http_client.request.return_value = '{"code": 0, "data": {}}'

    result = getattr(CCClient(component), method)(host="http://cc.example.com", path="/api/v3/test")

    assert result["result"] is True
    kwargs = component.outgoing.http_client.request.call_args[1]
    assert kwargs["with_jwt_header"] is enabled
    assert kwargs["headers"]["Bk-Username"] == "test-user"
    assert kwargs["headers"]["Bk-App-Code"] == "test-app"
