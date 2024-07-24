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
import time
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

from apigateway.biz.permission import ResourcePermissionHandler
from apigateway.biz.released_resource import get_released_resource_data
from apigateway.core.models import Resource, ResourceDebugHistory, Stage
from apigateway.utils.curlify import to_curl
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse
from apigateway.utils.time import convert_second_to_epoch_millisecond

from .helpers import APITestRequestBuilder
from .prepared_request import PreparedRequestHeaders, PreparedRequestURL
from .serializers import APIDebugHistoriesListOutputSLZ, APITestOutputSLZ

TEST_PERMISSION_EXPIRE_DAYS = 1


class APITestApi(generics.CreateAPIView):
    @swagger_auto_schema(
        request_body=APITestRequestBuilder,
        responses={status.HTTP_200_OK: APITestOutputSLZ},
        operation_description="在线调试发起请求",
        tags=["WebAPI.APITest"],
    )
    def post(self, request, *args, **kwargs):
        build = APITestRequestBuilder(**request.data)
        data = build.dict()

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
        start_time = time.perf_counter()
        request_time = timezone.now()
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
            end_time = time.perf_counter()
            duration = end_time - start_time
            success_history_data = {
                "gateway": request.gateway,
                "stage": stage,
                "resource": Resource(id=data["resource_id"]),
                "request_url": prepared_request_url.request_url,
                "request_method": data["method"],
                "request": {
                    "authorization": data.get("authorization", {}),
                    "path_params": data.get("path_params", {}),
                    "query_params": data.get("query_params", {}),
                    "body": data.get("body", ""),
                    "headers": data.get("headers", {}),
                    "subpath": data.get("subpath", ""),
                    "use_test_app": data.get("use_test_app", True),
                    "use_user_from_cookies": data.get("use_user_from_cookies", False),
                },
                "request_time": request_time,
                "status_code": response.status_code,
                "response": response.text,
                "proxy_time": duration,
                "spec_version": 1,
            }
            ResourceDebugHistory.objects.create(**success_history_data)
        except Exception as err:
            return FailJsonResponse(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="UNKNOWN",
                message=_("请求网关资源失败，错误消息：{err}。").format(err=err),
            )

        return OKJsonResponse(
            data=self._get_response_data(response, prepared_request_headers.headers_without_sensitive, verify=False),
        )

    def _get_response_data(self, response, headers_without_sensitive=Dict[str, Any], verify=False):
        return {
            "status_code": response.status_code,
            "proxy_time": round(convert_second_to_epoch_millisecond(response.elapsed.total_seconds())),
            "size": "{:.2f}".format(len(response.content) / 1024),
            "body": response.text,
            "headers": dict(response.headers),
            "curl": to_curl(
                response.request,
                verify=verify,
                headers=headers_without_sensitive,
            ),
        }

    def _get_authorization_from_cookies(self) -> Dict[str, str]:
        """从 cookies 中获取指定的登录票据"""
        cookies = self.request.COOKIES
        return {
            key: cookies.get(cookie_name, "")
            for key, cookie_name in settings.BK_LOGIN_TICKET_KEY_TO_COOKIE_NAME.items()
        }


class TestHistoriesQuerySetMixin:
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
class APIDebugHistoryListApi(TestHistoriesQuerySetMixin, generics.ListAPIView):
    queryset = ResourceDebugHistory.objects.order_by("-updated_time")
    serializer_class = APIDebugHistoriesListOutputSLZ

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        slz = APIDebugHistoriesListOutputSLZ(queryset, many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取调用历史详情",
        responses={status.HTTP_200_OK: APIDebugHistoriesListOutputSLZ()},
        tags=["WebAPI.Backend"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除调用历史",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Backend"],
    ),
)
class APIDebugHistoryRetrieveDestroyApi(TestHistoriesQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    serializer_class = APIDebugHistoriesListOutputSLZ
    queryset = ResourceDebugHistory.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = APIDebugHistoriesListOutputSLZ(instance)
        return OKJsonResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
