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
from __future__ import annotations

from typing import Dict, List

from django.db.models import Count
from django.db.transaction import atomic
from django.utils import timezone

from apigateway.apps.support.constants import (
    SDKArtifactStatusEnum,
    SDKArtifactTypeEnum,
    SDKDistributorEnum,
    SDKGenerationItemStatusEnum,
)
from apigateway.apps.support.models import GatewaySDK, SDKGenerationItem
from apigateway.biz.sdk.exceptions import LegacySDKVersionConflict
from apigateway.core.models import Release

from .models import SDKFactory

_PREFERRED_GENERIC_ARTIFACT_TYPES = {
    "python": SDKArtifactTypeEnum.WHEEL.value,
    "java": SDKArtifactTypeEnum.DISTRIBUTION_ZIP.value,
    "go": SDKArtifactTypeEnum.GO_ZIP.value,
    "javascript": SDKArtifactTypeEnum.NPM_TGZ.value,
}


def _preferred_generic_artifact(item: SDKGenerationItem):
    artifacts = list(
        item.artifacts.filter(
            distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
            status=SDKArtifactStatusEnum.SUCCESS.value,
        )
        .exclude(artifact_type=SDKArtifactTypeEnum.MANIFEST.value)
        .order_by("id")
    )
    preferred_type = _PREFERRED_GENERIC_ARTIFACT_TYPES.get(item.language)
    return next((artifact for artifact in artifacts if artifact.artifact_type == preferred_type), None) or (
        artifacts[0] if artifacts else None
    )


@atomic
def get_compatible_legacy_sdk(item: SDKGenerationItem) -> GatewaySDK | None:
    sdk = (
        GatewaySDK.objects.select_for_update()
        .filter(
            gateway=item.task.gateway,
            language=item.language,
            version_number=item.task.resource_version.version,
        )
        .first()
    )
    if not sdk:
        return None
    if sdk.resource_version_id != item.task.resource_version_id:
        raise LegacySDKVersionConflict()
    if SDKGenerationItem.objects.exclude(id=item.id).filter(gateway_sdk=sdk).exists():
        raise LegacySDKVersionConflict()
    return sdk


@atomic
def ensure_gateway_sdk_projection(item: SDKGenerationItem) -> GatewaySDK:
    """Create or link the compatibility row after Generic commit."""
    item = (
        SDKGenerationItem.objects.select_for_update()
        .select_related("task__gateway", "task__resource_version", "gateway_sdk")
        .get(id=item.id)
    )
    if item.gateway_sdk_id:
        if (
            item.gateway_sdk.gateway_id != item.task.gateway_id
            or item.gateway_sdk.resource_version_id != item.task.resource_version_id
            or item.gateway_sdk.language != item.language
            or item.gateway_sdk.version_number != item.task.resource_version.version
        ):
            raise LegacySDKVersionConflict()
        return item.gateway_sdk

    sdk = get_compatible_legacy_sdk(item)
    if sdk:
        item.gateway_sdk = sdk
        update_fields = ["gateway_sdk", "updated_time"]
        has_manifest = item.artifacts.filter(
            distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
            artifact_type=SDKArtifactTypeEnum.MANIFEST.value,
            status=SDKArtifactStatusEnum.SUCCESS.value,
        ).exists()
        if not has_manifest:
            item.status = SDKGenerationItemStatusEnum.SUCCESS.value
            item.finished_at = timezone.now()
            item.error_code = ""
            item.error_message = ""
            item.error_retryable = False
            update_fields.extend(["status", "finished_at", "error_code", "error_message", "error_retryable"])
        item.save(update_fields=update_fields)
        return sdk

    has_manifest = item.artifacts.filter(
        distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
        artifact_type=SDKArtifactTypeEnum.MANIFEST.value,
        status=SDKArtifactStatusEnum.SUCCESS.value,
    ).exists()
    artifact = _preferred_generic_artifact(item)
    if not has_manifest or artifact is None:
        raise ValueError("Generic SDK artifacts must be committed before creating a projection")

    sdk = GatewaySDK.objects.create(
        gateway=item.task.gateway,
        resource_version=item.task.resource_version,
        language=item.language,
        version_number=item.task.resource_version.version,
        name=item.config_snapshot.get("project_name", ""),
        url=artifact.url,
        include_private_resources=True,
        is_public=True,
        config={},
    )
    item.gateway_sdk = sdk
    item.save(update_fields=["gateway_sdk", "updated_time"])
    GatewaySDKHandler.mark_is_recommended(sdk)
    return sdk


class GatewaySDKHandler:
    @classmethod
    def get_stage_sdks(cls, gateway_id: int, language: str) -> List:
        releases = list(
            Release.objects.filter(gateway_id=gateway_id).values(
                "stage__id",
                "stage__name",
                "stage__is_public",
                "resource_version__id",
                "resource_version__version",
            )
        )

        resource_version_ids = [release["resource_version__id"] for release in releases]
        gateway_sdks = cls._get_resource_version_latest_public_sdk(gateway_id, resource_version_ids, language)

        stage_sdks = []
        for release in releases:
            if not release["stage__is_public"]:
                continue

            sdk = gateway_sdks.get(release["resource_version__id"])
            stage_sdks.append(
                {
                    "stage": {
                        "id": release["stage__id"],
                        "name": release["stage__name"],
                    },
                    "resource_version": {
                        "id": release["resource_version__id"],
                        "version": release["resource_version__version"],
                    },
                    "sdk": SDKFactory.create(sdk).as_dict() if sdk else None,
                }
            )

        return stage_sdks

    @staticmethod
    def _get_resource_version_latest_public_sdk(
        gateway_id: int, resource_version_ids: List[int], language: str
    ) -> Dict[int, GatewaySDK]:
        queryset = GatewaySDK.objects.filter(
            gateway_id=gateway_id,
            resource_version_id__in=resource_version_ids,
            is_public=True,
            language=language,
        ).order_by("id")

        sdks = {}
        for sdk in queryset:
            # 按 id 排序，则最后一个即为最新
            sdks[sdk.resource_version_id] = sdk

        return sdks

    @staticmethod
    def get_resource_version_sdk_count_map(resource_version_ids: List[int]):
        queryset = (
            GatewaySDK.objects.filter(resource_version_id__in=resource_version_ids)
            .values("resource_version_id")
            .annotate(count=Count("id"))
        )
        return {item["resource_version_id"]: item["count"] for item in queryset}

    @staticmethod
    def get_sdks(gateway_ids: List[int]) -> Dict[int, List[Dict]]:
        data: Dict[int, List[Dict]] = {}
        queryset = GatewaySDK.objects.filter(gateway_id__in=gateway_ids, is_recommended=True)
        for sdk in queryset:
            sdk_dict = SDKFactory().create(sdk).as_dict()
            gateway_id = sdk.gateway.id
            if gateway_id not in data:
                data[gateway_id] = [sdk_dict]
            else:
                data[gateway_id].append(sdk_dict)

        return data

    @staticmethod
    @atomic
    def mark_is_recommended(sdk: GatewaySDK):
        # 清理之前的标记
        GatewaySDK.objects.filter(
            is_recommended=True,
            gateway=sdk.gateway,
            language=sdk.language,
        ).update(is_public_latest=False, is_recommended=False)

        sdk.is_public_latest = True
        sdk.is_recommended = True
        sdk.save(update_fields=["is_public_latest", "is_recommended"])
