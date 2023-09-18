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
import itertools
import json
import operator
from typing import Any, Dict, List, Optional

from django.db.models import Q
from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.models import ResourceDoc
from apigateway.common.audit.shortcuts import record_audit_log
from apigateway.common.contexts import ResourceAuthContext
from apigateway.core.constants import ContextScopeTypeEnum
from apigateway.core.models import Context, Gateway, Proxy, Resource, StageResourceDisabled
from apigateway.utils import time


class ResourceHandler:
    @classmethod
    def save_auth_config(cls, resource_id: int, config: Dict[str, Any]):
        """存储资源认证配置"""
        # 获取当前的配置
        try:
            auth_config = ResourceAuthContext().get_config(resource_id)
        except Context.DoesNotExist:
            auth_config = cls.get_default_auth_config()

        # 用传入的配置，覆盖当前的配置
        auth_config.update(config)

        ResourceAuthContext().save(resource_id, auth_config)

    @staticmethod
    def delete_by_gateway_id(gateway_id):
        resource_ids = list(Resource.objects.filter(gateway_id=gateway_id).values_list("id", flat=True))
        if not resource_ids:
            return
        ResourceHandler.delete_resources(resource_ids)

    @staticmethod
    def delete_resources(resource_ids: List[int]):
        if not resource_ids:
            return

        # 1. delete auth config context
        Context.objects.filter(scope_type=ContextScopeTypeEnum.RESOURCE.value, scope_id__in=resource_ids).delete()

        # 2. delete proxy
        Proxy.objects.filter(resource_id__in=resource_ids).delete()

        # 3. delete plugin binding
        PluginBinding.objects.filter(
            scope_type=PluginBindingScopeEnum.RESOURCE.value,
            scope_id__in=resource_ids,
        ).delete()

        # 4. delete resource doc
        ResourceDoc.objects.filter(resource_id__in=resource_ids).delete()

        # 5. delete resource
        Resource.objects.filter(id__in=resource_ids).delete()

    @staticmethod
    def snapshot(
        resource,
        as_dict=False,
        proxy_map=None,
        context_map=None,
        disabled_stage_map=None,
        api_label_map=None,
        backends=None,
        plugin_map=None,
    ):
        """
        - can add field
        - should not delete field!!!!!!!!!
        """

        data = {
            "id": resource.pk,
            "name": resource.name,
            "description": resource.description,
            "description_en": resource.description_en,
            "method": resource.method,
            "path": resource.path,
            "match_subpath": resource.match_subpath,
            "is_public": resource.is_public,
            "allow_apply_permission": resource.allow_apply_permission,
            "created_time": time.format(resource.created_time),
            "updated_time": time.format(resource.updated_time),
        }

        if proxy_map is None:
            data["proxy"] = Proxy.objects.get(resource_id=resource.id).snapshot(as_dict=True)
        else:
            data["proxy"] = proxy_map[resource.id]

        if context_map is None:
            contexts = Context.objects.filter(
                scope_type=ContextScopeTypeEnum.RESOURCE.value,
                scope_id=resource.pk,
            ).all()
            data["contexts"] = {c.type: c.snapshot(as_dict=True) for c in contexts}
        else:
            data["contexts"] = context_map[resource.pk]

        if disabled_stage_map is None:
            data["disabled_stages"] = list(
                StageResourceDisabled.objects.filter(resource=resource).values_list("stage__name", flat=True)
            )
        else:
            data["disabled_stages"] = disabled_stage_map.get(resource.pk, [])

        if api_label_map is None:
            data["api_labels"] = list(
                ResourceLabel.objects.filter(resource_id=resource.pk).values_list("api_label_id", flat=True)
            )
        else:
            data["api_labels"] = api_label_map.get(resource.pk, [])

        if backends:
            data["backend_ids"] = backends

        if plugin_map:
            data["plugins"] = plugin_map.get(resource.pk, [])

        if as_dict:
            return data

        return json.dumps(data)

    @staticmethod
    def filter_by_resource_filter_condition(gateway_id: int, condition: Dict[str, Any]):
        """根据前端资源列表筛选条件，筛选出符合条件的资源"""
        queryset = Resource.objects.filter(gateway_id=gateway_id)

        if condition.get("name"):
            queryset = queryset.filter(name=condition["name"])

        if condition.get("path"):
            queryset = queryset.filter(path=condition["path"])

        if condition.get("method"):
            queryset = queryset.filter(method=condition["method"])

        if condition.get("backend_id"):
            resource_ids = Proxy.objects.filter(gateway_id=gateway_id, backend_id=condition["backend_id"]).values_list(
                "resource_id", flat=True
            )
            queryset = queryset.filter(id__in=resource_ids)

        if condition.get("label_ids"):
            labels = APILabel.objects.filter(gateway_id=gateway_id, id__in=condition["label_ids"])
            resource_ids = (
                ResourceLabel.objects.filter(api_label__in=labels).values_list("resource_id", flat=True).distinct()
            )
            queryset = queryset.filter(id__in=resource_ids)

        if condition.get("query"):
            query = condition.get("query")
            queryset = queryset.filter(Q(path__icontains=query) | Q(name__icontains=query))

        if condition.get("order_by"):
            queryset = queryset.order_by(condition["order_by"])

        return queryset

    @staticmethod
    def get_default_auth_config():
        return {
            # 跳过用户认证逻辑，值为False时，不根据请求参数中的用户信息校验用户
            "skip_auth_verification": False,
            "auth_verified_required": True,
            "app_verified_required": True,
            "resource_perm_required": True,
        }

    @staticmethod
    def record_audit_log_success(
        username: str,
        gateway_id: int,
        op_type: OpTypeEnum,
        instance_id: int,
        instance_name: str,
    ):
        comment = {
            OpTypeEnum.CREATE: _("创建资源"),
            OpTypeEnum.MODIFY: _("更新资源"),
            OpTypeEnum.DELETE: _("删除资源"),
        }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.RESOURCE.value,
            op_object_id=instance_id,
            op_object=instance_name,
            comment=comment,
        )

    @staticmethod
    def save_resource_labels(gateway: Gateway, resource: Resource, label_ids: List[int]):
        """
        存储资源标签
        - 删除未指定的标签

        :param label_ids: 网关标签 ID，忽略不存在的标签
        """
        # 资源当前已有的标签
        remaining_resource_labels = {
            label.api_label_id: label.id for label in ResourceLabel.objects.filter(resource=resource)
        }

        add_resource_labels = []
        for gateway_label in APILabel.objects.filter(gateway=gateway, id__in=label_ids):
            if gateway_label.id in remaining_resource_labels:
                remaining_resource_labels.pop(gateway_label.id)
                continue

            add_resource_labels.append(ResourceLabel(resource=resource, api_label=gateway_label))

        if add_resource_labels:
            # resource label 最多 10 个，不需要指定 batch_size
            ResourceLabel.objects.bulk_create(add_resource_labels)

        if remaining_resource_labels:
            ResourceLabel.objects.filter(id__in=remaining_resource_labels.values()).delete()

    @staticmethod
    def group_by_gateway_id(resource_ids: List[int]) -> Dict[int, List[int]]:
        """将资源 ID 按网关进行分组"""
        data = Resource.objects.filter(id__in=resource_ids).values("gateway_id", "id").order_by("gateway_id")
        return {
            gateway_id: [item["id"] for item in group]
            for gateway_id, group in itertools.groupby(data, key=operator.itemgetter("gateway_id"))
        }

    @staticmethod
    def get_last_updated_time(gateway_id: int) -> Optional[datetime.datetime]:
        """获取网关下资源的最近更新时间"""
        return (
            Resource.objects.filter(gateway_id=gateway_id)
            .order_by("-updated_time")
            .values_list("updated_time", flat=True)
            .first()
        )

    @staticmethod
    def get_id_to_resource(gateway_id: int) -> Dict[int, Resource]:
        return {r.id: r for r in Resource.objects.filter(gateway_id=gateway_id)}
