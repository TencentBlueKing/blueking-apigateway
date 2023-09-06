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
from ddf import G

from apigateway.apps.support.models import APISDK
from apigateway.biz.sdk.gateway_sdk import GatewaySdkHandler


class TestGatewaySdkHandler:
    def test_stage_sdks(self, fake_gateway, fake_stage, fake_release, fake_sdk):
        result = GatewaySdkHandler.get_stage_sdks(fake_gateway.id, fake_sdk.language)
        assert len(result) == 1
        assert result[0]["stage"]
        assert result[0]["resource_version"]
        assert result[0]["sdk"]

        result = GatewaySdkHandler.get_stage_sdks(fake_gateway.id, "not_exist")
        assert len(result) == 1
        assert result[0]["stage"]
        assert result[0]["resource_version"]
        assert result[0]["sdk"] is None

        fake_stage.is_public = False
        fake_stage.save()

        result = GatewaySdkHandler.get_stage_sdks(fake_gateway.id, fake_sdk.language)
        assert result == []

    def test_get_resource_version_latest_public_sdk(self, fake_gateway, fake_resource_version):
        G(APISDK, gateway=fake_gateway, is_public=True, resource_version_id=fake_resource_version, language="zh")
        latest_sdk = G(
            APISDK, gateway=fake_gateway, is_public=True, resource_version_id=fake_resource_version, language="zh"
        )

        assert GatewaySdkHandler._get_resource_version_latest_public_sdk(
            fake_gateway.id, [fake_resource_version], "zh"
        ) == {fake_resource_version.id: latest_sdk}
