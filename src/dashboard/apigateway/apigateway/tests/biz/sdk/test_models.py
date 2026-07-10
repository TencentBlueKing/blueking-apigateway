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
from types import SimpleNamespace

import pytest

from apigateway.biz.sdk import SDKDocContext, SDKFactory
from apigateway.biz.sdk.managers import SDKManagerFactory
from apigateway.biz.sdk.models import GolangSDK
from apigateway.utils.time import now_datetime


class TestSDKDocContext:
    def test_as_dict(self):
        now = now_datetime()
        context = SDKDocContext(
            gateway_name="foo-bar",
            stage_name="prod",
            resource_name="get_color",
            bk_api_url_tmpl="http://{api_name}.example.com",
            sdk_created_time=now,
        )
        result = context.as_dict()

        assert result["sdk_created_time"] == now
        assert result["gateway_name_with_underscore"] == "foo_bar"


def test_sdk_factory_displays_a_legacy_golang_record_as_go():
    sdk = SDKFactory.create(
        SimpleNamespace(
            language="golang",
            config={},
            name="bkapi-my-gateway",
            version_number="1.2.3",
            url="https://example.com/sdk.tgz",
        )
    )

    assert isinstance(sdk, GolangSDK)
    assert sdk.as_dict()["language"] == "go"


def test_legacy_golang_manager_does_not_accept_new_go_requests():
    assert SDKManagerFactory.create("golang").name == "golang"

    with pytest.raises(KeyError):
        SDKManagerFactory.create("go")
