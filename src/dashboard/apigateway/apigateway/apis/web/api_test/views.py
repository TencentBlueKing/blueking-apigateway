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
from typing import Any, Dict

import requests
from django.conf import settings
from django.http import Http404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.api_debug.constants import SPEC_VERSION
from apigateway.apps.api_debug.models import APIDebugHistory
from apigateway.biz.permission import ResourcePermissionHandler
from apigateway.biz.released_resource import get_released_resource_data
from apigateway.core.models import Stage
from apigateway.utils.curlify import to_curl
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse
from apigateway.utils.time import convert_second_to_epoch_millisecond

from .data_models import ApiDebugHistoryRequest, ApiDebugHistoryResponse
from .filters import APIDebugHistoryRecordFilter
from .prepared_request import PreparedRequestHeaders, PreparedRequestURL
from .serializers import APIDebugHistoriesListOutputSLZ, APITestInputSLZ, APITestOutputSLZ

TEST_PERMISSION_EXPIRE_DAYS = 1


class APITestApi(generics.CreateAPIView):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: APITestOutputSLZ},
        operation_description="在线调试发起请求",
        tags=["WebAPI.APITest"],
    )
    def post(self, request, *args, **kwargs):
        slz = APITestInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        # 获取资源
        stage = generics.get_object_or_404(Stage, gateway=request.gateway, id=data["stage_id"])
        released_resource = get_released_resource_data(request.gateway, stage, data["resource_id"])
        if not released_resource:
            raise Http404

        authorization = data.get("authorization", {})
        if data.get("use_test_app") and released_resource.resource_perm_required:
            # 为测试账号临时授权
            ResourcePermissionHandler().grant_or_renewal_expire_soon(
                request.gateway, released_resource.id, authorization["bk_app_code"], TEST_PERMISSION_EXPIRE_DAYS, 300
            )

        prepared_request_headers = PreparedRequestHeaders()
        prepared_request_headers.prepare_headers(
            headers=data["headers"],
            authorization=authorization,
            authorization_from_cookies=self._get_authorization_from_cookies()
            if data.get("use_user_from_cookies")
            else {},
        )

        prepared_request_url = PreparedRequestURL(
            resource_path=released_resource.path,
            subpath=data.get("subpath", ""),
            match_subpath=released_resource.match_subpath,
            path_params=data["path_params"],
            gateway_name=request.gateway.name,
            stage_name=stage.name,
        )

        # 开始时间
        request_time = timezone.now()

        # 入参检查
        history_request = {
            "request_url": prepared_request_url.request_url,
            "request_method": data["method"],
            "type": "HTTP",
            "path_params": data.get("path_params", {}),
            "query_params": data.get("query_params", {}),
            "body": data.get("body", ""),
            "headers": data.get("headers", {}),
            "subpath": data.get("subpath", ""),
            "use_test_app": data.get("use_test_app", True),
            "use_user_from_cookies": data.get("use_user_from_cookies", False),
            "spec_version": SPEC_VERSION,
        }
        validated_request = ApiDebugHistoryRequest(**history_request)
        try:
            response = requests.request(
                method=data["method"],
                url=prepared_request_url.request_url,
                params=data["query_params"],
                data=force_bytes(data.get("body", "")),
                headers=prepared_request_headers.headers,
                # 隐式使用 cookies，不便于用户了解用户认证参数
                # cookies=request.COOKIES,
                # 10 秒连接超时，300 秒读超时
                timeout=(10, 300),
                allow_redirects=False,
                verify=False,
            )
            response_data_dict = self._get_response_data(
                response, prepared_request_headers.headers_without_sensitive, verify=False
            )
            # 结果检查
            success_history_response = {
                "data": response_data_dict,
                "spec_version": SPEC_VERSION,
            }
            validated_response = ApiDebugHistoryResponse(**success_history_response)
            success_history_data = {
                "gateway": request.gateway,
                "stage": stage,
                "resource_name": released_resource.name,
                "request": validated_request.dict(),
                "response": validated_response.dict(),
            }
            APIDebugHistory.objects.create(**success_history_data)
        except Exception as err:
            # 结果检查
            error_history_response = {
                "error": err,
                "spec_version": SPEC_VERSION,
            }
            validated_response = ApiDebugHistoryResponse(**error_history_response)
            fail_history_data = {
                "gateway": request.gateway,
                "stage": stage,
                "resource_name": released_resource.name,
                "request": validated_request.dict(),
                "response": validated_response.dict(),
            }
            APIDebugHistory.objects.create(**fail_history_data)
            return FailJsonResponse(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="UNKNOWN",
                message=_("请求网关资源失败，错误消息：{err}。").format(err=err),
            )

        return OKJsonResponse(
            data=response_data_dict,
        )

    def _get_response_data(self, response, headers_without_sensitive=Dict[str, Any], verify=False):
        # 去掉 curl 字符串的换行
        original_curl = to_curl(
            response.request,
            verify=verify,
            headers=headers_without_sensitive,
        )
        modified_curl = original_curl.replace("\n", "")

        return {
            "status_code": response.status_code,
            "proxy_time": round(convert_second_to_epoch_millisecond(response.elapsed.total_seconds())),
            "size": "{:.2f}".format(len(response.content) / 1024),
            "body": response.text,
            "headers": dict(response.headers),
            "curl": modified_curl,
        }

    def _get_authorization_from_cookies(self) -> Dict[str, str]:
        """从 cookies 中获取指定的登录票据"""
        cookies = self.request.COOKIES
        return {
            key: cookies.get(cookie_name, "")
            for key, cookie_name in settings.BK_LOGIN_TICKET_KEY_TO_COOKIE_NAME.items()
        }


class APIDebugHistoriesQuerySetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(gateway=self.request.gateway)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取测试历史列表",
        responses={status.HTTP_200_OK: APIDebugHistoriesListOutputSLZ(many=True)},
        tags=["WebAPI.ResourceDebugHistory"],
    ),
)
class APIDebugHistoryListApi(APIDebugHistoriesQuerySetMixin, generics.ListAPIView):
    filterset_class = APIDebugHistoryRecordFilter
    queryset = APIDebugHistory.objects.order_by("-updated_time")
    serializer_class = APIDebugHistoriesListOutputSLZ

    def list(self, request, *args, **kwargs):
        time_start_stamp = request.query_params.get("time_start", None)
        time_end_stamp = request.query_params.get("time_end", None)

        # 将时间戳转换为datetime对象
        time_start = None
        time_end = None
        if time_start_stamp:
            time_start = timezone.datetime.fromtimestamp(int(time_start_stamp), timezone.get_current_timezone())
        if time_end_stamp:
            time_end = timezone.datetime.fromtimestamp(int(time_end_stamp), timezone.get_current_timezone())

        # 过滤查询集
        queryset = self.get_queryset()
        if time_start and time_end:
            queryset = queryset.filter(created_time__range=(time_start, time_end))
        # 应用额外的过滤器
        queryset = self.filter_queryset(queryset)

        # 序列化查询集
        serializer = self.serializer_class(queryset, many=True)

        # 返回响应
        return OKJsonResponse(data=serializer.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取调用历史详情",
        responses={status.HTTP_200_OK: APIDebugHistoriesListOutputSLZ()},
        tags=["WebAPI.ResourceDebugHistory"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除调用历史",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.ResourceDebugHistory"],
    ),
)
class APIDebugHistoryRetrieveDestroyApi(APIDebugHistoriesQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    serializer_class = APIDebugHistoriesListOutputSLZ
    queryset = APIDebugHistory.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = APIDebugHistoriesListOutputSLZ(instance)
        return OKJsonResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
