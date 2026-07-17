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
from ddf import G

from apigateway.apps.support.constants import SDKDistributorEnum, SDKGenerationStatusEnum
from apigateway.apps.support.models import GatewaySDK, SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk import GatewaySDKHandler
from apigateway.biz.sdk.artifacts import ArtifactManifest, ManifestFile

pytestmark = pytest.mark.django_db


class TestGatewaySDKHandler:
    def test_generation_projection_uses_manifest_artifact_types(self, fake_gateway, fake_resource_version):
        fake_resource_version.version = "1.2.3"
        fake_resource_version.save(update_fields=["version"])
        task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
        item = G(SDKGenerationItem, task=task, language="python", input_fingerprint="fingerprint")
        G(
            SDKArtifact,
            item=item,
            distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
            artifact_type="package",
            filename="demo.whl",
            url="https://repo/demo.whl",
            status=SDKGenerationStatusEnum.SUCCESS.value,
        )
        manifest = ArtifactManifest(
            gateway_name=fake_gateway.name,
            resource_version="1.2.3",
            language="python",
            package_version="1.2.3",
            input_fingerprint="fingerprint",
            tool_versions={"openapi-generator": "7.23.0"},
            files=(ManifestFile("wheel", "demo.whl", 5, "0" * 64),),
        )
        language_config = SimpleNamespace(
            project_name="demo",
            package_name="demo",
            package_version="1.2.3",
        )

        sdk = GatewaySDKHandler.upsert_generation_projection(item, language_config, manifest)

        assert sdk.config["artifacts"][0]["type"] == "wheel"

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
