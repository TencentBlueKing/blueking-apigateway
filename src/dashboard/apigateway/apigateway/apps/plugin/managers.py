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
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.db import models
from django.utils.translation import get_language

from apigateway.apps.plugin.constants import PluginBindingScopeEnum


class PluginConfigManager(models.Manager):
    pass


class PluginBindingManager(models.Manager):
    def delete_by_gateway_id(self, gateway_id: int):
        self.filter(gateway_id=gateway_id).delete()

    def create_or_update_bindings(
        self,
        gateway,
        scope_type: str,
        scope_ids: List[int],
        username: str,
        config=None,
    ):
        """将插件 plugin 绑定到指定 scopes"""
        for scope_id in scope_ids:
            binding, created = self.get_or_create(
                gateway=gateway,
                scope_type=scope_type,
                scope_id=scope_id,
                defaults={
                    "config": config,
                    "created_by": username,
                    "updated_by": username,
                },
            )
            if not created:
                binding.updated_by = username
                binding.save()

    def query_scope_id_to_bindings(
        self,
        gateway_id: int,
        scope_type: PluginBindingScopeEnum,
        scope_ids: Optional[List[int]] = None,
    ) -> Dict[int, Any]:
        qs = self.filter(gateway_id=gateway_id, scope_type=scope_type.value)
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
