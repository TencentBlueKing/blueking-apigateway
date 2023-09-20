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
import functools
import logging
from typing import Dict, List, Optional, Tuple, Type, Union

from django.db.models.query import QuerySet
from iam.collection import FancyDict
from iam.resource.provider import ListResult, ResourceProvider
from iam.resource.utils import Page, get_filter_obj, get_page_obj

from apigateway.apps.plugin.models import PluginConfig
from apigateway.components.bk_iam_bkapi import BKIAMClient
from apigateway.core.models import Gateway, Resource, Stage
from apigateway.iam.constants import ResourceTypeEnum
from apigateway.iam.models import IAMGradeManager

logger = logging.getLogger(__name__)


class BaseResourceProvider(ResourceProvider):
    def list_attr(self, **options) -> ListResult:
        return ListResult(results=[], count=0)

    def list_attr_value(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        return ListResult(results=[], count=0)

    def list_instance_by_policy(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        return ListResult(results=[], count=0)

    def fetch_instance_list(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        return ListResult(results=[], count=0)

    def fetch_resource_type_schema(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        return ListResult(results=[], count=0)

    def _fetch_gateway_approvers(self, gateway_ids: List[int]) -> Dict[int, List[str]]:
        bk_iam_client = BKIAMClient()
        return {
            grade_manager.gateway_id: bk_iam_client.fetch_grade_manager_members(grade_manager.grade_manager_id)
            for grade_manager in IAMGradeManager.objects.filter(gateway_id__in=gateway_ids)
        }


def fetch_gateway_id_in_filter(func):
    """装饰器：获取过滤条件中的网关 ID"""

    @functools.wraps(func)
    def wrapper(self, filter_obj: FancyDict, *args, **kwargs):
        parent = filter_obj.get("parent")
        if parent and parent.get("type") == "gateway":
            self.gateway_id_in_filter = int(parent["id"])
            return func(self, filter_obj, *args, **kwargs)

        return ListResult(results=[], count=0)

    return wrapper


class GatewayProvider(BaseResourceProvider):
    """网关反向拉取"""

    def _get_gateways_with_registered_to_iam(self) -> QuerySet:
        """
        仅获取已创建 IAM 分级管理员的网关

        :returns: 返回 values 中仅包含 id, name 字段
        """
        gateway_ids = IAMGradeManager.objects.all().values_list("gateway_id", flat=True)
        queryset = Gateway.objects.filter(id__in=list(gateway_ids))
        return queryset.values("id", "name")

    def list_instance(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        queryset = self._get_gateways_with_registered_to_iam()
        results = [
            {
                "id": str(gateway["id"]),
                "display_name": gateway["name"],
            }
            for gateway in queryset[page_obj.slice_from : page_obj.slice_to]
        ]
        return ListResult(results=results, count=queryset.count())

    def fetch_instance_info(self, filter_obj: FancyDict, **options) -> ListResult:
        ids = filter_obj.ids or []

        queryset = Gateway.objects.filter(id__in=map(int, ids)).values("id", "name")
        approvers = self._fetch_gateway_approvers([gateway["id"] for gateway in queryset])
        results = [
            {
                "id": str(gateway["id"]),
                "display_name": gateway["name"],
                "_bk_iam_approver_": approvers.get(gateway["id"]) or [],
            }
            for gateway in queryset
        ]

        return ListResult(results=results, count=len(results))

    def search_instance(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        """支持模糊搜索网关名"""
        queryset = self._get_gateways_with_registered_to_iam()
        if filter_obj.keyword:
            queryset = queryset.filter(name__icontains=filter_obj.keyword)

        results = [
            {
                "id": str(gateway["id"]),
                "display_name": gateway["name"],
            }
            for gateway in queryset[page_obj.slice_from : page_obj.slice_to]
        ]
        return ListResult(results=results, count=queryset.count())


class GatewayStageProvider(BaseResourceProvider):
    """网关环境反向拉取"""

    @fetch_gateway_id_in_filter
    def list_instance(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        queryset = Stage.objects.filter(gateway_id=self.gateway_id_in_filter).values("id", "name")
        results = [
            {
                "id": str(stage["id"]),
                "display_name": stage["name"],
            }
            for stage in queryset[page_obj.slice_from : page_obj.slice_to]
        ]
        return ListResult(results=results, count=queryset.count())

    @fetch_gateway_id_in_filter
    def fetch_instance_info(self, filter_obj: FancyDict, **options) -> ListResult:
        ids = filter_obj.ids or []

        approvers = self._fetch_gateway_approvers([self.gateway_id_in_filter])
        iam_approver = approvers.get(self.gateway_id_in_filter) or []

        queryset = Stage.objects.filter(gateway_id=self.gateway_id_in_filter, id__in=map(int, ids)).values(
            "id", "name"
        )
        results = [
            {
                "id": str(stage["id"]),
                "display_name": stage["name"],
                "_bk_iam_approver_": iam_approver,
            }
            for stage in queryset
        ]

        return ListResult(results=results, count=len(results))

    @fetch_gateway_id_in_filter
    def search_instance(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        """支持模糊搜索环境名"""
        queryset = Stage.objects.filter(gateway_id=self.gateway_id_in_filter)
        if filter_obj.keyword:
            queryset = queryset.filter(name__icontains=filter_obj.keyword)

        queryset = queryset.values("id", "name")
        results = [
            {
                "id": str(stage["id"]),
                "display_name": stage["name"],
            }
            for stage in queryset[page_obj.slice_from : page_obj.slice_to]
        ]

        return ListResult(results=results, count=queryset.count())


class GatewayResourceProvider(BaseResourceProvider):
    """网关资源反向拉取"""

    @fetch_gateway_id_in_filter
    def list_instance(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        queryset = Resource.objects.filter(gateway_id=self.gateway_id_in_filter).values("id", "name")
        results = [
            {
                "id": str(resource["id"]),
                "display_name": resource["name"],
            }
            for resource in queryset[page_obj.slice_from : page_obj.slice_to]
        ]
        return ListResult(results=results, count=queryset.count())

    @fetch_gateway_id_in_filter
    def fetch_instance_info(self, filter_obj: FancyDict, **options) -> ListResult:
        ids = filter_obj.ids or []

        approvers = self._fetch_gateway_approvers([self.gateway_id_in_filter])
        iam_approver = approvers.get(self.gateway_id_in_filter) or []

        queryset = Resource.objects.filter(gateway_id=self.gateway_id_in_filter, id__in=map(int, ids)).values(
            "id", "name"
        )
        results = [
            {
                "id": str(resource["id"]),
                "display_name": resource["name"],
                "_bk_iam_approver_": iam_approver,
            }
            for resource in queryset
        ]

        return ListResult(results=results, count=len(results))

    @fetch_gateway_id_in_filter
    def search_instance(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        """支持模糊搜索资源名"""
        queryset = Resource.objects.filter(gateway_id=self.gateway_id_in_filter)
        if filter_obj.keyword:
            queryset = queryset.filter(name__icontains=filter_obj.keyword)

        queryset = queryset.values("id", "name")
        results = [
            {
                "id": str(resource["id"]),
                "display_name": resource["name"],
            }
            for resource in queryset[page_obj.slice_from : page_obj.slice_to]
        ]
        return ListResult(results=results, count=queryset.count())


class GatewayPluginConfigProvider(BaseResourceProvider):
    """网关插件反向拉取"""

    @fetch_gateway_id_in_filter
    def list_instance(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        queryset = PluginConfig.objects.filter(gateway_id=self.gateway_id_in_filter).values("id", "name")
        results = [
            {
                "id": str(plugin["id"]),
                "display_name": plugin["name"],
            }
            for plugin in queryset[page_obj.slice_from : page_obj.slice_to]
        ]
        return ListResult(results=results, count=queryset.count())

    @fetch_gateway_id_in_filter
    def fetch_instance_info(self, filter_obj: FancyDict, **options) -> ListResult:
        ids = filter_obj.ids or []

        approvers = self._fetch_gateway_approvers([self.gateway_id_in_filter])
        iam_approver = approvers.get(self.gateway_id_in_filter) or []

        queryset = PluginConfig.objects.filter(gateway_id=self.gateway_id_in_filter, id__in=map(int, ids)).values(
            "id", "name"
        )
        results = [
            {
                "id": str(plugin["id"]),
                "display_name": plugin["name"],
                "_bk_iam_approver_": iam_approver,
            }
            for plugin in queryset
        ]

        return ListResult(results=results, count=queryset.count())

    @fetch_gateway_id_in_filter
    def search_instance(self, filter_obj: FancyDict, page_obj: Page, **options) -> ListResult:
        """支持模糊搜索插件配置名"""
        queryset = PluginConfig.objects.filter(gateway_id=self.gateway_id_in_filter)
        if filter_obj.keyword:
            queryset = queryset.filter(name__icontains=filter_obj.keyword)

        queryset = queryset.values("id", "name")
        results = [
            {
                "id": str(plugin["id"]),
                "display_name": plugin["name"],
            }
            for plugin in queryset[page_obj.slice_from : page_obj.slice_to]
        ]
        return ListResult(results=results, count=queryset.count())


class IAMResourceProviderFactory:
    """网关各类资源反向拉取工厂"""

    provider_cls_map: Dict[ResourceTypeEnum, Type[ResourceProvider]] = {
        ResourceTypeEnum.GATEWAY: GatewayProvider,
        ResourceTypeEnum.STAGE: GatewayStageProvider,
        ResourceTypeEnum.RESOURCE: GatewayResourceProvider,
        ResourceTypeEnum.PLUGIN_CONFIG: GatewayPluginConfigProvider,
    }

    def __init__(self, resource_type: ResourceTypeEnum):
        self.resource_provider = self.provider_cls_map[resource_type]()

    def provide(self, method: str, data: Dict, **options) -> Union[List, Dict]:
        """
        根据 method 值, 调用对应的方法返回数据

        :param method: 值包括 list_attr, list_attr_value, list_instance 等
        :param data: 其他查询条件数据，如分页数据等
        :return: method 方法返回的数据
        """
        handler = getattr(self, method)
        return handler(data, **options)

    def list_attr(self, data: Optional[Dict] = None, **options) -> List[Dict]:
        """
        查询某个资源类型可用于配置权限的属性列表

        :param data: 占位参数，为了 self.provide 方法的处理统一
        :return: 属性列表
        """
        result = self.resource_provider.list_attr(**options)
        return result.to_list()

    def list_attr_value(self, data: Dict, **options) -> Dict:
        """获取一个资源类型某个属性的值列表"""
        filter_obj, page_obj = self._parse_filter_and_page(data)
        result = self.resource_provider.list_attr_value(filter_obj, page_obj, **options)
        return result.to_dict()

    def list_instance(self, data: Dict, **options) -> Dict:
        """查询资源实例列表(支持分页)"""
        filter_obj, page_obj = self._parse_filter_and_page(data)
        result = self.resource_provider.list_instance(filter_obj, page_obj, **options)
        return result.to_dict()

    def fetch_instance_info(self, data: Dict, **options) -> List[Dict]:
        """查询资源实例列表"""
        filter_obj, _ = self._parse_filter_and_page(data)
        result = self.resource_provider.fetch_instance_info(filter_obj, **options)
        return result.to_list()

    def list_instance_by_policy(self, data: Dict, **options) -> List[Dict]:
        """根据策略表达式查询资源实例"""
        filter_obj, page_obj = self._parse_filter_and_page(data)
        result = self.resource_provider.list_instance_by_policy(filter_obj, page_obj, **options)
        return result.to_list()

    def search_instance(self, data: Dict, **options) -> Dict:
        """根据关键字查询资源实例"""
        filter_obj, page_obj = self._parse_filter_and_page(data)
        result = self.resource_provider.search_instance(filter_obj, page_obj, **options)
        return result.to_dict()

    def _parse_filter_and_page(self, data: Dict) -> Tuple[FancyDict, Page]:
        """处理请求参数"""
        filter_obj = get_filter_obj(
            data["filter"], ["ids", "parent", "search", "resource_type_chain", "keyword", "ancestors"]
        )
        page_obj = get_page_obj(data.get("page"))
        return filter_obj, page_obj
