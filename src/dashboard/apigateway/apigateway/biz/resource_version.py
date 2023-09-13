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
import datetime
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.label.models import ResourceLabel
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc, ResourceDocVersion
from apigateway.biz.context import ContextHandler
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.stage_resource_disabled import StageResourceDisabledHandler
from apigateway.common.audit.shortcuts import record_audit_log
from apigateway.core.constants import ContextScopeTypeEnum, ResourceVersionSchemaEnum
from apigateway.core.models import Backend, Gateway, Proxy, Release, Resource, ResourceVersion, Stage
from apigateway.utils import time as time_utils
from apigateway.utils.string import random_string


class ResourceVersionHandler:
    @staticmethod
    def make_version(gateway: Gateway):
        resource_queryset = Resource.objects.filter(gateway_id=gateway.id).all()
        resource_ids = list(resource_queryset.values_list("id", flat=True))

        proxy_map = Proxy.objects.get_resource_id_to_snapshot(resource_ids)

        context_map = ContextHandler.filter_id_type_snapshot_map(
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            scope_ids=resource_ids,
        )
        disabled_stage_map = {
            resource_id: [stage["name"] for stage in stages]
            for resource_id, stages in StageResourceDisabledHandler.filter_disabled_stages_by_gateway(gateway).items()
        }

        gateway_label_map = {
            resource_id: [label["id"] for label in labels]
            for resource_id, labels in ResourceLabel.objects.filter_labels_by_gateway(gateway).items()
        }

        # backend
        backend_ids = list(Backend.objects.filter(gateway_id=gateway.id).values_list("id", flat=True))

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
                backends=backend_ids,
                plugin_map=resource_plugins_map,
            )
            for r in resource_queryset
        ]

    @staticmethod
    def add_create_audit_log(gateway: Gateway, resource_version: ResourceVersion, username: str):
        record_audit_log(
            username=username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway.id,
            op_object_type=OpObjectTypeEnum.RESOURCE_VERSION.value,
            op_object_id=resource_version.id,
            op_object=resource_version.name,
            comment=_("生成版本"),
        )

    @staticmethod
    def get_data_by_id_or_new(gateway: Gateway, resource_version_id: Optional[int]) -> list:
        """
        根据版本 ID 获取 Data，或者获取当前资源列表中的版本数据
        """
        if resource_version_id:
            return ResourceVersion.objects.get(gateway=gateway, id=resource_version_id).data

        return ResourceVersionHandler.make_version(gateway)

    @staticmethod
    def delete_by_gateway_id(gateway_id: int):
        # delete gateway release
        Release.objects.delete_by_gateway_id(gateway_id)

        # delete resource version
        ResourceVersion.objects.filter(gateway_id=gateway_id).delete()

    @classmethod
    def create_resource_version(cls, gateway: Gateway, data: Dict[str, Any], username: str = "") -> ResourceVersion:
        # validate data
        cls._validate_resource_version_data(gateway, data.get("version", ""))

        now = time_utils.now_datetime()

        # todo: name 是否直接可以去掉？created_time：与版本名中时间保持一致，方便 SDK 使用此时间作为版本号
        name = ResourceVersionHandler.generate_version_name(gateway.name, now)
        data.update(
            {
                "name": name,
                "gateway": gateway,
                # TODO: 待 version 改为必填后，下面的 version 赋值去掉
                "version": data.get("version") or name,
                "created_time": now,
                "schema_version": ResourceVersionSchemaEnum.V2.value,
            }
        )
        resource_version = ResourceVersion(**data)

        resource_version.save()

        ResourceVersionHandler.add_create_audit_log(gateway, resource_version, username)

        return resource_version

    @staticmethod
    def _validate_resource_version_data(gateway: Gateway, version: str):
        # 判断是否创建资源
        if not Resource.objects.filter(gateway_id=gateway.id).exists():
            raise serializers.ValidationError(_("请先创建资源，然后再生成版本。"))

        # TODO: 临时跳过 version 校验，待提供 version 后，此部分删除
        if not version:
            return

        # 是否创建 backend
        if not Backend.objects.filter(gateway_id=gateway.id).exists():
            raise serializers.ValidationError(_("请先创建后端服务，然后再生成版本。"))

        # ResourceVersion 中数据量较大，因此，不使用 UniqueTogetherValidator
        if ResourceVersion.objects.filter(gateway=gateway, version=version).exists():
            raise serializers.ValidationError(_("版本 {version} 已存在。").format(version=version))
        return

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
        latest_resource = Resource.objects.get_latest_resource(gateway_id)

        if not (latest_version or latest_resource):
            return False

        # 无资源版本
        if not latest_version:
            return True

        # 如果有最近更新的资源，最近的更新资源时间 > 最新版本生成时间
        if latest_resource and latest_resource.updated_time > latest_version.created_time:
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
        return max(version["version"] for version in versions)

    @staticmethod
    def get_resource_version_display(data: Dict[str, Any]) -> str:
        if not data["version"]:
            return f"{data['name']}({data['title']})"

        return f"{data['version']}({data['title']})"

    @staticmethod
    def generate_version_name(gateway_name: str, now: datetime.datetime) -> str:
        """生成新的版本名称"""
        return "{gateway_name}_{now_str}_{random_str}".format(
            gateway_name=gateway_name,
            now_str=time_utils.format(now, fmt="YYYYMMDDHHmmss"),
            random_str=random_string(5),
        )

    @staticmethod
    def get_latest_created_time(gateway_id: int) -> Optional[datetime.datetime]:
        return ResourceVersion.objects.filter(gateway_id=gateway_id).values_list("created_time", flat=True).last()

    @staticmethod
    def get_resource_version_id_by_version(gateway, version: str) -> Optional[int]:
        return ResourceVersion.objects.get_id_by_version(gateway.id, version)

    @staticmethod
    def get_resource_version_id_by_name(gateway, resource_version_name: str) -> Optional[int]:
        return ResourceVersion.objects.get_id_by_name(gateway, resource_version_name)


