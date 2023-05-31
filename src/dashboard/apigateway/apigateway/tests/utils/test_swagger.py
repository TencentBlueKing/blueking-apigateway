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
from rest_framework import serializers

from apigateway.utils.swagger import get_paginated_response_serializer, get_response_serializer


class UserSerializer(serializers.Serializer):
    name = serializers.CharField()


class TestSwagger(TestCase):
    def test_get_response_serializer(self):
        data = [
            {
                "data_field": serializers.CharField(),
                "expected": serializers.CharField,
            },
            {
                "data_field": UserSerializer(),
                "expected": UserSerializer,
            },
        ]
        for test in data:
            slz = get_response_serializer(test["data_field"])
            self.assertIsInstance(slz.fields["data"], test["expected"])

    def test_get_paginated_response_serializer(self):
        data = [
            {
                "results_field": serializers.CharField(),
                "expected": serializers.CharField,
            },
            {
                "results_field": UserSerializer(),
                "expected": UserSerializer,
            },
        ]
        for test in data:
            slz = get_paginated_response_serializer(test["results_field"])
            self.assertIsInstance(slz.fields["data"].fields["results"], test["expected"])
