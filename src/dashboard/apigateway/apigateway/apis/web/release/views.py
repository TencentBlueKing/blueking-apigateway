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

from django.conf import settings
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.biz.release import ReleaseHandler
from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.biz.releaser import ReleaseError, Releaser
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Release, ReleaseHistory
from apigateway.utils.access_token import get_user_access_token_from_request
from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import Lock
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse

from .serializers import (
    ReleaseHistoryEventRetrieveOutputSLZ,
    ReleaseHistoryOutputSLZ,
    ReleaseHistoryQueryInputSLZ,
    ReleaseInputSLZ,
)

logger = logging.getLogger(__name__)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["WebAPI.Release"], operation_description="获取环境下可用的资源列表接口(在线调试)"
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
        data = defaultdict(list)
        for resource in instance.resource_version.data:
            resource_data = ReleasedResourceData.from_data(resource)
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

        raise error_codes.NOT_FOUND.format(_("当前选择环境未发布版本，请先发布版本到该环境。"))


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

        releaser = Releaser(access_token=get_user_access_token_from_request(request))
        try:
            with Lock(
                f"{gateway_id}_{stage_id}",
                timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
                try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
            ):
                history = releaser.release(
                    request.gateway,
                    slz.validated_data["stage_id"],
                    slz.validated_data["resource_version_id"],
                    slz.validated_data.get("comment", ""),
                    request.user.username,
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
                "release_history_events_map": ReleaseHandler.get_release_history_id_to_latest_publish_event_map(
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
                "release_history_events_map": ReleaseHandler.get_release_history_id_to_latest_publish_event_map(
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
                "release_history_events_map": ReleaseHandler.get_release_history_id_to_latest_publish_event_map(
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
                "release_history_events_map": ReleaseHandler.get_release_history_id_to_latest_publish_event_map(
                    [release_history.id]
                ),
            },
        )
        return OKJsonResponse(data=slz.data)
