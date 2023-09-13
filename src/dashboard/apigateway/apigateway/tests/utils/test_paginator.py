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

from apigateway.utils.paginator import LimitOffsetPaginator


class TestLimitOffsetPaginator(TestCase):
    def test_has_next(self):
        data = [
            # count < offset
            {
                "count": 1,
                "offset": 10,
                "limit": 3,
                "expected": False,
            },
            # count == offset + limit
            {
                "count": 10,
                "offset": 5,
                "limit": 5,
                "expected": False,
            },
            # count < offset + limit
            {
                "count": 10,
                "offset": 8,
                "limit": 5,
                "expected": False,
            },
            # count > offset + limit
            {
                "count": 32,
                "offset": 8,
                "limit": 5,
                "expected": True,
            },
        ]
        for test in data:
            paginator = LimitOffsetPaginator(test["count"], test["offset"], test["limit"])
            self.assertEqual(paginator.has_next(), test["expected"])

    def test_has_previous(self):
        data = [
            # offset <= 0
            {
                "count": 1,
                "offset": 0,
                "limit": 3,
                "expected": False,
            },
            # offset > 0
            {
                "count": 10,
                "offset": 5,
                "limit": 5,
                "expected": True,
            },
        ]
        for test in data:
            paginator = LimitOffsetPaginator(test["count"], test["offset"], test["limit"])
            self.assertEqual(paginator.has_previous(), test["expected"])

    def test_get_paginated_data(self):
        data = [
            {
                "count": 32,
                "offset": 10,
                "limit": 10,
                "expected": {
                    "count": 32,
                    "has_next": True,
                    "has_previous": True,
                },
            },
        ]
        for test in data:
            paginator = LimitOffsetPaginator(test["count"], test["offset"], test["limit"])
            paginated_data = paginator.get_paginated_data(["test"])
            self.assertEqual(paginated_data["count"], test["expected"]["count"])
            self.assertEqual(paginated_data["has_next"], test["expected"]["has_next"])
            self.assertEqual(paginated_data["has_previous"], test["expected"]["has_previous"])
            self.assertEqual(paginated_data["results"], ["test"])