class ResourceDocVersionHandler:
    @staticmethod
    def get_doc_data_by_rv_or_new(gateway_id: int, resource_version_id: Optional[int]) -> List[Any]:
        """获取版本中文档内容"""
        if resource_version_id:
            try:
                return ResourceDocVersion.objects.get(
                    gateway_id=gateway_id, resource_version_id=resource_version_id
                ).data
            except ResourceDocVersion.DoesNotExist:
                return []

        return ResourceDocVersion.objects.make_version(gateway_id)

    @staticmethod
    def get_doc_updated_time(gateway_id: int, resource_version_id: Optional[int]):
        """获取文档更新时间

        @return:
        {
            1: {
                "zh": "1970-01-01 12:30:50 +8000",
                "en": "1970-01-01 12:30:50 +8000"
            }
        }
        """
        doc_data = ResourceDocVersionHandler.get_doc_data_by_rv_or_new(gateway_id, resource_version_id)

        result: Dict[int, Dict[str, Any]] = defaultdict(dict)
        for doc in doc_data:
            language = doc.get("language", DocLanguageEnum.ZH.value)
            result[doc["resource_id"]][language] = doc["updated_time"]

        return result

    @staticmethod
    def need_new_version(gateway_id):
        """
        是否需要创建新的资源文档版本
        """

        latest_version = ResourceDocVersion.objects.get_latest_version(gateway_id)
        latest_resource_doc = ResourceDoc.objects.get_latest_resource_doc(gateway_id)

        if not (latest_version or latest_resource_doc):
            return False

        if not latest_version:
            return True

        if latest_resource_doc and latest_resource_doc.updated_time > latest_version.created_time:
            return True

        # 文档不可直接删除，资源删除导致的文档删除，在判断“是否需要创建资源版本”时校验
        return False
