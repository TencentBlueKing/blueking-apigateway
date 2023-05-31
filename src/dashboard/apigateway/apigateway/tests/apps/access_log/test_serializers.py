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
from django.test import TestCase

from apigateway.apps.access_log import serializers


class TestSearchLogQuerySerializer(TestCase):
    def test_validate(self):
        data = [
            {
                "data": {
                    "api_id": 1,
                    "stage_id": 1,
                    "offset": 0,
                    "limit": 10,
                    "time_start": 1,
                    "time_end": 2,
                },
                "will_error": False,
            },
            {
                "data": {
                    "api_id": 1,
                    "stage_id": 1,
                    "offset": 0,
                    "limit": 10,
                    "time_range": 100000,
                },
                "will_error": False,
            },
            # error, time_start+time_end or time_range is required
            {
                "data": {
                    "api_id": 1,
                    "stage_id": 1,
                    "offset": 0,
                    "limit": 10,
                },
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.SearchLogQuerySerializer(data=test["data"])
            slz.is_valid()
            if test["will_error"]:
                self.assertTrue(slz.errors)
            else:
                self.assertFalse(slz.errors)


class TestLogLinkSerializer(TestCase):
    def test_to_representation(self):
        data = [
            {
                "data": {
                    "request_id": "2230d0e25b274cb98b57ca5d0946d0f7",
                    "link": "test",
                },
                "expected": {
                    "link": "test",
                },
            },
        ]
        for test in data:
            slz = serializers.LogLinkSerializer(test["data"])
            self.assertEqual(slz.data, test["expected"])
