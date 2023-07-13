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

from apigateway.apps.metrics import serializers
from apigateway.apps.metrics.dimension_metrics import DimensionMetricsFactory
from apigateway.apps.metrics.utils import MetricsSmartTimeRange
from apigateway.core.models import Resource, Stage
from apigateway.utils.responses import OKJsonResponse


class QueryRangeAPIView(APIView):
    @swagger_auto_schema(
        query_serializer=serializers.MetricsQuerySLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Metrics"],
    )
    def get(self, request, *args, **kwargs):
        slz = serializers.MetricsQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        stage_name = Stage.objects.get_name(request.gateway.id, data["stage_id"])
        if not stage_name:
            raise Http404

        resource_name = None
        if data.get("resource_id"):
            resource_name = Resource.objects.get_name(request.gateway.id, data["resource_id"])

        smart_time_range = MetricsSmartTimeRange(
            data.get("time_start"),
            data.get("time_end"),
            data.get("time_range"),
        )
        time_start, time_end = smart_time_range.get_head_and_tail()
        step = smart_time_range.get_recommended_step()

        metrics = DimensionMetricsFactory.create_dimension_metrics(data["dimension"], data["metrics"])
        data = metrics.query_range(
            gateway_name=request.gateway.name,
            stage_name=stage_name,
            resource_name=resource_name,
            start=time_start,
            end=time_end,
            step=step,
        )

        return OKJsonResponse("OK", data=data)
