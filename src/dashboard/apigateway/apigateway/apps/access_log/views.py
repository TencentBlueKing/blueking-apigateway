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
import random
import time
import urllib

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView

from apigateway.apps.access_log.constants import ES_LOG_FIELDS, LOG_LINK_EXPIRE_SECONDS, LOG_SHARED_LINK_PATH
from apigateway.apps.access_log.helpers import DataScrubber, get_es_client_class
from apigateway.apps.access_log.serializers import (
    LogDetailQuerySerializer,
    LogLinkSerializer,
    LogSerializer,
    SearchLogQuerySerializer,
    TimeChartSerializer,
)
from apigateway.common.signature import SignatureGenerator, SignatureValidator
from apigateway.core.models import Stage
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class BaseLogAPIView(APIView):
    def _generate_client(self, request, serializer_class):
        slz = serializer_class(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        stage = get_object_or_404(Stage, api=request.gateway, id=data["stage_id"])

        client_class = get_es_client_class()
        client = client_class(
            api_id=request.gateway.id,
            stage_name=stage.name,
            query=data.get("query"),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
            time_range=data.get("time_range"),
        )
        return client, data


class LogTimeChartAPIView(BaseLogAPIView):
    @swagger_auto_schema(
        query_serializer=SearchLogQuerySerializer,
        responses={status.HTTP_200_OK: TimeChartSerializer()},
        tags=["AccessLog"],
    )
    def get(self, request, *args, **kwargs):
        client, _ = self._generate_client(request, SearchLogQuerySerializer)
        data = client.get_time_chart()
        return OKJsonResponse("OK", data=data)


class SearchLogsAPIView(BaseLogAPIView):
    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=SearchLogQuerySerializer,
        responses={status.HTTP_200_OK: LogSerializer(many=True)},
        tags=["AccessLog"],
    )
    def get(self, request, *args, **kwargs):
        client, data = self._generate_client(request, SearchLogQuerySerializer)
        total_count, logs = client.search_logs(
            offset=data["offset"],
            limit=data["limit"],
        )

        # 去除params、body中的敏感数据
        logs = DataScrubber().scrub_sensitive_data(logs)
        # 添加扩展数据
        logs = self._add_extend_fields(logs)

        paginator = LimitOffsetPaginator(total_count, data["offset"], data["limit"])

        # 将字段信息添加到结果中，便于前端展示
        results = paginator.get_paginated_data(logs)
        results["fields"] = ES_LOG_FIELDS

        return OKJsonResponse("OK", data=results)

    def _add_extend_fields(self, logs):
        """为日志添加扩展字段"""
        for log in logs:
            if log.get("error"):
                log["response_desc"] = _("网关未请求或请求后端接口异常，响应内容由网关提供。")
            else:
                log["response_desc"] = _("网关已请求后端接口，并将其响应原样返回。")

        return logs


class LogViewSet(viewsets.GenericViewSet):

    api_permission_exempt = False

    def _generate_client(self, request, request_id):
        client_class = get_es_client_class()
        client = client_class(
            request_id=request_id,
        )
        return client

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=LogDetailQuerySerializer,
        responses={status.HTTP_200_OK: LogSerializer(many=True)},
        tags=["AccessLog"],
    )
    def retrieve(self, request, request_id, *args, **kwargs):
        """
        获取指定 request_id 的日志内容
        """
        validator = SignatureValidator(settings.LOG_LINK_SECRET, request, LOG_LINK_EXPIRE_SECONDS)
        validator.is_valid(raise_exception=True)

        client = self._generate_client(request, request_id)

        total_count, logs = client.search_logs()
        # 去除params、body中的敏感数据
        logs = DataScrubber().scrub_sensitive_data(logs)

        paginator = LimitOffsetPaginator(total_count, 0, total_count)

        # 将字段信息添加到结果中，便于前端展示
        results = paginator.get_paginated_data(logs)
        results["fields"] = ES_LOG_FIELDS

        return OKJsonResponse("OK", data=results)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: LogLinkSerializer()},
        tags=["AccessLog"],
    )
    def link(self, request, request_id, *args, **kwargs):
        """
        获取指定 request_id 日志的分享链接
        """
        shared_link_path = LOG_SHARED_LINK_PATH.format(
            api_id=request.gateway.id,
            request_id=request_id,
        )

        log_detail_path = reverse(
            "access_log.logs.detail",
            kwargs={
                "gateway_id": request.gateway.id,
                "request_id": request_id,
            },
        )

        params = {
            "bk_timestamp": int(time.time()),
            "bk_nonce": random.randint(1, 999999),
            "shared_by": request.user.username,
        }
        params["bk_signature"] = SignatureGenerator(settings.LOG_LINK_SECRET).generate_signature(
            "GET", log_detail_path, params
        )
        query_str = urllib.parse.urlencode(params)

        apigw_domain = getattr(settings, "DASHBOARD_FE_URL", "").rstrip("/")

        return OKJsonResponse("OK", data={"link": f"{apigw_domain}{shared_link_path}?{query_str}"})
