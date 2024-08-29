# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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

from apigateway.core.models import Gateway, GatewayRelatedApp
from apigateway.utils.django import get_object_or_None


class OpenAPIPermission(permissions.BasePermission):
    """仅验证来自于网关的请求
    适用：申请网关接口权限后，就能访问的接口，路径参数中没有 gateway_id or gateway_name
    """

    message = gettext_lazy("只能通过网关访问该接口")

    def has_permission(self, request, view):
        # openapi 的请求来源必须是网关，此时经过网关的中间件（所有都开启了应用认证）, 请求中会注入 app 对象
        if not hasattr(request, "app"):
            return False

        return True


class OpenAPIGatewayIdPermission(permissions.BasePermission):
    """验证来自于网关的请求，并且路径参数中有 gateway_id, 且这个 gateway_id 对应网关存在
    适用：申请网关接口权限后 + 路径参数中 gateway_id 的接口
    """

    message = gettext_lazy("只能通过网关访问该接口，并且 gateway_id 对应网关必须存在")

    def has_permission(self, request, view):
        # openapi 的请求来源必须是网关，此时经过网关的中间件（所有都开启了应用认证）, 请求中会注入 app 对象
        if not hasattr(request, "app"):
            return False

        # 路径参数 gateway_id 必须存在
        gateway_obj = self.get_gateway_object(view)

        if not gateway_obj:
            raise Http404
        request.gateway = gateway_obj

        return True

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


class OpenAPIGatewayNamePermission(permissions.BasePermission):
    """验证来自于网关的请求，并且路径参数中有 gateway_name, 且这个 gateway_name 对应网关存在
    适用：申请网关接口权限后 + 路径参数中 gateway_name 的接口
    """

    message = gettext_lazy("只能通过网关访问该接口，并且 gateway_name 对应网关必须存在")

    def has_permission(self, request, view):
        # openapi 的请求来源必须是网关，此时经过网关的中间件（所有都开启了应用认证）, 请求中会注入 app 对象
        if not hasattr(request, "app"):
            return False

        # 路径参数 gateway_id 必须存在
        gateway_obj = self.get_gateway_object(view)

        if not gateway_obj:
            raise Http404
        request.gateway = gateway_obj

        return True

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


class OpenAPIGatewayRelatedAppPermission(permissions.BasePermission):
    """验证来自于网关的请求 + 路径参数中有 gateway_name, 且这个 gateway_name 对应网关存在 + 这个应用有操作这个网关的权限 (GatewayRelatedApp)
    适用：SDK 使用的 API，某个应用通过网关的接口对网关进行变更
    """

    message = gettext_lazy("应用无操作网关权限")

    def has_permission(self, request, view):
        # openapi 的请求来源必须是网关，此时经过网关的中间件（所有都开启了应用认证）, 请求中会注入 app 对象
        if not hasattr(request, "app"):
            return False

        gateway_obj = self.get_gateway_object(view)

        # NOTE: only for GatewaySyncApi /<slug:gateway_name>/sync/, at that time, the gateway_obj is None
        # DO NOT USE IN OTHER PLACE
        if not gateway_obj and getattr(view, "allow_gateway_not_exist", False):
            return True

        if not gateway_obj:
            raise Http404

        request.gateway = gateway_obj

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
