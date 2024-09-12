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
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy
from rest_framework import permissions

from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, GatewayRelatedApp
from apigateway.utils.django import get_object_or_None


class GatewayPermission(permissions.BasePermission):
    """
    获取网关并验证网关权限
    """

    message = gettext_lazy("当前用户无访问网关权限")

    def has_permission(self, request, view):
        # openapi 的请求来源必须是网关，此时经过网关的中间件（所有都开启了应用认证）, 请求中会注入 app 对象
        if getattr(view, "request_from_gateway_required", False) and not hasattr(request, "app"):
            return False

        gateway_obj = self.get_gateway_object(view)

        # FIXME: 可能的越权，待重构 open api 之后，确认剩下的逻辑哪里有需要这个的
        # 路径参数 gateway_id 不存在，不需要校验网关权限
        if not gateway_obj:
            return True

        request.gateway = gateway_obj

        # 跳过网关权限校验
        if getattr(view, "gateway_permission_exempt", False):
            return True

        return gateway_obj.has_permission(request.user.username)

    def get_gateway_object(self, view):
        """
        根据路径参数 gateway_id 获取网关对象
        如果 gateway_id 不在路径参数中，则返回 None，忽略此权限验证
        否则，返回 api 对象或抛出异常
        """
        lookup_url_kwarg = "gateway_id"

        if lookup_url_kwarg not in view.kwargs:
            return None

        filter_kwargs = {"id": view.kwargs[lookup_url_kwarg]}
        return get_object_or_404(Gateway, **filter_kwargs)


class GatewayRelatedAppPermission(permissions.BasePermission):
    """
    获取网关并验证应用是否有操作网关的权限
    """

    message = gettext_lazy("应用无操作网关权限")

    def has_permission(self, request, view):
        # openapi 的请求来源必须是网关，此时经过网关的中间件（所有都开启了应用认证）, 请求中会注入 app 对象
        if not hasattr(request, "app"):
            return False

        gateway_obj = self.get_gateway_object(view)
        # NOTE: only for GatewaySyncApi /<slug:gateway_name>/sync/, at that time, the gateway_obj is None
        # should be refactored in the future 新版 openapi 不要这么设计了
        if not gateway_obj and getattr(view, "allow_gateway_not_exist", False):
            return True

        if not gateway_obj:
            raise Http404

        request.gateway = gateway_obj

        # 跳过网关权限校验
        if getattr(view, "gateway_permission_exempt", False):
            return True

        return GatewayRelatedApp.objects.filter(gateway=request.gateway, bk_app_code=request.app.app_code).exists()

    def get_gateway_object(self, view):
        """
        根据路径参数 gateway_name 获取网关对象
        若 gateway_name 不在路径参数中，或网关不存在，返回 None
        """
        lookup_url_kwarg = "gateway_name"

        if lookup_url_kwarg not in view.kwargs:
            return None

        filter_kwargs = {"name": view.kwargs[lookup_url_kwarg]}
        return get_object_or_None(Gateway, **filter_kwargs)


class GatewayDisplayablePermission(permissions.BasePermission):
    """
    校验网关是否可公开展示
    - 网关已启用
    - 网关允许公开
    """

    message = gettext_lazy("网关不存在")

    def has_permission(self, request, view):
        gateway_obj = self._get_displayable_gateway(view)
        if not gateway_obj:
            raise Http404

        request.gateway = gateway_obj
        return True

    def _get_displayable_gateway(self, view):
        lookup_url_kwarg = "gateway_name"

        if lookup_url_kwarg not in view.kwargs:
            return None

        gateway_name = view.kwargs[lookup_url_kwarg]
        return Gateway.objects.filter(
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
            name=gateway_name,
        ).first()
