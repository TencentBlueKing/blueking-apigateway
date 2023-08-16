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
import arrow
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apis.web.label.serializers import GatewayLabelInputSLZ, GatewayLabelOutputSLZ
from apigateway.apps.label.models import APILabel
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import create_request


class TestGatewayLabelOutputSLZ(TestCase):
    def test_to_representation(self):
        gateway = G(Gateway)
        updated_time = arrow.get("2019-01-01 12:30:00").datetime
        api_label = G(APILabel, api=gateway, name="test", updated_time=updated_time)

        expected = {
            "id": api_label.id,
            "name": "test",
            "updated_time": "2019-01-01 20:30:00",
        }

        slz = GatewayLabelOutputSLZ(instance=api_label)
        self.assertEqual(slz.data, expected)


class TestGatewayLabelInputSLZ(TestCase):
    def test_to_internal_value(self):
        gateway = G(Gateway)
        api_label = G(APILabel, api=gateway, name="test")
        G(APILabel, api=gateway, name="exist")

        request = create_request()
        request.gateway = gateway

        data = [
            # ok, create
            {
                "instance": None,
                "name": "new",
                "will_error": False,
                "expected": {
                    "api": gateway,
                    "name": "new",
                },
            },
            # fail, create
            {
                "instance": None,
                "name": "exist",
                "will_error": True,
            },
            # ok, update
            {
                "instance": api_label,
                "name": "update-name",
                "will_error": False,
                "expected": {
                    "api": gateway,
                    "name": "update-name",
                },
            },
            # ok, update with old-name
            {
                "instance": api_label,
                "name": "update-name",
                "will_error": False,
                "expected": {
                    "api": gateway,
                    "name": "update-name",
                },
            },
            # error, update with exist-name
            {
                "instance": api_label,
                "name": "exist",
                "will_error": True,
            },
        ]

        for test in data:
            slz = GatewayLabelInputSLZ(instance=test["instance"], data=test, context={"request": request})
            slz.is_valid()
            if test["will_error"]:
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data, test["expected"])
