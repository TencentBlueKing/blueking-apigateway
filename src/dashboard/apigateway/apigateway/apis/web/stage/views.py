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
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.audit import Auditor
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.biz.stage import StageHandler
from apigateway.common.error_codes import error_codes
from apigateway.components.paas import get_paas_repo_info, paas_app_module_offline
from apigateway.controller.publisher.publish import trigger_gateway_publish
from apigateway.core.constants import PublishSourceEnum, StageStatusEnum
from apigateway.core.models import BackendConfig, Stage
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.user_credentials import get_user_credentials_from_request

from .serializers import (
    BackendConfigInputSLZ,
    ProgrammableStageDeployOutputSLZ,
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
        return queryset.filter(gateway=self.request.gateway)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取环境列表",
        responses={status.HTTP_200_OK: StageOutputSLZ(many=True)},
        tags=["WebAPI.Stage"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建环境",
        responses={status.HTTP_201_CREATED: ""},
        request_body=StageInputSLZ,
        tags=["WebAPI.Stage"],
    ),
)
class StageListCreateApi(StageQuerySetMixin, generics.ListCreateAPIView):
    queryset = Stage.objects.order_by("id")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        stage_ids = [stage.id for stage in queryset]
        serializer = StageOutputSLZ(
            queryset,
            many=True,
            context={
                # 状态为 active 的环境，Release 中存在记录，则为已发布，否则为未发布
                "stage_release": ReleasedResourceHandler.get_stage_release(
                    gateway=request.gateway, stage_ids=stage_ids
                ),
                "stage_publish_status": ReleaseHandler.batch_get_stage_release_status(stage_ids),
                "new_resource_version": ResourceVersionHandler.get_latest_version_by_gateway(request.gateway.id),
            },
        )

        return OKJsonResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        slz = StageInputSLZ(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        stage = StageHandler.create(data, request.user.username)

        Auditor.record_stage_op_success(
            op_type=OpTypeEnum.CREATE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=stage.id,
            instance_name=stage.name,
            data_before={},
            data_after=get_model_dict(stage),
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取环境详情",
        responses={status.HTTP_200_OK: StageOutputSLZ()},
        tags=["WebAPI.Stage"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新环境",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=StageInputSLZ,
        tags=["WebAPI.Stage"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除环境",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Stage"],
    ),
)
@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        operation_description="局部更新环境",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=StagePartialInputSLZ,
        tags=["WebAPI.Stage"],
    ),
)
class StageRetrieveUpdateDestroyApi(StageQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    queryset = Stage.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = StageOutputSLZ(
            instance,
            context={
                "stage_release": ReleasedResourceHandler.get_stage_release(
                    gateway=request.gateway, stage_ids=[instance.id]
                ),
                "stage_publish_status": ReleaseHandler.batch_get_stage_release_status([instance.id]),
                "new_resource_version": ResourceVersionHandler.get_latest_version_by_gateway(request.gateway.id),
            },
        )

        return OKJsonResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)

        slz = StageInputSLZ(instance=instance, data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        username = request.user.username
        stage = StageHandler.update(instance, data, username)

        Auditor.record_stage_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=stage.id,
            instance_name=stage.name,
            data_before=data_before,
            data_after=get_model_dict(stage),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)

        # 判断环境是否已下线
        if not instance.deletable:
            raise error_codes.FAILED_PRECONDITION.format(_("请先下线环境，然后再删除。"))

        stage_id = instance.id
        stage_name = instance.name
        StageHandler.delete(instance)

        Auditor.record_stage_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=stage_id,
            instance_name=stage_name,
            data_before=data_before,
            data_after={},
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        slz = StagePartialInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        instance = self.get_object()
        data_before = {"description": instance.description}

        instance.description = data["description"]
        instance.save()

        Auditor.record_stage_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before,
            data_after={"description": instance.description},
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取环境变量",
        responses={status.HTTP_200_OK: StageVarsSLZ()},
        tags=["WebAPI.Stage"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新环境变量",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=StageVarsSLZ,
        tags=["WebAPI.Stage"],
    ),
)
class StageVarsRetrieveUpdateApi(StageQuerySetMixin, generics.RetrieveUpdateAPIView):
    lookup_field = "id"
    serializer_class = StageVarsSLZ
    queryset = Stage.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(instance, context={"gateway": request.gateway})

        return OKJsonResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        instance = self.get_object()
        data_before = {"vars": instance.vars}

        instance.vars = data["vars"]
        instance.save()

        username = request.user.username
        # 触发环境发布
        trigger_gateway_publish(PublishSourceEnum.STAGE_UPDATE, username, instance.gateway_id, instance.id)

        Auditor.record_stage_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            comment="更新环境变量",
            data_before=data_before,
            data_after={"vars": instance.vars},
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


class BackendConfigQuerySetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(gateway=self.request.gateway, stage_id=self.kwargs["id"])


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取环境的后端服务列表",
        responses={status.HTTP_200_OK: StageBackendOutputSLZ(many=True)},
        tags=["WebAPI.Stage"],
    ),
)
class StageBackendListApi(BackendConfigQuerySetMixin, generics.ListAPIView):
    queryset = BackendConfig.objects.order_by("backend_id").prefetch_related("backend")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = StageBackendOutputSLZ(queryset, many=True)
        return OKJsonResponse(data=serializer.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取环境的后端服务详情",
        responses={status.HTTP_200_OK: StageBackendOutputSLZ()},
        tags=["WebAPI.Stage"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新环境的后端服务",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=BackendConfigInputSLZ,
        tags=["WebAPI.Stage"],
    ),
)
class StageBackendRetrieveUpdateApi(BackendConfigQuerySetMixin, generics.RetrieveUpdateAPIView):
    queryset = BackendConfig.objects.prefetch_related("backend")
    serializer_class = BackendConfigInputSLZ

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), backend_id=self.kwargs["backend_id"])

        serializer = StageBackendOutputSLZ(instance)
        return OKJsonResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), backend_id=self.kwargs["backend_id"])
        data_before = get_model_dict(instance)

        slz = self.get_serializer(data=request.data, context={"backend": instance.backend})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        instance.config = data
        instance.save()

        Auditor.record_stage_backend_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance.id,
            instance_name=f"{instance.stage.name}:{instance.backend.name}",
            data_before=data_before,
            data_after=get_model_dict(instance),
        )

        username = request.user.username
        # 触发环境发布
        trigger_gateway_publish(PublishSourceEnum.BACKEND_UPDATE, username, instance.gateway_id, instance.stage_id)

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="环境下架",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=StageStatusInputSLZ,
        tags=["WebAPI.Stage"],
    ),
)
class StageStatusUpdateApi(StageQuerySetMixin, generics.UpdateAPIView):
    lookup_field = "id"
    serializer_class = StageStatusInputSLZ
    queryset = Stage.objects.all()

    def update(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        instance = self.get_object()
        data_before = {"status": instance.status}

        username = request.user.username
        StageHandler.set_status(instance, data["status"], username)

        if data["status"] == StageStatusEnum.INACTIVE.value and instance.gateway.is_programmable:
            # 调用paas下架接口
            paas_app_module_offline(
                app_code=request.gateway.name,
                module="default",
                env=instance.name,
                user_credentials=get_user_credentials_from_request(request),
            )

        Auditor.record_stage_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            comment="环境状态变更",
            data_before=data_before,
            data_after={"status": data["status"]},
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取编程网关环境部署详情",
        responses={status.HTTP_200_OK: ProgrammableStageDeployOutputSLZ()},
        tags=["WebAPI.Stage"],
    ),
)
class ProgrammableStageDeployRetrieveApi(StageQuerySetMixin, generics.RetrieveUpdateAPIView):
    lookup_field = "id"
    serializer_class = ProgrammableStageDeployOutputSLZ
    queryset = Stage.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        gateway = request.gateway
        stage_id = instance.id

        # 查询当前deploy历史
        deploy_history = ProgrammableGatewayDeployHistory.objects.filter(gateway=gateway).order_by("-id").first()

        stage_release = ReleasedResourceHandler.get_stage_release(gateway, [stage_id]).get(stage_id)
        if stage_release:
            # 优先使用与 stage_release 匹配的记录
            instance = (
                ProgrammableGatewayDeployHistory.objects.filter(
                    gateway=gateway, version=stage_release["resource_version_display"]
                ).first()
                or deploy_history  # 回退到最新记录
            )
        else:
            instance = deploy_history or ProgrammableGatewayDeployHistory()  # 空对象

        context_data = {
            "latest_deploy_history": instance,
            "repo_info": get_paas_repo_info(gateway.name, "default", get_user_credentials_from_request(request)),
            "stage_publish_status": ReleaseHandler.batch_get_stage_release_status([stage_id]),
        }

        output_slz = self.get_serializer(instance=instance, context=context_data)
        return OKJsonResponse(data=output_slz.data)
