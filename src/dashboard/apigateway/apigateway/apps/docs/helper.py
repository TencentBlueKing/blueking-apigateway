# -*- coding: utf-8 -*-
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
import operator
from typing import Optional

from cachetools import TTLCache, cached
from django.db.models import Q
from django.utils.translation import gettext as _
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apis.open.gateway.serializers import GatewayV1SLZ
from apigateway.apis.open.released.serializers import ReleasedResourceListV1SLZ
from apigateway.apis.open.stage.serializers import StageV1SLZ
from apigateway.apis.open.support.serializers import APISDKV1SLZ
from apigateway.apps.label.models import ResourceLabel
from apigateway.apps.support.api_sdk.models import SDKFactory
from apigateway.apps.support.models import APISDK, ReleasedResourceDoc, ResourceVersion
from apigateway.apps.support.utils import get_doc_language
from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.constants import CACHE_MAXSIZE, CacheTimeLevel
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.error_codes import error_codes
from apigateway.common.funcs import get_resource_version_display
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, Stage
from apigateway.core.utils import get_path_display, get_resource_url
from apigateway.utils.paginator import LimitOffsetPaginator

# TODO: 去slz


class SupportHelper:
    def _get_gateway(self, id) -> Gateway:
        gateway = Gateway.objects.get(id=id)

        if not gateway.is_active_and_public:
            raise error_codes.REMOTE_REQUEST_ERROR.format(_("网关非启用或未公开。"))

        return gateway

    def get_gateways(self, user_auth_type: str = "", query: str = "", name: str = "", fuzzy: bool = False) -> list:
        # /api/v1/apis/
        # response = self._client.api.get_apis.request(
        #     {
        #         "user_auth_type": user_auth_type,
        #         "query": query,
        #         "fuzzy": fuzzy,
        #         "name": name,
        #     },
        # )
        # return self._parse_response(response)
        # FIXME: duplicate with /api/v1/apis view
        # 过滤出状态为 active，且公开的网关
        queryset = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value, is_public=True)
        if name:
            if fuzzy:
                # 模糊匹配，查询名称中包含 name 的网关
                queryset = queryset.filter(name__contains=name)
            else:
                # 精确匹配，查询名称为 name 的网关
                queryset = queryset.filter(name=name)

        if query and fuzzy:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

        gateway_ids = list(queryset.values_list("id", flat=True))
        # 过滤出用户类型为指定类型的网关
        if user_auth_type:
            scope_id_config_map = GatewayAuthContext().filter_scope_id_config_map(scope_ids=gateway_ids)
            gateway_ids = [
                scope_id
                for scope_id, config in scope_id_config_map.items()
                if config["user_auth_type"] == user_auth_type
            ]
        # 过滤出已发布的网关ID
        released_gateway_ids = Release.objects.filter_released_gateway_ids(gateway_ids)

        gateway_queryset = queryset.filter(id__in=released_gateway_ids)
        gateway_ids = list(gateway_queryset.values_list("id", flat=True))

        slz = GatewayV1SLZ(
            gateway_queryset,
            many=True,
            context={
                "api_auth_contexts": GatewayAuthContext().filter_scope_id_config_map(scope_ids=gateway_ids),
            },
        )
        return sorted(slz.data, key=operator.itemgetter("name"))

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_SHORT.value))
    def get_gateway_by_name(self, gateway_name: str) -> dict:
        data = self.get_gateways(name=gateway_name, fuzzy=False)
        if data:
            return data[0]
        return {}

    def get_stages(self, gateway_id: int) -> list:
        # /api/v1/apis/{api_id}/stages/
        # response = self._client.api.get_stages.request(path_params={"api_id": api_id})
        # return self._parse_response(response)
        # FIXME: duplicate with /api/v1/apis/{api_id}/stages/ view
        gateway = self._get_gateway(gateway_id)

        # queryset = self.get_queryset()
        queryset = Stage.objects.filter(
            api=gateway,
            status=StageStatusEnum.ACTIVE.value,
            is_public=True,
        )

        slz = StageV1SLZ(queryset, many=True)
        return slz.data

    def get_released_resources(self, gateway_id: int, stage_name: str) -> dict:
        """获取网关环境下的资源列表"""
        # /api/v1/apis/{api_id}/released/stages/{stage_name}/resources/
        # response = self._client.api.get_released_resources.request(
        #     path_params={"api_id": api_id, "stage_name": stage_name},
        # )
        # return self._parse_response(response)
        # FIXME: duplicate with /api/v1/apis/{api_id}/released/stages/{stage_name}/resources/ view
        gateway = self._get_gateway(gateway_id)

        resources = ResourceVersionHandler().get_released_public_resources(gateway.id, stage_name=stage_name)
        resource_ids = [resource["id"] for resource in resources]
        paginator = LimitOffsetPaginator(count=len(resources), offset=0, limit=len(resources))

        slz = ReleasedResourceListV1SLZ(
            resources,
            many=True,
            context={
                "resource_labels": ResourceLabel.objects.get_labels(resource_ids),
            },
        )
        return paginator.get_paginated_data(slz.data)

    # @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_SHORT.value))
    def get_released_resource(self, gateway_id: int, stage_name: str, resource_name: str) -> dict:
        """获取网关环境下发布的资源"""
        # /api/v1/apis/{api_id}/released/stages/{stage_name}/resources/{resource_name}/
        # response = self._client.api.get_released_resource.request(
        #     path_params={"api_id": api_id, "stage_name": stage_name, "resource_name": resource_name},
        # )
        # return self._parse_response(response)
        # FIXME: duplicate with /api/v1/apis/{api_id}/released/stages/{stage_name}/resources/{resource_name}/ view
        gateway = self._get_gateway(gateway_id)

        resource_version_id = Release.objects.get_released_resource_version_id(gateway.id, stage_name)
        if not resource_version_id:
            raise error_codes.REMOTE_REQUEST_ERROR.format(_("资源未发布。"))

        resource = ReleasedResource.objects.get_released_resource(gateway.id, resource_version_id, resource_name)
        # 资源在已发布版本中不存在，或者资源未公开
        if not resource or not resource["is_public"]:
            raise error_codes.REMOTE_REQUEST_ERROR.format(_("资源在已发布版本中不存在，或者资源未公开。"))

        return resource

    def get_resource_doc(self, gateway_id: int, stage_name: str, resource_name: str) -> dict:
        """获取资源文档"""
        # /api/v1/apis/{api_id}/support/stages/{stage_name}/resources/{resource_name}/doc/
        # response = self._client.api.get_resource_doc.request(
        #     path_params={"api_id": api_id, "stage_name": stage_name, "resource_name": resource_name},
        # )
        # return self._parse_response(response)
        # FIXME: remove the /api/open/support
        gateway = self._get_gateway(gateway_id)

        resource_version_id = Release.objects.get_released_resource_version_id(gateway_id, stage_name)
        if not resource_version_id:
            raise error_codes.REMOTE_REQUEST_ERROR.format(_("资源未发布。"))

        resource = ReleasedResource.objects.get_released_resource(gateway_id, resource_version_id, resource_name)
        # 资源在已发布版本中不存在，或者资源未公开
        if not resource or not resource["is_public"] or stage_name in resource["disabled_stages"]:
            raise error_codes.REMOTE_REQUEST_ERROR.format(_("资源在已发布版本中不存在，或者资源未公开。"))

        doc = ReleasedResourceDoc.objects.get_released_resource_doc(
            gateway_id,
            resource_version_id,
            resource["id"],
            language=get_doc_language(get_current_language_code()),
        )

        return {
            "resource": resource,
            "doc": doc,
            "resource_url": get_resource_url(
                resource_url_tmpl=ResourceURLHandler.get_resource_url_tmpl(gateway.name, stage_name),
                gateway_name=gateway.name,
                stage_name=stage_name,
                resource_path=get_path_display(resource["path"], resource["match_subpath"]),
            ),
        }

    def get_latest_sdks(
        self, language: str, gateway_id: Optional[int] = None, gateway_name: Optional[str] = None
    ) -> list:
        """获取网关下最新sdk"""
        # /api/v1/apis/latest-sdks/
        # response = self._client.api.get_latest_sdks.request(
        #     {
        #         "api_id": api_id or "",
        #         "language": language,
        #         "api_name": api_name,
        #     },
        # )
        # return self._parse_response(response)
        # FIXME: duplicate with /api/v1/apis/latest-sdks/ view
        if not gateway_id and gateway_name:
            gateway = Gateway.objects.filter(name=gateway_name).last()
            if not gateway:
                raise error_codes.PARAMETER_ERROR.format(_("网关不存在。"))
            gateway_id = gateway.id

        queryset = APISDK.objects.filter_recommended_sdks(
            language,
            gateway_id=gateway_id,
        )

        resource_version_ids = list(set(queryset.values_list("resource_version_id", flat=True)))

        slz = APISDKV1SLZ(
            [SDKFactory.create(i) for i in queryset],
            many=True,
            context={
                "api_id_map": Gateway.objects.filter_id_object_map(),
                "api_id_config_map": GatewayAuthContext().filter_scope_id_config_map(),
                "released_stages": Release.objects.get_released_stages(resource_version_ids=resource_version_ids),
                "resource_versions": ResourceVersion.objects.get_id_to_fields_map(
                    resource_version_ids=resource_version_ids,
                ),
            },
        )
        return slz.data

    def get_stage_sdks(self, gateway_id: int, language: str) -> list:
        """获取各网关环境，当前的发布资源版本，及对应的SDK"""
        # /api/v1/apis/{api_id}/support/stages/sdks/
        # response = self._client.api.get_stage_sdks.request(
        #     {
        #         "language": language,
        #     },
        #     path_params={"api_id": api_id},
        # )
        # return self._parse_response(response)
        # FIXME: remove the /api/open/support
        gateway = Gateway.objects.get(id=gateway_id)
        if not gateway.is_active_and_public:
            return []

        released_resource_version_ids = Release.objects.get_released_resource_version_ids(gateway.id)
        public_latest_sdks = {
            k: SDKFactory.create(v)
            for k, v in APISDK.objects.filter_resource_version_public_latest_sdk(
                gateway_id=gateway.id,
                resource_version_ids=released_resource_version_ids,
            ).items()
        }

        releases = Release.objects.filter(api_id=gateway.id).values(
            "stage__id",
            "stage__name",
            "stage__is_public",
            "resource_version__id",
            "resource_version__name",
            "resource_version__title",
            "resource_version__version",
        )
        stage_sdks = []
        for release in releases:
            if not release["stage__is_public"]:
                continue

            sdk = public_latest_sdks.get(release["resource_version__id"])
            stage_sdks.append(
                {
                    "stage_id": release["stage__id"],
                    "stage_name": release["stage__name"],
                    "resource_version_id": release["resource_version__id"],
                    "resource_version_name": release["resource_version__name"],
                    "resource_version_title": release["resource_version__title"],
                    "resource_version_display": get_resource_version_display(
                        {
                            "version": release["resource_version__version"],
                            "name": release["resource_version__name"],
                            "title": release["resource_version__title"],
                        }
                    ),
                    "language": sdk.language.value if sdk else "",
                    "sdk_version_number": sdk.version if sdk else "",
                    "sdk_download_url": sdk.url if sdk else "",
                    "sdk_name": sdk.name if sdk else "",
                    "sdk_install_command": sdk.install_command if sdk else "",
                }
            )

        return sorted(stage_sdks, key=operator.itemgetter("stage_name"))


support_helper = SupportHelper()
