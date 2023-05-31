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
from django.db import transaction
from rest_framework import viewsets
from rest_framework.views import APIView

from apigateway.apis.open.access_strategy import serializers
from apigateway.apis.open.access_strategy.constants import IPGroupActionEnum
from apigateway.apps.access_strategy.access_strategy.serializers import AccessStrategySLZ
from apigateway.apps.access_strategy.binding.views import AccessStrategyBindingBatchViewSet
from apigateway.apps.access_strategy.constants import AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategy, IPGroup
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.utils.django import get_object_or_None
from apigateway.utils.responses import OKJsonResponse


class IPGroupV1ViewSet(viewsets.ModelViewSet):
    queryset = IPGroup.objects.all()
    serializer_class = serializers.IPGroupV1SLZ
    lookup_field = "id"
    api_permission_exempt = True

    def post(self, request, *args, **kwargs):
        """
        创建或更新IP分组
        """
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        obj, created = IPGroup.objects.get_or_create(
            api=self.request.gateway,
            name=data["name"],
            defaults={
                "_ips": data["ips"],
                "comment": data.get("comment", ""),
                "created_by": request.user.username,
            },
        )

        if not created:
            obj._ips = self._get_latest_ips(obj._ips, data["ips"], action=data["action"])
            obj.comment = data.get("comment", "")
            obj.updated_by = request.user.username
            obj.save(update_fields=["_ips", "comment", "updated_by", "updated_time"])

        return OKJsonResponse(
            "OK",
            data={
                "id": obj.id,
                "name": obj.name,
                "created": created,
            },
        )

    def _get_latest_ips(self, old_ips, new_ips, action=None):
        """
        根据 action 获取IP分组的最新IP列表
        """
        if action == IPGroupActionEnum.SET.value:
            return new_ips

        elif action == IPGroupActionEnum.APPEND.value:
            ip_list = old_ips.splitlines()
            for ip in new_ips.splitlines():
                if ip not in ip_list:
                    ip_list.append(ip)
            return "\n".join(ip_list)

        return old_ips


class AccessStrategyAddIPGroupsV1APIView(APIView):
    """
    为策略添加IP白名单
    """

    api_permission_exempt = True

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = serializers.AccessStrategyAddIPGroupsV1SLZ(
            data=request.data,
            context={
                "request": request,
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = AccessStrategy.objects.filter(
            api=self.request.gateway,
            type=AccessStrategyTypeEnum.IP_ACCESS_CONTROL.value,
            id__in=data["access_strategy_ids"],
        )
        for strategy in queryset:
            strategy.add_ip_group_list(data["ip_group_list"])
            strategy.save(update_fields=["_config", "updated_time"])

        return OKJsonResponse("OK")


class AccessStrategyBindingsV1ViewSet(AccessStrategyBindingBatchViewSet):
    """
    为环境、资源添加绑定策略
    """

    api_permission_exempt = True


class AccessStrategySyncViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @transaction.atomic
    def sync(self, request, gateway_name: str, *args, **kwargs):
        # 创建或更新策略
        instance = get_object_or_None(
            AccessStrategy,
            api=request.gateway,
            name=request.data.get("name", ""),
            type=request.data.get("type", ""),
        )

        slz = AccessStrategySLZ(
            instance=instance,
            data=request.data,
            context={
                "request": request,
            },
        )
        slz.is_valid(raise_exception=True)
        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        # 同步策略绑定
        bind_slz = serializers.AccessStrategyBindingSyncSLZ(
            data=request.data,
            context={
                "request": request,
                "access_strategy": slz.instance,
            },
        )
        bind_slz.is_valid(raise_exception=True)
        bind_slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return OKJsonResponse(
            "OK",
            data={
                "id": slz.instance.id,
                "name": slz.instance.name,
            },
        )
