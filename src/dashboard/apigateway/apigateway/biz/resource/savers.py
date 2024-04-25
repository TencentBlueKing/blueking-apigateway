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
from typing import Any, Dict, List

from django.db.models import Count
from django.utils.translation import gettext as _
from pydantic import parse_obj_as

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.biz.resource import ResourceHandler
from apigateway.common.factories import SchemaFactory
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum, ProxyTypeEnum
from apigateway.core.models import Context, Gateway, Proxy, Resource
from apigateway.utils.time import now_datetime

from .models import ResourceData
from ...apps.openapi.models import OpenAPIResourceSchema

BULK_BATCH_SIZE = 100


class ResourceProxyDuplicateError(Exception):
    """资源存在多个后端配置"""


class ResourcesSaver:
    def __init__(self, gateway: Gateway, resource_data_list: List[ResourceData], username: str):
        self.gateway = gateway
        self.resource_data_list = resource_data_list
        self.username = username

    @classmethod
    def from_resources(cls, gateway: Gateway, resources: List[Dict[str, Any]], username: str):
        resource_data_list = parse_obj_as(List[ResourceData], resources)
        return cls(gateway, resource_data_list, username)

    def save(self) -> List[Resource]:
        self._check_proxies(
            [resource_data.resource.id for resource_data in self.resource_data_list if resource_data.resource]
        )

        has_created = self._save_resources()
        if has_created:
            self._complete_with_resource()

        # 添加 if 条件，为通过 lint 校验
        resource_ids = [
            resource_data.resource.id for resource_data in self.resource_data_list if resource_data.resource
        ]
        self._save_proxies(resource_ids)
        self._save_auth_configs(resource_ids)
        self._save_resource_labels(resource_ids)
        self._save_resource_openapi_schema(resource_ids)

        return [resource_data.resource for resource_data in self.resource_data_list if resource_data.resource]

    def _save_resources(self) -> bool:
        add_resources = []
        update_resources = []
        now = now_datetime()
        for resource_data in self.resource_data_list:
            if resource_data.resource:
                resource = resource_data.resource
                resource.updated_by = self.username
                resource.updated_time = now
                for key, value in resource_data.basic_data.items():
                    setattr(resource, key, value)

                update_resources.append(resource)
            else:
                resource = Resource(
                    gateway=self.gateway,
                    created_by=self.username,
                    updated_by=self.username,
                    proxy_id=0,
                    **resource_data.basic_data,
                )
                add_resources.append(resource)

        if add_resources:
            Resource.objects.bulk_create(add_resources, batch_size=BULK_BATCH_SIZE)

        if update_resources:
            field_names = ResourceData.basic_field_names() + ["updated_by", "updated_time"]
            Resource.objects.bulk_update(update_resources, fields=field_names, batch_size=BULK_BATCH_SIZE)

        return bool(add_resources)

    def _complete_with_resource(self):
        # bulk_create 返回的资源列表中，无资源 ID，因此，根据资源名称将新增资源补充到资源数据中
        resources = {resource.name: resource for resource in Resource.objects.filter(gateway=self.gateway)}
        for resource_data in self.resource_data_list:
            if resource_data.resource:
                continue

            # 资源中，不应该存在同名资源，但由于 DB 中无约束规则，为防止意外，添加此校验
            resource = resources[resource_data.name]
            if resource_data.method != resource.method or resource_data.path != resource.path:
                raise ValueError(
                    _(
                        "根据资源名称匹配资源时，匹配资源的 method + path 和用户输入的不一致，请检查资源 (name={name}) 是否已存在。"
                    ).format(name=resource_data.name)
                )

            resource_data.resource = resource

    def _check_proxies(self, resource_ids: List[int]):
        if not resource_ids:
            return

        proxy_count = (
            Proxy.objects.filter(resource_id__in=resource_ids)
            .values("resource_id")
            .annotate(count=Count("resource_id"))
        )
        duplicate_resource_id = [item["resource_id"] for item in proxy_count if item["count"] > 1]
        if duplicate_resource_id:
            raise ResourceProxyDuplicateError(
                _("网关资源 (id={resource_ids}) 存在多个后端配置，请联系网关管理员检查。").format(
                    resource_ids=", ".join(map(str, duplicate_resource_id))
                )
            )

    def _save_proxies(self, resource_ids: List[int]):
        proxies = {proxy.resource_id: proxy for proxy in Proxy.objects.filter(resource_id__in=resource_ids)}
        schema = SchemaFactory().get_proxy_schema(ProxyTypeEnum.HTTP.value)

        add_proxies = []
        update_proxies = []
        now = now_datetime()
        for resource_data in self.resource_data_list:
            assert resource_data.resource

            proxy = proxies.get(resource_data.resource.id)
            if proxy:
                proxy.type = ProxyTypeEnum.HTTP.value
                proxy.backend = resource_data.backend
                proxy.schema = schema
                proxy._config = resource_data.backend_config.json()
                proxy.updated_time = now

                update_proxies.append(proxy)
            else:
                proxy = Proxy(
                    resource=resource_data.resource,
                    type=ProxyTypeEnum.HTTP.value,
                    backend=resource_data.backend,
                    # TODO: 1.13 后续 issue 统一去除 schema
                    schema=schema,
                    _config=resource_data.backend_config.json(),
                )
                add_proxies.append(proxy)

        if add_proxies:
            Proxy.objects.bulk_create(add_proxies, batch_size=BULK_BATCH_SIZE)

        if update_proxies:
            Proxy.objects.bulk_update(
                update_proxies,
                fields=["type", "backend", "schema", "_config", "updated_time"],
                batch_size=BULK_BATCH_SIZE,
            )

    def _save_auth_configs(self, resource_ids: List[int]):
        contexts = {
            ctx.scope_id: ctx
            for ctx in Context.objects.filter(
                scope_id__in=resource_ids,
                scope_type=ContextScopeTypeEnum.RESOURCE.value,
                type=ContextTypeEnum.RESOURCE_AUTH.value,
            )
        }
        schema = SchemaFactory().get_context_resource_bkauth_schema()

        add_contexts = []
        update_contexts = []
        now = now_datetime()
        for resource_data in self.resource_data_list:
            assert resource_data.resource

            context = contexts.get(resource_data.resource.id)

            auth_config = (context and context.config) or ResourceHandler.get_default_auth_config()
            auth_config.update(resource_data.auth_config.dict())

            if context:
                context._config = json.dumps(auth_config)
                context.updated_time = now

                update_contexts.append(context)
            else:
                context = Context(
                    scope_type=ContextScopeTypeEnum.RESOURCE.value,
                    type=ContextTypeEnum.RESOURCE_AUTH.value,
                    scope_id=resource_data.resource.id,
                    _config=json.dumps(auth_config),
                    # TODO: 1.13 统一去除 context schema
                    schema=schema,
                )
                add_contexts.append(context)

        if add_contexts:
            Context.objects.bulk_create(add_contexts, batch_size=BULK_BATCH_SIZE)

        if update_contexts:
            Context.objects.bulk_update(
                update_contexts, fields=["_config", "updated_time"], batch_size=BULK_BATCH_SIZE
            )

    def _save_resource_labels(self, resource_ids: List[int]):
        gateway_labels = {label.id: label for label in APILabel.objects.filter(gateway=self.gateway)}

        remaining_resource_labels = {}
        for label in ResourceLabel.objects.filter(resource_id__in=resource_ids):
            remaining_resource_labels[f"{label.resource_id}:{label.api_label_id}"] = label.id

        add_resource_labels = []
        for resource_data in self.resource_data_list:
            assert resource_data.resource

            for label_id in resource_data.label_ids:
                key = f"{resource_data.resource.id}:{label_id}"
                if key in remaining_resource_labels:
                    remaining_resource_labels.pop(key)
                    continue

                if label_id not in gateway_labels:
                    continue

                add_resource_labels.append(
                    ResourceLabel(resource=resource_data.resource, api_label=gateway_labels[label_id])
                )

        if add_resource_labels:
            ResourceLabel.objects.bulk_create(add_resource_labels, batch_size=BULK_BATCH_SIZE)

        if remaining_resource_labels:
            ResourceLabel.objects.filter(id__in=remaining_resource_labels.values()).delete()

    def _save_resource_openapi_schema(self, resource_ids: List[int]):
        """
        保存resource openapi schema
        """

        remaining_resource_schemas: Dict[int, OpenAPIResourceSchema] = {}
        for resource_openapi_schema in OpenAPIResourceSchema.objects.filter(resource_id__in=resource_ids):
            remaining_resource_schemas[resource_openapi_schema.resource_id] = resource_openapi_schema

        add_resource_openapi_schemas = []
        update_resource_openapi_schemas = []
        del_resource_openapi_schema_ids = []
        for resource_data in self.resource_data_list:
            assert resource_data.resource
            no_schema = False
            if (
                len(resource_data.openapi_schema.get("requestBody", {}))
                + len(resource_data.openapi_schema.get("parameters", {}))
                + len(resource_data.openapi_schema.get("responses", {}))
                == 0
            ):
                no_schema = True

            if resource_data.resource.id in remaining_resource_schemas:
                old_resource_openapi_schema = remaining_resource_schemas[resource_data.resource.id]
                if no_schema:
                    del_resource_openapi_schema_ids.append(old_resource_openapi_schema.id)
                    continue
                # 更新schema
                old_resource_openapi_schema.schema = resource_data.openapi_schema
                old_resource_openapi_schema.update_by = self.username
                old_resource_openapi_schema.updated_time = now_datetime()
                update_resource_openapi_schemas.append(old_resource_openapi_schema)
            else:
                if no_schema:
                    continue

                # 新增schema
                add_resource_openapi_schemas.append(
                    OpenAPIResourceSchema(
                        resource=resource_data.resource,
                        schema=resource_data.openapi_schema,
                        created_by=self.username,
                        updated_by=self.username,
                    )
                )

        if len(add_resource_openapi_schemas) > 0:
            OpenAPIResourceSchema.objects.bulk_create(add_resource_openapi_schemas, batch_size=BULK_BATCH_SIZE)

        if len(del_resource_openapi_schema_ids) > 0:
            OpenAPIResourceSchema.objects.filter(id__in=del_resource_openapi_schema_ids).delete()

        if len(update_resource_openapi_schemas) > 0:
            OpenAPIResourceSchema.objects.bulk_update(
                update_resource_openapi_schemas,
                fields=["schema", "updated_time", "updated_by"],
                batch_size=BULK_BATCH_SIZE,
            )
