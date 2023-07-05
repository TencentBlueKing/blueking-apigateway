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
import itertools
import json
import operator
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set

from cachetools import TTLCache, cached
from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from apigateway.common.constants import CACHE_MAXSIZE, CacheTimeLevel
from apigateway.common.error_codes import error_codes
from apigateway.common.exceptions import InstanceDeleteError
from apigateway.common.factories import SchemaFactory
from apigateway.common.funcs import get_resource_version_display
from apigateway.common.mcryptography import AESCipherManager
from apigateway.core.constants import (
    DEFAULT_STAGE_NAME,
    STAGE_VAR_PATTERN,
    APIHostingTypeEnum,
    APIStatusEnum,
    BackendConfigTypeEnum,
    ProxyTypeEnum,
    SSLCertificateBindingScopeTypeEnum,
    StageStatusEnum,
)
from apigateway.core.utils import get_resource_doc_link
from apigateway.utils.crypto import KeyGenerator
from apigateway.utils.time import now_datetime


class GatewayManager(models.Manager):
    def search_gateways(self, username, name=None, order_by=None):
        """
        根据用户、网关名筛选网关
        """
        queryset = self.filter(Q(created_by=username) | Q(_maintainers__contains=username))

        if name:
            queryset = queryset.filter(name__contains=name)

        if order_by:
            queryset = queryset.order_by(order_by)

        return [api for api in queryset if api.has_permission(username)]

    def fetch_authorized_gateway_ids(self, username: str) -> List[str]:
        """获取用户有权限的网关 ID 列表"""
        queryset = self.filter(_maintainers__contains=username)
        return [gateway.id for gateway in queryset if gateway.has_permission(username)]

    # def save_auth_config(
    #     self,
    #     gateway_id: int,
    #     user_auth_type: Optional[str] = None,
    #     user_conf: Optional[dict] = None,
    #     api_type: Optional[APITypeEnum] = None,
    #     allow_update_api_auth: Optional[bool] = None,
    #     unfiltered_sensitive_keys: Optional[List[str]] = None,
    # ):
    #     """
    #     存储网关认证配置
    #
    #     :param gateway_id: 网关id
    #     :param user_auth_type:
    #     :param user_conf: 用户类型为 default 的用户的认证配置
    #     :param api_type: 网关类型，只有 ESB 才能被设置为 SUPER_OFFICIAL_API 网关，网关会将所有请求参数透传给其后端服务
    #     :param allow_update_api_auth: 是否允许编辑网关资源安全设置中的应用认证配置
    #     :param unfiltered_sensitive_keys:
    #     """
    #     new_config: Dict[str, Any] = {}
    #
    #     if user_auth_type is not None:
    #         new_config["user_auth_type"] = user_auth_type
    #
    #     if user_conf is not None:
    #         new_config["user_conf"] = user_conf
    #
    #     if api_type is not None:
    #         new_config["api_type"] = api_type.value
    #
    #     if allow_update_api_auth is not None:
    #         new_config["allow_update_api_auth"] = allow_update_api_auth
    #
    #     if unfiltered_sensitive_keys is not None:
    #         new_config["unfiltered_sensitive_keys"] = unfiltered_sensitive_keys
    #
    #     if not new_config:
    #         return
    #
    #     current_config = self.get_current_gateway_auth_config(gateway_id)
    #
    #     # 因用户配置为 dict，参数 user_conf 仅传递了部分用户配置，因此需合并当前配置与传入配置
    #     api_auth_config = APIAuthConfig.parse_obj(deep_update(current_config, new_config))
    #
    #     return APIAuthContext().save(gateway_id, api_auth_config.config)
    #
    # def get_current_gateway_auth_config(self, gateway_id: int) -> dict:
    #     """
    #     获取网关当前的认证配置
    #     """
    #     from apigateway.core.models import Context
    #
    #     try:
    #         return APIAuthContext().get_config(gateway_id)
    #     except Context.DoesNotExist:
    #         return {}

    # def delete_gateway(self, gateway_id):
    #     # 1. delete api context
    #     from apigateway.core.models import Context
    #
    #     Context.objects.delete_by_scope_ids(
    #         scope_type=ContextScopeTypeEnum.API.value,
    #         scope_ids=[gateway_id],
    #     )
    #
    #     # 2. delete release
    #     from apigateway.core.models import Release
    #
    #     Release.objects.delete_by_gateway_id(gateway_id)
    #
    #     # 3. delete stage
    #     from apigateway.core.models import Stage
    #
    #     Stage.objects.delete_by_gateway_id(gateway_id)
    #
    #     # 4. delete resource
    #     from apigateway.core.models import Resource
    #
    #     Resource.objects.delete_by_gateway_id(gateway_id)
    #
    #     # 5. delete resource-version
    #     from apigateway.core.models import ResourceVersion
    #
    #     ResourceVersion.objects.delete_by_gateway_id(gateway_id)
    #
    #     # 6. delete access_strategy
    #     from apigateway.apps.access_strategy.models import AccessStrategy
    #
    #     AccessStrategy.objects.delete_by_gateway_id(gateway_id)
    #
    #     # plugin bindings
    #     from apigateway.apps.plugin.models import PluginBinding
    #
    #     PluginBinding.objects.delete_by_gateway_id(gateway_id)
    #
    #     # delete ssl-certificate
    #     from apigateway.core.models import SslCertificate
    #
    #     SslCertificate.objects.delete_by_gateway_id(gateway_id)
    #
    #     # delete api
    #     self.filter(id=gateway_id).delete()

    def get_or_new_gateway(self, name):
        if self.filter(name=name).exists():
            return self.get(name=name)
        gateway = self.model()
        gateway.name = name

        return gateway

    def filter_id_object_map(self, ids=None):
        """
        获取网关ID对
        """
        queryset = self.all()
        if ids is not None:
            queryset = queryset.filter(id__in=ids)
        return {gateway.id: gateway for gateway in queryset}

    def filter_micro_and_active_queryset(self):
        """获取托管类型为微网关，且已启用的网关，用于获取可发布到共享微网关实例的网关"""
        return self.filter(hosting_type=APIHostingTypeEnum.MICRO.value, status=APIStatusEnum.ACTIVE.value)

    def query_micro_and_active_ids(self, ids: List[int] = None) -> List[int]:
        """获取托管类型为微网关，且已启用的网关 ID 列表；如果给定了网关 ID 列表，则返回其中符合条件的 ID 列表"""
        queryset = self.filter_micro_and_active_queryset()
        if ids is not None:
            queryset = queryset.filter(id__in=ids)

        return list(queryset.values_list("id", flat=True))

    # def save_related_data(
    #     self,
    #     gateway,
    #     user_auth_type: str,
    #     username: str,
    #     related_app_code: Optional[str] = None,
    #     user_config: Optional[dict] = None,
    #     unfiltered_sensitive_keys: Optional[List[str]] = None,
    #     api_type: Optional[APITypeEnum] = None,
    # ):
    #     # 1. save api auth_config
    #     self.save_auth_config(
    #         gateway.id,
    #         user_auth_type=user_auth_type,
    #         user_conf=user_config,
    #         api_type=api_type,
    #         unfiltered_sensitive_keys=unfiltered_sensitive_keys,
    #     )
    #
    #     # 2. save jwt
    #     from apigateway.core.models import JWT
    #
    #     JWT.objects.create_jwt(gateway)
    #
    #     # 3. create default stage
    #     from apigateway.core.models import Stage
    #
    #     Stage.objects.create_default(gateway, created_by=username)
    #
    #     # 4. create default alarm-strategy
    #     from apigateway.apps.monitor.models import AlarmStrategy
    #
    #     AlarmStrategy.objects.create_default_strategy(gateway, created_by=username)
    #
    #     # 5. create related app
    #     if related_app_code:
    #         from apigateway.core.models import APIRelatedApp
    #
    #         APIRelatedApp.objects.create(api=gateway, bk_app_code=related_app_code)

    # def add_create_audit_log(self, gateway, username: str):
    #     record_audit_log(
    #         username=username,
    #         op_type=OpTypeEnum.CREATE.value,
    #         op_status=OpStatusEnum.SUCCESS.value,
    #         op_object_group=gateway.id,
    #         op_object_type=OpObjectTypeEnum.API.value,
    #         op_object_id=gateway.id,
    #         op_object=gateway.name,
    #         comment=_("创建网关"),
    #     )

    # def add_update_audit_log(self, gateway, username: str):
    #     record_audit_log(
    #         username=username,
    #         op_type=OpTypeEnum.MODIFY.value,
    #         op_status=OpStatusEnum.SUCCESS.value,
    #         op_object_group=gateway.id,
    #         op_object_type=OpObjectTypeEnum.API.value,
    #         op_object_id=gateway.id,
    #         op_object=gateway.name,
    #         comment=_("更新网关"),
    #     )


