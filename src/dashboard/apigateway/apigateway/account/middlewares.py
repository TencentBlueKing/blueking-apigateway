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
import json
import logging
from collections import namedtuple
from typing import Optional, Tuple

from apigw_manager.apigw.authentication import ApiGatewayJWTAppMiddleware as BaseApiGatewayJWTAppMiddleware
from apigw_manager.apigw.authentication import ApiGatewayJWTUserMiddleware as BaseApiGatewayJWTUserMiddleware
from django.conf import settings

logger = logging.getLogger(__name__)


class ApiGatewayJWTAppMiddleware(BaseApiGatewayJWTAppMiddleware):

    App = namedtuple("App", ["app_code"])

    def make_app(self, bk_app_code=None, verified=False, **jwt_app):
        return self.App(app_code=bk_app_code or "")


class ApiGatewayJWTUserMiddleware(BaseApiGatewayJWTUserMiddleware):

    User = namedtuple("User", ["username", "is_active", "is_authenticated"])

    def get_user(self, request, api_name=None, bk_username=None, verified=False, **credentials):
        return self.User(username=bk_username or "", is_active=True, is_authenticated=True)


class SelfAppCodeAppSecretLoginMiddleware:
    """
    此中间件用于支持 APIGW-Dashbord 不通过网关API而访问自身 openapi 接口的场景

    使用请求头 X-Bk-App-Code、X-Bk-App-Secret 实现请求来源应用、用户的认证
    - X-Bk-App-Code、X-Bk-App-Secret 应与 settings 中的 BK_APP_CODE、BK_APP_SECRET 一致，以判断请求来源于 APIGW-Dashboard
    - 用户为用户名为 "" 的有效用户，以跳过后面的用户认证
    """

    App = namedtuple("App", ["app_code"])
    User = namedtuple("User", ["username", "is_active", "is_authenticated"])

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        bk_app_code, bk_app_secret = self._get_app_code_app_secret_from_header(request)
        if not (bk_app_code == settings.BK_APP_CODE and bk_app_secret == settings.BK_APP_SECRET):
            return self.get_response(request)

        request.app = self.App(app_code=bk_app_code)
        # 如果用户未认证，提供一个默认的已认证用户（用户名为""），以通过 DRF 的 SessionAuthentication 验证
        if hasattr(request, "user") and not request.user.is_authenticated:
            request.user = self.User(username="", is_active=True, is_authenticated=True)

        # disable csrf checks
        request._dont_enforce_csrf_checks = True

        return self.get_response(request)

    def _get_app_code_app_secret_from_header(self, request) -> Tuple[Optional[str], Optional[str]]:
        try:
            authorization = json.loads(request.META.get("HTTP_X_BKAPI_AUTHORIZATION"))
        except Exception:
            return None, None

        return authorization.get("bk_app_code"), authorization.get("bk_app_secret")
