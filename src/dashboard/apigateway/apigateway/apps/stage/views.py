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
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum
from apigateway.apps.access_strategy.models import AccessStrategyBinding
from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.stage import serializers
from apigateway.biz.stage import StageHandler
from apigateway.common.contexts import StageProxyHTTPContext
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Release, Stage
from apigateway.core.signals import reversion_update_signal
from apigateway.utils.responses import V1FailJsonResponse, V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class StageViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StageSLZ
    lookup_field = "id"

    def get_queryset(self):
        return Stage.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=serializers.StageSLZ, tags=["Stage"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
            status=StageStatusEnum.INACTIVE.value,
        )

        return V1OKJsonResponse("OK", data={"id": slz.instance.id})

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.QueryStageSLZ,
        responses={status.HTTP_200_OK: serializers.ListStageSLZ(many=True)},
        tags=["Stage"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.QueryStageSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        if data.get("name"):
            queryset = queryset.filter(name__contains=data["name"])

        # order
        queryset = queryset.order_by(data.get("order_by") or "-updated_time")

        page = self.paginate_queryset(queryset)

        stage_ids = [stage.id for stage in page]
        serializer = serializers.ListStageSLZ(
            page,
            many=True,
            context={
                # 状态为 active 的环境，Release 中存在记录，则为已发布，否则为未发布
                "stage_release": Release.objects.get_stage_release(gateway=request.gateway, stage_ids=stage_ids),
                # 环境绑定策略
                "scope_bindings": AccessStrategyBinding.objects.query_scope_binding(
                    api=request.gateway,
                    scope_type=AccessStrategyBindScopeEnum.STAGE,
                    scope_ids=stage_ids,
                ),
                # 网关插件不适合放在环境列表中展示，应该放入详情中，保留此字段为了兼容前端逻辑
                "scope_bound_plugins": [],
                "stage_id_to_micro_gateway_fields": StageHandler().get_id_to_micro_gateway_fields(request.gateway.id),
            },
        )
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(
        query_serializer=serializers.QueryStageReleaseSLZ,
        responses={status.HTTP_200_OK: serializers.ListStageReleaseSLZ(many=True)},
        tags=["Stage"],
    )
    def list_release(self, request, *args, **kwargs):
        slz = serializers.QueryStageReleaseSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        queryset = queryset.filter(id__in=data["ids"]).order_by("name")

        stage_ids = list(queryset.values_list("id", flat=True))
        slz = serializers.ListStageReleaseSLZ(
            queryset,
            many=True,
            context={
                "stage_release": Release.objects.get_stage_release(gateway=request.gateway, stage_ids=stage_ids),
            },
        )

        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: serializers.ListStageBasicSLZ(many=True)},
        tags=["Stage"],
    )
    def list_basic(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = queryset.order_by("name")

        page = self.paginate_queryset(queryset)

        stage_ids = [stage.id for stage in page]
        serializer = serializers.ListStageBasicSLZ(
            page,
            many=True,
            context={
                "proxy_http_id_config_map": StageProxyHTTPContext().filter_scope_id_config_map(scope_ids=stage_ids),
            },
        )

        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["Stage"])
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(updated_by=request.user.username)

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(tags=["Stage"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["Stage"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id

        if instance.is_active:
            return V1FailJsonResponse(_("请先下线环境，然后再删除。"))

        StageHandler().delete_stages(request.gateway.id, [instance_id])

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=instance_id,
            op_object=instance.name,
            comment=_("删除环境"),
        )

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.UpdateStageStatusSLZ, tags=["Stage"]
    )
    @transaction.atomic
    def update_status(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.UpdateStageStatusSLZ(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        # 1. update stage status
        slz.save(updated_by=request.user.username)

        # 2. 删除环境的部署信息
        Release.objects.delete_by_stage_ids(stage_ids=[instance.id])

        # 3. send signal
        reversion_update_signal.send(sender=Stage, instance_id=instance.id, action="update status")

        # 4. record audit log
        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.name,
            comment=_("环境下线"),
        )

        return V1OKJsonResponse("OK")
