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
import logging

import pytest
from django_dynamic_fixture import G
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.backend import serializers
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum
from apigateway.core.models import BackendConfig, Stage


def test_ai_backend_config_rejects_non_mapping_instance():
    slz = serializers.AIBackendConfigSLZ(data={"stage_id": 1, "instances": [[{}]]})

    assert not slz.is_valid()
    assert "instances" in slz.errors


def test_ai_backend_connectivity_rejects_zero_backend_id():
    slz = serializers.AIBackendConnectivityInputSLZ(
        data={
            "backend_id": 0,
            "config": {
                "stage_id": 1,
                "provider": "openai",
                "api_key": "secret",
                "model_options": {},
                "timeout": 300,
            },
        },
        context={"gateway": None},
    )

    assert not slz.is_valid()
    assert set(slz.errors) == {"backend_id"}


def test_ai_backend_connectivity_reports_unrepresentable_existing_config(fake_backend, fake_stage):
    fake_stage.gateway.kind = GatewayKindEnum.AI.value
    fake_stage.gateway.save(update_fields=["kind"])
    fake_backend.kind = BackendKindEnum.AI.value
    fake_backend.save(update_fields=["kind"])
    backend_config = BackendConfig.objects.get(backend=fake_backend, stage=fake_stage)
    backend_config.config = {
        "timeout": 300,
        "instances": [
            {
                "name": "primary",
                "provider": "openai-compatible",
                "weight": 0,
                "auth": {"header": {"X-Api-Key": "secret", "X-Tenant": "tenant"}},
                "options": {},
                "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
            }
        ],
    }
    backend_config.save(update_fields=["_config"])
    slz = serializers.AIBackendConnectivityInputSLZ(
        data={
            "backend_id": fake_backend.id,
            "config": {
                "stage_id": fake_stage.id,
                "provider": "openai-compatible",
                "endpoint": "https://llm.example.com/v1/chat/completions",
                "auth_header": {"name": "X-Api-Key", "value": "se****et"},
                "model_options": {},
                "timeout": 300,
            },
        },
        context={"gateway": fake_stage.gateway},
    )

    with pytest.raises(ValidationError, match="无法通过 Web 接口编辑"):
        slz.is_valid(raise_exception=True)


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
                False,
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
                True,
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
                True,
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
                True,
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
                True,
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
                False,
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
                False,
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
                False,
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
                False,
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
                False,
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
                True,
            ),
        ]

        for test in data:
            record = test[0]
            will_error = test[1]
            slz = serializers.BackendInputSLZ(data=record, context={"gateway": fake_stage.gateway})

            if will_error:
                with pytest.raises(ValidationError):
                    slz.is_valid(raise_exception=True)

    def test_update_selects_backend_for_existing_configs(self, django_assert_num_queries, fake_backend, fake_stage):
        another_stage = G(Stage, gateway=fake_stage.gateway)
        config = {
            "type": "node",
            "timeout": 30,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 100}],
        }
        G(
            BackendConfig,
            gateway=fake_stage.gateway,
            stage=another_stage,
            backend=fake_backend,
            _config=config,
        )
        slz = serializers.BackendInputSLZ(
            instance=fake_backend,
            data={
                "name": fake_backend.name,
                "description": fake_backend.description,
                "type": fake_backend.type,
                "configs": [
                    {"stage_id": fake_stage.id, **config},
                    {"stage_id": another_stage.id, **config},
                ],
            },
            context={"gateway": fake_stage.gateway},
        )

        with django_assert_num_queries(2):
            slz.is_valid(raise_exception=True)

    def test_update_reports_corrupted_existing_ai_config(self, caplog, fake_backend, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save(update_fields=["kind"])
        fake_backend.kind = BackendKindEnum.AI.value
        fake_backend.save(update_fields=["kind"])
        ciphertext = "backend-ciphertext-sentinel"
        BackendConfig.objects.filter(backend=fake_backend, stage=fake_stage).update(_config={"encrypted": ciphertext})
        slz = serializers.BackendInputSLZ(
            instance=fake_backend,
            data={
                "name": fake_backend.name,
                "description": fake_backend.description,
                "type": fake_backend.type,
                "configs": [
                    {
                        "stage_id": fake_stage.id,
                        "provider": "openai",
                        "api_key": "secret",
                        "model_options": {},
                        "timeout": 300,
                    }
                ],
            },
            context={"gateway": fake_stage.gateway},
        )

        with caplog.at_level(logging.ERROR), pytest.raises(ValidationError) as exc_info:
            slz.is_valid(raise_exception=True)

        assert "configs" in exc_info.value.detail
        assert "已有后端配置无法读取" in str(exc_info.value.detail["configs"])
        assert ciphertext not in caplog.text


def test_backend_retrieve_selects_stage_and_backend(django_assert_num_queries, fake_backend, fake_stage):
    another_stage = G(Stage, gateway=fake_stage.gateway)
    G(
        BackendConfig,
        gateway=fake_stage.gateway,
        stage=another_stage,
        backend=fake_backend,
        _config={
            "type": "node",
            "timeout": 30,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 100}],
        },
    )

    with django_assert_num_queries(1):
        data = serializers.BackendRetrieveOutputSLZ(fake_backend).data

    assert {item["stage"]["id"] for item in data["configs"]} == {fake_stage.id, another_stage.id}
