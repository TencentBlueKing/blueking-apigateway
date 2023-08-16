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

import copy
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import Count
from django.utils.translation import gettext as _

from apigateway.apps.access_strategy.models import AccessStrategy
from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.biz.iam import IAMHandler
from apigateway.biz.release import ReleaseHandler
from apigateway.common.contexts import GatewayAuthContext, GatewayFeatureFlagContext
from apigateway.core.api_auth import APIAuthConfig
from apigateway.core.constants import ContextScopeTypeEnum, GatewayTypeEnum
from apigateway.core.models import JWT, APIRelatedApp, Context, Gateway, Release, Resource, SslCertificate, Stage
from apigateway.utils.dict import deep_update

from .resource import ResourceHandler
from .resource_version import ResourceVersionHandler
from .stage import StageHandler


class GatewayHandler:
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
        stages = Stage.objects.filter(api_id__in=gateway_ids).values("id", "name", "api_id")
        released_stage_ids = ReleaseHandler.get_released_stage_ids(gateway_ids)
        stage_release_status = dict.fromkeys(released_stage_ids, True)

        gateway_id_to_stages = defaultdict(list)
        for stage in stages:
            gateway_id_to_stages[stage["api_id"]].append(
                {
                    "id": stage["id"],
                    "name": stage["name"],
                    "released": stage_release_status.get(stage["id"], False),
                }
            )

        return gateway_id_to_stages

    @staticmethod
    def get_current_gateway_auth_config(gateway_id: int) -> dict:
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
    ):
        """
        存储网关认证配置

        :param gateway_id: 网关id
        :param user_auth_type:
        :param user_conf: 用户类型为 default 的用户的认证配置
        :param api_type: 网关类型，只有 ESB 才能被设置为 SUPER_OFFICIAL_API 网关，网关会将所有请求参数透传给其后端服务
        :param allow_update_api_auth: 是否允许编辑网关资源安全设置中的应用认证配置
        :param unfiltered_sensitive_keys:
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

        if not new_config:
            return

        current_config = GatewayHandler().get_current_gateway_auth_config(gateway_id)

        # 因用户配置为 dict，参数 user_conf 仅传递了部分用户配置，因此需合并当前配置与传入配置
        api_auth_config = APIAuthConfig.parse_obj(deep_update(current_config, new_config))

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
    ):
        # 1. save api auth_config
        GatewayHandler().save_auth_config(
            gateway.id,
            user_auth_type=user_auth_type,
            user_conf=user_config,
            api_type=api_type,
            unfiltered_sensitive_keys=unfiltered_sensitive_keys,
        )

        # 2. save jwt

        JWT.objects.create_jwt(gateway)

        # 3. create default stage

        StageHandler().create_default(gateway, created_by=username)

        # 4. create default alarm-strategy

        AlarmStrategy.objects.create_default_strategy(gateway, created_by=username)

        # 5. create related app
        if related_app_code:
            APIRelatedApp.objects.add_related_app(gateway.id, related_app_code)

        # 6. 在权限中心注册分级管理员，创建用户组
        if settings.USE_BK_IAM_PERMISSION:
            IAMHandler.register_grade_manager_and_builtin_user_groups(gateway)

    @staticmethod
    def delete_gateway(gateway_id: int):
        # 0. 删除权限中心中网关的分级管理员和用户组
        IAMHandler.delete_grade_manager_and_builtin_user_groups(gateway_id)

        # 1. delete api context

        Context.objects.delete_by_scope_ids(
            scope_type=ContextScopeTypeEnum.GATEWAY.value,
            scope_ids=[gateway_id],
        )

        # 2. delete release

        Release.objects.delete_by_gateway_id(gateway_id)

        # 3. delete stage

        StageHandler().delete_by_gateway_id(gateway_id)

        # 4. delete resource

        ResourceHandler().delete_by_gateway_id(gateway_id)

        # 5. delete resource-version

        ResourceVersionHandler().delete_by_gateway_id(gateway_id)

        # 6. delete access_strategy

        AccessStrategy.objects.delete_by_gateway_id(gateway_id)

        # plugin bindings

        PluginBinding.objects.delete_by_gateway_id(gateway_id)

        # delete ssl-certificate

        SslCertificate.objects.delete_by_gateway_id(gateway_id)

        # delete api
        Gateway.objects.filter(id=gateway_id).delete()

    @staticmethod
    def record_audit_log_success(
        username: str, gateway_id: int, op_type: OpTypeEnum, instance_id: int, instance_name: str
    ):
        comment = {
            OpTypeEnum.CREATE: _("创建网关"),
            OpTypeEnum.MODIFY: _("更新网关"),
            OpTypeEnum.DELETE: _("删除网关"),
        }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.API.value,
            op_object_id=instance_id,
            op_object=instance_name,
            comment=comment,
        )

    @staticmethod
    def get_feature_flag(gateway_id: int) -> Dict[str, bool]:
        feature_flags = copy.deepcopy(settings.GLOBAL_GATEWAY_FEATURE_FLAG)
        feature_flags.update(GatewayFeatureFlagContext().get_config(gateway_id, {}))
        return feature_flags

    @staticmethod
    def get_docs_url(gateway: Gateway) -> str:
        # 如果无可展示的资源文档，则不提供文档地址
        if ReleasedResourceDoc.objects.filter(api=gateway).exists():
            return settings.API_DOCS_URL_TMPL.format(api_name=gateway.name)
        return ""

    @staticmethod
    def get_api_domain(gateway: Gateway) -> str:
        return settings.BK_API_URL_TMPL.format(api_name=gateway.name)

    @staticmethod
    def get_resource_count(gateway_ids: List[int]) -> Dict[int, int]:
        """获取网关资源数量"""
        resource_count = (
            Resource.objects.filter(api_id__in=gateway_ids).values("api_id").annotate(count=Count("api_id"))
        )
        return {i["api_id"]: i["count"] for i in resource_count}
