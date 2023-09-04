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
from collections import defaultdict

from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.released_resource import ReleasedResourceDataHandler
from apigateway.biz.releaser import ReleaseBatchHandler, ReleaseError
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Release, ReleasedResource, ReleaseHistory
from apigateway.utils.access_token import get_user_access_token_from_request
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema

from .serializers import (
    PublishEventQueryOutputSLZ,
    ReleaseBatchInputSLZ,
    ReleaseHistoryOutputSLZ,
    ReleaseHistoryQueryInputSLZ,
)

logger = logging.getLogger(__name__)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(tags=["WebAPI.Release"]),
)
class ReleaseAvailableResourceListApi(generics.ListAPIView):
    serializer_class = None
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
            return FailJsonResponse(
                status=status.HTTP_404_NOT_FOUND,
                code=error_codes.NOT_FOUND,
                message=_("当前选择环境未发布版本，请先发布版本到该环境。"),
            )
        stage_name = instance.stage.name
        data = defaultdict(list)
        for resource in instance.resource_version.data:
            resource_data = ReleasedResourceDataHandler.from_data(resource)
            # 禁用环境时，去掉相应资源
            if resource_data.is_disabled_in_stage(stage_name):
                continue
            path_display = resource_data.path_display
            data[path_display].append(
                {
                    "id": resource_data.id,
                    "method": resource_data.method,
                    "path": path_display,
                    "match_subpath": resource_data.match_subpath,
                    "verified_user_required": resource_data.verified_user_required,
                }
            )

        if data:
            return OKJsonResponse(data=data)

        return FailJsonResponse(
            status=status.HTTP_404_NOT_FOUND,
            code=error_codes.NOT_FOUND,
            message=_("当前选择环境的发布版本中资源为空，请发布新版本到该环境"),
        )


class ReleasedResourceRetrieveApi(generics.RetrieveAPIView):
    lookup_field = "stage_id"

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    @method_decorator(
        name="get",
        decorator=swagger_auto_schema(tags=["WebAPI.Release"]),
    )
    def get(self, request, *args, **kwargs):
        try:
            resource_version_id = request.query_params.get("resource_version_id")
            resource_id = request.query_params.get("resource_id")
            released_resource = ReleasedResource.objects.get(
                gateway_id=request.gateway.id,
                resource_version_id=resource_version_id,
                resource_id=resource_id,
            )
        except ReleasedResource.DoesNotExist:
            raise Http404

        resource_data = released_resource.data
        resource_data.update(
            doc_updated_time=ReleasedResourceDoc.objects.get_doc_updated_time(
                gateway_id=request.gateway.id,
                resource_version_id=resource_version_id,
                resource_id=resource_id,
            )
        )
        return OKJsonResponse(data=resource_data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=ReleaseBatchInputSLZ,
        responses={status.HTTP_200_OK: ReleaseHistoryOutputSLZ()},
        tags=["WebAPI.Release"],
    ),
)
class ReleaseBatchCreateApi(generics.CreateAPIView):
    serializer_class = ReleaseBatchInputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    def create(self, request, *args, **kwargs):
        handler = ReleaseBatchHandler(access_token=get_user_access_token_from_request(request))

        try:
            slz = ReleaseBatchInputSLZ(data=request.data, context={"gateway": request.gateway})
            slz.is_valid(raise_exception=True)
            history = handler.release_batch(
                request.gateway,
                slz.validated_data["stage_ids"],
                slz.validated_data["resource_version_id"],
                slz.validated_data.get("comment", ""),
                request.user.username,
            )
        except ReleaseError as err:
            logger.exception("release failed.")
            # 因设置了 transaction，views 中不能直接抛出异常，否则，将导致数据不会写入 db
            return FailJsonResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR, code="UNKNOWN", message=str(err))

        slz = ReleaseHistoryOutputSLZ(
            history,
            context={
                "publish_events_map": ReleaseHandler.get_latest_publish_event_by_release_history_ids([history.id]),
            },
        )
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=ReleaseHistoryQueryInputSLZ(),
        responses={status.HTTP_200_OK: ReleaseHistoryOutputSLZ(many=True)},
        tags=["WebAPI.Release"],
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
            query=data.get("query"),
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
                "publish_events_map": ReleaseHandler.get_latest_publish_event_by_release_history_ids(
                    [release_history.id for release_history in page]
                ),
            },
        )
        return OKJsonResponse(data=self.paginator.get_paginated_data(slz.data))


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(responses={status.HTTP_200_OK: ReleaseHistoryOutputSLZ()}, tags=["WebAPI.Release"]),
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
                "publish_events_map": ReleaseHandler.get_latest_publish_event_by_release_history_ids([instance.id]),
            },
        )
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="查询发布事件(日志)",
        responses={status.HTTP_200_OK: PublishEventQueryOutputSLZ()},
        tags=["WebAPI.Release"],
    ),
)
class PublishEventsRetrieveAPI(generics.RetrieveAPIView):
    serializer_class = PublishEventQueryOutputSLZ
    lookup_url_kwarg = "publish_id"

    def get_queryset(self):
        return ReleaseHistory.objects.filter(gateway=self.request.gateway)

    def retrieve(self, request, *args, **kwargs):
        release_history = self.get_object()
        slz = self.get_serializer(
            release_history,
            context={
                "publish_events": ReleaseHandler.get_publish_events_by_release_history_id(release_history.id),
                "publish_events_map": ReleaseHandler.get_latest_publish_event_by_release_history_ids(
                    [release_history.id]
                ),
            },
        )
        return OKJsonResponse(data=slz.data)
