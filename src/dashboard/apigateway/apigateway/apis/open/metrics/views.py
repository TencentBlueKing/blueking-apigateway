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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.metrics.models import StatisticsAPIRequestByDay, StatisticsAppRequestByDay
from apigateway.core.models import Gateway
from apigateway.utils.responses import V1OKJsonResponse

from . import serializers


class StatisticsV1ViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StatisticsAPIRequestV1SLZ
    lookup_field = "id"
    gateway_permission_exempt = True

    @swagger_auto_schema(
        query_serializer=serializers.StatisticsAPIRequestQueryV1SLZ,
        responses={status.HTTP_200_OK: None},
        tags=["OpenAPI.Metrics"],
    )
    def query_api_metrics(self, request, *args, **kwargs):
        slz = serializers.StatisticsAPIRequestQueryV1SLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        start_time = slz.validated_data["start_time"]
        end_time = slz.validated_data["end_time"]

        # 获取网关请求数据
        api_request_data = StatisticsAPIRequestByDay.objects.filter_and_aggregate_by_gateway(
            start_time=start_time,
            end_time=end_time,
        )

        # 获取应用请求数据
        app_request_data = StatisticsAppRequestByDay.objects.filter_app_and_aggregate_by_gateway(
            start_time=start_time,
            end_time=end_time,
        )

        # 获取网关
        gateway_id_map = {gateway.id: gateway for gateway in Gateway.objects.filter(id__in=api_request_data.keys())}

        slz = serializers.StatisticsAPIRequestV1SLZ(
            api_request_data.values(),
            many=True,
            context={
                "app_request_data": app_request_data,
                "api_id_map": gateway_id_map,
            },
        )

        return V1OKJsonResponse("OK", data=slz.data)
