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
import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from openapi_schema_to_json_schema import to_json_schema
from rest_framework import generics, status

from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.biz.releaser import ProgramGatewayReleaser, ReleaseError, release
from apigateway.biz.resource_label import ResourceLabelHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.error_codes import error_codes
from apigateway.components.paas import (
    get_paas_deploy_phases_framework,
    get_paas_deploy_phases_instance,
    get_paas_deployment_result,
    get_pass_deploy_streams_history_events,
)
from apigateway.core.models import PublishEvent, Release, ReleaseHistory
from apigateway.utils import openapi
from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import Lock
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse
from apigateway.utils.user_credentials import get_user_credentials_from_request

from .serializers import (
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
        operation_description="获取环境下可用的资源列表接口(在线调试)",
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
        operation_description="获取环境下可用的某个资源接口schema(在线调试)",
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
        用于在线调试时，获取某个资源的schema数据,以及自动生成 request_body example
        """
        try:
            instance = self.get_object()
        except Http404:
            raise error_codes.NOT_FOUND.format(_("当前选择环境未发布版本，请先发布版本到该环境。"))

        resource_id = self.kwargs["resource_id"]
        schema_result = {"resource_id": resource_id}

        # 获取对应资源的schema
        schema = ResourceVersionHandler.get_resource_schema(instance.resource_version.id, resource_id)
        schema_result["parameter_schema"] = schema.get("parameters", [])
        schema_result["response_schema"] = schema.get("responses", {})
        request_body = schema.get("requestBody")
        if request_body and "content" in request_body and "application/json" in request_body["content"]:
            # todo: 暂时在只支持application/json
            json_schema = to_json_schema(
                request_body["content"]["application/json"]["schema"], {"keepNotSupported": ["example"]}
            )
            example = openapi.generate_example(json_schema)
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

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    def create(self, request, *args, **kwargs):
        slz = ReleaseInputSLZ(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        # 发布加锁
        stage_id = slz.validated_data["stage_id"]
        gateway_id = request.gateway.id

        try:
            with Lock(
                f"{gateway_id}_{stage_id}",
                timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
                try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
            ):
                history = release(
                    gateway=request.gateway,
                    stage_id=slz.validated_data["stage_id"],
                    resource_version_id=slz.validated_data["resource_version_id"],
                    comment=slz.validated_data.get("comment", ""),
                    username=request.user.username,
                    user_credentials=get_user_credentials_from_request(request),
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
        operation_description="查询发布事件(日志)",
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

        slz = ProgrammableDeployCreateInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        deploy_id = ProgramGatewayReleaser.deploy(
            gateway=request.gateway,
            stage_id=slz.validated_data["stage_id"],
            branch=slz.validated_data["branch"],
            comment=slz.validated_data.get("comment", ""),
            commit_id=slz.validated_data.get("commit_id", ""),
            version=slz.validated_data.get("version", ""),
            username=request.user.username,
            user_credentials=get_user_credentials_from_request(request),
        )

        return OKJsonResponse(data={"deploy_id": deploy_id})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.Release"],
        operation_description="编程网关pass部署详情查询",
    ),
)
class ProgrammableDeployRetrieveApi(generics.RetrieveAPIView):
    def get_queryset(self):
        return ProgrammableGatewayDeployHistory.objects.filter(gateway=self.request.gateway)

    def get(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), deploy_id=self.kwargs["deploy_id"])
        # 查询pass部署详情
        data = get_paas_deployment_result(
            app_code=request.gateway.name,
            module="default",
            deploy_id=instance.deploy_id,
            user_credentials=get_user_credentials_from_request(request),
        )
        return OKJsonResponse(data=data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: ProgrammableDeployEventGetOutputSLZ()},
        tags=["WebAPI.Release"],
        operation_description="编程网关pass部署event查询",
    ),
)
class ProgrammableDeployEventsRetrieveApi(generics.RetrieveAPIView):
    serializer_class = ProgrammableDeployEventGetOutputSLZ

    def get_queryset(self):
        return ProgrammableGatewayDeployHistory.objects.filter(gateway=self.request.gateway)

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), deploy_id=self.kwargs["deploy_id"])
        # 查询pass部署步骤框架
        user_credentials = get_user_credentials_from_request(request)
        events_framework = get_paas_deploy_phases_framework(
            app_code=request.gateway.name,
            module="default",
            env=instance.stage.name,
            user_credentials=user_credentials,
        )

        # 查询pass部署实例步骤
        events_instance = get_paas_deploy_phases_instance(
            app_code=request.gateway.name,
            env=instance.stage.name,
            module="default",
            deploy_id=instance.deploy_id,
            user_credentials=user_credentials,
        )
        # 查询pass部署事件
        events = get_pass_deploy_streams_history_events(
            deploy_id=instance.deploy_id,
            user_credentials=user_credentials,
        )

        slz_class = self.get_serializer_class()
        slz = slz_class(
            instance,
            context={"events_framework": events_framework, "events_instance": events_instance, "events": events},
        )
        return OKJsonResponse(data=slz.data)
