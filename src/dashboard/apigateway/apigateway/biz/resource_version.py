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
from typing import Any, Dict, List, Optional

from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.label.models import ResourceLabel
from apigateway.core.constants import ContextScopeTypeEnum
from apigateway.core.models import (
    Context,
    Gateway,
    Proxy,
    Release,
    Resource,
    ResourceVersion,
    Stage,
    StageResourceDisabled,
)

from .resource import ResourceHandler


class ResourceVersionHandler:
    @staticmethod
    def make_version(gateway: Gateway):
        resource_queryset = Resource.objects.filter(api_id=gateway.id).all()
        resource_ids = list(resource_queryset.values_list("id", flat=True))

        proxy_map = Proxy.objects.get_resource_id_to_snapshot(resource_ids)

        context_map = Context.objects.filter_id_type_snapshot_map(
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            scope_ids=resource_ids,
        )

        disabled_stage_map = {
            resource_id: [stage["name"] for stage in stages]
            for resource_id, stages in StageResourceDisabled.objects.filter_disabled_stages_by_gateway(gateway).items()
        }

        api_label_map = {
            resource_id: [label["id"] for label in labels]
            for resource_id, labels in ResourceLabel.objects.filter_labels_by_gateway(gateway).items()
        }

        return [
            ResourceHandler.snapshot(
                r,
                as_dict=True,
                proxy_map=proxy_map,
                context_map=context_map,
                disabled_stage_map=disabled_stage_map,
                api_label_map=api_label_map,
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
        根据版本ID获取Data，或者获取当前资源列表中的版本数据
        """
        if resource_version_id:
            return ResourceVersion.objects.get(gateway=gateway, id=resource_version_id).data

        return ResourceVersionHandler().make_version(gateway)

    @staticmethod
    def delete_by_gateway_id(gateway_id: int):
        # delete api release
        Release.objects.delete_by_gateway_id(gateway_id)

        # delete resource version
        ResourceVersion.objects.filter(gateway_id=gateway_id).delete()

    @staticmethod
    def create_resource_version(gateway: Gateway, data: Dict[str, Any], username: str = "") -> ResourceVersion:
        # FIXME: 从manager迁移过来的, 但是为什么这里依赖于上层的slz? => 应该去掉!
        from apigateway.apps.resource_version.serializers import ResourceVersionSLZ

        slz = ResourceVersionSLZ(data=data, context={"gateway": gateway})
        slz.is_valid(raise_exception=True)

        slz.save(
            data=ResourceVersionHandler().make_version(gateway),
            created_by=username,
            updated_by=username,
        )

        ResourceVersionHandler().add_create_audit_log(gateway, slz.instance, username)

        return slz.instance

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
        resource_count = Resource.objects.filter(api_id=gateway_id).count()
        if resource_count != len(latest_version.data):
            return True

        return False

    @staticmethod
    def get_latest_created_time(gateway_id: int) -> Optional[datetime.datetime]:
        return ResourceVersion.objects.filter(gateway_id=gateway_id).values_list("created_time", flat=True).last()
