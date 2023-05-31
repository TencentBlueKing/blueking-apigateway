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
from operator import itemgetter

import pytest
from bkapi_client_core.exceptions import BKAPIError
from requests import Response

from apigateway.components.exceptions import RemoteAPIResultError, RemoteRequestError
from apigateway.components.handler import RequestAPIHandler


class TestRequestAPIHandler:
    def test_call_api(self, mocker, faker):
        action = mocker.MagicMock(request=mocker.MagicMock(return_value=Response()))
        parse_response = mocker.MagicMock(return_value={})
        handler = RequestAPIHandler(faker.pystr(), parse_response)
        api_result, response = handler.call_api(action)
        assert api_result == {}
        assert isinstance(response, Response)

        action = mocker.MagicMock(request=mocker.MagicMock(side_effect=BKAPIError(faker.pystr())))
        parse_response = mocker.MagicMock(return_value={})
        handler = RequestAPIHandler(faker.pystr(), parse_response)
        with pytest.raises(RemoteRequestError):
            handler.call_api(action)

        action = mocker.MagicMock(request=mocker.MagicMock(return_value=Response()))
        parse_response = mocker.MagicMock(side_effect=BKAPIError(faker.pystr()))
        handler = RequestAPIHandler(faker.pystr(), parse_response)
        with pytest.raises(RemoteRequestError):
            handler.call_api(action)

    def test_parse_api_result(self, mocker, faker):
        response = mocker.MagicMock()
        parse_response = mocker.MagicMock(return_value={})
        handler = RequestAPIHandler(faker.pystr(), parse_response)

        api_result = {"result": True, "data": {"color": "green"}}
        result = handler.parse_api_result(api_result, response, {"result": True}, itemgetter("data"))
        assert result == {"color": "green"}

        api_result = {"result": False, "data": {}}
        with pytest.raises(RemoteAPIResultError):
            handler.parse_api_result(api_result, response, {"result": True}, itemgetter("data"))

        api_result = {"result": False, "data": {}}
        result = handler.parse_api_result(api_result, response)
        assert result == api_result
