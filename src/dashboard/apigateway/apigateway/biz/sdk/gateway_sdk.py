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
from typing import Dict, List

from django.db.models import Count

from apigateway.apps.support.api_sdk.models import SDKFactory
from apigateway.apps.support.models import GatewaySDK
from apigateway.core.models import Release


class GatewaySDKHandler:
    @classmethod
    def get_stage_sdks(cls, gateway_id: int, language: str) -> List:
        releases = list(
            Release.objects.filter(gateway_id=gateway_id).values(
                "stage__id",
                "stage__name",
                "stage__is_public",
                "resource_version__id",
                "resource_version__name",
                "resource_version__title",
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
