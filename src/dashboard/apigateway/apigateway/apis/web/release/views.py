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
from rest_framework import generics, status

from apigateway.apis.web.release import serializers
from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.biz.releasers import ReleaseBatchManager, ReleaseError
from apigateway.core.models import PublishEvent, Release, ReleasedResource, ReleaseHistory
from apigateway.utils.access_token import get_user_access_token_from_request
from apigateway.utils.responses import V1FailJsonResponse, V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class ReleaseAvailableResourceListApi(generics.ListAPIView):
    serializer_class = None
    lookup_field = "stage_id"

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(tags=["WebAPI.Release"])
    def list(self, request, *args, **kwargs):
        """
        用于在线调试时，获取环境下可用的资源列表
        """
        try:
            instance = self.get_object()
        except Http404:
            return V1OKJsonResponse(_("当前选择环境未发布版本，请先发布版本到该环境。"), data=[])

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
            return V1OKJsonResponse("OK", data=data)
        return V1OKJsonResponse(_("当前选择环境的发布版本中资源为空，请发布新版本到该环境。"), data=data)


class ReleasedResourceGetApi(generics.RetrieveAPIView):
    serializer_class = None
    lookup_field = "stage_id"

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(tags=["WebAPI.Release"])
    def get(self, request, resource_version_id: int, resource_id: int, *args, **kwargs):
        try:
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
        return V1OKJsonResponse("OK", data=resource_data)


class ReleaseBatchCreateApi(generics.CreateAPIView):
    serializer_class = serializers.ReleaseBatchInputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return Release.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(
        request_body=serializers.ReleaseBatchInputSLZ,
        responses={status.HTTP_200_OK: serializers.ReleaseHistoryOutputSLZ()},
        tags=["Web.Release"],
    )
    def create(self, request, *args, **kwargs):
        manager = ReleaseBatchManager(access_token=get_user_access_token_from_request(request))

        try:
            history = manager.release_batch(request.gateway, request.data, request.user.username)
        except ReleaseError as err:
            # 因设置了 transaction，views 中不能直接抛出异常，否则，将导致数据不会写入 db
            return V1FailJsonResponse(str(err))

        slz = serializers.ReleaseHistoryOutputSLZ(history)
        return V1OKJsonResponse("OK", data=slz.data)


class ReleaseHistoryListViewSet(generics.ListAPIView):
    serializer_class = serializers.ReleaseHistoryOutputSLZ

    def get_queryset(self):
        return ReleaseHistory.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.ReleaseHistoryQueryInputSLZ(),
        responses={status.HTTP_200_OK: serializers.ReleaseHistoryOutputSLZ(many=True)},
        tags=["Web.Release"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.ReleaseHistoryQueryInputSLZ(data=request.query_params)
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

        # 查询发布事件,填充message为最后一个发布事件的状态信息
        publish_ids = [release_history.id for release_history in page]

        # 发布事件dict：key：publish_id,value: 最后一个事件
        # 需要按照 "publish_id", "step", "status" 升序(django默认 ASC)排列,正确排列每个事件节点的不同状态事件
        publish_events = PublishEvent.objects.filter(publish_id__in=publish_ids).order_by(
            "publish_id", "step", "status"
        )
        publish_last_event = dict((event.publish_id, event) for event in publish_events)

        for history in page:
            event = publish_last_event.get(history.id)
            if event:
                history.message = f"{event.name}:{event.status}"

        serializer = self.get_serializer(page, many=True)
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))


class ReleaseHistoryRetrieveApi(generics.RetrieveAPIView):
    serializer_class = serializers.ReleaseHistoryOutputSLZ

    def get_queryset(self):
        return ReleaseHistory.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ReleaseHistoryOutputSLZ()}, tags=["WebAPI.Release"]
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            # created_time 在极端情况下可能重复，因此，添加字段 id
            instance = ReleaseHistory.objects.filter(gateway=request.gateway).latest("created_time", "id")
        except ReleaseHistory.DoesNotExist:
            return V1OKJsonResponse("OK", data={})

        slz = self.get_serializer(instance)
        return V1OKJsonResponse("OK", data=slz.data)
