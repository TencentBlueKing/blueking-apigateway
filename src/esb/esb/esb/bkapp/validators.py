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

import base64
import hashlib
import hmac
import time

from cachetools import TTLCache, cached
from django.conf import settings
from django.utils.encoding import force_bytes

from common.base_utils import get_first_not_empty_value
from common.base_validators import BaseValidator, ValidationError
from common.errors import error_codes
from common.log import logger
from esb.bkapp.helpers import BKAuthHelper


class AppAuthValidator(BaseValidator):
    def __init__(self, verified_type="signature_or_app_secret", *args, **kwargs):
        """
        :param str verified_type: 验证类型，支持"app_secret", "signature", "signature_or_app_secret"
        """
        self.verified_type = verified_type
        super(AppAuthValidator, self).__init__(*args, **kwargs)

    def validate(self, request):
        if request.apigw.enabled:
            if request.g.get("is_app_verified"):
                return

            raise ValidationError(
                request.g.get("app_valid_error_message")
                or "verify app fail, please check if the authentication parameters are correct"
            )

        if request.g.authorization.get("access_token"):
            validator = AccessTokenValidator()
            validator.validate(request)

            self._set_request_current_app(request, validator.get_bk_app_code())
            return

        if self.verified_type == "app_secret":
            validator = AppSecretValidator()
            validator.validate(request)
            return

        elif self.verified_type == "signature":
            validator = SignatureValidator()
            validator.validate(request)
            return

        elif self.verified_type == "signature_or_app_secret":
            signature = request.GET.get("bk_signature") or request.GET.get("signature")
            app_secret = get_first_not_empty_value(request.g.authorization, keys=["bk_app_secret", "app_secret"])
            if signature:
                validator = SignatureValidator()
                validator.validate(request)
            elif app_secret:
                validator = AppSecretValidator()
                validator.validate(request)
            else:
                raise ValidationError(
                    "Signature [bk_signature] and APP Secret [bk_app_secret] cannot be empty at the same time"
                )
            return
        else:
            raise ValidationError("Please choose a valid APP verification method")

    def _set_request_current_app(self, request, bk_app_code):
        request.g.app_code = bk_app_code


class AccessTokenValidator(BaseValidator):
    def validate(self, request):
        bk_app_code, bk_username = self._verify_access_token(request.g.authorization["access_token"])

        self._validated_data = {
            "bk_app_code": bk_app_code,
            "bk_username": bk_username,
        }

    @property
    def validated_data(self):
        if not hasattr(self, "_validated_data"):
            raise ValidationError("You must call `.validate()` before accessing validated_data")

        return self._validated_data

    def get_bk_app_code(self):
        return self.validated_data["bk_app_code"]

    def get_bk_username(self):
        # ESB 要求用户不能为空，因此，access_token 必须为用户类型
        if not self.validated_data["bk_username"]:
            raise ValidationError("the access_token is the application type and cannot indicate the user")

        return self.validated_data["bk_username"]

    @staticmethod
    @cached(
        cache=TTLCache(
            maxsize=settings.BK_SSM_ACCESS_TOKEN_CACHE_MAXSIZE,
            ttl=settings.BK_SSM_ACCESS_TOKEN_CACHE_TTL_SECONDS,
        )
    )
    def _verify_access_token(access_token):
        from components.bk.apisv2.bk_ssm.verify_access_token import VerifyAccessToken

        result = VerifyAccessToken().invoke(kwargs={"access_token": access_token})

        if not result["result"]:
            raise ValidationError("verify access_token failed, please check if the access_token is valid")

        bk_app_code = result["data"].get("bk_app_code")
        bk_username = result["data"].get("identity", {}).get("username", "")

        return bk_app_code, bk_username


class AppSecretValidator(BaseValidator):
    """
    Validate app_code and app_secret
    """

    def __init__(self, *args, **kwargs):
        super(AppSecretValidator, self).__init__(*args, **kwargs)

    def validate(self, request):
        app_code = request.g.app_code
        app_secret = get_first_not_empty_value(request.g.authorization, keys=["bk_app_secret", "app_secret"])

        if not app_code:
            raise ValidationError("APP Code [bk_app_code] cannot be empty")

        if not app_secret:
            raise ValidationError("APP Secret [bk_app_secret] cannot be empty")

        try:
            verified, message = BKAuthHelper.verify_app_secret(app_code, app_secret)
        except Exception:
            logger.exception("verify app secret error, app_code: %s", app_code)
            raise ValidationError(
                "request bkauth api error, please try again later or contact component developer to handle",
            )

        if not verified:
            raise ValidationError(message)


