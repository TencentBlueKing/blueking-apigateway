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
from django_dynamic_fixture import G

from apigateway.apps.access_strategy.ip_group.serializers import IPGroupQuerySLZ, IPGroupSLZ
from apigateway.apps.access_strategy.models import IPGroup
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import create_request, dummy_time


class TestIPGroupQuerySLZ(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway)

    def test_to_internal_value(self):
        data = [
            {
                "query": "",
                "expected": {
                    "query": "",
                },
            },
            {
                "query": "test",
                "expected": {
                    "query": "test",
                },
            },
        ]
        for test in data:
            slz = IPGroupQuerySLZ(data=test)
            slz.is_valid()
            self.assertEqual(slz.validated_data["query"], test["expected"]["query"])


class TestIPGroupSLZ(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway)
        cls.request = create_request()
        cls.request.gateway = cls.gateway

    def test_validate_ips(self):
        data = [
            # one ip
            {
                "name": "test",
                "ips": "1.0.0.1",
                "expected": "1.0.0.1",
                "is_valid": True,
            },
            # mutiple ip
            {
                "name": "test",
                "ips": "1.0.0.1\n1.0.0.2",
                "expected": "1.0.0.1\n1.0.0.2",
                "is_valid": True,
            },
            # contain comment
            {
                "name": "test",
                "ips": "1.0.0.1\n# test\n1.0.0.2",
                "expected": "1.0.0.1\n# test\n1.0.0.2",
                "is_valid": True,
            },
            {
                "name": "test",
                "ips": "1.0.0.1\n# test\n1.0.0.555",
                "expected": "",
                "is_valid": False,
            },
        ]

        for test in data:
            slz = IPGroupSLZ(data=test, context={"request": self.request})
            is_valid = slz.is_valid()
            self.assertEqual(is_valid, test["is_valid"])
            if is_valid:
                self.assertEqual(slz.validated_data["_ips"], test["expected"])

    def test_to_internal_value(self):
        data = [
            {
                "id": 1,
                "name": "test",
                "ips": "1.0.0.1",
                "comment": "comment",
                "created_by": "2019-01-01 12:30:00",
                "expected": {
                    "api": self.gateway,
                    "name": "test",
                    "_ips": "1.0.0.1",
                    "comment": "comment",
                },
            },
        ]
        for test in data:
            slz = IPGroupSLZ(data=test, context={"request": self.request})
            slz.is_valid()
            self.assertEqual(slz.validated_data, test["expected"])

    def test_to_representation(self):
        data = [
            {
                "ip_group": IPGroup(
                    id=1,
                    api=self.gateway,
                    name="test",
                    _ips="1.0.0.1\n\n# comment\n1.0.0.2",
                    comment="comment",
                    created_by="admin",
                    created_time=dummy_time.time,
                    updated_time=dummy_time.time,
                ),
                "expected": {
                    "id": 1,
                    "name": "test",
                    "ips": "1.0.0.1\n\n# comment\n1.0.0.2",
                    "comment": "comment",
                    "created_by": "admin",
                    "created_time": dummy_time.str,
                    "updated_time": dummy_time.str,
                },
            },
        ]
        for test in data:
            slz = IPGroupSLZ(instance=test["ip_group"])
            self.assertEqual(slz.data, test["expected"])
