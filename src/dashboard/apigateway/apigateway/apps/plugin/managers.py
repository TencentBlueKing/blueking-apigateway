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
from collections import defaultdict
from typing import Any, Dict, List, Optional, Union

from django.db import models
from django.utils.translation import get_language

from apigateway.apps.plugin.constants import PluginBindingScopeEnum


class PluginConfigManager(models.Manager):
    def with_type(self, code: str):
        return self.filter(type__code=code)


class PluginBindingManager(models.Manager):
    def delete_by_gateway_id(self, gateway_id):
        self.filter(api_id=gateway_id).delete()

    def bulk_delete(self, objs):
        return self.filter(id__in=[i.pk for i in objs]).delete()

    def bulk_update_or_create(self, objs, fields):
        to_updates = []
        to_creates = []

        for obj in objs:
            if obj.pk is not None:
                to_updates.append(obj)
            else:
                to_creates.append(obj)

        if to_updates:
            self.bulk_update(to_updates, fields=fields)

        if to_creates:
            self.bulk_create(to_creates)

    def create_or_update_bindings(
        self,
        gateway,
        scope_type: str,
        scope_ids: List[int],
        username: str,
        plugin=None,
        config=None,
        type_=None,
    ):
        """将插件 plugin 绑定到指定 scopes"""
        for scope_id in scope_ids:
            binding, created = self.get_or_create(
                api=gateway,
                scope_type=scope_type,
                scope_id=scope_id,
                type=type_,
                defaults={
                    "plugin": plugin,
                    "config": config,
                    "created_by": username,
                    "updated_by": username,
                },
            )
            if not created:
                binding.plugin = plugin
                binding.updated_by = username
                binding.save()

    def delete_unspecified_bindings(
        self,
        gateway,
        scope_type: str,
        scope_ids: List[int],
        plugin=None,
        config=None,
        type_=None,
    ) -> None:
        qs = self.filter(api=gateway, scope_type=scope_type).exclude(scope_id__in=scope_ids)

        if plugin:
            qs = qs.filter(plugin=plugin, type=type_)

        if config:
            qs = qs.filter(config=config)

        qs.delete()

    def delete_bindings(
        self, gateway_id: int, plugin_ids: Union[List[int], None] = None, config_ids: Union[List[int], None] = None
    ):
        queryset = self.filter(api_id=gateway_id)
        if plugin_ids is not None:
            queryset = queryset.filter(plugin_id__in=plugin_ids)
        if config_ids is not None:
            queryset = queryset.filter(config_id__in=config_ids)
        queryset.delete()

    def delete_by_scopes(self, scope_type: str, scope_ids: List[int]):
        self.filter(scope_type=scope_type, scope_id__in=scope_ids).delete()

    def get_valid_scope_ids(self, gateway_id: int, scope_type: str, scope_ids: List[int]) -> List[int]:
        from apigateway.core.models import Resource, Stage

        if scope_type == PluginBindingScopeEnum.STAGE.value:
            return list(Stage.objects.filter(gateway_id=gateway_id, id__in=scope_ids).values_list("id", flat=True))
        elif scope_type == PluginBindingScopeEnum.RESOURCE.value:
            return list(Resource.objects.filter(api_id=gateway_id, id__in=scope_ids).values_list("id", flat=True))

        raise ValueError(f"unsupported scope_type: {scope_type}")

    def query_scope_id_to_bindings(
        self,
        gateway_id: int,
        scope_type: PluginBindingScopeEnum,
        scope_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        qs = self.filter(api_id=gateway_id, scope_type=scope_type.value)
        if scope_ids is not None:
            qs = qs.filter(scope_id__in=scope_ids)

        scope_id_to_binding = defaultdict(list)
        # 获取插件类型时，需要使用 PluginConfig 的 type 数据，因此添加 config__type，减少 db 查询
        for binding in qs.prefetch_related("config", "config__type"):
            scope_id_to_binding[binding.scope_id].append(binding)

        return scope_id_to_binding


class PluginFormManager(models.Manager):
    def with_language(self, language=None):
        if language is None:
            language = get_language()

        # default language is always available(as a blank string)
        q = models.Q(language="")

        if language:
            q |= models.Q(language=language)

        # sorting the query results by language make the default language(the blank string) always at the end
        return self.filter(q).order_by("-language")

    def get_by_natural_key(self, language: str, type_code: str):
        return self.get(language=language, type__code=type_code)


class PluginTypeManager(models.Manager):
    def get_by_natural_key(self, code: str):
        return self.get(code=code)
