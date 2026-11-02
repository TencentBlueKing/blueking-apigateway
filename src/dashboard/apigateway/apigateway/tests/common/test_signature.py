# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apigateway.common.signature import SignatureGenerator, SignatureValidator

pytestmark = pytest.mark.no_meta_schema


class TestSignatureGenerator:
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
            assert signature == test["expected"]


class TestSignatureValidator:
    @pytest.mark.parametrize(
        "nonce, timestamp, signature_valid, expected_error",
        [
            (12345, 1000, True, None),
            (12345, 990, True, None),
            (12345, 989, True, "bk_timestamp has expired"),
            ("a", 1000, True, "bk_nonce is illegal"),
            (0, 1000, True, "bk_nonce is illegal, must be a positive integer"),
            (12345, None, True, "bk_timestamp is required"),
            (12345, "bad", True, "bk_timestamp is illegal, must be a timestamp integer"),
            (12345, 1000, False, "bk_signature validate failed, please check if the parameters are correct"),
        ],
    )
    def test_is_valid(self, mocker, nonce, timestamp, signature_valid, expected_error):
        mocker.patch("apigateway.common.signature.time.time", return_value=1000)
        params = {"bk_nonce": nonce, "shared_by": "admin"}
        if timestamp is not None:
            params["bk_timestamp"] = timestamp
        signature = SignatureGenerator("test").generate_signature("GET", "/echo/", params)
        params["bk_signature"] = signature if signature_valid else "invalid-signature"
        request = APIRequestFactory().get("/echo/", data=params)
        validator = SignatureValidator("test", Request(request), timestamp_expire_seconds=10)
        assert validator.is_valid(raise_exception=False) is (expected_error is None)
        assert validator.error == expected_error
