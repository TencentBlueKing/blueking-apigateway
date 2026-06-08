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
from unittest.mock import call

import pytest
from ddf import G

from apigateway.apps.support.models import GatewaySDK
from apigateway.biz.sdk import GatewaySDKHandler, exceptions, generate_sdks_for_resource_version
from apigateway.common.error_codes import APIError


class TestGatewaySDKHandler:
    def test_stage_sdks(self, fake_gateway, fake_stage, fake_release, fake_sdk):
        result = GatewaySDKHandler.get_stage_sdks(fake_gateway.id, fake_sdk.language)
        assert len(result) == 1
        assert result[0]["stage"]
        assert result[0]["resource_version"]
        assert result[0]["sdk"]

        result = GatewaySDKHandler.get_stage_sdks(fake_gateway.id, "not_exist")
        assert len(result) == 1
        assert result[0]["stage"]
        assert result[0]["resource_version"]
        assert result[0]["sdk"] is None

        fake_stage.is_public = False
        fake_stage.save()

        result = GatewaySDKHandler.get_stage_sdks(fake_gateway.id, fake_sdk.language)
        assert result == []

    def test_get_resource_version_latest_public_sdk(self, fake_gateway, fake_resource_version):
        G(GatewaySDK, gateway=fake_gateway, is_public=True, resource_version=fake_resource_version, language="zh")
        latest_sdk = G(
            GatewaySDK, gateway=fake_gateway, is_public=True, resource_version=fake_resource_version, language="zh"
        )

        assert GatewaySDKHandler._get_resource_version_latest_public_sdk(
            fake_gateway.id, [fake_resource_version.id], "zh"
        ) == {fake_resource_version.id: latest_sdk}

    def test_mark_is_recommended(self, fake_gateway, fake_resource_version):
        sdk1 = G(GatewaySDK, gateway=fake_gateway, is_recommended=True, is_public=True, language="zh")
        sdk2 = G(GatewaySDK, gateway=fake_gateway, is_recommended=True, is_public=True, language="zh")
        sdk3 = G(GatewaySDK, gateway=fake_gateway, is_recommended=True, is_public=True, language="en")

        GatewaySDKHandler.mark_is_recommended(sdk2)

        assert GatewaySDK.objects.get(id=sdk1.id).is_recommended is False
        assert GatewaySDK.objects.get(id=sdk2.id).is_recommended is True
        assert GatewaySDK.objects.get(id=sdk3.id).is_recommended is True


def test_generate_sdks_for_resource_version_returns_sdk_payload(fake_resource_version, mocker):
    helper = mocker.MagicMock()
    helper.create.side_effect = [
        SimpleNamespace(
            sdk=SimpleNamespace(name="python-sdk", version_number=fake_resource_version.version, url="url1")
        ),
        SimpleNamespace(sdk=SimpleNamespace(name="go-sdk", version_number=fake_resource_version.version, url="url2")),
    ]
    mocked_helper = mocker.patch("apigateway.biz.sdk.helper.SDKHelper")
    mocked_helper.return_value.__enter__.return_value = helper

    result = generate_sdks_for_resource_version(
        resource_version=fake_resource_version,
        languages=["python", "go"],
        version="",
    )

    assert result == [
        {
            "name": "python-sdk",
            "version": fake_resource_version.version,
            "url": "url1",
        },
        {
            "name": "go-sdk",
            "version": fake_resource_version.version,
            "url": "url2",
        },
    ]
    assert helper.create.call_args_list == [
        call(language="python", version=fake_resource_version.version, operator=None),
        call(language="go", version=fake_resource_version.version, operator=None),
    ]


def test_generate_sdks_for_resource_version_maps_sdk_errors(fake_resource_version, mocker):
    helper = mocker.MagicMock()
    helper.create.side_effect = exceptions.ResourcesIsEmpty
    mocked_helper = mocker.patch("apigateway.biz.sdk.helper.SDKHelper")
    mocked_helper.return_value.__enter__.return_value = helper

    with pytest.raises(APIError) as err:
        generate_sdks_for_resource_version(
            fake_resource_version,
            ["python"],
            "",
        )

    assert err.value.code.message == "网关下无资源，无法生成 SDK。"
