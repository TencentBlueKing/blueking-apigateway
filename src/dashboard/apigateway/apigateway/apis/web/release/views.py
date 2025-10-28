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

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from openapi_schema_to_json_schema import to_json_schema
from rest_framework import generics, status

from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.gateway import ReleaseError, release
from apigateway.biz.programmable import ProgrammableGatewayReleaser
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.biz.resource import ResourceLabelHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.user_credentials import get_user_credentials_from_request
from apigateway.components.bkpaas import (
    get_paas_deploy_phases_framework,
    get_paas_deploy_phases_instance,
    get_paas_deployment_result,
    get_paas_offline_result,
    get_pass_deploy_streams_history_events,
)
from apigateway.core.constants import PublishSourceEnum
from apigateway.core.models import Backend, PublishEvent, Release, ReleaseHistory, ResourceVersion
from apigateway.utils import openapi as openapi_utils
from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import Lock
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse

from .serializers import (
    DeployHistoryOutputSLZ,
    ProgrammableDeployCreateInputSLZ,
    ProgrammableDeployEventGetOutputSLZ,
    ReleaseHistoryEventRetrieveOutputSLZ,
    ReleaseHistoryOutputSLZ,
    ReleaseHistoryQueryInputSLZ,
    ReleaseInputSLZ,
    ReleaseResourceSchemaOutputSLZ,
    ResourceOutputSLZ,
)