class SignatureValidator(BaseValidator):
    """
    Validate signature
    """

    def __init__(self, *args, **kwargs):
        super(SignatureValidator, self).__init__(*args, **kwargs)

    def get_request_path(self, request):
        """
        为了应对使用proxy_pass拿不到完整path的情况，先尝试获取自定义头信息，再尝试 path_info
        """
        path = request.META.get("HTTP_X_REQUEST_URI", "").split("?")[0]
        if not path:
            path = request.META["PATH_INFO"]
        return path

    def validate(self, request):
        # if skip signature verify
        if getattr(request, "__esb_skip_signature__", False):
            return

        req_get_params = dict(list(request.GET.items()))

        # 将 signature 参数从参数字典中拿掉
        signature = req_get_params.pop("bk_signature", None) or req_get_params.pop("signature", None)
        if not signature:
            raise ValidationError("Signature [bk_signature] cannot be empty")

        app_code = request.g.app_code

        self.check_nonce(req_get_params.get("bk_nonce"))
        self.check_timestamp(req_get_params.get("bk_timestamp"))

        path = self.get_request_path(request)
        params = req_get_params.copy()
        if request.method == "POST":
            params["data"] = request.body

        app_secrets = self._get_app_secrets(app_code)
        is_valid = self.verify_signature(request.method, path, params, signature, app_secrets)
        if not is_valid:
            raise ValidationError(
                "Signature [bk_signature] verification failed, please provide valid parameters and signature"
            )

    def verify_signature(self, method, path, params, signature, valid_app_secret_list):
        """
        校验signature有效
        """
        # 校验signature
        req_params = "&".join(["%s=%s" % (k, v) for k, v in sorted(iter(list(params.items())), key=lambda x: x[0])])
        message = "%s%s?%s" % (method, path, req_params)
        for valid_app_secret in valid_app_secret_list:
            sign = base64.b64encode(
                hmac.new(force_bytes(valid_app_secret), force_bytes(message), hashlib.sha1).digest()
            )
            if force_bytes(sign) == force_bytes(signature):
                return True
        return False

    def _get_app_secrets(self, app_code):
        """
        验证 app_code
        """
        if not app_code:
            raise ValidationError("APP Code [bk_app_code] cannot be empty")

        try:
            app_secrets, message = BKAuthHelper.list_app_secrets(app_code)
        except Exception:
            logger.exception("request bkauth api error, app_code: %s", app_code)
            raise ValidationError(
                "request bkauth api error, please try again later or contact component developer to handle",
            )

        if not app_secrets:
            raise ValidationError(message)

        return app_secrets

    def check_nonce(self, bk_nonce):
        """
        验证 bk_nonce
        """
        if not bk_nonce:
            raise ValidationError("Parameter bk_nonce does not exist")

        try:
            nonce = int(bk_nonce)
        except Exception:
            raise ValidationError("Parameter bk_nonce is illegal")

        if nonce <= 0:
            raise ValidationError("Parameter bk_nonce is illegal, it must be a positive integer")

        return nonce

    def check_timestamp(self, bk_timestamp):
        """
        验证时间戳是否合法
        """
        if not bk_timestamp:
            raise ValidationError("Parameter bk_timestamp does not exist")

        try:
            timestamp = int(bk_timestamp)
        except Exception:
            raise ValidationError("Parameter bk_timestamp is illegal, due to non-time format")

        # 有效期为300s
        if timestamp < int(time.time()) - 300:
            raise ValidationError("Parameter bk_timestamp is illegal, because it has expired")

        return timestamp


class SelfAppCodeAppSecret(BaseValidator):
    """自认证，认证请求来自API网关相关服务"""

    def validate(self, request):
        app_code = request.g.app_code
        app_secret = request.g.authorization.get("bk_app_secret")

        if not (app_code or app_secret):
            raise ValidationError("authorization bk_app_code, bk_app_secret cannot be empty")

        if app_code == settings.BK_APP_CODE and app_secret == settings.BK_APP_SECRET:
            return

        raise ValidationError(f"verify app secret error, app_code: {app_code}")


class AppCodeWhiteListValidator(BaseValidator):
    def __init__(self, white_list=(), *args, **kwargs):
        self.white_list = white_list
        super(AppCodeWhiteListValidator, self).__init__(*args, **kwargs)

    def validate(self, request):
        app_code = request.g.app_code
        if app_code not in self.white_list:
            raise error_codes.APP_PERMISSION_DENIED.format_prompt(
                "APP [bk_app_code=%s] is forbidden to access this component" % app_code
            )
