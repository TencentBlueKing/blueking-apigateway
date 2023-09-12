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
import re

from rest_framework import serializers

from apigateway.common.mixins.contexts import GetGatewayFromContextMixin
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


# 单位为秒的持续时间
DURATION_IN_SECOND_PATTERN = re.compile(r"^(\d+)s$")