logger = logging.getLogger(__name__)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Release"],
        operation_description="获取环境下可用的资源列表接口 (在线调试)",
        responses={status.HTTP_200_OK: ResourceOutputSLZ(many=True)},
    ),
)
class ReleaseAvailableResourceListApi(generics.ListAPIView):
    lookup_field = "stage_id"

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    def list(self, request, *args, **kwargs):
        """
        用于在线调试时，获取环境下可用的资源列表
        """
        try:
            instance = self.get_object()
        except Http404:
            raise error_codes.NOT_FOUND.format(_("当前选择环境未发布版本，请先发布版本到该环境。"))

        stage_name = instance.stage.name
        resources = ReleasedResourceHandler.get_public_released_resource_data_list(
            request.gateway.id, stage_name, is_only_public=False
        )
        label_ids = list({label_id for resource in resources for label_id in resource.gateway_labels})
        output_slz = ResourceOutputSLZ(
            resources,
            many=True,
            context={
                "labels": ResourceLabelHandler.get_labels_by_ids(label_ids),
            },
        )
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Release"],
        operation_description="获取环境下可用的某个资源接口 schema(在线调试)",
        responses={status.HTTP_200_OK: ReleaseResourceSchemaOutputSLZ()},
    ),
)
class ReleaseAvailableResourceSchemaRetrieveApi(generics.RetrieveAPIView):
    lookup_field = "stage_id"
    serializer_class = ReleaseResourceSchemaOutputSLZ

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    def retrieve(self, request, *args, **kwargs):
        """
        用于在线调试时，获取某个资源的 schema 数据，以及自动生成 request_body example
        """
        try:
            instance = self.get_object()
        except Http404:
            raise error_codes.NOT_FOUND.format(_("当前选择环境未发布版本，请先发布版本到该环境。"))

        resource_id = self.kwargs["resource_id"]
        schema_result = {"resource_id": resource_id}

        # 获取对应资源的 schema
        schema = ResourceVersionHandler.get_resource_schema(instance.resource_version.id, resource_id)
        schema_result["parameter_schema"] = schema.get("parameters", [])
        schema_result["response_schema"] = schema.get("responses", {})
        request_body = schema.get("requestBody")
        if request_body and "content" in request_body and "application/json" in request_body["content"]:
            # todo: 暂时在只支持 application/json
            json_schema = to_json_schema(
                request_body["content"]["application/json"]["schema"], {"keepNotSupported": ["example"]}
            )
            example = openapi_utils.generate_example(json_schema)
            schema_result.update(
                {
                    "body_schema": request_body,
                    "body_example": example,
                }
            )

        slz = self.get_serializer(schema_result)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=ReleaseInputSLZ,
        responses={status.HTTP_200_OK: ReleaseHistoryOutputSLZ()},
        tags=["WebAPI.Release"],
        operation_description="版本发布接口",
    ),
)
class ReleaseCreateApi(generics.CreateAPIView):
    serializer_class = ReleaseInputSLZ
    lookup_field = "id"

    def _check_resource_version_backend(self, resource_version_id: int) -> None:
        """检查资源版本的后端是否存在"""
        try:
            resource_version = ResourceVersion.objects.get(id=resource_version_id)
        except ResourceVersion.DoesNotExist:
            raise error_codes.NOT_FOUND.format(_("资源版本不存在"))

        backend_to_resources = defaultdict(list)
        for resource_data in resource_version.data:
            backend_id = resource_data.get("proxy", {}).get("backend_id", None)
            if backend_id:
                backend_to_resources[backend_id].append(resource_data["name"])

        exist_backend_ids = set(
            Backend.objects.filter(id__in=backend_to_resources.keys()).values_list("id", flat=True)
        )

        not_exist_backend_ids = set(backend_to_resources.keys()) - exist_backend_ids
        if not_exist_backend_ids:
            resource_names = []
            for backend_id in not_exist_backend_ids:
                resource_names.extend(backend_to_resources[backend_id])

            raise error_codes.NOT_FOUND.format(
                _("资源【{}】对应的后端服务不存在，不可发布".format(", ".join(resource_names)))
            )

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    def create(self, request, *args, **kwargs):
        slz = ReleaseInputSLZ(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        # 发布加锁
        stage_id = slz.validated_data["stage_id"]
        gateway_id = request.gateway.id

        resource_version_id = slz.validated_data["resource_version_id"]
        if resource_version_id:
            self._check_resource_version_backend(resource_version_id)

        try:
            with Lock(
                f"{gateway_id}_{stage_id}",
                timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
                try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
            ):
                history = release(
                    gateway=request.gateway,
                    stage_id=slz.validated_data["stage_id"],
                    resource_version_id=resource_version_id,
                    comment=slz.validated_data.get("comment", ""),
                    username=request.user.username,
                )
        except LockTimeout as err:
            logger.exception("retrieve lock timeout")
            return FailJsonResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR, code="UNKNOWN", message=str(err))
        except ReleaseError as err:
            logger.exception("release failed.")
            return FailJsonResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR, code="UNKNOWN", message=str(err))

        slz = ReleaseHistoryOutputSLZ(
            history,
            context={
                "release_history_events_map": PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
                    [history.id]
                ),
            },
        )
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=ReleaseHistoryQueryInputSLZ(),
        responses={status.HTTP_200_OK: ReleaseHistoryOutputSLZ(many=True)},
        tags=["WebAPI.Release"],
        operation_description="发布历史列表获取接口",
    ),
)
class ReleaseHistoryListApi(generics.ListAPIView):
    serializer_class = ReleaseHistoryOutputSLZ

    def get_queryset(self):
        return ReleaseHistory.objects.filter(gateway=self.request.gateway)

    def list(self, request, *args, **kwargs):
        slz = ReleaseHistoryQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = ReleaseHistory.objects.filter_release_history(
            gateway=request.gateway,
            query=data.get("keyword"),
            stage_id=data.get("stage_id"),
            created_by=data.get("created_by"),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
            order_by="-created_time",
            fuzzy=True,
        )
        page = self.paginate_queryset(queryset)

        slz = self.get_serializer(
            page,
            many=True,
            context={
                "release_history_events_map": PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
                    [release_history.id for release_history in page]
                ),
            },
        )
        return self.get_paginated_response(slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=ReleaseHistoryQueryInputSLZ(),
        responses={status.HTTP_200_OK: DeployHistoryOutputSLZ(many=True)},
        tags=["WebAPI.Release"],
        operation_description="编程部署历史列表获取接口",
    ),
)
class DeployHistoryListApi(generics.ListAPIView):
    serializer_class = DeployHistoryOutputSLZ

    def get_queryset(self):
        return ProgrammableGatewayDeployHistory.objects.filter(gateway=self.request.gateway)

    def list(self, request, *args, **kwargs):
        slz = ReleaseHistoryQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        queryset = ProgrammableGatewayDeployHistory.objects.filter_deploy_history(
            gateway=request.gateway,
            query=data.get("keyword"),
            stage_id=data.get("stage_id"),
            created_by=data.get("created_by"),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
            order_by="-created_time",
            fuzzy=True,
        )
        page = self.paginate_queryset(queryset)
        slz = self.get_serializer(
            page,
            many=True,
            context={
                "release_history_events_map": PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
                    [deploy_history.publish_id for deploy_history in page if deploy_history.publish_id]
                )
            },
        )
        return self.get_paginated_response(slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: ReleaseHistoryOutputSLZ()},
        tags=["WebAPI.Release"],
        operation_description="发布详情接口",
    ),
)
class ReleaseHistoryRetrieveApi(generics.RetrieveAPIView):
    serializer_class = ReleaseHistoryOutputSLZ

    def get_queryset(self):
        return ReleaseHistory.objects.filter(gateway=self.request.gateway)

    def retrieve(self, request, *args, **kwargs):
        try:
            # created_time 在极端情况下可能重复，因此，添加字段 id
            instance = ReleaseHistory.objects.filter(gateway=request.gateway).latest("created_time", "id")
        except ReleaseHistory.DoesNotExist:
            return OKJsonResponse(data={})

        slz_class = self.get_serializer_class()
        slz = slz_class(
            instance,
            context={
                "release_history_events_map": PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
                    [instance.id]
                ),
            },
        )
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: ReleaseHistoryEventRetrieveOutputSLZ()},
        tags=["WebAPI.Release"],
        operation_description="查询发布事件 (日志)",
    ),
)
class RelishHistoryEventsRetrieveAPI(generics.RetrieveAPIView):
    serializer_class = ReleaseHistoryEventRetrieveOutputSLZ
    lookup_url_kwarg = "history_id"

    def get_queryset(self):
        return ReleaseHistory.objects.filter(gateway=self.request.gateway)

    def retrieve(self, request, *args, **kwargs):
        release_history = self.get_object()
        slz = self.get_serializer(
            release_history,
            context={
                "release_history_events": ReleaseHandler.list_publish_events_by_release_history_id(release_history.id),
                "release_history_events_map": PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
                    [release_history.id]
                ),
            },
        )
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=ProgrammableDeployCreateInputSLZ(),
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.Release"],
        operation_description="编程网关部署接口",
    ),
)
class ProgrammableDeployCreateApi(generics.CreateAPIView):
    serializer_class = ProgrammableDeployCreateInputSLZ

    def create(self, request, *args, **kwargs):
        if not request.gateway.is_programmable:
            raise error_codes.FAILED_PRECONDITION.format(_("当前网关类型不支持应用部署。"), replace=True)

        slz = ProgrammableDeployCreateInputSLZ(
            data=request.data,
            context={
                "gateway": request.gateway,
            },
        )

        slz.is_valid(raise_exception=True)

        deploy_id = ProgrammableGatewayReleaser.deploy(
            gateway=request.gateway,
            stage_id=slz.validated_data["stage_id"],
            branch=slz.validated_data["branch"],
            comment=slz.validated_data.get("comment", ""),
            commit_id=slz.validated_data.get("commit_id", ""),
            version=slz.validated_data.get("version", ""),
            username=request.user.username,
            version_type=slz.validated_data.get("version_type", ""),
            user_credentials=get_user_credentials_from_request(request),
        )

        return OKJsonResponse(data={"deploy_id": deploy_id})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.Release"],
        operation_description="编程网关 pass 部署详情查询",
    ),
)
class ProgrammableDeployRetrieveApi(generics.RetrieveAPIView):
    def get_queryset(self):
        return ProgrammableGatewayDeployHistory.objects.filter(gateway=self.request.gateway)

    def get(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), deploy_id=self.kwargs["deploy_id"])
        # 查询 pass 部署详情
        data = get_paas_deployment_result(
            app_code=request.gateway.name,
            module="default",
            deploy_id=instance.deploy_id,
            user_credentials=get_user_credentials_from_request(request),
        )
        return OKJsonResponse(data=data)


