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
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.biz.stage import StageHandler
from apigateway.common.error_codes import error_codes
from apigateway.core.models import BackendConfig, Release, Stage
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    BackendConfigInputSLZ,
    StageBackendOutputSLZ,
    StageInputSLZ,
    StageOutputSLZ,
    StagePartialInputSLZ,
    StageStatusInputSLZ,
    StageVarsSLZ,
)


class StageQuerySetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(api=self.request.gateway)


class StageListCreateApi(StageQuerySetMixin, generics.ListCreateAPIView):
    queryset = Stage.objects.order_by("id")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: StageOutputSLZ(many=True)},
        tags=["Stage"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        stage_ids = [stage.id for stage in queryset]
        serializer = StageOutputSLZ(
            queryset,
            many=True,
            context={
                # 状态为 active 的环境，Release 中存在记录，则为已发布，否则为未发布
                "stage_release": Release.objects.get_stage_release(gateway=request.gateway, stage_ids=stage_ids),
                # TODO 获取各个环境的发布状态与publish_id
                "new_resource_version": "",  # TODO 获取网关的新资源版本号
            },
        )

        return OKJsonResponse(data=serializer.data)

    @swagger_auto_schema(
        responses={status.HTTP_201_CREATED: ""},
        request_body=StageInputSLZ,
        tags=["Stage"],
    )
    def create(self, request, *args, **kwargs):
        slz = StageInputSLZ(data=request.data, context={"api": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        stage = StageHandler.create(data, request.user.username)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=stage.id,
            op_object=stage.name,
            comment=_("创建环境"),
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


class StageRetrieveUpdateDestroyApi(StageQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    queryset = Stage.objects.all()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: StageOutputSLZ()},
        tags=["Stage"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = StageOutputSLZ(
            instance,
            context={
                "stage_release": Release.objects.get_stage_release(gateway=request.gateway, stage_ids=[instance.id]),
                # TODO 获取各个环境的发布状态与publish_id
                "new_resource_version": "",  # TODO 获取网关的新资源版本号
            },
        )

        return OKJsonResponse(data=serializer.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=StageInputSLZ,
        tags=["Stage"],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = StageInputSLZ(instance=instance, data=request.data, context={"api": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        stage = StageHandler.update(instance, data, request.user.username)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=stage.id,
            op_object=stage.name,
            comment=_("更新环境"),
        )

        return OKJsonResponse()

    @swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["Stage"],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 判断环境是否已下线
        if not instance.deletable:
            raise error_codes.INVALID_ARGUMENT.format(_("请先下线环境，然后再删除。"))

        StageHandler.delete(instance)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=instance.id,
            op_object=instance.name,
            comment=_("删除环境"),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=StagePartialInputSLZ,
        tags=["Stage"],
    )
    def partial_update(self, request, *args, **kwargs):
        slz = StagePartialInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        instance = self.get_object()
        instance.description = data["description"]
        instance.save()

        return OKJsonResponse()


class StageVarsRetrieveUpdateApi(StageQuerySetMixin, generics.RetrieveUpdateAPIView):
    lookup_field = "id"
    queryset = Stage.objects.all()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: StageOutputSLZ()},
        tags=["Stage"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = StageVarsSLZ(instance, context={"api": request.gateway})

        return OKJsonResponse(data=serializer.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=StageVarsSLZ,
        tags=["Stage"],
    )
    def update(self, request, *args, **kwargs):
        slz = StageVarsSLZ(data=request.data, context={"api": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        instance = self.get_object()
        instance.vars = data["vars"]
        instance.save()

        return OKJsonResponse()


class BackendConfigQuerySetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(gateway=self.request.gateway, stage_id=self.kwargs["id"])


class StageBackendListApi(BackendConfigQuerySetMixin, generics.ListAPIView):
    queryset = BackendConfig.objects.order_by("backend__id").prefetch_related("backend")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: StageBackendOutputSLZ(many=True)},
        tags=["Stage"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = StageBackendOutputSLZ(queryset, many=True)
        return OKJsonResponse(data=serializer.data)


class StageBackendRetrieveUpdateApi(BackendConfigQuerySetMixin, generics.RetrieveUpdateAPIView):
    queryset = BackendConfig.objects.prefetch_related("backend")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: StageBackendOutputSLZ()},
        tags=["Stage"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), backend__id=self.kwargs["backend_id"])

        serializer = StageBackendOutputSLZ(instance)
        return OKJsonResponse(data=serializer.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=BackendConfigInputSLZ,
        tags=["Stage"],
    )
    def update(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), backend__id=self.kwargs["backend_id"])

        slz = BackendConfigInputSLZ(data=request.data, context={"backend": instance.backend})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        instance.config = data
        instance.save()

        return OKJsonResponse()


class StageStatusUpdateApi(StageQuerySetMixin, generics.UpdateAPIView):
    lookup_field = "id"
    queryset = Stage.objects.all()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=StageStatusInputSLZ,
        tags=["Stage"],
    )
    def update(self, request, *args, **kwargs):
        slz = StageStatusInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        instance = self.get_object()

        StageHandler.set_status(instance, data["status"], request.user.username)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=instance.id,
            op_object=instance.name,
            comment=_("环境状态变更"),
        )

        return OKJsonResponse()
