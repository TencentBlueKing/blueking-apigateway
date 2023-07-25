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
import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.access_log import serializers


class TestSearchLogQuerySerializer:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "stage_id": 1,
                    "offset": 0,
                    "limit": 10,
                    "time_start": 1,
                    "time_end": 2,
                },
                {
                    "stage_id": 1,
                    "offset": 0,
                    "limit": 10,
                    "time_start": 1,
                    "time_end": 2,
                },
            ),
            (
                {
                    "stage_id": 1,
                    "offset": 0,
                    "limit": 10,
                    "time_range": 100000,
                },
                {
                    "stage_id": 1,
                    "offset": 0,
                    "limit": 10,
                    "time_range": 100000,
                },
            ),
        ],
    )
    def test_validate(self, data, expected):
        slz = serializers.SearchLogQuerySerializer(data=data)
        slz.is_valid()
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "data",
        [
            # error, time_start+time_end or time_range is required
            {
                "stage_id": 1,
                "offset": 0,
                "limit": 10,
            }
        ],
    )
    def test_validate__error(self, data):
        with pytest.raises(ValidationError):
            slz = serializers.SearchLogQuerySerializer(data=data)
            slz.is_valid(raise_exception=True)


class TestLogLinkSerializer:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "request_id": "2230d0e25b274cb98b57ca5d0946d0f7",
                    "link": "test",
                },
                {
                    "link": "test",
                },
            )
        ],
    )
    def test_to_representation(self, data, expected):
        slz = serializers.LogLinkSerializer(data)
        assert slz.data == expected
