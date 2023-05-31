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

from cachetools import TTLCache, cached
from django.conf import settings

from common.base_utils import get_first_not_empty_value
from common.base_validators import BaseValidator, ValidationError
from esb.bkapp.validators import AccessTokenValidator
from esb.bkcore.models import AccessToken
from esb.utils.func_ctrl import FunctionControllerClient


class BaseUserAuthValidator(BaseValidator):
    def validate_bk_token(self, request, bk_token):
        username = self._verify_bk_token(bk_token, request.g.app_code)
        self.sync_current_username(request, username, verified=True)

    def validate_access_token(self, request, app_code, access_token):
        if not app_code:
            raise ValidationError("APP Code [bk_app_code] cannot be empty")
        if not access_token:
            raise ValidationError("User TOKEN [bk_access_token] cannot be empty")

        access_token = AccessToken.objects.filter(bk_app_code=app_code, access_token=access_token).first()
        if not access_token:
            raise ValidationError("The specified user TOKEN [bk_access_token] does not exist")
        if access_token.has_expired():
            raise ValidationError(
                "The specified user TOKEN [bk_access_token] has expired, please apply for authorization again"
            )

        self.sync_current_username(request, access_token.user_id, verified=True)

    def sync_current_username(self, request, username, verified=False):
        request.g.current_user_username = username
        request.g.current_user_verified = verified

    @staticmethod
    @cached(
        cache=TTLCache(
            maxsize=settings.BK_TOKEN_CACHE_MAXSIZE,
            ttl=settings.BK_TOKEN_CACHE_TTL_SECONDS,
        )
    )
    def _verify_bk_token(bk_token, app_code):
        from components.bk.apis.bk_login.is_login import IsLogin

        check_result = IsLogin().invoke(kwargs={"bk_token": bk_token}, app_code=app_code)
        if not check_result["result"]:
            raise ValidationError("User authentication failed, please check if the bk_token is valid")

        return check_result.get("data", {}).get("username", "")


class UserAuthValidator(BaseUserAuthValidator):
    """
    validate user
    """

    def validate(self, request):
        app_code = request.g.app_code

        if request.apigw.enabled:
            # 用户认证、用户认证应用白名单，托管到网关侧，如果是来自网关的请求，仅验证用户名不能为空
            username = request.g.get("current_user_username", "")
            if not username:
                raise ValidationError(
                    request.g.get("user_valid_error_message")
                    or "Please provide a valid user identity, such as bk_username"
                )

            return

        if request.g.authorization.get("access_token"):
            validator = AccessTokenValidator()
            validator.validate(request)

            self.sync_current_username(request, validator.get_bk_username(), verified=True)
            return

        if request.g.kwargs.get("bk_access_token"):
            self.validate_access_token(request, app_code, request.g.kwargs["bk_access_token"])
            return

        if request.g.authorization.get("bk_token"):
            self.validate_bk_token(request, request.g.authorization["bk_token"])
            return

        username = get_first_not_empty_value(request.g.authorization, keys=["bk_username", "username"])
        if username and FunctionControllerClient.is_skip_user_auth(app_code):
            self.sync_current_username(request, username, verified=False)
            return

        raise ValidationError(
            request.g.get("user_valid_error_message")
            or "User authentication failed, please provide a valid user identity, such as bk_token, bk_username"
        )


class VerifiedUserRequiredValidator(BaseUserAuthValidator):
    """
    validate user with bk-token
    """

    def validate(self, request):
        if request.apigw.enabled:
            if request.g.get("current_user_username") and request.g.get("current_user_verified"):
                return

            raise ValidationError(
                request.g.get("user_valid_error_message")
                or "User authentication failed, authentication parameter bk_token is required"
            )

        bk_token = request.g.authorization.get("bk_token") or request.COOKIES.get("bk_token")
        if bk_token:
            self.validate_bk_token(request, bk_token)
            return

        raise ValidationError("User authentication failed, please provide the parameter bk_token as the user identity")
