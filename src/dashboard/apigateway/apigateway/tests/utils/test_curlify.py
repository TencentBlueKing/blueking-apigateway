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
import pytest
from requests import PreparedRequest

from apigateway.utils.curlify import to_curl


@pytest.fixture
def fake_request():
    request = PreparedRequest()
    request.prepare(
        method="GET",
        url="http://example.com",
        headers={"X-Request-Token": "testing"},
    )
    return request


def test_to_curl(fake_request):
    result = to_curl(fake_request)
    assert "-X GET" in result
    assert "http://example.com" in result
    assert "X-Request-Token: testing" in result

    result = to_curl(fake_request, headers={"foo": "bar"})
    assert "-X GET" in result
    assert "http://example.com" in result
    assert "foo: bar" in result
    assert "X-Request-Token: testing" not in result

    result = to_curl(fake_request, headers={"foo": "bar"}, header_keys=())
    assert "-X GET" in result
    assert "http://example.com" in result
    assert "foo: bar" not in result
    assert "X-Request-Token: testing" not in result