class BaseProgrammableDeployEventsRetrieveApi(generics.RetrieveAPIView):
    """部署事件查询基类"""

    serializer_class = ProgrammableDeployEventGetOutputSLZ

    def get_common_context(self, instance):
        """公共上下文数据准备"""
        user_credentials = get_user_credentials_from_request(self.request)

        events_framework = {}
        events_instance = {}
        deploy_result = {}
        events = []

        # 是否是下线
        is_offline = instance.source != PublishSourceEnum.VERSION_PUBLISH.value

        # 获取发布历史事件
        release_history = ReleaseHistory.objects.filter(id=instance.publish_id).first()
        if not is_offline:
            # 获取部署阶段框架数据
            events_framework = get_paas_deploy_phases_framework(
                app_code=self.request.gateway.name,
                module="default",
                env=instance.stage.name,
                user_credentials=user_credentials,
            )
            # 获取部署实例阶段数据
            events_instance = get_paas_deploy_phases_instance(
                app_code=self.request.gateway.name,
                env=instance.stage.name,
                module="default",
                deploy_id=instance.deploy_id,
                user_credentials=user_credentials,
            )
            # 获取部署事件流数据
            events = get_pass_deploy_streams_history_events(
                deploy_id=instance.deploy_id,
                user_credentials=user_credentials,
            )
            if len(events) == 0:
                # 如果 paas event 没有了，补充返回 result
                deploy_result = get_paas_deployment_result(
                    app_code=self.request.gateway.name,
                    module="default",
                    deploy_id=instance.deploy_id,
                    user_credentials=user_credentials,
                )
        else:
            deploy_result = get_paas_offline_result(
                app_code=self.request.gateway.name,
                module="default",
                deploy_id=instance.deploy_id,
                user_credentials=user_credentials,
            )

        release_history_events = []
        release_history_events_map = {}
        if release_history:
            release_history_events = ReleaseHandler.list_publish_events_by_release_history_id(release_history.id)
            release_history_events_map = PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
                [release_history.id]
            )
        return {
            "events_framework": events_framework,
            "events_instance": events_instance,
            "events": events,
            "deploy_result": deploy_result,
            "release_history_events": release_history_events,
            "release_history_events_map": release_history_events_map,
        }

    def build_response_data(self, instance):
        """构造响应数据"""
        release_history = ReleaseHistory.objects.filter(pk=instance.publish_id).first()
        slz = self.get_serializer(
            release_history
            or ReleaseHistory(
                stage=instance.stage,
                resource_version=ResourceVersion(version=instance.version, gateway=self.request.gateway),
            ),
            context=self.get_common_context(instance),
        )
        return slz.data


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_id="get_deploy_events_by_deploy_id",
        manual_parameters=[
            openapi.Parameter(
                name="deploy_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="部署任务 ID",
                required=True,
            )
        ],
        responses={status.HTTP_200_OK: ProgrammableDeployEventGetOutputSLZ()},
        tags=["WebAPI.Release"],
        operation_description="通过部署 ID 查询编程网关事件",
    ),
)
class DeployIdEventsRetrieveApi(BaseProgrammableDeployEventsRetrieveApi):
    serializer_class = ProgrammableDeployEventGetOutputSLZ

    def get_object(self):
        """通过 deploy_id 获取部署历史"""
        return get_object_or_404(
            ProgrammableGatewayDeployHistory.objects.filter(gateway=self.request.gateway),
            deploy_id=self.kwargs["deploy_id"],
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return OKJsonResponse(data=self.build_response_data(instance))


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_id="get_deploy_events_by_history_id",
        manual_parameters=[
            openapi.Parameter(
                name="history_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="发布历史 ID",
                required=True,
            )
        ],
        responses={status.HTTP_200_OK: ProgrammableDeployEventGetOutputSLZ()},
        tags=["WebAPI.Release"],
        operation_description="通过发布历史 ID 查询编程网关事件",
    ),
)
class HistoryIdEventsRetrieveApi(BaseProgrammableDeployEventsRetrieveApi):
    def get_object(self):
        """通过 history_id 获取部署历史"""
        # 再获取对应的部署记录
        return get_object_or_404(
            ProgrammableGatewayDeployHistory.objects.filter(gateway=self.request.gateway),
            publish_id=self.kwargs["history_id"],
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return OKJsonResponse(data=self.build_response_data(instance))
