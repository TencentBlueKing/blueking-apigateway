# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import Count

from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.biz.stage import StageHandler
from apigateway.common.constants import CallSourceTypeEnum
from apigateway.common.tenant.query import gateway_filter_by_user_tenant_id
from apigateway.core.api_auth import APIAuthConfig
from apigateway.core.constants import ContextScopeTypeEnum, GatewayTypeEnum
from apigateway.core.models import Backend, BackendConfig, Context, Gateway, Release, Resource, Stage
from apigateway.service.alarm_strategy import create_default_alarm_strategy
from apigateway.service.contexts import GatewayAuthContext
from apigateway.service.gateway_jwt import GatewayJWTHandler
from apigateway.utils.dict import deep_update

from .app_binding import GatewayAppBindingHandler
from .related_app import GatewayRelatedAppHandler

logger = logging.getLogger(__name__)


class GatewayHandler:
    @staticmethod
    def list_gateways_by_user(username: str, tenant_id: str = "") -> List[Gateway]:
        """获取用户有权限的的网关列表"""

        queryset = Gateway.objects.filter(_maintainers__contains=username)
        if tenant_id:
            queryset = gateway_filter_by_user_tenant_id(queryset, tenant_id)

        # 使用 _maintainers 过滤的数据并不准确，需要根据其中人员列表二次过滤
        return [gateway for gateway in queryset if gateway.has_permission(username)]

    @staticmethod
    def get_stages_with_release_status(gateway_ids: List[int]) -> Dict[int, list]:
        """
        查询网关环境，并添加环境发布状态

        :return: e.g.
        {
            1: [
                {
                    "id": 10,
                    "name": "prod",
                    "released": True,
                }
            ]
        }
        """
        stages = Stage.objects.filter(gateway_id__in=gateway_ids).values("id", "name", "gateway_id")
        released_stage_ids = ReleaseHandler.get_released_stage_ids(gateway_ids)
        stage_release_status = dict.fromkeys(released_stage_ids, True)

        gateway_id_to_stages = defaultdict(list)
        for stage in stages:
            gateway_id_to_stages[stage["gateway_id"]].append(
                {
                    "id": stage["id"],
                    "name": stage["name"],
                    "released": stage_release_status.get(stage["id"], False),
                }
            )

        return gateway_id_to_stages

    @staticmethod
    def get_gateway_auth_config(gateway_id: int) -> dict:
        """
        获取网关当前的认证配置
        """

        try:
            return GatewayAuthContext().get_config(gateway_id)
        except Context.DoesNotExist:
            return {}

    @staticmethod
    def save_auth_config(
        gateway_id: int,
        user_auth_type: Optional[str] = None,
        user_conf: Optional[dict] = None,
        api_type: Optional[GatewayTypeEnum] = None,
        allow_update_api_auth: Optional[bool] = None,
        unfiltered_sensitive_keys: Optional[List[str]] = None,
        allow_auth_from_params: Optional[bool] = None,
        allow_delete_sensitive_params: Optional[bool] = None,
    ):
        """
        存储网关认证配置

        :param gateway_id: 网关 id
        :param user_auth_type:
        :param user_conf: 用户类型为 default 的用户的认证配置
        :param api_type: 网关类型，只有 ESB 才能被设置为 SUPER_OFFICIAL_API 网关，网关会将所有请求参数透传给其后端服务
        :param allow_update_api_auth: 是否允许编辑网关资源安全设置中的应用认证配置
        :param unfiltered_sensitive_keys: 网关请求后端时，不去除的敏感字段
        :param allow_auth_from_params: 网关从请求中获取认证信息时，是否允许从请求参数 (querystring, body 等) 获取认证信息；如果不允许，则只能从请求头获取
        :param allow_delete_sensitive_params: 网关转发请求到后端时，是否需要删除请求参数（querystring, body 等）中的敏感参数
        """
        new_config: Dict[str, Any] = {}

        if user_auth_type is not None:
            new_config["user_auth_type"] = user_auth_type

        if user_conf is not None:
            new_config["user_conf"] = user_conf

        if api_type is not None:
            new_config["api_type"] = api_type.value

        if allow_update_api_auth is not None:
            new_config["allow_update_api_auth"] = allow_update_api_auth

        if unfiltered_sensitive_keys is not None:
            new_config["unfiltered_sensitive_keys"] = unfiltered_sensitive_keys

        if allow_auth_from_params is not None:
            new_config["allow_auth_from_params"] = allow_auth_from_params

            # 多租户版本，只允许从请求头获取认证信息，如果注册方配置 allow_auth_from_params 为 True，则强制设置为 False
            if allow_auth_from_params and settings.ENABLE_MULTI_TENANT_MODE:
                logger.warning(
                    "multi-tenant mode, allow_auth_from_params=True is not supported, force set to False, gateway_id=%s",
                    gateway_id,
                )
                new_config["allow_auth_from_params"] = False

        if allow_delete_sensitive_params is not None:
            new_config["allow_delete_sensitive_params"] = allow_delete_sensitive_params

        if not new_config:
            return None

        current_config = GatewayHandler.get_gateway_auth_config(gateway_id)

        # 因用户配置为 dict，参数 user_conf 仅传递了部分用户配置，因此需合并当前配置与传入配置
        api_auth_config = APIAuthConfig.model_validate(deep_update(current_config, new_config))

        return GatewayAuthContext().save(gateway_id, api_auth_config.config)

    @staticmethod
    def save_related_data(
        gateway: Gateway,
        user_auth_type: str,
        username: str,
        related_app_code: Optional[str] = None,
        user_config: Optional[dict] = None,
        unfiltered_sensitive_keys: Optional[List[str]] = None,
        api_type: Optional[GatewayTypeEnum] = None,
        allow_auth_from_params: Optional[bool] = None,
        allow_delete_sensitive_params: Optional[bool] = None,
        app_codes_to_binding: Optional[List[str]] = None,
        # 用于标识创建网关的来源
        source: Optional[CallSourceTypeEnum] = None,
    ):
        # 1. save gateway auth_config
        GatewayHandler.save_auth_config(
            gateway.id,
            user_auth_type=user_auth_type,
            user_conf=user_config,
            api_type=api_type,
            unfiltered_sensitive_keys=unfiltered_sensitive_keys,
            allow_auth_from_params=allow_auth_from_params,
            allow_delete_sensitive_params=allow_delete_sensitive_params,
        )

        # 2. save jwt

        GatewayJWTHandler.create_jwt(gateway)

        # 3. create default stage

        StageHandler().create_default(gateway, created_by=username, source=source)

        # 4. create default alarm-strategy

        create_default_alarm_strategy(gateway, created_by=username)

        # 5. create related app
        if related_app_code:
            GatewayRelatedAppHandler.add_related_app(gateway.id, related_app_code)

        # 6. update gateway app binding
        if app_codes_to_binding is not None:
            GatewayAppBindingHandler.update_gateway_app_bindings(gateway, app_codes_to_binding)

    @staticmethod
    def delete_gateway(gateway_id: int):
        # 1. delete gateway context

        Context.objects.delete_by_scope_ids(
            scope_type=ContextScopeTypeEnum.GATEWAY.value,
            scope_ids=[gateway_id],
        )

        # 2. delete release

        Release.objects.delete_by_gateway_id(gateway_id)

        # delete backend config
        BackendConfig.objects.filter(gateway_id=gateway_id).delete()

        # 3. delete stage

        StageHandler.delete_by_gateway_id(gateway_id)

        # 4. delete resource

        ResourceHandler.delete_by_gateway_id(gateway_id)

        # 5. delete resource-version

        ResourceVersionHandler.delete_by_gateway_id(gateway_id)

        # plugin bindings

        PluginBinding.objects.delete_by_gateway_id(gateway_id)

        # delete backend

        Backend.objects.filter(gateway_id=gateway_id).delete()

        # delete gateway
        Gateway.objects.filter(id=gateway_id).delete()

    @staticmethod
    def get_docs_url(gateway: Gateway) -> str:
        # 如果网关未启用则不提供文档地址
        if not gateway.is_active:
            return ""

        # 如果是非公开的不显示文档链接
        if not gateway.is_public:
            return ""

        # 对于没有发布过的也不显示文档链接
        stage_ids = ReleaseHandler.get_released_stage_ids([gateway.id])
        if len(stage_ids) == 0:
            return ""

        # 如果无可展示的资源文档，则不提供文档地址
        if ReleasedResourceDoc.objects.filter(gateway=gateway).exists():
            return settings.API_DOCS_URL_TMPL.format(api_name=gateway.name)
        return ""

    @staticmethod
    def get_api_domain(gateway: Gateway) -> str:
        return settings.BK_API_URL_TMPL.format(api_name=gateway.name)

    @staticmethod
    def get_resource_count(gateway_ids: List[int]) -> Dict[int, int]:
        """获取网关资源数量"""
        resource_count = (
            Resource.objects.filter(gateway_id__in=gateway_ids)
            .values("gateway_id")
            .annotate(count=Count("gateway_id"))
        )
        return {i["gateway_id"]: i["count"] for i in resource_count}

    @staticmethod
    def get_max_resource_count(gateway_name: str):
        return settings.API_GATEWAY_RESOURCE_LIMITS["max_resource_count_per_gateway_whitelist"].get(
            gateway_name, settings.API_GATEWAY_RESOURCE_LIMITS["max_resource_count_per_gateway"]
        )
