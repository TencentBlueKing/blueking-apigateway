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
import abc
from abc import ABCMeta

import jwt

from common.errors import error_codes
from common.log import logger
from esb.utils.jwt_utils import JWTKey

HEADER_BKAPI_JWT = "HTTP_X_BKAPI_JWT"
HEADER_BKAPI_REQUEST_ID = "HTTP_X_BKAPI_REQUEST_ID"


def is_from_gateway_with_jwt(request):
    """Detect if this request is from BK API Gateway with JWT way"""
    return bool(request.META.get(HEADER_BKAPI_JWT))


class APIGWBase(metaclass=ABCMeta):
    def __init__(self, request):
        self.request = request

    @abc.abstractmethod
    def get_enabled(self):
        """是否开启"""

    @abc.abstractmethod
    def get_app(self):
        """APP信息"""

    @abc.abstractmethod
    def get_user(self):
        """用户信息"""


class JWTClient(APIGWBase):
    def __init__(self, request):
        super().__init__(request)

        self._jwt_payload = request.META.get(HEADER_BKAPI_JWT, "")
        self._apigw_request_id = request.META.get(HEADER_BKAPI_REQUEST_ID, "")
        self.payload = {}

        self.decode_jwt_content()

        self.enabled = self.get_enabled()
        self.app = self.get_app()
        self.user = self.get_user()

    def decode_jwt_content(self):
        if not self._jwt_payload:
            return

        jwt_public_key = JWTKey().get_public_key()
        if not jwt_public_key:
            logger.error("get api gateway jwt public_key fail, please check settings")
            raise error_codes.APIGW_ERROR.format_prompt(
                "get jwt public_key fail. please contact the component developer to handle"
            )

        try:
            self.payload = jwt.decode(self._jwt_payload, jwt_public_key, algorithms=["RS512"])
            logger.debug("valid jwt success, %s, request_id: %s" % (self._jwt_payload, self._apigw_request_id))
        except jwt.DecodeError:
            logger.error(
                "valid jwt.DecodeError, jwt_public_key: %s, jwt_payload: %s, request_id: %s",
                jwt_public_key,
                self._jwt_payload,
                self._apigw_request_id,
            )
            raise error_codes.APIGW_ERROR.format_prompt(
                "[X-Bkapi-JWT] decode error, please check if jwt is correct, or if its private key is correct"
            )
        except jwt.ExpiredSignatureError:
            logger.warning(
                "valid jwt.ExpiredSignatureError %s, request_id: %s", self._jwt_payload, self._apigw_request_id
            )
            raise error_codes.APIGW_ERROR.format_prompt("[X-Bkapi-JWT] has expired")
        except jwt.InvalidIssuerError:
            logger.warning(
                "valid jwt.InvalidIssuerError %s, request_id: %s", self._jwt_payload, self._apigw_request_id
            )
            raise error_codes.APIGW_ERROR.format_prompt("[X-Bkapi-JWT] has invalid issuer")
        except Exception:
            logger.exception(
                "valid jwt Exception. jwt_content: %s, request_id: %s", self._jwt_payload, self._apigw_request_id
            )
            raise error_codes.APIGW_ERROR.format_prompt(
                "[X-Bkapi-JWT] decode error, please contact the component developer to handle"
            )

    def get_enabled(self):
        return bool(self.request.META.get(HEADER_BKAPI_JWT))

    def get_app(self):
        return self.payload.get("app")

    def get_user(self):
        return self.payload.get("user")
