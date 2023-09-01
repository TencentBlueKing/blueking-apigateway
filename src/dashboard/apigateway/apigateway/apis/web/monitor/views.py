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


from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.biz.monitor import ResourceMonitorHandler
from apigateway.common.factories import SchemaFactory
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema
from apigateway.utils.time import now_datetime

from . import filters
from .serializers import (
    AlarmRecordQueryInputSLZ,
    AlarmRecordQueryOutputSLZ,
    AlarmRecordSummaryQueryInputSLZ,
    AlarmRecordSummaryQueryOutputSLZ,
    AlarmStrategyInputSLZ,
    AlarmStrategyListOutputSLZ,
    AlarmStrategyQueryInputSLZ,
    AlarmStrategyUpdateStatusInputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=AlarmStrategyQueryInputSLZ,
        responses={status.HTTP_200_OK: AlarmStrategyListOutputSLZ(many=True)},
        tags=["WebAPI.Monitor"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        responses={status.HTTP_201_CREATED: ""},
        tags=["WebAPI.Monitor"],
    ),
)
class AlarmStrategyListCreateApi(generics.ListCreateAPIView):
    serializer_class = AlarmStrategyInputSLZ

    def get_queryset(self):
        return AlarmStrategy.objects.filter(api=self.request.gateway)

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        api_label_ids = slz.validated_data.pop("api_label_ids", [])

        slz.save(
            created_by=request.user.username,
            schema=SchemaFactory().get_monitor_alarm_strategy_schema(),
        )

        # 存储关联的标签
        slz.instance.api_labels.set(api_label_ids)

        return OKJsonResponse(status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        slz = AlarmStrategyQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = AlarmStrategy.objects.filter_alarm_strategy(
            gateway=request.gateway,
            api_label_id=data.get("api_label_id"),
            query=data.get("query"),
            order_by=data.get("order_by") or "-id",
        )

        page = self.paginate_queryset(queryset)
        serializer = AlarmStrategyListOutputSLZ(page, many=True)
        return OKJsonResponse(data=self.paginator.get_paginated_data(serializer.data))


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["WebAPI.monitor"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Monitor"],
    ),
)
@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Monitor"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Monitor"],
    ),
)
class AlarmStrategyRetrieveUpdateDestroyApi(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AlarmStrategyInputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return AlarmStrategy.objects.filter(api=self.request.gateway)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        api_label_ids = slz.validated_data.pop("api_label_ids", [])

        slz.save(
            updated_by=request.user.username,
        )

        slz.instance.api_labels.set(api_label_ids)

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse(data=slz.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=AlarmStrategyUpdateStatusInputSLZ,
        tags=["WebAPI.monitor"],
    ),
)
@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=AlarmStrategyUpdateStatusInputSLZ,
        tags=["WebAPI.monitor"],
    ),
)
class AlarmStrategyUpdateStatusApi(generics.UpdateAPIView):
    lookup_field = "id"

    serializer_class = AlarmStrategyUpdateStatusInputSLZ

    def get_queryset(self):
        return AlarmStrategy.objects.filter(api=self.request.gateway)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
            updated_time=now_datetime(),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=AlarmRecordQueryInputSLZ,
        responses={status.HTTP_200_OK: AlarmRecordQueryOutputSLZ(many=True)},
        tags=["WebAPI.Monitor"],
    ),
)
class AlarmRecordListApi(generics.ListAPIView):
    serializer_class = AlarmRecordQueryOutputSLZ
    filter_backends = [filters.AlarmRecordFilterBackend]

    def get_queryset(self):
        return AlarmRecord.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by("-id")

        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)
        return OKJsonResponse(data=self.paginator.get_paginated_data(serializer.data))


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: AlarmRecordQueryOutputSLZ()},
        tags=["WebAPI.Monitor"],
    ),
)
class AlarmRecordRetrieveApi(generics.RetrieveAPIView):
    serializer_class = AlarmRecordQueryOutputSLZ
    filter_backends = [filters.AlarmRecordFilterBackend]

    lookup_field = "id"

    def get_queryset(self):
        return AlarmRecord.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=AlarmRecordSummaryQueryInputSLZ,
        responses={status.HTTP_200_OK: AlarmRecordSummaryQueryOutputSLZ(many=True)},
        tags=["WebAPI.Monitor"],
    ),
)
class AlarmRecordSummaryListApi(generics.ListAPIView):
    def get_queryset(self):
        return AlarmRecord.objects.all()

    def list(self, request, *args, **kwargs):
        slz = AlarmRecordSummaryQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        results = ResourceMonitorHandler.statistics_api_alarm_record(
            username=self.request.user.username,
            name=data.get("query"),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
        )

        return OKJsonResponse(data=results)
