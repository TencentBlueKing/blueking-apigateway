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

from apigateway.apis.web.backend import serializers


class TestBackendInputSLZ:
    def test_to_internal_value(self, fake_stage):
        data = [
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "http",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                        }
                    ],
                },
                {False},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "http",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "grpc", "host": "www.example.com", "weight": 1}
                            ],  # 类型是http,但是scheme是grpc报错
                        }
                    ],
                },
                {True},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "http",
                    "configs": [
                        {
                            "stage_id": 0,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "http", "host": "www.example.com", "weight": 1}
                            ],  # stage_id为0找不到该配置
                        }
                    ],
                },
                {True},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "http",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                        },
                        {
                            "stage_id": 0,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [{"scheme": "http", "host": "www.example1.com", "weight": 1}],
                        },
                    ],
                },
                {True},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "http",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "http", "host": "www.example.com", "weight": 1},
                                {"scheme": "https", "host": "www.example.com", "weight": 1},
                            ],
                        }
                    ],
                },
                {True},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "http",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "http", "host": "www.example.com", "weight": 1},
                                {"scheme": "http", "host": "www.example1.com", "weight": 1},
                            ],
                        }
                    ],
                },
                {False},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "grpc",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [{"scheme": "grpc", "host": "www.example.com", "weight": 1}],
                        }
                    ],
                },
                {False},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "grpc",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "grpcs", "host": "www.example.com", "weight": 1},
                            ],
                        }
                    ],
                },
                {False},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "grpc",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "grpc", "host": "www.example.com", "weight": 1},
                                {"scheme": "grpc", "host": "www.example1.com", "weight": 1},
                            ],
                        }
                    ],
                },
                {False},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "grpc",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "grpc", "host": "www.example.com", "weight": 1},
                                {"scheme": "grpc", "host": "www.example1.com", "weight": 1},
                            ],
                        }
                    ],
                },
                {False},
            ),
            (
                {
                    "gateway": fake_stage.gateway,
                    "name": "backend-test",
                    "description": "test",
                    "type": "grpc",
                    "configs": [
                        {
                            "stage_id": fake_stage.id,
                            "type": "node",
                            "timeout": 1,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {"scheme": "grpc", "host": "www.example.com", "weight": 1},
                                {"scheme": "grpcs", "host": "www.example.com", "weight": 1},
                            ],
                        }
                    ],
                },
                {True},
            ),
        ]

        for test in data:
            slz = serializers.BackendInputSLZ(data=test[0], context={"gateway": fake_stage.gateway})

            if test[1] is True:
                with pytest.raises(ValidationError):
                    slz.is_valid(raise_exception=True)