class StageManager(models.Manager):
    def get_names(self, gateway_id):
        return list(self.filter(api_id=gateway_id).values_list("name", flat=True))

    def get_ids(self, gateway_id):
        return list(self.filter(api_id=gateway_id).values_list("id", flat=True))

    def get_name_id_map(self, gateway):
        return dict(self.filter(api_id=gateway.id).values_list("name", "id"))

    def get_id_to_fields(self, gateway_id: int, fields: List[str]) -> Dict[int, Dict[str, Any]]:
        return {stage["id"]: stage for stage in self.filter(api_id=gateway_id).values(*fields)}

    def filter_valid_ids(self, gateway, ids):
        return list(self.filter(api_id=gateway.id, id__in=ids).values_list("id", flat=True))

    # def create_default(self, gateway, created_by):
    #     """
    #     创建默认 stage，网关创建时，需要创建一个默认环境
    #     """
    #     stage = self.create(
    #         api=gateway,
    #         name=DEFAULT_STAGE_NAME,
    #         description=_("正式环境"),
    #         description_en="Prod",
    #         vars={},
    #         status=StageStatusEnum.INACTIVE.value,
    #         created_by=created_by,
    #         updated_by=created_by,
    #         created_time=now_datetime(),
    #         updated_time=now_datetime(),
    #     )
    #
    #     # 保存关联数据
    #     self.save_related_data(
    #         stage,
    #         proxy_http_config={
    #             "timeout": 30,
    #             "upstreams": settings.DEFAULT_STAGE_UPSTREAMS,
    #             "transform_headers": {
    #                 "set": {},
    #                 "delete": [],
    #             },
    #         },
    #         rate_limit_config=settings.DEFAULT_STAGE_RATE_LIMIT_CONFIG,
    #     )
    #
    #     return stage

    # def save_related_data(self, stage, proxy_http_config: dict, rate_limit_config: Optional[dict]):
    #     # 1. save proxy http config
    #     StageProxyHTTPContext().save(stage.id, proxy_http_config)
    #
    #     # 2. save rate-limit config
    #     if rate_limit_config is not None:
    #         StageRateLimitContext().save(stage.id, rate_limit_config)

    # def delete_stages(self, gateway_id, stage_ids):
    #     # 1. delete proxy http config/rate-limit config
    #     from apigateway.core.models import Context
    #
    #     Context.objects.delete_by_scope_ids(
    #         scope_type=ContextScopeTypeEnum.STAGE.value,
    #         scope_ids=stage_ids,
    #     )
    #
    #     # 2. delete release
    #     from apigateway.core.models import Release
    #
    #     Release.objects.delete_by_stage_ids(stage_ids)
    #
    #     # 3. delete access-strategy-binding
    #     from apigateway.apps.access_strategy.models import AccessStrategyBinding
    #
    #     AccessStrategyBinding.objects.delete_by_scope_ids(
    #         scope_type=AccessStrategyBindScopeEnum.STAGE.value,
    #         scope_ids=stage_ids,
    #     )
    #
    #     # 4. delete stages
    #     self.filter(id__in=stage_ids).delete()
    #
    #     # 5. delete release-history
    #     from apigateway.core.models import ReleaseHistory
    #
    #     ReleaseHistory.objects.delete_without_stage_related(gateway_id)
    #
    # def delete_by_gateway_id(self, gateway_id):
    #     stage_ids = list(self.filter(api_id=gateway_id).values_list("id", flat=True))
    #     if not stage_ids:
    #         return
    #
    #     self.delete_stages(gateway_id, stage_ids)

    # def add_create_audit_log(self, gateway, stage, username: str):
    #     record_audit_log(
    #         username=username,
    #         op_type=OpTypeEnum.CREATE.value,
    #         op_status=OpStatusEnum.SUCCESS.value,
    #         op_object_group=gateway.id,
    #         op_object_type=OpObjectTypeEnum.STAGE.value,
    #         op_object_id=stage.id,
    #         op_object=stage.name,
    #         comment=_("创建环境"),
    #     )

    # def add_update_audit_log(self, gateway, stage, username: str):
    #     record_audit_log(
    #         username=username,
    #         op_type=OpTypeEnum.MODIFY.value,
    #         op_status=OpStatusEnum.SUCCESS.value,
    #         op_object_group=gateway.id,
    #         op_object_type=OpObjectTypeEnum.STAGE.value,
    #         op_object_id=stage.id,
    #         op_object=stage.name,
    #         comment=_("更新环境"),
    #     )

    def get_micro_gateway_id_to_fields(self, gateway_id: int) -> Dict[str, Dict[str, Any]]:
        return {
            item["micro_gateway_id"]: item
            for item in self.filter(api_id=gateway_id).values("id", "name", "micro_gateway_id")
            if item["micro_gateway_id"]
        }

    # def get_id_to_micro_gateway_id(self, gateway_id: int) -> Dict[int, Optional[str]]:
    #     return dict(self.filter(api_id=gateway_id).values_list("id", "micro_gateway_id"))
    #
    # def get_id_to_micro_gateway_fields(self, gateway_id: int) -> Dict[int, Optional[Dict[str, Any]]]:
    #     id_to_micro_gateway_id = self.get_id_to_micro_gateway_id(gateway_id)
    #     result: Dict[int, Optional[Dict[str, Any]]] = {i: None for i in id_to_micro_gateway_id}
    #
    #     valid_micro_gateway_ids = set(i for i in id_to_micro_gateway_id.values() if i is not None)
    #     if not valid_micro_gateway_ids:
    #         return result
    #
    #     from apigateway.core.models import MicroGateway
    #
    #     micro_gateway_id_to_fields = MicroGateway.objects.get_id_to_fields(valid_micro_gateway_ids)
    #     for id_, micro_gateway_id in id_to_micro_gateway_id.items():
    #         if micro_gateway_id is not None:
    #             result[id_] = micro_gateway_id_to_fields.get(micro_gateway_id)
    #
    #     return result

    def get_gateway_name_to_active_stage_names(self, gateways) -> Dict[str, List[str]]:
        gateway_id_to_name = {g.id: g.name for g in gateways}

        gateway_name_to_stage_names = defaultdict(list)
        stages = self.filter(api_id__in=gateway_id_to_name.keys(), status=StageStatusEnum.ACTIVE.value).values(
            "api_id", "name"
        )
        for stage in stages:
            gateway_id = stage["api_id"]
            gateway_name = gateway_id_to_name[gateway_id]
            gateway_name_to_stage_names[gateway_name].append(stage["name"])

        return gateway_name_to_stage_names


