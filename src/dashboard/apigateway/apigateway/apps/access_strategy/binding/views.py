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
from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.access_strategy.binding import serializers
from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum
from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Resource, Stage
from apigateway.core.signals import reversion_update_signal
from apigateway.utils.responses import V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class AccessStrategyBindingBatchViewSet(viewsets.ModelViewSet):
    lookup_field = "id"

    def get_access_strategy_object(self):
        lookup_url_kwarg = "access_strategy_id"

        assert lookup_url_kwarg in self.kwargs

        try:
            return AccessStrategy.objects.filter(api=self.request.gateway).get(id=self.kwargs[lookup_url_kwarg])
        except AccessStrategy.DoesNotExist:
            raise Http404

    def _get_scope_queryset(self, scope_type, scope_ids):
        if scope_type == AccessStrategyBindScopeEnum.STAGE.value:
            queryset = Stage.objects.filter(api=self.request.gateway)
        elif scope_type == AccessStrategyBindScopeEnum.RESOURCE.value:
            queryset = Resource.objects.filter(api=self.request.gateway)
        else:
            raise error_codes.INVALID_ARGS.format(f"scope_type 不支持 {scope_type}")

        return queryset.filter(id__in=scope_ids)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.AccessStrategyBindingBindSLZ,
        tags=["AccessStrategy"],
    )
    @transaction.atomic
    def bind(self, request, *args, **kwargs):
        access_strategy = self.get_access_strategy_object()

        slz = serializers.AccessStrategyBindingBindSLZ(
            data=request.data,
            context={"access_strategy": access_strategy},
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        queryset = self._get_scope_queryset(data["scope_type"], data["scope_ids"])
        valid_scope_ids = queryset.values_list("id", flat=True)

        for scope_id in valid_scope_ids:
            binding, created = AccessStrategyBinding.objects.get_or_create(
                scope_type=data["scope_type"],
                scope_id=scope_id,
                type=data["type"],
                defaults={
                    "access_strategy": access_strategy,
                    "created_by": request.user.username,
                    "updated_by": request.user.username,
                },
            )
            if not created:
                binding.access_strategy = access_strategy
                binding.updated_by = request.user.username
                binding.save()

        if data.get("delete"):
            AccessStrategyBinding.objects.filter(
                access_strategy=access_strategy,
                scope_type=data["scope_type"],
                type=data["type"],
            ).exclude(scope_id__in=valid_scope_ids).delete()

        reversion_update_signal.send(sender=AccessStrategyBinding, instance_id=None, action="bind")

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.AccessStrategyBindingBatchSLZ,
        tags=["AccessStrategy"],
    )
    @transaction.atomic
    def unbind(self, request, *args, **kwargs):
        access_strategy = self.get_access_strategy_object()

        slz = serializers.AccessStrategyBindingBatchSLZ(
            data=request.data,
            context={"access_strategy": access_strategy},
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        queryset = self._get_scope_queryset(data["scope_type"], data["scope_ids"])

        AccessStrategyBinding.objects.filter(
            scope_type=data["scope_type"],
            type=data["type"],
            access_strategy=access_strategy,
            scope_id__in=list(queryset.values_list("id", flat=True)),
        ).delete()

        reversion_update_signal.send(sender=AccessStrategyBinding, instance_id=None, action="unbind")

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.AccessStrategyBindingQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AccessStrategyBindingListSLZ(many=True)},
        tags=["AccessStrategy"],
    )
    def list(self, request, *args, **kwargs):
        access_strategy = self.get_access_strategy_object()

        slz = serializers.AccessStrategyBindingQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = AccessStrategyBinding.objects.filter(
            scope_type=slz.validated_data["scope_type"],
            type=slz.validated_data["type"],
            access_strategy=access_strategy,
        )
        page = self.paginate_queryset(queryset)

        serializer = serializers.AccessStrategyBindingListSLZ(page, many=True)
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(
        query_serializer=serializers.AccessStrategyBindingDiffQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AccessStrategyBindingDiffDataSLZ()},
        tags=["AccessStrategy"],
    )
    def diff(self, request, *args, **kwargs):
        access_strategy = self.get_access_strategy_object()

        slz = serializers.AccessStrategyBindingDiffQuerySLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        diff_data = self._diff_bindings(access_strategy, data["scope_type"], data["scope_ids"], data["type"])

        serializer = serializers.AccessStrategyBindingDiffDataSLZ({"data": diff_data})
        return V1OKJsonResponse("OK", data=serializer.data["data"])

    def _diff_bindings(self, access_strategy, scope_type, scope_ids, _type):
        # 普通绑定，绑定对象原来未和其他策略绑定，可直接绑定
        normal_bindings = []
        # 覆盖绑定，绑定对象和其他策略已绑定，绑定会覆盖原绑定
        overwrite_bindings = []

        # 解绑
        unbind_binding_queryset = AccessStrategyBinding.objects.filter(
            access_strategy=access_strategy,
            scope_type=scope_type,
            type=_type,
        ).exclude(scope_id__in=scope_ids)

        # 查询网关下，指定 scope_type、type 的绑定
        scope_binding_queryset = AccessStrategyBinding.objects.filter(
            access_strategy__in=AccessStrategy.objects.filter(api=self.request.gateway),
            scope_type=scope_type,
            type=_type,
            scope_id__in=scope_ids,
        )
        scope_binding_map = {binding.scope_id: binding for binding in scope_binding_queryset}
        for scope_id in scope_ids:
            binding = scope_binding_map.get(scope_id)
            if not binding:
                # 普通新绑定
                normal_bindings.append(
                    {
                        "scope_type": scope_type,
                        "type": _type,
                        "scope_id": scope_id,
                    }
                )
                continue
            # 绑定对象，同类型绑定已存在，且与其他策略已绑定
            if binding.access_strategy.id != access_strategy.id:
                overwrite_bindings.append(binding)
        return {
            "unbind": unbind_binding_queryset,
            "normal_bind": normal_bindings,
            "overwrite_bind": overwrite_bindings,
        }
