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
import datetime
from typing import Optional

from rest_framework import serializers

from apigateway.common.mixins.contexts import GetGatewayFromContextMixin
from apigateway.core.constants import DURATION_IN_SECOND_PATTERN
from apigateway.utils.time import timestamp, utctime


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
        except Exception:
            raise serializers.ValidationError("A valid timestamp is required.", code="invalid")

    def to_representation(self, value):
        if value is None:
            return None

        assert isinstance(value, datetime.datetime), "Only accept datetime"
        return timestamp(value)


class DurationInSecondField(serializers.IntegerField):
    # 使用 to_internal_value 时，无法验证 min_value，因此，覆盖 run_validation
    def run_validation(self, data: Optional[int]) -> str:
        data = super().run_validation(data)
        return f"{data}s" if data is not None else ""

    def to_representation(self, value: str) -> Optional[int]:
        if not value:
            return None

        match = DURATION_IN_SECOND_PATTERN.match(value)
        if not match:
            raise serializers.ValidationError("invalid data", code="invalid")

        return int(match.group(1))