class ResourceManager(models.Manager):
    # TODO: 断点, 把这个函数挪到 ResourceHandler里面去
    # def save_related_data(
    #     self,
    #     gateway,
    #     resource,
    #     proxy_type,
    #     proxy_config,
    #     auth_config,
    #     label_ids,
    #     disabled_stage_ids,
    #     backend_config_type: str = BackendConfigTypeEnum.DEFAULT.value,
    #     backend_service_id: Optional[int] = None,
    # ):
    #     # 1. save proxy, and set resource proxy_id
    #     self.save_proxy_config(
    #         resource,
    #         proxy_type,
    #         proxy_config,
    #         backend_config_type=backend_config_type,
    #         backend_service_id=backend_service_id,
    #     )
    #
    #     # 2. save auth config
    #     self.save_auth_config(resource.id, auth_config)
    #
    #     # 3. save labels
    #     self.save_labels(gateway, resource, label_ids, delete_unspecified=True)
    #
    #     # 4. save disabled stags
    #     self.save_disabled_stages(gateway, resource, disabled_stage_ids, delete_unspecified=True)

    # def delete_resources(self, resource_ids: List[int], api=None):
    #     if not resource_ids:
    #         return
    #
    #     if api is not None:
    #         # 指定网关时，二次确认资源属于该网关，防止误删除
    #         resource_ids = self.filter_by_ids(api, resource_ids)
    #         assert resource_ids
    #
    #     # 1. delete auth config context
    #     from apigateway.core.models import Context
    #
    #     Context.objects.delete_by_scope_ids(
    #         scope_type=ContextScopeTypeEnum.RESOURCE.value,
    #         scope_ids=resource_ids,
    #     )
    #
    #     # 2. delete proxy
    #     from apigateway.core.models import Proxy
    #
    #     Proxy.objects.delete_by_resource_ids(resource_ids)
    #
    #     # 3. delete access-strategy binding
    #     from apigateway.apps.access_strategy.models import AccessStrategyBinding
    #
    #     AccessStrategyBinding.objects.delete_by_scope_ids(
    #         scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
    #         scope_ids=resource_ids,
    #     )
    #
    #     # 4. delete resource doc
    #     from apigateway.apps.support.models import ResourceDoc
    #
    #     ResourceDoc.objects.delete_by_resource_ids(resource_ids)
    #
    #     # 5. delete resource
    #     self.filter(id__in=resource_ids).delete()

    # def delete_by_gateway_id(self, gateway_id):
    #     resource_ids = list(self.filter(api_id=gateway_id).values_list("id", flat=True))
    #     if not resource_ids:
    #         return
    #     self.delete_resources(resource_ids)

    # def save_labels(self, gateway, resource, label_ids, delete_unspecified=False):
    #     """
    #     存储标签
    #     :param bool delete_unspecified: 是否删除未指定的标签，资源下非本次提供的即为未指定标签
    #     """
    #     from apigateway.apps.label.models import APILabel, ResourceLabel
    #
    #     # 筛选出在 ResourceLabel 中不存在的 label_ids 进行添加
    #     exist_label_ids = ResourceLabel.objects.filter(resource=resource, api_label__id__in=label_ids).values_list(
    #         "api_label__id", flat=True
    #     )
    #     labels_to_add = APILabel.objects.filter(api=gateway, id__in=list(set(label_ids) - set(exist_label_ids)))
    #     for label in labels_to_add:
    #         ResourceLabel.objects.update_or_create(resource=resource, api_label=label)
    #
    #     if delete_unspecified:
    #         # 清理非本次添加的标签
    #         ResourceLabel.objects.filter(resource=resource).exclude(api_label__id__in=label_ids).delete()

    # def save_disabled_stages(self, gateway, resource, disabled_stage_ids, delete_unspecified=False):
    #     """
    #     存储资源禁用环境
    #     :param bool delete_unspecified: 是否删除未指定的禁用环境，资源下非本次提供的禁用环境即为未指定禁用环境
    #     """
    #     from apigateway.core.models import Stage, StageResourceDisabled
    #
    #     # 筛选出 StageResourceDisabled 中不存在的 disabled_stage_ids 进行添加
    #     exist_disabled_stage_ids = StageResourceDisabled.objects.filter(
    #         resource=resource, stage__id__in=disabled_stage_ids
    #     ).values_list("stage__id", flat=True)
    #     disabled_stages_to_add = Stage.objects.filter(
    #         api=gateway, id__in=list(set(disabled_stage_ids) - set(exist_disabled_stage_ids))
    #     )
    #     for stage in disabled_stages_to_add:
    #         StageResourceDisabled.objects.update_or_create(stage=stage, resource=resource)
    #
    #     if delete_unspecified:
    #         # 清理非本次添加的禁用环境
    #         StageResourceDisabled.objects.filter(resource=resource).exclude(stage__id__in=disabled_stage_ids).delete()

    # def save_auth_config(self, resource_id, config):
    #     """
    #     存储资源认证配置
    #     """
    #     auth_config = self._get_current_auth_config(resource_id)
    #     auth_config.update(config)
    #
    #     return ResourceAuthContext().save(resource_id, auth_config)
    #
    # def _get_current_auth_config(self, resource_id):
    #     """
    #     获取资源当前认证配置
    #     """
    #     default_hidden_config = {
    #         # 跳过用户认证逻辑，值为False时，不根据请求参数中的用户信息校验用户
    #         "skip_auth_verification": False,
    #         "auth_verified_required": True,
    #         "app_verified_required": True,
    #         "resource_perm_required": True,
    #     }
    #
    #     from apigateway.core.models import Context
    #
    #     try:
    #         return ResourceAuthContext().get_config(resource_id)
    #     except Context.DoesNotExist:
    #         return default_hidden_config

    # def save_proxy_config(
    #     self,
    #     resource,
    #     proxy_type,
    #     proxy_config,
    #     backend_config_type: str = BackendConfigTypeEnum.DEFAULT.value,
    #     backend_service_id: Optional[int] = None,
    # ):
    #     from apigateway.core.models import Proxy
    #
    #     proxy, created = Proxy.objects.save_proxy_config(
    #         resource,
    #         proxy_type,
    #         proxy_config,
    #         backend_config_type=backend_config_type,
    #         backend_service_id=backend_service_id,
    #     )
    #     resource.proxy_id = proxy.id
    #     resource.save(update_fields=["proxy_id", "updated_time"])
    #     return proxy, created

    # def filter_resource(self, gateway, query=None, path=None,
    #       method=None, label_name=None, order_by=None, fuzzy=True):
    #     """
    #     查询资源，根据模糊查询串匹配，根据path、method匹配，根据标签匹配
    #     """
    #     queryset = self.filter(api=gateway)
    #
    #     # query 不是模型字段，仅支持模糊匹配，如需精确匹配，可使用具体字段
    #     if query and fuzzy:
    #         queryset = queryset.filter(Q(path__contains=query) | Q(name__contains=query))
    #
    #     if path:
    #         if fuzzy:
    #             queryset = queryset.filter(path__contains=path)
    #         else:
    #             queryset = queryset.filter(path=path)
    #
    #     if method:
    #         queryset = queryset.filter(method=method)
    #
    #     if label_name:
    #         from apigateway.apps.label.models import ResourceLabel
    #
    #         resource_ids = ResourceLabel.objects.filter_resource_ids(gateway=gateway, label_name=label_name)
    #         queryset = queryset.filter(id__in=resource_ids)
    #
    #     if order_by:
    #         queryset = queryset.order_by(order_by)
    #
    #     return queryset

    def get_api_resource_count(self, gateway_ids):
        """
        获取网关资源数量
        """
        api_resource_count = self.filter(api_id__in=gateway_ids).values("api_id").annotate(count=Count("api_id"))
        return {i["api_id"]: i["count"] for i in api_resource_count}

    # def get_proxy_configs(self, resource):
    #     """
    #     获取资源代理配置，及当前代理类型
    #     """
    #     from apigateway.core.models import Proxy
    #
    #     current_proxy = Proxy.objects.get(id=resource.proxy_id)
    #
    #     return {
    #         "type": current_proxy.type,
    #         "backend_config_type": current_proxy.backend_config_type,
    #         "backend_service_id": current_proxy.backend_service_id,
    #         "configs": {proxy.type: proxy.config for proxy in Proxy.objects.filter(resource=resource)},
    #     }

    def filter_by_ids(self, gateway, ids):
        if not ids:
            return self.none()

        return self.filter(api=gateway, id__in=ids)

    def filter_valid_ids(self, gateway, ids):
        return list(self.filter(api=gateway, id__in=ids).values_list("id", flat=True))

    def get_latest_resource(self, gateway_id):
        return self.filter(api_id=gateway_id).order_by("-updated_time").first()

    def filter_resource_path_method_to_id(self, gateway_id):
        """
        :return: {
            "/test/": {
                "GET": 1,
            }
        }
        """
        resources = self.filter(api_id=gateway_id).values("id", "method", "path")
        path_method_to_id = defaultdict(dict)
        for resource in resources:
            path_method_to_id[resource["path"]][resource["method"]] = resource["id"]
        return path_method_to_id

    def filter_id_to_fields(self, gateway_id: int, fields: List[str]) -> Dict[int, Dict[str, Any]]:
        return {resource["id"]: resource for resource in self.filter(api_id=gateway_id).values(*fields)}

    def filter_resource_name_to_id(self, gateway_id):
        return dict(self.filter(api_id=gateway_id).values_list("name", "id"))

    def filter_id_is_public_map(self, gateway_id):
        return dict(self.filter(api_id=gateway_id).values_list("id", "is_public"))

    def filter_public_resource_ids(self, gateway_id: int) -> List[int]:
        return list(self.filter(api_id=gateway_id, is_public=True).values_list("id", flat=True))

    def filter_id_object_map(self, gateway_id):
        return {obj.id: obj for obj in self.filter(api_id=gateway_id)}

    def filter_resource_names(self, gateway_id, ids):
        if not ids:
            return []

        return list(self.filter(api_id=gateway_id, id__in=ids).values_list("name", flat=True))

    def get_id_to_fields_map(self, resource_ids: List[int]) -> Dict[int, dict]:
        if not resource_ids:
            return {}

        return {
            r["id"]: dict(r, api_name=r["api__name"])
            for r in self.filter(id__in=resource_ids).values("id", "name", "description", "api_id", "api__name")
        }

    def get_id_to_name(self, gateway_id: int, resource_ids: Optional[List[int]] = None) -> Dict[int, str]:
        qs = self.filter(api_id=gateway_id)

        if resource_ids is not None:
            qs = qs.filter(id__in=resource_ids)

        return dict(qs.values_list("id", "name"))

    def group_by_api_id(self, resource_ids: List[int]) -> Dict[int, List[int]]:
        data = self.filter(id__in=resource_ids).values("api_id", "id").order_by("api_id")
        return {
            api_id: [item["id"] for item in group]
            for api_id, group in itertools.groupby(data, key=operator.itemgetter("api_id"))
        }

    def get_unspecified_resource_fields(self, gateway_id: int, ids: List[int]) -> List[Dict[str, Any]]:
        """获取指定网关下，未在指定 ids 中的资源的一些字段数据"""
        return list(self.filter(api_id=gateway_id).exclude(id__in=ids).values("id", "name", "method", "path"))

    def get_resource_ids_by_names(self, gateway_id: int, resource_names: Optional[List[str]]) -> List[int]:
        if not resource_names:
            return []

        return list(self.filter(api_id=gateway_id, name__in=resource_names).values_list("id", flat=True))


