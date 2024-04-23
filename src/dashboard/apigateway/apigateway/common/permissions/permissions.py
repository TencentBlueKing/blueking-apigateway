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
from cachetools import TTLCache, cached
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy
from rest_framework import permissions

from apigateway.common.constants import CACHE_MAXSIZE
from apigateway.biz.iam import IAMAuthHandler
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, GatewayRelatedApp
from apigateway.iam.models import IAMGradeManager
from apigateway.utils.django import get_object_or_None


class GatewayPermission(permissions.BasePermission):
    """
    获取网关并验证网关权限
    """

    message = gettext_lazy("当前用户无访问网关权限")

    iam_handler = IAMAuthHandler()

    def has_permission(self, request, view):
        gateway_obj = self.get_gateway_object(view)

        # 路径参数 gateway_id 不存在，不需要校验网关权限
        if not gateway_obj:
            return True

        request.gateway = gateway_obj

        # 跳过网关权限校验
        if getattr(view, "gateway_permission_exempt", False):
            return True

        # 没有开启 IAM，判断是否是网关维护者
        if not self._has_iam_grade_manager(gateway_obj.id):
            return gateway_obj.has_permission(request.user.username)

        # 校验 IAM 权限
        if hasattr(view, "method_permission"):
            method = request.method.lower()
            # 没有在 method_permission 中配置的的 method 不能通过
            if method not in view.method_permission:
                return False

            return self.iam_handler.is_allowed(request.user.username, view.method_permission[method], gateway_obj.id)

        return False

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=10))
    def _has_iam_grade_manager(self, gateway_id: int) -> bool:
        return IAMGradeManager.objects.filter(gateway_id=gateway_id).exists()

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
        gateway_obj = self.get_gateway_object(view)

        # 通过 view 属性 allow_gateway_not_exist，控制是否允许网关为 None
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
