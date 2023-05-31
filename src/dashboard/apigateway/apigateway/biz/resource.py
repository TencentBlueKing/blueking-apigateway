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


import json
from typing import List, Optional

from django.db.models import Q

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum
from apigateway.apps.access_strategy.models import AccessStrategyBinding
from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.apps.support.models import ResourceDoc
from apigateway.common.contexts import ResourceAuthContext
from apigateway.core.constants import BackendConfigTypeEnum, ContextScopeTypeEnum
from apigateway.core.models import Context, Proxy, Resource, Stage, StageResourceDisabled
from apigateway.utils import time


class ResourceHandler:
    @staticmethod
    def save_related_data(
        gateway,
        resource,
        proxy_type,
        proxy_config,
        auth_config,
        label_ids,
        disabled_stage_ids,
        backend_config_type: str = BackendConfigTypeEnum.DEFAULT.value,
        backend_service_id: Optional[int] = None,
    ):
        # 1. save proxy, and set resource proxy_id
        ResourceHandler().save_proxy_config(
            resource,
            proxy_type,
            proxy_config,
            backend_config_type=backend_config_type,
            backend_service_id=backend_service_id,
        )

        # 2. save auth config
        ResourceHandler().save_auth_config(resource.id, auth_config)

        # 3. save labels
        ResourceHandler().save_labels(gateway, resource, label_ids, delete_unspecified=True)

        # 4. save disabled stags
        ResourceHandler().save_disabled_stages(gateway, resource, disabled_stage_ids, delete_unspecified=True)

    @staticmethod
    def save_labels(gateway, resource, label_ids, delete_unspecified=False):
        """
        存储标签
        :param bool delete_unspecified: 是否删除未指定的标签，资源下非本次提供的即为未指定标签
        """
        # 筛选出在 ResourceLabel 中不存在的 label_ids 进行添加
        exist_label_ids = ResourceLabel.objects.filter(resource=resource, api_label__id__in=label_ids).values_list(
            "api_label__id", flat=True
        )
        labels_to_add = APILabel.objects.filter(api=gateway, id__in=list(set(label_ids) - set(exist_label_ids)))
        for label in labels_to_add:
            ResourceLabel.objects.update_or_create(resource=resource, api_label=label)

        if delete_unspecified:
            # 清理非本次添加的标签
            ResourceLabel.objects.filter(resource=resource).exclude(api_label__id__in=label_ids).delete()

    @staticmethod
    def save_disabled_stages(gateway, resource, disabled_stage_ids, delete_unspecified=False):
        """
        存储资源禁用环境
        :param bool delete_unspecified: 是否删除未指定的禁用环境，资源下非本次提供的禁用环境即为未指定禁用环境
        """

        # 筛选出 StageResourceDisabled 中不存在的 disabled_stage_ids 进行添加
        exist_disabled_stage_ids = StageResourceDisabled.objects.filter(
            resource=resource, stage__id__in=disabled_stage_ids
        ).values_list("stage__id", flat=True)
        disabled_stages_to_add = Stage.objects.filter(
            api=gateway, id__in=list(set(disabled_stage_ids) - set(exist_disabled_stage_ids))
        )
        for stage in disabled_stages_to_add:
            StageResourceDisabled.objects.update_or_create(stage=stage, resource=resource)

        if delete_unspecified:
            # 清理非本次添加的禁用环境
            StageResourceDisabled.objects.filter(resource=resource).exclude(stage__id__in=disabled_stage_ids).delete()

    @staticmethod
    def save_auth_config(resource_id, config):
        """
        存储资源认证配置
        """
        auth_config = ResourceHandler()._get_current_auth_config(resource_id)
        auth_config.update(config)

        return ResourceAuthContext().save(resource_id, auth_config)

    # TODO: move into save_auth_config?
    @staticmethod
    def _get_current_auth_config(resource_id):
        """
        获取资源当前认证配置
        """
        default_hidden_config = {
            # 跳过用户认证逻辑，值为False时，不根据请求参数中的用户信息校验用户
            "skip_auth_verification": False,
            "auth_verified_required": True,
            "app_verified_required": True,
            "resource_perm_required": True,
        }
        try:
            return ResourceAuthContext().get_config(resource_id)
        except Context.DoesNotExist:
            return default_hidden_config

    @staticmethod
    def save_proxy_config(
        resource,
        proxy_type,
        proxy_config,
        backend_config_type: str = BackendConfigTypeEnum.DEFAULT.value,
        backend_service_id: Optional[int] = None,
    ):
        proxy, created = Proxy.objects.save_proxy_config(
            resource,
            proxy_type,
            proxy_config,
            backend_config_type=backend_config_type,
            backend_service_id=backend_service_id,
        )
        resource.proxy_id = proxy.id
        resource.save(update_fields=["proxy_id", "updated_time"])
        return proxy, created

    @staticmethod
    def get_proxy_configs(resource):
        """
        获取资源代理配置，及当前代理类型
        """
        current_proxy = Proxy.objects.get(id=resource.proxy_id)

        return {
            "type": current_proxy.type,
            "backend_config_type": current_proxy.backend_config_type,
            "backend_service_id": current_proxy.backend_service_id,
            "configs": {proxy.type: proxy.config for proxy in Proxy.objects.filter(resource=resource)},
        }

    @staticmethod
    def delete_by_gateway_id(gateway_id):
        resource_ids = list(Resource.objects.filter(api_id=gateway_id).values_list("id", flat=True))
        if not resource_ids:
            return
        ResourceHandler().delete_resources(resource_ids)

    @staticmethod
    def delete_resources(resource_ids: List[int], api=None):
        if not resource_ids:
            return

        if api is not None:
            # 指定网关时，二次确认资源属于该网关，防止误删除
            resource_ids = Resource.objects.filter_by_ids(api, resource_ids)
            assert resource_ids

        # 1. delete auth config context
        Context.objects.delete_by_scope_ids(
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            scope_ids=resource_ids,
        )

        # 2. delete proxy

        Proxy.objects.delete_by_resource_ids(resource_ids)

        # 3. delete access-strategy binding

        AccessStrategyBinding.objects.delete_by_scope_ids(
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            scope_ids=resource_ids,
        )

        # 4. delete resource doc

        ResourceDoc.objects.delete_by_resource_ids(resource_ids)

        # 5. delete resource
        Resource.objects.filter(id__in=resource_ids).delete()

    @staticmethod
    def filter_resource(gateway, query=None, path=None, method=None, label_name=None, order_by=None, fuzzy=True):
        """
        查询资源，根据模糊查询串匹配，根据path、method匹配，根据标签匹配
        """
        queryset = Resource.objects.filter(api=gateway)

        # query 不是模型字段，仅支持模糊匹配，如需精确匹配，可使用具体字段
        if query and fuzzy:
            queryset = queryset.filter(Q(path__contains=query) | Q(name__contains=query))

        if path:
            if fuzzy:
                queryset = queryset.filter(path__contains=path)
            else:
                queryset = queryset.filter(path=path)

        if method:
            queryset = queryset.filter(method=method)

        if label_name:
            resource_ids = ResourceLabel.objects.filter_resource_ids(gateway=gateway, label_name=label_name)
            queryset = queryset.filter(id__in=resource_ids)

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset

    @staticmethod
    def snapshot(
        resource,
        as_dict=False,
        proxy_map=None,
        context_map=None,
        disabled_stage_map=None,
        api_label_map=None,
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
            data["proxy"] = Proxy.objects.get(id=resource.proxy_id).snapshot(as_dict=True)
        else:
            data["proxy"] = proxy_map[resource.proxy_id]

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

        if as_dict:
            return data

        return json.dumps(data)