class ProxyManager(models.Manager):
    # FIXME: move to biz layer
    def save_proxy_config(
        self,
        resource,
        type,
        config,
        backend_config_type: str = BackendConfigTypeEnum.DEFAULT.value,
        backend_service_id: Optional[int] = None,
    ):
        factory = SchemaFactory()
        return self.update_or_create(
            resource=resource,
            type=type,
            defaults={
                "backend_config_type": backend_config_type,
                "backend_service_id": backend_service_id,
                "config": config,
                "schema": factory.get_proxy_schema(type),
            },
        )

    def get_proxy_type(self, proxy_id):
        """
        获取代理的类型
        """
        return self.get(id=proxy_id).type

    def filter_proxies(self, resource_ids):
        queryset = self.filter(resource_id__in=resource_ids)
        return {
            proxy.id: {
                "type": proxy.type,
                "config": proxy.config,
            }
            for proxy in queryset
        }

    def delete_by_resource_ids(self, resource_ids):
        self.filter(resource_id__in=resource_ids).delete()

    def filter_id_snapshot_map(self, resource_ids):
        from apigateway.schema.models import Schema

        schemas = Schema.objects.filter_id_snapshot_map()
        return {
            proxy.id: proxy.snapshot(as_dict=True, schemas=schemas)
            for proxy in self.filter(resource_id__in=resource_ids)
        }


class StageResourceDisabledManager(models.Manager):
    def get_disabled_stages(self, resource_id):
        disabled_stages = self.filter(resource_id=resource_id).values("stage__id", "stage__name")
        return [
            {
                "id": stage["stage__id"],
                "name": stage["stage__name"],
            }
            for stage in disabled_stages
        ]

    # TODO: move to biz/stage_resource_disabled.py StageResourceDisabledHandler?
    def filter_disabled_stages_by_gateway(self, gateway):
        from apigateway.core.models import Stage

        stage_ids = Stage.objects.get_ids(gateway.id)

        queryset = self.filter(stage_id__in=stage_ids)
        queryset = queryset.values("stage_id", "stage__name", "resource_id")

        disabled = sorted(queryset, key=operator.itemgetter("resource_id"))

        disabled_groups = itertools.groupby(disabled, key=operator.itemgetter("resource_id"))
        resource_disabled = {}
        for resource_id, group in disabled_groups:
            resource_disabled[resource_id] = [
                {
                    "id": stage["stage_id"],
                    "name": stage["stage__name"],
                }
                for stage in group
            ]
        return resource_disabled

    def is_exists(self, stage_id, resource_id):
        return self.filter(stage__id=stage_id, resource__id=resource_id).exists()

    def delete_enabled_records(self, stage_id, resource_id):
        return self.filter(stage__id=stage_id, resource__id=resource_id).delete()

    def get_record(self, stage_id, resource_id):
        return self.get(stage__id=stage_id, resource__id=resource_id)

    def get_or_new_record(self, stage_id, resource_id):
        if self.is_exists(stage_id, resource_id):
            return self.get_record(stage_id, resource_id)

        record = self.model()
        record.stage_id = stage_id
        record.resource_id = resource_id

        return record


