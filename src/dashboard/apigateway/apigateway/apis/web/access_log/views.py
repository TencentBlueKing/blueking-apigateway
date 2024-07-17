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
from typing import Dict, List
from urllib.parse import urlencode

from django.conf import settings
from django.http import Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.biz.access_log.constants import ES_LOG_FIELDS, LOG_LINK_SHARED_PATH
from apigateway.biz.access_log.data_scrubber import DataScrubber
from apigateway.biz.access_log.log_search import LogSearchClient
from apigateway.common.signature import SignatureGenerator
from apigateway.core.models import Stage
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    LogDetailQueryInputSLZ,
    LogLinkOutputSLZ,
    RequestLogOutputSLZ,
    RequestLogQueryInputSLZ,
    TimeChartOutputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=RequestLogQueryInputSLZ,
        responses={status.HTTP_200_OK: TimeChartOutputSLZ()},
        tags=["WebAPI.Log"],
    ),
)
class LogTimeChartRetrieveApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        slz = RequestLogQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        stage_name = Stage.objects.get_name(request.gateway.id, data["stage_id"])
        if not stage_name:
            raise Http404

        client = LogSearchClient(
            gateway_id=request.gateway.id,
            stage_name=stage_name,
            resource_id=data.get("resource_id"),
            query=data.get("query"),
            include_conditions=data.get("include_conditions"),
            exclude_conditions=data.get("exclude_conditions"),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
            time_range=data.get("time_range"),
        )
        slz = TimeChartOutputSLZ(instance=client.get_time_chart())
        return OKJsonResponse(data=slz.data)


def add_or_refine_fields(logs: List[Dict]):
    """为日志添加扩展字段"""
    for log in logs:
        if log.get("error"):
            log["response_desc"] = _("网关未请求或请求后端接口异常，响应内容由网关提供。")
        else:
            log["response_desc"] = _("网关已请求后端接口，并将其响应原样返回。")

        if log.get("status") == 200 and log.get("response_body") == "":
            log["response_body"] = _("当状态码为 200 时，不记录响应正文")

    return logs


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: RequestLogOutputSLZ(many=True)},
        tags=["WebAPI.Log"],
    ),
)
class SearchLogListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        slz = RequestLogQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        stage_name = Stage.objects.get_name(request.gateway.id, data["stage_id"])
        if not stage_name:
            raise Http404

        client = LogSearchClient(
            gateway_id=request.gateway.id,
            stage_name=stage_name,
            resource_id=data.get("resource_id"),
            query=data.get("query"),
            include_conditions=data.get("include_conditions"),
            exclude_conditions=data.get("exclude_conditions"),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
            time_range=data.get("time_range"),
        )
        total_count, logs = client.search_logs(
            offset=data["offset"],
            limit=data["limit"],
        )

        # 去除 params、body 中的敏感数据
        logs = DataScrubber().scrub_sensitive_data(logs)
        # 添加扩展数据
        logs = add_or_refine_fields(logs)

        paginator = LimitOffsetPaginator(total_count, data["offset"], data["limit"])

        # 将字段信息添加到结果中，便于前端展示
        results = paginator.get_paginated_data(logs)
        results["fields"] = ES_LOG_FIELDS

        return OKJsonResponse(data=results)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=LogDetailQueryInputSLZ,
        responses={status.HTTP_200_OK: RequestLogOutputSLZ(many=False)},
        tags=["WebAPI.Log"],
    ),
)
class LogDetailRetrieveApi(generics.RetrieveAPIView):
    # 打开分享日志链接的，可能不是网关负责人，因此去除权限校验
    gateway_permission_exempt = True

    def retrieve(self, request, request_id, *args, **kwargs):
        """
        获取指定 request_id 的日志内容
        """
        client = LogSearchClient(request_id=request_id)

        total_count, logs = client.search_logs()
        # 去除 params、body 中的敏感数据
        logs = DataScrubber().scrub_sensitive_data(logs)
        logs = add_or_refine_fields(logs)

        paginator = LimitOffsetPaginator(total_count, 0, total_count)

        # 将字段信息添加到结果中，便于前端展示
        results = paginator.get_paginated_data(logs)
        results["fields"] = ES_LOG_FIELDS

        return OKJsonResponse(data=results)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: LogLinkOutputSLZ()},
        tags=["WebAPI.Log"],
    ),
)
class LogLinkRetrieveApi(generics.RetrieveAPIView):
    gateway_permission_exempt = False

    def retrieve(self, request, request_id, *args, **kwargs):
        """
        获取指定 request_id 日志的分享链接
        """
        shared_link_path = LOG_LINK_SHARED_PATH.format(gateway_id=request.gateway.id, request_id=request_id)
        query_string = self._get_query_string(request.user.username, request.gateway.id, request_id)
        slz = LogLinkOutputSLZ(instance={"link": f"{settings.DASHBOARD_FE_URL}{shared_link_path}?{query_string}"})
        return OKJsonResponse(data=slz.data)

    def _get_query_string(self, username: str, gateway_id: int, request_id: str):
        params = {
            "bk_timestamp": int(time.time()),
            "bk_nonce": random.randint(1, 999999),
            "shared_by": username,
        }

        log_detail_path = reverse(
            "access_log.logs.detail",
            kwargs={"gateway_id": gateway_id, "request_id": request_id},
        )
        params["bk_signature"] = SignatureGenerator(settings.LOG_LINK_SECRET).generate_signature(
            "GET", log_detail_path, params
        )
        return urlencode(params)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=LogDetailQueryInputSLZ,
        responses={status.HTTP_200_OK: RequestLogOutputSLZ(many=False)},
        tags=["WebAPI.Log"],
    ),
)
class LogDetailInfoApi(generics.RetrieveAPIView):
    gateway_permission_exempt = True

    def list(self, request, request_id, *args, **kwargs):
        """
        获取指定 request_id 日志的分享链接
        """
        client = LogSearchClient(request_id=request_id)

        total_count, logs = client.search_logs()
        # 去除 params、body 中的敏感数据
        logs = DataScrubber().scrub_sensitive_data(logs)
        logs = add_or_refine_fields(logs)

        paginator = LimitOffsetPaginator(total_count, 0, total_count)

        # 将字段信息添加到结果中，便于前端展示
        results = paginator.get_paginated_data(logs)
        results["fields"] = ES_LOG_FIELDS

        return OKJsonResponse(data=results)
