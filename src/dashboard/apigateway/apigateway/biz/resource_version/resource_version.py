# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import datetime
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from cachetools import TTLCache, cached
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.openapi.models import (
    OpenAPIFileResourceSchemaVersion,
    OpenAPIResourceSchema,
    OpenAPIResourceSchemaVersion,
)
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.biz.audit import Auditor
from apigateway.biz.context import ContextHandler
from apigateway.biz.resource import (
    ProxyHandler,
    ResourceDisabledStageHandler,
    ResourceHandler,
    ResourceLabelHandler,
    ResourceOpenAPISchemaVersionHandler,
)
from apigateway.common.constants import CACHE_TIME_5_MINUTES
from apigateway.common.error_codes import error_codes
from apigateway.core.constants import ContextScopeTypeEnum, ProxyTypeEnum, ResourceVersionSchemaEnum
from apigateway.core.models import Gateway, Release, Resource, ResourceVersion, Stage
from apigateway.utils import time as time_utils
from apigateway.utils.version import max_version


class ResourceVersionHandler:
    @staticmethod
    def make_version(gateway: Gateway):
        resource_queryset = Resource.objects.filter(gateway_id=gateway.id).all()

        resource_ids = list(resource_queryset.values_list("id", flat=True))

        proxy_map = ProxyHandler.get_resource_id_to_snapshot(resource_ids)

        context_map = ContextHandler.filter_id_type_snapshot_map(
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            scope_ids=resource_ids,
        )
        disabled_stage_map = {
            resource_id: [stage["name"] for stage in stages]
            for resource_id, stages in ResourceDisabledStageHandler.filter_disabled_stages_by_gateway(gateway).items()
        }

        gateway_label_map = {
            resource_id: [label["id"] for label in labels]
            for resource_id, labels in ResourceLabelHandler.get_labels_by_gateway(gateway).items()
        }

        # plugin
        resource_id_to_plugin_bindings = PluginBinding.objects.query_scope_id_to_bindings(
            gateway.id, PluginBindingScopeEnum.RESOURCE, resource_ids
        )

        resource_plugins_map: Dict[int, List[Dict]] = defaultdict(list)

        for resource_id, bindings in resource_id_to_plugin_bindings.items():
            resource_plugins_map[resource_id].extend([binding.snapshot() for binding in bindings])

        return [
            ResourceHandler.snapshot(
                r,
                as_dict=True,
                proxy_map=proxy_map,
                context_map=context_map,
                disabled_stage_map=disabled_stage_map,
                api_label_map=gateway_label_map,
                plugin_map=resource_plugins_map,
            )
            for r in resource_queryset
        ]

    @staticmethod
    def get_data_by_id_or_new(gateway: Gateway, resource_version_id: Optional[int]) -> list:
        """
        根据版本 ID 获取 Data，或者获取当前资源列表中的版本数据
        """
        if resource_version_id:
            resource_version_data = ResourceVersion.objects.get(gateway=gateway, id=resource_version_id).data
            resource_id_to_schema = ResourceVersionHandler.get_resource_id_to_schema_by_resource_version(
                resource_version_id
            )
            for resource in resource_version_data:
                resource["openapi_schema"] = resource_id_to_schema.get(resource["id"], {})
            return resource_version_data

        # 如果没有指定版本 ID，则根据编辑区数据生成版本数据(包含schema信息)
        resource_version_data = ResourceVersionHandler.make_version(gateway)
        resource_ids = [resource["id"] for resource in resource_version_data if "id" in resource]
        # 查询资源所有的schema
        resource_schemas = OpenAPIResourceSchema.objects.filter(resource_id__in=resource_ids)
        resource_id_to_schema = {schema.resource_id: schema.schema for schema in resource_schemas}
        for resource in resource_version_data:
            resource["openapi_schema"] = resource_id_to_schema.get(resource["id"], {})
        return resource_version_data

    @staticmethod
    def delete_by_gateway_id(gateway_id: int):
        # delete gateway release
        Release.objects.filter(gateway_id=gateway_id).delete()

        # delete gateway openapi resource schema version
        OpenAPIResourceSchemaVersion.objects.filter(resource_version__gateway_id=gateway_id).delete()

        # delete gateway openapi file resource schema version
        OpenAPIFileResourceSchemaVersion.objects.filter(gateway_id=gateway_id).delete()

        # delete resource version
        ResourceVersion.objects.filter(gateway_id=gateway_id).delete()

    @classmethod
    def create_resource_version(cls, gateway: Gateway, data: Dict[str, Any], username: str = "") -> ResourceVersion:
        now = time_utils.now_datetime()

        data.update(
            {
                "data": ResourceVersionHandler.make_version(gateway),
                "gateway": gateway,
                "version": data.get("version"),
                "created_time": now,
                "schema_version": ResourceVersionSchemaEnum.V2.value,
                "created_by": username,
                "updated_by": username,
            }
        )
        resource_version = ResourceVersion(**data)

        resource_version.save()

        # 创建资源schema版本
        ResourceOpenAPISchemaVersionHandler.make_new_version(resource_version)

        Auditor.record_resource_version_op_success(
            op_type=OpTypeEnum.CREATE,
            username=(username or settings.GATEWAY_DEFAULT_CREATOR),
            gateway_id=gateway.id,
            instance_id=resource_version.id,
            instance_name=resource_version.version,
            data_before={},
            data_after={"version": data.get("version")},
        )

        return resource_version

    @staticmethod
    def get_released_public_resources(gateway_id: int, stage_name: Optional[str] = None) -> List[dict]:
        """
        获取已发布的所有资源，将各环境发布的资源合并
        """

        # 已发布版本中，以最新版本中资源配置为准
        resource_mapping = {}
        resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id, stage_name)
        for resource_version_id in sorted(resource_version_ids):
            resources_in_version = ResourceVersion.objects.get_resources(gateway_id, resource_version_id)
            resource_mapping.update(resources_in_version)

        # 只展示公开的资源
        resources = filter(lambda x: x["is_public"], resource_mapping.values())

        # 若资源无可用环境，则不展示该资源
        # 比如：资源测试阶段，禁用环境 prod，则 prod 环境下不应展示该资源
        current_stage_names = set([stage_name] if stage_name else Stage.objects.get_names(gateway_id))
        return [
            resource
            for resource in resources
            if not resource["disabled_stages"] or (current_stage_names - set(resource["disabled_stages"]))
        ]

    @staticmethod
    def need_new_version(gateway_id: int):
        """
        是否需要创建新的资源版本
        """
        latest_version = ResourceVersion.objects.get_latest_version(gateway_id)
        resource_last_updated_time = ResourceHandler.get_last_updated_time(gateway_id)

        if not (latest_version or resource_last_updated_time):
            return False

        # 无资源版本
        if not latest_version:
            return True

        # 如果有最近更新的资源，最近的更新资源时间 > 最新版本生成时间
        if resource_last_updated_time and resource_last_updated_time > latest_version.created_time:
            return True

        # 版本中资源数量是否发生变化
        # some resource could be deleted
        resource_count = Resource.objects.filter(gateway_id=gateway_id).count()
        if resource_count != len(latest_version.data):
            return True

        return False

    @staticmethod
    def get_latest_version_by_gateway(gateway_id: int):
        """通过 gateway_id 获取最新的版本号"""

        # 查询最近的 10 条数据，并根据 id 字段排序
        versions = ResourceVersion.objects.filter(gateway_id=gateway_id).order_by("-id")[:10].values("version")
        if not versions:
            return ""

        # 取最大的 version
        # return max([ver["version"] for ver in versions], key=version.parse)
        return max_version([ver["version"] for ver in versions])

    @staticmethod
    def get_latest_created_time(gateway_id: int) -> Optional[datetime.datetime]:
        return ResourceVersion.objects.filter(gateway_id=gateway_id).values_list("created_time", flat=True).last()

    # TODO: 缓存优化：可使用 django cache(with database backend) or dogpile 缓存
    # 版本中包含的配置不会变化，但是处理逻辑可能调整，因此，缓存需支持版本
    @staticmethod
    @cached(cache=TTLCache(maxsize=300, ttl=CACHE_TIME_5_MINUTES))
    def get_used_stage_vars(gateway_id: int, id: int):
        resource_version = ResourceVersion.objects.filter(gateway_id=gateway_id, id=id).first()
        if not resource_version:
            return None

        used_in_path = set()
        used_in_host = set()
        for resource in resource_version.data:
            if resource["proxy"]["type"] != ProxyTypeEnum.HTTP.value:
                continue
            if resource.get("stage_vars"):
                stage_vars = resource["stage_vars"]
            else:
                stage_vars = ResourceHandler.get_resource_use_stage_vars(resource)
            used_in_path.update(stage_vars["in_path"])
            used_in_host.update(stage_vars["in_host"])
        return {
            "in_path": list(used_in_path),
            "in_host": list(used_in_host),
        }

    @staticmethod
    def get_resource_schema(resource_version_id: int, resource_id: int) -> dict:
        """
        获取指定版本的资源对应的api schema
        """
        resources_version_schema = OpenAPIResourceSchemaVersion.objects.filter(
            resource_version_id=resource_version_id
        ).first()
        if resources_version_schema is None:
            return {}
        # 筛选资源数据
        for schema_info in resources_version_schema.schema:
            schema = schema_info["schema"]
            if resource_id == schema_info["resource_id"]:
                return schema
        return {}

    @staticmethod
    def get_resource_id_to_schema_by_resource_version(resource_version_id: int) -> dict:
        """
        获取资源版本下的资源与 api schema 的映射关系
        """
        resources_version_schema = OpenAPIResourceSchemaVersion.objects.filter(
            resource_version_id=resource_version_id
        ).first()
        if resources_version_schema is None:
            return {}
        return {schema_info["resource_id"]: schema_info["schema"] for schema_info in resources_version_schema.schema}

    @staticmethod
    def get_resource_id(resource_version_id: int, resource_name: str) -> int:
        resource_version = ResourceVersion.objects.filter(id=resource_version_id).first()
        if not resource_version:
            return -1
        for resource in resource_version.data:
            if resource["name"] == resource_name:
                return resource["id"]
        return -1

    @staticmethod
    @cached(cache=TTLCache(maxsize=300, ttl=CACHE_TIME_5_MINUTES))
    def get_resource_names_set(resource_version_id: int, raise_exception: bool = False) -> Set[str]:
        """获取资源版本中的资源名称列表, 缓存 5 分钟

        Args:
            resource_version_id (int): 资源版本 ID
            raise_exception (bool, optional): 是否抛出异常, 如果资源版本不存在, 则抛出异常. 默认 False
        """
        resource_version = ResourceVersion.objects.filter(id=resource_version_id).first()
        if not resource_version:
            if raise_exception:
                raise error_codes.NOT_FOUND.format(_("资源版本不存在"))
            return set()
        return {resource["name"] for resource in resource_version.data}