class ResourceVersionManager(models.Manager):
    # def make_version(self, gateway):
    #     from apigateway.apps.label.models import ResourceLabel
    #     from apigateway.core.models import Context, Proxy, Resource, StageResourceDisabled
    #
    #     resource_queryset = Resource.objects.filter(api_id=gateway.id).all()
    #     resource_ids = list(resource_queryset.values_list("id", flat=True))
    #
    #     proxy_map = Proxy.objects.filter_id_snapshot_map(resource_ids)
    #
    #     context_map = Context.objects.filter_id_type_snapshot_map(
    #         scope_type=ContextScopeTypeEnum.RESOURCE.value,
    #         scope_ids=resource_ids,
    #     )
    #
    #     disabled_stage_map = {
    #         resource_id: [stage["name"] for stage in stages]
    #       for resource_id, stages in StageResourceDisabled.objects.filter_disabled_stages_by_gateway(gateway).items()
    #     }
    #
    #     api_label_map = {
    #         resource_id: [label["id"] for label in labels]
    #         for resource_id, labels in ResourceLabel.objects.filter_labels_by_gateway(gateway).items()
    #     }
    #
    #     return [
    #         r.snapshot(
    #             as_dict=True,
    #             proxy_map=proxy_map,
    #             context_map=context_map,
    #             disabled_stage_map=disabled_stage_map,
    #             api_label_map=api_label_map,
    #         )
    #         for r in resource_queryset
    #     ]

    # def get_data_by_id_or_new(self, gateway, resource_version_id: Optional[int]) -> list:
    #     """
    #     根据版本ID获取Data，或者获取当前资源列表中的版本数据
    #     """
    #     if resource_version_id:
    #         return self.get(api=gateway, id=resource_version_id).data
    #
    #     return self.make_version(gateway)

    def get_latest_version(self, gateway_id: int):
        """
        网关最新的版本
        """
        return self.filter(api_id=gateway_id).last()

    # def delete_by_gateway_id(self, gateway_id):
    #     from apigateway.core.models import Release
    #
    #     # delete api release
    #     Release.objects.delete_by_gateway_id(gateway_id)
    #
    #     # delete resource version
    #     self.filter(api_id=gateway_id).delete()

    # TODO: 缓存优化：可使用 django cache(with database backend) or dogpile 缓存
    # 版本中包含的配置不会变化，但是处理逻辑可能调整，因此，缓存需支持版本
    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_LONG.value))
    def get_used_stage_vars(self, gateway_id, id):
        resoruce_version = self.filter(api_id=gateway_id, id=id).first()
        if not resoruce_version:
            return None

        used_in_path = set()
        used_in_host = set()
        for resource in resoruce_version.data:
            if resource["proxy"]["type"] != ProxyTypeEnum.HTTP.value:
                continue

            proxy_config = json.loads(resource["proxy"]["config"])

            proxy_path = proxy_config["path"]
            used_in_path.update(STAGE_VAR_PATTERN.findall(proxy_path))

            proxy_upstreams = proxy_config.get("upstreams")
            if proxy_upstreams:
                # 覆盖环境配置
                used_in_host.update(
                    STAGE_VAR_PATTERN.findall(";".join([host["host"] for host in proxy_upstreams["hosts"]]))
                )

        return {
            "in_path": list(used_in_path),
            "in_host": list(used_in_host),
        }

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_LONG.value))
    def has_used_stage_upstreams(self, gateway_id: int, id: int) -> bool:
        """资源 Hosts 是否存在使用默认配置"""
        resoruce_version = self.filter(api_id=gateway_id, id=id).first()
        for resource in resoruce_version.data:
            if resource["proxy"]["type"] != ProxyTypeEnum.HTTP.value:
                continue

            proxy_config = json.loads(resource["proxy"]["config"])
            proxy_upstreams = proxy_config.get("upstreams")
            if not proxy_upstreams:
                return True

        return False

    # def get_released_public_resources(self, gateway_id: int, stage_name: Optional[str] = None) -> List[dict]:
    #     """
    #     获取已发布的所有资源，将各环境发布的资源合并
    #     """
    #     from apigateway.core.models import Release, Stage
    #
    #     # 已发布版本中，以最新版本中资源配置为准
    #     resource_mapping = {}
    #     resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id, stage_name)
    #     for resource_version_id in sorted(resource_version_ids):
    #         resources_in_version = self.get_resources(gateway_id, resource_version_id)
    #         resource_mapping.update(resources_in_version)
    #
    #     # 只展示公开的资源
    #     resources = filter(lambda x: x["is_public"], resource_mapping.values())
    #
    #     # 若资源无可用环境，则不展示该资源
    #     # 比如：资源测试阶段，禁用环境 prod，则 prod 环境下不应展示该资源
    #     current_stage_names = set([stage_name] if stage_name else Stage.objects.get_names(gateway_id))
    #     return [
    #         resource
    #         for resource in resources
    #         if not resource["disabled_stages"] or (current_stage_names - set(resource["disabled_stages"]))
    #     ]

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_LONG.value))
    def get_resources(self, gateway_id: int, id: int) -> Dict[int, dict]:
        resource_version = self.filter(api_id=gateway_id, id=id).first()
        if not resource_version:
            return {}

        resources = {}
        for resource in resource_version.data:
            resource_auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])
            resources[resource["id"]] = {
                "id": resource["id"],
                "name": resource["name"],
                "description": resource.get("description", ""),
                "description_en": resource.get("description_en", ""),
                "method": resource["method"],
                "path": resource["path"],
                "match_subpath": resource.get("match_subpath", False),
                "is_public": resource["is_public"],
                "disabled_stages": resource.get("disabled_stages") or [],
                "allow_apply_permission": resource.get("allow_apply_permission", True),
                "resource_perm_required": resource_auth_config["resource_perm_required"],
                "app_verified_required": resource_auth_config["app_verified_required"],
                "user_verified_required": resource_auth_config["auth_verified_required"],
            }
        return resources

    # def need_new_version(self, gateway_id):
    #     """
    #     是否需要创建新的资源版本
    #     """
    #     from apigateway.core.models import Resource
    #
    #     latest_version = self.get_latest_version(gateway_id)
    #     latest_resource = Resource.objects.get_latest_resource(gateway_id)
    #
    #     if not (latest_version or latest_resource):
    #         return False
    #
    #     # 无资源版本
    #     if not latest_version:
    #         return True
    #
    #     # 如果有最近更新的资源，最近的更新资源时间 > 最新版本生成时间
    #     if latest_resource and latest_resource.updated_time > latest_version.created_time:
    #         return True
    #
    #     # 版本中资源数量是否发生变化
    #     # some resource could be deleted
    #     resource_count = Resource.objects.filter(api_id=gateway_id).count()
    #     if resource_count != len(latest_version.data):
    #         return True
    #
    #     return False

    def get_id_to_fields_map(
        self,
        gateway_id: Optional[int] = None,
        resource_version_ids: Optional[List[int]] = None,
    ) -> Dict[int, dict]:
        """获取资源版本信息"""
        queryset = self.all()

        if gateway_id is not None:
            queryset = queryset.filter(api_id=gateway_id)

        if resource_version_ids is not None:
            queryset = queryset.filter(id__in=resource_version_ids)

        return {rv["id"]: dict(rv) for rv in queryset.values("id", "name", "title", "version")}

    # def add_create_audit_log(self, gateway, resource_version, username: str):
    #     record_audit_log(
    #         username=username,
    #         op_type=OpTypeEnum.CREATE.value,
    #         op_status=OpStatusEnum.SUCCESS.value,
    #         op_object_group=gateway.id,
    #         op_object_type=OpObjectTypeEnum.RESOURCE_VERSION.value,
    #         op_object_id=resource_version.id,
    #         op_object=resource_version.name,
    #         comment=_("生成版本"),
    #     )

    def get_id_by_name(self, gateway, name: str) -> Optional[int]:
        # 版本中 data 数据量较大，查询时不查询 data 数据
        ids = self.filter(api=gateway, name=name).values_list("id", flat=True)
        if not ids:
            return None
        return ids[0]

    def get_id_by_version(self, gateway_id: int, version: str) -> Optional[int]:
        if not version:
            return None

        ids = self.filter(api_id=gateway_id, version=version).values_list("id", flat=True)
        if not ids:
            return None
        return ids[0]

    def get_object_fields(self, id_: int) -> Dict[str, Any]:
        """获取字段数据，因部分字段数据量过大，因此只获取部分数据量不大的字段"""
        return self.filter(id=id_).values("id", "name", "title", "version").first() or {}

    def check_version_exists(self, gateway_id: int, version: str) -> bool:
        return self.filter(api_id=gateway_id, version=version).exists()

    def filter_objects_fields(self, gateway_id: int, version: Optional[str]):
        qs = self.filter(api_id=gateway_id)

        if version:
            qs = qs.filter(version=version)

        return qs.values("id", "version", "title", "comment")


