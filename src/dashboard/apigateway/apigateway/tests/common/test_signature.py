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
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apigateway.common.signature import SignatureGenerator, SignatureValidator


class TestSignatureGenerator(TestCase):
    def test_generate_signature(self):
        data = [
            {
                "secret": "test",
                "method": "GET",
                "path": "/echo/",
                "params": {
                    "bk_nonce": 12345,
                    "bk_timestamp": 1881403843,
                    "shared_by": "admin",
                },
                "expected": "1b4d93765f4f81f9081897b595a789386c87a994",
            },
            {
                "secret": "test",
                "method": "GET",
                "path": "/apis/2/logs/56ce84caa368463381f4431cff9ddb41/",
                "params": {
                    "bk_nonce": 12345,
                    "bk_timestamp": 1881403843,
                    "shared_by": "admin",
                },
                "expected": "03d5d9714b50e898b14d6a9f85a9b245c7dcb5db",
            },
        ]
        for test in data:
            generator = SignatureGenerator(test["secret"])
            signature = generator.generate_signature(
                test["method"],
                test["path"],
                test["params"],
            )
            self.assertEqual(signature, test["expected"])


class TestSignatureValidator(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

    def test_is_valid(self):
        data = [
            {
                "secret": "test",
                "path": "/echo/",
                "params": {
                    "bk_nonce": 12345,
                    "bk_timestamp": 1881403843,
                    "bk_signature": "1b4d93765f4f81f9081897b595a789386c87a994",
                    "shared_by": "admin",
                },
                "expected": True,
            },
            # fail, bk_nonce invalid
            {
                "secret": "test",
                "path": "/echo/",
                "params": {
                    "bk_nonce": "a",
                    "bk_timestamp": 1881403843,
                    "bk_signature": "1b4d93765f4f81f9081897b595a789386c87a994",
                    "shared_by": "admin",
                },
                "expected": False,
            },
            # fail, bk_timestamp invalid
            {
                "secret": "test",
                "path": "/echo/",
                "params": {
                    "bk_nonce": "a",
                    "bk_timestamp": 1581403843,
                    "bk_signature": "1b4d93765f4f81f9081897b595a789386c87a994",
                    "shared_by": "admin",
                },
                "expected": False,
            },
            # fail, bk_signature invalid
            {
                "secret": "test",
                "path": "/echo/",
                "params": {
                    "bk_nonce": 12345,
                    "bk_timestamp": 1881403843,
                    "bk_signature": "ac5e93765f4f81f9081897b595a789386c87a994",
                    "shared_by": "admin",
                },
                "expected": False,
            },
        ]
        for test in data:
            request = self.factory.get(test["path"], data=test["params"])
            validator = SignatureValidator(
                test["secret"],
                Request(request),
                timestamp_expire_seconds=10,
            )
            self.assertEqual(validator.is_valid(raise_exception=False), test["expected"])
