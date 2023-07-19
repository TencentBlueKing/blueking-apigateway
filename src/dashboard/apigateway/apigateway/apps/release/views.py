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
from collections import defaultdict

from django.http import Http404
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.release import serializers
from apigateway.apps.release.releasers import ReleaseBatchManager, ReleaseError
from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.core.models import PublishEvent, Release, ReleasedResource, ReleaseHistory
from apigateway.utils.access_token import get_user_access_token_from_request
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class ReleaseViewSet(viewsets.GenericViewSet):
    serializer_class = None
    lookup_field = "stage_id"

    def get_queryset(self):
        return Release.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(tags=["Release"])
    def get_available_resources(self, request, *args, **kwargs):
        """
        用于在线调试时，获取环境下可用的资源列表
        """
        try:
            instance = self.get_object()
        except Http404:
            return OKJsonResponse(_("当前选择环境未发布版本，请先发布版本到该环境。"), data=[])

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
            return OKJsonResponse("OK", data=data)
        return OKJsonResponse(_("当前选择环境的发布版本中资源为空，请发布新版本到该环境。"), data=data)

    @swagger_auto_schema(tags=["Release"])
    def get_released_resource(self, request, resource_version_id: int, resource_id: int, *args, **kwargs):
        try:
            released_resource = ReleasedResource.objects.get(
                api_id=request.gateway.id,
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

        return OKJsonResponse("OK", data=resource_data)


class ReleaseBatchViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ReleaseBatchSLZ
    lookup_field = "id"

    def get_queryset(self):
        return Release.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        request_body=serializers.ReleaseBatchSLZ,
        responses={status.HTTP_200_OK: serializers.ReleaseHistorySLZ},
        tags=["Release"],
    )
    def release(self, request, *args, **kwargs):
        manager = ReleaseBatchManager(access_token=get_user_access_token_from_request(request))

        try:
            history = manager.release_batch(request.gateway, request.data, request.user.username)
        except ReleaseError as err:
            # 因设置了 transaction，views 中不能直接抛出异常，否则，将导致数据不会写入 db
            return FailJsonResponse(str(err))

        slz = serializers.ReleaseHistorySLZ(history)
        return OKJsonResponse("OK", data=slz.data)


class ReleaseHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ReleaseHistorySLZ

    def get_queryset(self):
        return ReleaseHistory.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.ReleaseHistoryQuerySLZ,
        responses={status.HTTP_200_OK: serializers.ReleaseHistorySLZ(many=True)},
        tags=["Release"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.ReleaseHistoryQuerySLZ(data=request.query_params)
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
        # 查询发布事件
        publish_ids = [release_history.id for release_history in page]
        publish_last_events = PublishEvent.objects.get_publish_events_by_publish_ids(publish_ids)
        for history in page:
            event = publish_last_events.get(history.id)
            if event:
                history.message = f"{event.name}:{event.status}"

        serializer = self.get_serializer(page, many=True)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(responses={status.HTTP_200_OK: serializers.ReleaseHistorySLZ}, tags=["Release"])
    def retrieve_latest(self, request, *args, **kwargs):
        try:
            # created_time 在极端情况下可能重复，因此，添加字段 id
            instance = ReleaseHistory.objects.filter(api=request.gateway).latest("created_time", "id")
        except ReleaseHistory.DoesNotExist:
            return OKJsonResponse("OK", data={})

        slz = self.get_serializer(instance)
        return OKJsonResponse("OK", data=slz.data)