class ReleaseManager(models.Manager):
    def get_stage_release_status(self, stage_ids):
        """
        获取环境部署状态
        """
        released_stage_ids = self.filter(
            stage_id__in=stage_ids, stage__status=StageStatusEnum.ACTIVE.value
        ).values_list("stage_id", flat=True)
        return {stage_id: True for stage_id in released_stage_ids}

    def get_stage_release(self, gateway, stage_ids=None):
        """
        获取环境部署信息
        """
        queryset = self.filter(api_id=gateway.id, stage__status=StageStatusEnum.ACTIVE.value)
        if stage_ids is not None:
            queryset = queryset.filter(stage_id__in=stage_ids)

        stage_release = queryset.values(
            "stage_id",
            "resource_version_id",
            "resource_version__name",
            "resource_version__title",
            "resource_version__version",
            "updated_time",
        )
        return {
            release["stage_id"]: {
                "release_status": True,
                "release_time": release["updated_time"],
                "resource_version_id": release["resource_version_id"],
                "resource_version_name": release["resource_version__name"],
                "resource_version_title": release["resource_version__title"],
                "resource_version": {
                    "version": release["resource_version__version"],
                },
                "resource_version_display": get_resource_version_display(
                    {
                        "version": release["resource_version__version"],
                        "name": release["resource_version__name"],
                        "title": release["resource_version__title"],
                    }
                ),
            }
            for release in stage_release
        }

    def get_released_stages(self, gateway=None, resource_version_ids=None):
        # 查询版本信息，并按照版本ID排序
        # 只显示Stage未下线的发布信息
        queryset = self.filter(stage__status=StageStatusEnum.ACTIVE.value)

        if gateway is not None:
            queryset = self.filter(api_id=gateway.id)

        if resource_version_ids is not None:
            queryset = queryset.filter(resource_version_id__in=resource_version_ids)

        releases = queryset.values("stage_id", "stage__name", "resource_version_id").order_by("resource_version_id")

        # 根据版本ID对列表中的数据进行分组，分组前，需要根据分组的 key 进行排序
        release_groups = itertools.groupby(releases, key=operator.itemgetter("resource_version_id"))

        # 获取每个版本对应的环境信息
        released_stages = {}
        for resource_version_id, group in release_groups:
            released_stages[resource_version_id] = sorted(
                [
                    {
                        "id": stage["stage_id"],
                        "name": stage["stage__name"],
                    }
                    for stage in group
                ],
                key=lambda x: x["name"],
            )

        return released_stages

    def get_resource_version_released_stage_names(self, resource_version_ids: List[int]) -> Dict[int, List[str]]:
        released_stages = self.get_released_stages(resource_version_ids=resource_version_ids)
        return {
            resource_version_id: [stage["name"] for stage in stages]
            for resource_version_id, stages in released_stages.items()
        }

    def save_related_data(self, gateway, stage):
        # 发布后，将环境状态更新为可用
        stage.status = StageStatusEnum.ACTIVE.value
        stage.save(update_fields=["status", "updated_time"])

    def save_release(self, gateway, stage, resource_version, comment, username):
        obj, created = self.get_or_create(
            api=gateway,
            stage=stage,
            defaults={
                "resource_version": resource_version,
                "comment": comment,
                "created_by": username,
                "updated_by": username,
                "created_time": now_datetime(),
                "updated_time": now_datetime(),
            },
        )
        if not created:
            obj.resource_version = resource_version
            obj.comment = comment
            obj.updated_by = username
            obj.updated_time = now_datetime()
            obj.save()

        return obj

    def delete_by_gateway_id(self, gateway_id):
        self.filter(api_id=gateway_id).delete()

    def delete_by_stage_ids(self, stage_ids):
        self.filter(stage_id__in=stage_ids).delete()

    def filter_released_gateway_ids(self, gateway_ids):
        return set(self.filter(api_id__in=gateway_ids).values_list("api_id", flat=True))

    def get_released_resource_version_ids(self, gateway_id: int, stage_name: Optional[str] = None) -> List[int]:
        qs = self.filter(api_id=gateway_id)

        if stage_name:
            qs = qs.filter(stage__name=stage_name)

        return list(qs.values_list("resource_version_id", flat=True))

    def get_released_resource_version_id(self, gateway_id: int, stage_name: str) -> Optional[int]:
        ids = self.get_released_resource_version_ids(gateway_id, stage_name)
        if not ids:
            return None
        return ids[0]

    def get_released_stage_names(self, gateway_id: int) -> List[str]:
        return list(self.filter(api_id=gateway_id).values_list("stage__name", flat=True))

    def get_released_stage_count(self, resource_version_ids: List[int]) -> Dict[int, int]:
        """获取资源版本已发布的环境数量"""
        count = (
            self.filter(resource_version_id__in=resource_version_ids)
            .values("resource_version_id")
            .annotate(count=Count("resource_version_id"))
        )
        return {i["resource_version_id"]: i["count"] for i in count}

    def get_stage_id_to_fields_map(
        self,
        gateway_id: int,
        resource_version_ids: Optional[List[int]] = None,
    ) -> Dict[int, dict]:
        """获取已发布环境的信息"""
        queryset = self.filter(api_id=gateway_id)
        if resource_version_ids is not None:
            queryset = queryset.filter(resource_version_id__in=resource_version_ids)

        return {release["stage_id"]: dict(release) for release in queryset.values("stage_id", "resource_version_id")}

    def get_stage_ids_unreleased_the_version(
        self,
        gateway_id: int,
        stage_ids: List[int],
        resource_version_id: int,
    ) -> List[int]:
        """获取未发布此版本的环境列表"""
        released_stage_ids = self.filter(
            api_id=gateway_id,
            resource_version_id=resource_version_id,
        ).values_list("stage_id", flat=True)
        return list(set(stage_ids) - set(released_stage_ids))


