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
from ddf import G

from apigateway.apps.support.constants import SDKArtifactStatusEnum, SDKGenerationItemStatusEnum
from apigateway.apps.support.models import GatewaySDK, SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk import GatewaySDKHandler
from apigateway.biz.sdk.exceptions import LegacySDKVersionConflict
from apigateway.biz.sdk.gateway_sdk import ensure_gateway_sdk_projection
from apigateway.core.models import ResourceVersion

pytestmark = pytest.mark.django_db


class TestGatewaySDKHandler:
    def test_generation_projection_links_item_without_duplicating_artifact_state(
        self, fake_gateway, fake_resource_version
    ):
        fake_resource_version.version = "1.2.3"
        fake_resource_version.save(update_fields=["version"])
        task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
        item = G(
            SDKGenerationItem,
            task=task,
            language="python",
            input_fingerprint="fingerprint",
            config_snapshot={
                "project_name": "bkapi-openapi-demo",
                "package_name": "bkapi_openapi_demo",
                "package_version": "1.2.3rc1",
            },
        )
        G(
            SDKArtifact,
            item=item,
            distributor="bkrepo_generic",
            artifact_type="wheel",
            filename="demo.whl",
            url="https://repo/demo.whl",
            package_version="1.2.3rc1",
            status=SDKArtifactStatusEnum.SUCCESS.value,
        )
        G(
            SDKArtifact,
            item=item,
            distributor="bkrepo_generic",
            artifact_type="manifest",
            filename="manifest.json",
            url="https://repo/manifest.json",
            status=SDKArtifactStatusEnum.SUCCESS.value,
        )

        sdk = ensure_gateway_sdk_projection(item)
        item.refresh_from_db()

        assert item.gateway_sdk == sdk
        assert sdk.config == {}
        assert sdk.version_number == "1.2.3"
        assert sdk.name == "bkapi-openapi-demo"
        assert sdk.url == "https://repo/demo.whl"

    def test_projection_links_matching_legacy_sdk_without_updating_or_backfilling(
        self, fake_gateway, fake_resource_version
    ):
        fake_resource_version.version = "1.2.3"
        fake_resource_version.save(update_fields=["version"])
        task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
        item = G(
            SDKGenerationItem,
            task=task,
            language="go",
            status=SDKGenerationItemStatusEnum.PENDING.value,
        )
        legacy = G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=fake_resource_version,
            language="go",
            version_number="1.2.3",
            name="legacy-name",
            url="https://legacy/sdk.zip",
            _config='{"go":{"legacy":true}}',
        )
        original = (legacy.name, legacy.url, legacy._config, legacy.updated_time)

        sdk = ensure_gateway_sdk_projection(item)
        item.refresh_from_db()
        legacy.refresh_from_db()

        assert sdk == legacy
        assert item.gateway_sdk == legacy
        assert item.status == SDKGenerationItemStatusEnum.SUCCESS.value
        assert not item.artifacts.exists()
        assert (legacy.name, legacy.url, legacy._config, legacy.updated_time) == original

    def test_projection_rejects_legacy_sdk_for_another_resource_version(self, fake_gateway, fake_resource_version):
        fake_resource_version.version = "1.2.3"
        fake_resource_version.save(update_fields=["version"])
        other_version = G(ResourceVersion, gateway=fake_gateway, version="older-resource-version")
        legacy = G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=other_version,
            language="python",
            version_number="1.2.3",
        )
        task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
        item = G(SDKGenerationItem, task=task, language="python")

        with pytest.raises(LegacySDKVersionConflict):
            ensure_gateway_sdk_projection(item)

        item.refresh_from_db()
        assert item.gateway_sdk_id is None
        assert not SDKGenerationItem.objects.filter(gateway_sdk=legacy).exists()

    def test_projection_rejects_legacy_sdk_owned_by_another_item(self, fake_gateway, fake_resource_version):
        fake_resource_version.version = "1.2.3"
        fake_resource_version.save(update_fields=["version"])
        legacy = G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=fake_resource_version,
            language="java",
            version_number="1.2.3",
        )
        owner_version = G(ResourceVersion, gateway=fake_gateway, version="owner-resource-version")
        owner_task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=owner_version)
        owner = G(SDKGenerationItem, task=owner_task, language="java", gateway_sdk=legacy)
        target_task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
        target = G(SDKGenerationItem, task=target_task, language="java")

        with pytest.raises(LegacySDKVersionConflict):
            ensure_gateway_sdk_projection(target)

        target.refresh_from_db()
        assert target.gateway_sdk_id is None
        assert SDKGenerationItem.objects.get(gateway_sdk=legacy) == owner

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
