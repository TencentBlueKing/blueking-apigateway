# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apigw_manager.apigw.authentication import ApiGatewayJWTAppMiddleware as BaseApiGatewayJWTAppMiddleware
from apigw_manager.apigw.authentication import ApiGatewayJWTUserMiddleware as BaseApiGatewayJWTUserMiddleware
from django.conf import settings
from django.utils import timezone as dj_timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ApiGatewayJWTAppMiddleware(BaseApiGatewayJWTAppMiddleware):
    App = namedtuple("App", ["app_code", "tenant_mode", "tenant_id"])

    def make_app(self, bk_app_code=None, verified=False, tenant_mode="", tenant_id="", **jwt_app):
        return self.App(
            app_code=bk_app_code or "",
            tenant_mode=tenant_mode,
            tenant_id=tenant_id,
        )


class ApiGatewayJWTUserMiddleware(BaseApiGatewayJWTUserMiddleware):
    User = namedtuple("User", ["username", "is_active", "is_authenticated"])

    def get_user(self, request, api_name=None, bk_username=None, verified=False, **credentials):
        return self.User(username=bk_username or "", is_active=True, is_authenticated=True)


class SelfAppCodeAppSecretLoginMiddleware:
    """
    此中间件用于支持 APIGW-Dashbord 不通过网关 API 而访问自身 openapi 接口的场景

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
        except Exception:  # pylint: disable=broad-except
            return None, None

        return authorization.get("bk_app_code"), authorization.get("bk_app_secret")


class UserTimezoneMiddleware(MiddlewareMixin):
    """按用户的时区属性激活 Django 时区。

    该中间件从用户管理系统获取用户时区信息并激活，使所有时间相关的序列化输出
    都使用用户所在时区的偏移量。

    执行逻辑：
    1. 未登录用户跳过处理
    2. 从 request.user 读取 time_zone 属性
    3. 若时区字段缺失或非法，回退到默认时区 settings.TIME_ZONE
    4. 在响应返回时重置时区，避免线程复用导致的时区污染

    Note: 必须放在所有用户认证中间件之后
    """

    def process_request(self, request):
        # Ignore anonymous user
        if not request.user.is_authenticated:
            return

        user = request.user
        tz_name = getattr(user, "time_zone", None)

        # Try to activate user's timezone if it's a non-empty string
        if tz_name and isinstance(tz_name, str):
            try:
                user_tz = ZoneInfo(tz_name)
                dj_timezone.activate(user_tz)
            except ZoneInfoNotFoundError as e:
                logger.warning(
                    "Invalid time_zone '%s' for user '%s', fallback to default. Error: %s",
                    tz_name,
                    user.username,
                    str(e),
                )
            else:
                logger.debug("Activated timezone '%s' for user '%s'", tz_name, user.username)
                return

        # Fallback to default timezone when time_zone is empty or invalid
        dj_timezone.activate(dj_timezone.get_default_timezone())

    def process_response(self, request, response):
        """重置时区"""
        dj_timezone.deactivate()
        return response