class ReleasedResourceManager(models.Manager):
    def save_released_resource(self, resource_version, force: bool = False) -> None:
        """保存资源版本中的资源配置"""
        queryset = self.filter(resource_version_id=resource_version.id)
        exists = queryset.exists()

        if exists and not force:
            return

        if exists:
            queryset.delete()

        resource_to_add = [
            self.model(
                api_id=resource_version.api_id,
                resource_version_id=resource_version.id,
                resource_id=resource["id"],
                resource_name=resource["name"],
                resource_method=resource["method"],
                resource_path=resource["path"],
                data=resource,
            )
            for resource in resource_version.data
        ]
        self.bulk_create(resource_to_add, batch_size=settings.RELEASED_RESOURCE_CREATE_BATCH_SIZE)

    # FIXME: move to biz/released_resource ReleasedResource
    def clear_unreleased_resource(self, gateway_id: int) -> None:
        """清理未发布的资源，如已发布版本被新版本替换的情况"""
        from apigateway.core.models import Release

        resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
        self.filter(api_id=gateway_id).exclude(resource_version_id__in=resource_version_ids).delete()

    def get_resource_version_id_to_obj_map(self, gateway_id: int, resource_id: int):
        """获取已发布资源版本ID对应的发布资源"""
        return {
            resource.resource_version_id: resource
            for resource in self.filter(api_id=gateway_id, resource_id=resource_id)
        }

    # FIXME: move to biz/released_resource ReleasedResource
    def get_resource_released_stage_count(self, gateway_id: int, resource_ids: List[int]) -> Dict[int, int]:
        """获取资源已发布环境的数量"""
        from apigateway.core.models import Release

        resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
        released_stage_count = Release.objects.get_released_stage_count(resource_version_ids)

        resource_released_stage_count: dict = defaultdict(int)

        queryset = self.filter(api_id=gateway_id, resource_id__in=resource_ids).values(
            "resource_id", "resource_version_id"
        )
        for resource in queryset:
            resource_id = resource["resource_id"]
            resource_version_id = resource["resource_version_id"]
            resource_released_stage_count[resource_id] += released_stage_count.get(resource_version_id, 0)

        return resource_released_stage_count

    # FIXME: move to biz/released_resource ReleasedResource
    def get_resource_released_stages(self, gateway_id: int, resource_id: int) -> Dict[int, dict]:
        """获取资源已发布的环境信息"""
        from apigateway.core.models import Release, ResourceVersion

        rv_id_to_released_resource_map = self.get_resource_version_id_to_obj_map(gateway_id, resource_id)
        released_stage_id_map = Release.objects.get_stage_id_to_fields_map(
            gateway_id, rv_id_to_released_resource_map.keys()
        )
        resource_version_id_map = ResourceVersion.objects.get_id_to_fields_map(
            gateway_id,
            rv_id_to_released_resource_map.keys(),
        )

        resource_released_stages = {}
        for stage_id, stage_release in released_stage_id_map.items():
            resource_version_id = stage_release["resource_version_id"]
            resource_version = resource_version_id_map[resource_version_id]
            released_resource = rv_id_to_released_resource_map[resource_version_id]
            resource_released_stages[stage_id] = {
                "stage_id": stage_id,
                "resource_version_id": resource_version["id"],
                "resource_version_name": resource_version["name"],
                "resource_version_title": resource_version["title"],
                "resource_version_display": get_resource_version_display(resource_version),
                "released_resource": released_resource,
            }

        return resource_released_stages

    def get_released_resource(self, gateway_id: int, resource_version_id: int, resource_name: str) -> Optional[dict]:
        released_resource = self.filter(
            api_id=gateway_id,
            resource_version_id=resource_version_id,
            resource_name=resource_name,
        ).first()
        if not released_resource:
            return None

        return self._parse_released_resource(released_resource)

    def get_latest_released_resource(self, gateway_id: int, resource_id: int) -> dict:
        """获取资源最新的发布配置"""
        released_resource = (
            self.filter(api_id=gateway_id, resource_id=resource_id).order_by("-resource_version_id").first()
        )
        if not released_resource:
            return {}

        return self._parse_released_resource(released_resource)

    def filter_latest_released_resources(self, resource_ids: List[int]) -> List[dict]:
        """获取已发布资源的最新配置"""
        resources = (
            self.filter(resource_id__in=resource_ids)
            .order_by("resource_id", "-resource_version_id")
            .values("id", "resource_id", "resource_version_id")
        )

        ids = [next(group)["id"] for _, group in itertools.groupby(resources, key=operator.itemgetter("resource_id"))]

        return [self._parse_released_resource(resource) for resource in self.filter(id__in=ids)]

    def _filter_resource_version_ids(self, resource_ids: List[int]) -> List[int]:
        """过滤出资源所属的资源版本号"""
        return list(
            self.filter(resource_id__in=resource_ids)
            .order_by("resource_version_id")
            .distinct()
            .values_list("resource_version_id", flat=True)
        )

    # FIXME: move to biz/released_resource ReleasedResource
    def get_latest_doc_link(self, resource_ids: List[int]) -> Dict[int, str]:
        from apigateway.core.models import Release

        if not resource_ids:
            return {}

        resource_version_ids = self._filter_resource_version_ids(resource_ids)
        released_stage_names = Release.objects.get_resource_version_released_stage_names(resource_version_ids)

        # 按照资源版本从小到大排序，可使最新版本数据覆盖前面版本的数据
        released_resources = self.filter(resource_id__in=resource_ids).order_by("resource_id", "resource_version_id")

        doc_links = {}
        for resource in released_resources:
            stage_names = released_stage_names.get(resource.resource_version_id)
            if not stage_names:
                continue

            disabled_stages = resource.data.get("disabled_stages") or []
            recommeded_stage = self._get_recommended_stage_name(stage_names, disabled_stages)
            if not recommeded_stage:
                continue

            doc_links[resource.resource_id] = get_resource_doc_link(
                resource.api.name,
                recommeded_stage,
                resource.resource_name,
            )

        return doc_links

    def _get_recommended_stage_name(self, stage_names: List[str], disabled_stages: List[str]) -> Optional[str]:
        available_stages = set(stage_names) - set(disabled_stages)
        if not available_stages:
            return None

        if DEFAULT_STAGE_NAME in available_stages:
            return DEFAULT_STAGE_NAME

        return sorted(available_stages)[0]

    def _parse_released_resource(self, released_resource):
        resource = released_resource.data
        resource_auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])
        return {
            "id": resource["id"],
            "name": resource["name"],
            "description": resource.get("description", ""),
            "description_en": resource.get("description_en", ""),
            "method": resource["method"],
            "path": resource["path"],
            "match_subpath": resource.get("match_subpath", False),
            "is_public": resource["is_public"],
            "disabled_stages": resource.get("disabled_stages") or [],
            "allow_apply_permission": resource.get("allow_apply_permission", True),
            "app_verified_required": resource_auth_config["app_verified_required"],
            "resource_perm_required": resource_auth_config["resource_perm_required"],
            "user_verified_required": resource_auth_config["auth_verified_required"],
        }


class ReleaseHistoryManager(models.Manager):
    def filter_release_history(
        self,
        gateway,
        query="",
        stage_id=None,
        created_by="",
        time_start=None,
        time_end=None,
        order_by=None,
        fuzzy=False,
    ):
        queryset = self.filter(api=gateway)

        # query 不是模型字段，仅支持模糊匹配，如需精确匹配，可使用具体字段
        if query and fuzzy:
            queryset = queryset.filter(
                Q(stages__name__contains=query)
                | Q(resource_version__name__contains=query)
                | Q(resource_version__title__contains=query)
                | Q(resource_version__version__contains=query)
            )

        if stage_id:
            queryset = queryset.filter(stages__id=stage_id)

        if created_by:
            if fuzzy:
                queryset = queryset.filter(created_by__contains=created_by)
            else:
                queryset = queryset.filter(created_by=created_by)

        if time_start and time_end:
            # time_start、time_end须同时存在，否则无效
            queryset = queryset.filter(created_time__range=(time_start, time_end))

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset.distinct()

    # FIXME: move to biz/released_resource ReleasedResource
    def delete_without_stage_related(self, gateway_id):
        """
        删除无 stages 关联的数据

        因与 stages 为 ManyToMany 关联，删除 stage 时，
        仅自动清理了 stage 与 release-history 的关联数据，
        需要清理一次 release-history 本身的无效数据
        """
        from apigateway.core.models import Stage

        stage_ids = Stage.objects.get_ids(gateway_id)

        self.filter(api_id=gateway_id).exclude(stages__id__in=stage_ids).delete()

    def get_recent_releasers(self, gateway_id: int) -> List[str]:
        qs = self.filter(api_id=gateway_id).order_by("-id")[:10]
        return list(set(qs.values_list("created_by", flat=True)))


class ContextManager(models.Manager):
    def save_config(self, scope_type, scope_id, type, config, schema):
        return self.update_or_create(
            scope_type=scope_type,
            scope_id=scope_id,
            type=type,
            defaults={
                "config": config,
                "schema": schema,
            },
        )

    def get_config(self, scope_type, scope_id, type):
        return self.get(scope_type=scope_type, scope_id=scope_id, type=type).config

    def delete_by_scope_ids(self, scope_type, scope_ids):
        self.filter(scope_type=scope_type, scope_id__in=scope_ids).delete()

    # FIXME: move to biz/context ContextHandler? or not
    def filter_id_type_snapshot_map(self, scope_type, scope_ids):
        """
        获取 id=>type=>snapshot 的数据，如
        {
            1: {
                "resource_auth": {
                    "id": 123,
                    ...
                }
            }
        }
        """
        from apigateway.schema.models import Schema

        schemas = Schema.objects.filter_id_snapshot_map()
        id_type_snapshot_map = defaultdict(dict)
        queryset = self.filter(scope_type=scope_type, scope_id__in=scope_ids)
        for c in queryset:
            id_type_snapshot_map[c.scope_id][c.type] = c.snapshot(
                as_dict=True,
                schemas=schemas,
            )
        return id_type_snapshot_map


class JWTManager(models.Manager):
    def create_jwt(self, gateway):
        private_key, public_key = KeyGenerator().generate_rsa_key()
        cipher = AESCipherManager.create_jwt_cipher()
        return self.create(
            api=gateway,
            # 使用加密数据，不保存明文的 private_key
            # private_key=smart_str(private_key),
            private_key="",
            public_key=smart_str(public_key),
            encrypted_private_key=cipher.encrypt_to_hex(smart_str(private_key)),
        )

    def update_jwt_key(self, gateway, private_key: bytes, public_key: bytes):
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = self.get(api=gateway)
        jwt.public_key = smart_str(public_key)
        jwt.encrypted_private_key = cipher.encrypt_to_hex(smart_str(private_key))
        jwt.save(update_fields=["public_key", "encrypted_private_key"])

    def get_private_key(self, gateway_id: int) -> str:
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = self.get(api_id=gateway_id)
        return cipher.decrypt_from_hex(jwt.encrypted_private_key)

    def get_jwt(self, gateway):
        try:
            return self.get(api=gateway)
        except Exception:
            raise error_codes.NOT_FOUND_ERROR.format(_("网关密钥不存在。"), replace=True)

    def is_jwt_key_changed(self, gateway, private_key: bytes, public_key: bytes) -> bool:
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = self.get(api=gateway)
        return jwt.public_key != smart_str(public_key) or cipher.decrypt_from_hex(
            jwt.encrypted_private_key
        ) != smart_str(private_key)


