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
from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView

from apigateway.components.prometheus import prometheus_component
from apigateway.core.models import Stage
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.time import SmartTimeRange

from . import serializers
from .helpers import DimensionMetricsManager


class QueryRangeAPIView(APIView):
    def _get_stage(self, stage_id):
        try:
            return Stage.objects.get(api=self.request.gateway, id=stage_id)
        except Stage.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        query_serializer=serializers.MetricsQuerySLZ,
        responses={status.HTTP_200_OK: serializers.PrometheusMatrixDataSLZ},
        tags=["Metrics"],
    )
    def get(self, request, *args, **kwargs):
        slz = serializers.MetricsQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        smart_time_range = SmartTimeRange(
            data.get("time_start"),
            data.get("time_end"),
            data.get("time_range"),
        )
        time_start, time_end = smart_time_range.get_head_and_tail()
        step = smart_time_range.get_interval()

        # generate query expression
        metrics = DimensionMetricsManager.create_dimension_metrics(data["dimension"], data["metrics"])
        query_expression = metrics.get_query_expression(
            gateway_id=request.gateway.id,
            stage_name=self._get_stage(data["stage_id"]).name,
            resource_id=data.get("resource_id"),
            step=step,
        )

        # request prometheus http api to get metrics data
        data = prometheus_component.query_range(
            query=query_expression,
            start=time_start,
            end=time_end,
            step=step,
        )

        return OKJsonResponse("OK", data=data.dict())
