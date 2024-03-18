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
import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.stage import serializers


class TestStageInputSLZ:
    def test_to_internal_value(self, fake_gateway, fake_backend):
        data = [
            {
                "gateway": fake_gateway,
                "name": "stage-test",
                "description": "test",
                "backends": [
                    {
                        "id": fake_backend.id,
                        "config": {
                            "type": "node",
                            "timeout": {"connect": 1, "read": 1, "send": 1},
                            "loadbalance": "roundrobin",
                            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                            "retries": 0,
                            "retry_timeout": 0,
                        },
                    }
                ],
            },
            {
                "gateway": fake_gateway,
                "name": "stage-test",
                "description": "test",
                "backends": [
                    {
                        "id": 0,
                        "config": {
                            "type": "node",
                            "timeout": {"connect": 1, "read": 1, "send": 1},
                            "loadbalance": "roundrobin",
                            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                            "retries": 0,
                            "retry_timeout": 0,
                        },
                    }
                ],
                "will_error": True,
            },
            {
                "gateway": fake_gateway,
                "name": "stage-test",
                "description": "test",
                "backends": [],
                "will_error": True,
            },
            {
                "gateway": fake_gateway,
                "name": "stage-test",
                "description": "test",
                "backends": [
                    {
                        "id": fake_backend.id,
                        "config": {
                            "type": "node",
                            "timeout": {"connect": 1, "read": 1, "send": 1},
                            "loadbalance": "roundrobin",
                            "hosts": [{"scheme": "grpc", "host": "www.example.com", "weight": 1}],
                            "retries": 0,
                            "retry_timeout": 0,
                        },
                    }
                ],
                "will_error": True,
            },
        ]

        for test in data:
            slz = serializers.StageInputSLZ(data=test, context={"gateway": fake_gateway})

            if not test.get("will_error"):
                slz.is_valid(raise_exception=True)
                assert test == slz.validated_data
                continue

            with pytest.raises(ValidationError):
                slz.is_valid(raise_exception=True)


class TestBackendConfigInputSLZ:
    def test_to_internal_value(self, fake_backend):
        data = [
            {
                "type": "node",
                "timeout": {"connect": 1, "read": 1, "send": 1},
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                "retries": 0,
                "retry_timeout": 0,
            },
            {
                "type": "node",
                "timeout": {"connect": 1, "read": 1, "send": 1},
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "grpc", "host": "www.example.com", "weight": 1}],
                "retries": 0,
                "retry_timeout": 0,
                "will_error": True,
            },
        ]

        for test in data:
            slz = serializers.BackendConfigInputSLZ(data=test, context={"backend": fake_backend})

            if not test.get("will_error"):
                slz.is_valid(raise_exception=True)
                assert test == slz.validated_data
                continue

            with pytest.raises(ValidationError):
                slz.is_valid(raise_exception=True)