class APIRelatedAppManager(models.Manager):
    def allow_app_manage_api(self, gateway_id: int, bk_app_code: str) -> bool:
        """是否允许应用管理网关"""
        return self.filter(api_id=gateway_id, bk_app_code=bk_app_code).exists()

    def add_related_app(self, gateway_id: int, bk_app_code: str):
        """添加关联应用"""

        # 检查app能关联的网关最大数量
        self._check_app_gateway_limit(bk_app_code)

        self.get_or_create(api_id=gateway_id, bk_app_code=bk_app_code)

    def _check_app_gateway_limit(self, bk_app_code: str):
        max_gateway_per_app = settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app_whitelist"].get(
            bk_app_code, settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app"]
        )
        if self.filter(bk_app_code=bk_app_code).count() >= max_gateway_per_app:
            raise error_codes.VALIDATE_ERROR.format(
                f"The app [{bk_app_code}] exceeds the limit of the number of gateways that can be related."
                + f" The maximum limit is {max_gateway_per_app}."
            )


class MicroGatewayManager(models.Manager):
    def get_id_to_fields(self, ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        if not ids:
            return {}

        return {item["id"]: item for item in self.filter(id__in=ids).values("id", "name")}

    def get_default_shared_gateway(self):
        return self.get(is_shared=True, id=settings.DEFAULT_MICRO_GATEWAY_ID)

    def get_count_by_gateway(self, gateway_ids: List[int]) -> Dict[int, int]:
        if not gateway_ids:
            return {}

        count = self.filter(api_id__in=gateway_ids).values("api_id").annotate(count=Count("api_id"))
        return {i["api_id"]: i["count"] for i in count}


class BackendServiceManager(models.Manager):
    def delete_backend_service(self, id: int):
        self._precheck_delete_instance(id)
        self.filter(id=id).delete()

    def _precheck_delete_instance(self, id: int):
        from apigateway.core.models import Proxy

        proxy = Proxy.objects.filter(backend_service_id=id).first()
        if not proxy:
            return

        raise InstanceDeleteError(
            _("后端服务【id={id}】被资源【id={resource_id}】引用，无法删除。").format(id=id, resource_id=proxy.resource_id)
        )


class SslCertificateManager(models.Manager):
    def delete_by_gateway_id(self, gateway_id: int):
        from apigateway.core.models import SslCertificateBinding

        # delete binding
        SslCertificateBinding.objects.filter(api_id=gateway_id).delete()

        # delete ssl-certificate
        self.filter(api_id=gateway_id).delete()

    def delete_by_id(self, id: int):
        self._check_for_delete(id)
        self.filter(id=id).delete()

    def _check_for_delete(self, id: int):
        """检查是否能被删除"""
        from apigateway.core.models import SslCertificateBinding

        binding = SslCertificateBinding.objects.filter(ssl_certificate_id=id).first()
        if not binding:
            return

        scope_label = SSLCertificateBindingScopeTypeEnum.get_choice_label(binding.scope_type)
        raise InstanceDeleteError(
            _("SSL 证书【id={id}】被 {scope_label}【id={scope_id}】引用，无法删除。").format(
                id=id,
                scope_label=scope_label,
                scope_id=binding.scope_id,
            )
        )

    def get_valid_ids(self, gateway_id: int, ids: List[int]) -> List[int]:
        return list(self.filter(api_id=gateway_id, id__in=ids).values_list("id", flat=True))

    def get_valid_id(self, gateway_id: int, id_: int) -> Optional[int]:
        return self.filter(api_id=gateway_id, id=id_).values_list("id", flat=True).first()


class SslCertificateBindingManager(models.Manager):
    def sync_binding(
        self,
        gateway_id: int,
        scope_type: SSLCertificateBindingScopeTypeEnum,
        scope_id: int,
        ssl_certificate_id: Optional[int],
    ):
        """同步绑定关系，将新增，更新或删除绑定关系，保持其与实际一致"""
        if not ssl_certificate_id:
            self.filter(api_id=gateway_id, scope_type=scope_type.value, scope_id=scope_id).delete()
            return

        self.update_or_create(
            api_id=gateway_id,
            scope_type=scope_type.value,
            scope_id=scope_id,
            defaults={
                "ssl_certificate_id": ssl_certificate_id,
            },
        )

    def get_scope_objects(self, gateway_id: int, scope_type: str, scope_ids: List[int]):
        if scope_type == SSLCertificateBindingScopeTypeEnum.STAGE.value:
            from apigateway.core.models import Stage

            return Stage.objects.filter(api_id=gateway_id, id__in=scope_ids)

        raise error_codes.INVALID_ARGS.format(f"unsupported scope_type: {scope_type}")

    def get_valid_scope_ids(self, gateway_id: int, scope_type: str, scope_ids: List[int]) -> List[int]:
        scope_objects = self.get_scope_objects(gateway_id, scope_type, scope_ids)
        return list(scope_objects.values_list("id", flat=True))

    def get_valid_scope_id(self, gateway_id: int, scope_type: str, scope_id: int) -> Optional[int]:
        scope_objects = self.get_scope_objects(gateway_id, scope_type, [scope_id])
        return scope_objects.values_list("id", flat=True).first()


class StageItemManager(models.Manager):
    def delete_stage_item(self, id: int):
        self._check_for_delete(id)
        self.filter(id=id).delete()

    def _check_for_delete(self, id: int):
        from apigateway.core.models import BackendService

        backend_service = BackendService.objects.filter(stage_item_id=id).first()
        if not backend_service:
            return

        raise InstanceDeleteError(
            _("环境配置项【id={id}】被后端服务【id={backend_service_id}, name={backend_service_name}】引用，无法删除。").format(
                id=id, backend_service_id=backend_service.id, backend_service_name=backend_service.name
            )
        )

    def get_reference_instances(self, gateway_id: int) -> Dict[str, List[Any]]:
        from apigateway.core.models import BackendService

        result: Dict[str, List[Any]] = defaultdict(list)

        backend_services = (
            BackendService.objects.filter(api_id=gateway_id).exclude(stage_item=None).values("stage_item__id", "name")
        )
        for service in backend_services:
            stage_item_id = service["stage_item__id"]
            result[stage_item_id].append(
                {
                    "instance_display": service["name"],
                    "type_display": _("后端服务"),
                }
            )

        return result


class StageItemConfigManager(models.Manager):
    def get_configured_item_ids(self, gateway_id: int, stage_id: int) -> Set[int]:
        return set(self.filter(api_id=gateway_id, stage_id=stage_id).values_list("stage_item_id", flat=True))

    def get_stage_item_id_to_configured_stages(self, gateway_id: int) -> Dict[str, List[Any]]:
        result = defaultdict(list)

        values = self.filter(api_id=gateway_id).values("stage__id", "stage__name", "stage_item_id")
        for value in values:
            stage_item_id = value["stage_item_id"]
            result[stage_item_id].append(
                {
                    "id": value["stage__id"],
                    "name": value["stage__name"],
                }
            )

        return result

    def get_configs(self, gateway_id, stage_item_id: int) -> List[Dict[str, Any]]:
        values = self.filter(api_id=gateway_id, stage_item_id=stage_item_id).values(
            "stage_id", "stage__name", "config"
        )
        return [
            {"stage_id": value["stage_id"], "stage_name": value["stage__name"], "config": value["config"]}
            for value in values
        ]
