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

import json

import pytest
import responses
from bkapi_component.open.client import Client

from apigateway.components.bkcmsi import CMSIComponent

pytestmark = pytest.mark.no_meta_schema

SEND_RTX_URL = "https://esb.example.com/api/c/compapi/v2/cmsi/send_rtx/"


@pytest.fixture
def cmsi_client(mocker):
    client = Client(endpoint="https://esb.example.com", bk_api_ver="v2")
    get_client = mocker.patch("apigateway.components.bkcmsi.get_client_by_username", return_value=client)
    return client, get_client


@pytest.mark.parametrize("username", ["", "alice"])
def test_send_im_repeatedly_uses_sdk_operation(cmsi_client, username):
    _, get_client = cmsi_client
    messages = [
        {"bk_username": "sender", "receiver__username": ["alice"], "title": "Alert", "content": "first alert"},
        {"bk_username": "sender", "receiver__username": ["bob"], "title": "Alert", "content": "second alert"},
    ]

    with responses.RequestsMock(assert_all_requests_are_fired=False) as requests:
        requests.post(SEND_RTX_URL, json={"result": True, "code": 0, "data": {}})

        for params in messages:
            assert CMSIComponent().send_im("default", params, username) == (True, "")

        assert [json.loads(call.request.body) for call in requests.calls] == messages
        assert [call.request.method for call in requests.calls] == ["POST", "POST"]

    assert [call.args for call in get_client.call_args_list] == [(username,), (username,)]


def test_send_im_returns_api_error_and_allows_next_send(cmsi_client):
    params = {"receiver__username": ["alice"], "title": "Alert", "content": "backend error"}
    component = CMSIComponent()

    with responses.RequestsMock(assert_all_requests_are_fired=False) as requests:
        requests.post(SEND_RTX_URL, status=503)
        requests.post(SEND_RTX_URL, json={"result": True, "code": 0, "data": {}})

        ok, message = component.send_im("default", params)

        assert ok is False
        assert "发送消息失败" in message
        assert "503" in message
        assert component.send_im("default", params) == (True, "")
        assert [json.loads(call.request.body) for call in requests.calls] == [params, params]
