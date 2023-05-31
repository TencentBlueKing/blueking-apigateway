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

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.serializers import DateTimeField

from apigateway.apps.monitor import filters, serializers
from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.common.factories import SchemaFactory
from apigateway.common.mixins.views import ActionSerializerMixin
from apigateway.core.models import Gateway
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema
from apigateway.utils.time import now_datetime


class AlarmStrategyViewSet(ActionSerializerMixin, viewsets.ModelViewSet):
    serializer_class = serializers.AlarmStrategySLZ
    action_serializers = {
        "list": serializers.AlarmStrategyListSLZ,
        "update_status": serializers.AlarmStrategyUpdateStatusSLZ,
    }
    lookup_field = "id"

    def get_queryset(self):
        return AlarmStrategy.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["AlarmStrategy"],
    )
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

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.AlarmStrategyQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AlarmStrategyListSLZ(many=True)},
        tags=["AlarmStrategy"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.AlarmStrategyQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = AlarmStrategy.objects.filter_alarm_strategy(
            gateway=request.gateway,
            api_label_id=data.get("api_label_id"),
            query=data.get("query"),
            order_by=data.get("order_by") or "-id",
        )

        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["AlarmStrategy"],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        api_label_ids = slz.validated_data.pop("api_label_ids", [])

        slz.save(
            updated_by=request.user.username,
        )

        slz.instance.api_labels.set(api_label_ids)

        return OKJsonResponse("OK")

    @swagger_auto_schema(tags=["AlarmStrategy"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["AlarmStrategy"],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return OKJsonResponse("OK")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.AlarmStrategyUpdateStatusSLZ,
        tags=["AlarmStrategy"],
    )
    def update_status(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
            updated_time=now_datetime(),
        )

        return OKJsonResponse("OK")


class AlarmRecordViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.AlarmRecordSLZ
    filter_backends = [filters.AlarmRecordFilterBackend]
    lookup_field = "id"

    def get_queryset(self):
        return AlarmRecord.objects.all()

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.AlarmRecordQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AlarmRecordSLZ(many=True)},
        tags=["AlarmStrategy"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by("-id")

        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(tags=["AlarmStrategy"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse("OK", data=slz.data)


class AlarmRecordSummaryViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        query_serializer=serializers.AlarmRecordSummaryQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AlarmRecordSummarySLZ(many=True)},
        tags=["AlarmStrategy"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.AlarmRecordSummaryQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        # 1. get current user's gateways
        gateways = Gateway.objects.search_gateways(username=self.request.user.username, name=data.get("query"))
        gateway_id_map = {g.id: g for g in gateways}

        # 2. annotate alarm-record by strategy
        strategies = AlarmStrategy.objects.annotate_alarm_record_by_strategy(
            gateway_ids=gateway_id_map.keys(),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
        )

        # 3. annotate alarm-record by api
        api_alarmrecord_count_map = AlarmStrategy.objects.annotate_alarm_record_by_api(
            gateway_ids=gateway_id_map.keys(),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
        )

        # 4. summary
        results = self._statistics_api_alarm_record(strategies, api_alarmrecord_count_map, gateway_id_map)

        return OKJsonResponse("OK", data=results)

    def _statistics_api_alarm_record(self, strategies, api_alarmrecord_count_map, api_id_map):
        """
        统计网关下，各策略的告警信息
        """
        latest_alarm_record_ids = [s.latest_alarm_record_id for s in strategies]
        alarm_record_id_map = AlarmRecord.objects.in_bulk(latest_alarm_record_ids)

        api_summary_map = defaultdict(list)
        for strategy in strategies:
            alarm_record = alarm_record_id_map[strategy.latest_alarm_record_id]
            api_summary_map[strategy.api_id].append(
                {
                    "id": strategy.id,
                    "name": strategy.name,
                    "alarm_record_count": strategy.alarm_record_count,
                    "latest_alarm_record": {
                        "id": alarm_record.id,
                        "message": alarm_record.message,
                        "created_time": DateTimeField().to_representation(alarm_record.created_time),
                    },
                }
            )

        api_summary = []
        for api_id, summary in api_summary_map.items():
            api = api_id_map[api_id]
            api_summary.append(
                {
                    "api_id": api.id,
                    "api_name": api.name,
                    # 因为一个告警记录可能属于多条策略，因此将策略告警记录数量相加，并不等于网关告警记录数量
                    "alarm_record_count": api_alarmrecord_count_map.get(api.id, 0),
                    "strategy_summary": summary,
                }
            )

        return sorted(api_summary, key=lambda x: x["api_name"])
