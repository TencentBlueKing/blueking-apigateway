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
import pytest
from rest_framework import serializers

from apigateway.common.fields import TimestampField
from apigateway.tests.utils.testing import dummy_time


class TestTimestampField:
    class TimestampSLZ(serializers.Serializer):
        time = TimestampField(allow_null=True)

    @pytest.mark.parametrize(
        "_time, expected, will_error",
        [
            (dummy_time.timestamp, dummy_time.time, False),
            (None, None, False),
            ("abc", None, True),
            # arrow 会根据整数范围，自动判断其为秒或是毫秒
            # 1679922524 => 2023-03-27T13:08:44+00:00
            # 1679922524000 => 2023-03-27T13:08:44+00:00
            # 1111111111111 => 2005-03-18T01:58:31.111000+00:00
            (1111111111111000000, None, True),
        ],
    )
    def test_to_internal_value(self, _time, expected, will_error):
        slz = self.TimestampSLZ(data={"time": _time})
        slz.is_valid()
        if will_error:
            assert slz.errors
            return

        assert slz.validated_data["time"] == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            (dummy_time.time, dummy_time.timestamp),
            (None, None),
        ],
    )
    def test_to_representation(self, value, expected):
        slz = self.TimestampSLZ(instance={"time": value})
        assert slz.data["time"] == expected
