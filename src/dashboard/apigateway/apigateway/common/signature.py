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
import hashlib
import hmac
import time

from django.utils.encoding import force_bytes, force_str

from apigateway.common.error_codes import error_codes


class SignatureGenerator:
    def __init__(self, secret):
        self.secret = secret

    def generate_signature(self, method, path, params, data=""):
        params_str = "&".join([f"{k}={v}" for k, v in sorted(params.items(), key=lambda x: x[0])])
        original = "\n".join([method, path, params_str, data])
        return hmac.new(force_bytes(self.secret), force_bytes(original), hashlib.sha1).hexdigest()


class SignatureValidator(SignatureGenerator):
    def __init__(self, secret, request, timestamp_expire_seconds):
        self.secret = secret
        self.request = request
        self.timestamp_expire_seconds = timestamp_expire_seconds
        self.error = None

    def is_valid(self, raise_exception=True):
        try:
            self.validate()
        except ValueError as e:
            self.error = str(e)
        else:
            self.error = None

        if self.error and raise_exception:
            raise error_codes.INVALID_ARGS.format(self.error)

        return not bool(self.error)

    def validate(self):
        path = self.get_request_path(self.request)

        query_params = dict(self.request.query_params.items())

        bk_signature = query_params.pop("bk_signature", None)
        if not bk_signature:
            raise ValueError("bk_signature is required")

        self.check_nonce(query_params.get("bk_nonce"))
        self.check_timestamp(query_params.get("bk_timestamp"))

        expected_signature = self.generate_signature(
            self.request.method,
            path,
            query_params,
            force_str(self.request.body),
        )
        if bk_signature != expected_signature:
            raise ValueError("bk_signature validate failed, please check if the parameters are correct")

    def get_request_path(self, request):
        path = request.META.get("HTTP_X_REQUEST_URI", "").split("?")[0]
        if not path:
            return request.META["PATH_INFO"]
        return path

    def check_nonce(self, bk_nonce):
        """验证 bk_nonce"""
        if not bk_nonce:
            raise ValueError("bk_nonce is required")
        try:
            nonce = int(bk_nonce)
        except Exception:
            raise ValueError("bk_nonce is illegal")
        if nonce <= 0:
            raise ValueError("bk_nonce is illegal, must be a positive integer")
        return nonce

    def check_timestamp(self, bk_timestamp):
        """验证时间戳是否合法"""
        if not bk_timestamp:
            raise ValueError("bk_timestamp is required")
        try:
            timestamp = int(bk_timestamp)
        except Exception:
            raise ValueError("bk_timestamp is illegal, must be a timestamp integer")

        # 有效期为 24h
        if timestamp < int(time.time()) - self.timestamp_expire_seconds:
            raise ValueError("bk_timestamp has expired")
        return timestamp
