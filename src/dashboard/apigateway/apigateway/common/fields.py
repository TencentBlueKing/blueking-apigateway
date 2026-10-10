# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

import datetime
import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import empty

from apigateway.common.mixins.contexts import GetGatewayFromContextMixin
from apigateway.utils.crypto import decrypt_frontend_encrypted_value
from apigateway.utils.time import timestamp, utctime

logger = logging.getLogger(__name__)


class CurrentGatewayDefault(GetGatewayFromContextMixin):
    requires_context = True

    def __call__(self, serializer_field):
        return self._get_gateway(serializer_field)

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class TimestampField(serializers.IntegerField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        try:
            return utctime(data).datetime if data else None
        except Exception:  # pylint: disable=broad-except
            raise serializers.ValidationError("A valid timestamp is required.", code="invalid")

    def to_representation(self, value):
        if value is None:
            return None

        assert isinstance(value, datetime.datetime), "Only accept datetime"
        return timestamp(value)


class DecryptableCharField(serializers.CharField):
    """可接收前端加密值的字符串字段，解密后按普通 CharField 校验

    支持两种输入格式：
    - 明文值：原始字符串，如 "the_value"
    - 加密值：{"_encrypted": true, "_encrypted_value": "xxxxx"}，其中 _encrypted_value 为 Base64 编码的 SM2 密文
    """

    ENCRYPTED_FLAG_KEY = "_encrypted"
    ENCRYPTED_VALUE_KEY = "_encrypted_value"

    default_error_messages = {
        "invalid_encrypted_value": _("无效的加密值格式。"),
        "decrypt_failed": _("解密失败，请刷新页面后重试。"),
    }

    def run_validation(self, data=empty):
        if isinstance(data, dict):
            data = self._decrypt(data)
        return super().run_validation(data)

    def _decrypt(self, data: dict) -> str:
        encrypted_value = data.get(self.ENCRYPTED_VALUE_KEY)
        if (
            data.get(self.ENCRYPTED_FLAG_KEY) is not True
            or not isinstance(encrypted_value, str)
            or not encrypted_value
        ):
            raise self._error("invalid_encrypted_value")

        try:
            return decrypt_frontend_encrypted_value(encrypted_value)
        except Exception as err:  # pylint: disable=broad-except
            # 异常信息与堆栈可能包含密文，仅记录异常类型
            logger.warning("decrypt frontend encrypted value failed: %s", type(err).__name__)
            raise self._error("decrypt_failed")

    def _error(self, code: str) -> serializers.ValidationError:
        return serializers.ValidationError(self.error_messages[code], code=code)
