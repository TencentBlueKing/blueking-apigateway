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
from django.utils.encoding import force_bytes
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.biz.permission import ResourcePermissionHandler
from apigateway.biz.released_resource import get_released_resource_data
from apigateway.core.models import Stage
from apigateway.utils.curlify import to_curl
from apigateway.utils.responses import V1FailJsonResponse, V1OKJsonResponse
from apigateway.utils.time import convert_second_to_epoch_millis

from .prepared_request import PreparedRequestHeaders, PreparedRequestURL
from .serializers import APITestInputSLZ, APITestOutputSLZ

TEST_PERMISSION_EXPIRE_DAYS = 1


class APITestApi(generics.CreateAPIView):
    @swagger_auto_schema(
        request_body=APITestInputSLZ,
        responses={status.HTTP_200_OK: APITestOutputSLZ},
        tags=["APITest"],
    )
    def post(self, request, *args, **kwargs):
        slz = APITestInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        # 获取资源
        stage = generics.get_object_or_404(Stage, api=request.gateway, id=data["stage_id"])
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
        except Exception as err:
            return V1FailJsonResponse(_("请求网关资源失败，错误消息：{err}。").format(err=err))

        return V1OKJsonResponse(
            "OK",
            data=self._get_response_data(response, prepared_request_headers.headers_without_sensitive, verify=False),
        )

    def _get_response_data(self, response, headers_without_sensitive=Dict[str, Any], verify=False):
        return {
            "status_code": response.status_code,
            "proxy_time": round(convert_second_to_epoch_millis(response.elapsed.total_seconds())),
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
