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
from ddf import G
from rest_framework.exceptions import ValidationError

from apigateway.apps.stage_item.config import serializers
from apigateway.core.constants import StageItemTypeEnum
from apigateway.core.models import SslCertificate, SslCertificateBinding, Stage, StageItemConfig

pytestmark = pytest.mark.django_db


class TestEtcdDiscoveryConfigSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "",
                },
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "",
                    "ssl_certificate_id": None,
                    "username": "",
                    "password": "",
                },
                None,
            ),
            (
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "ssl",
                    "ssl_certificate_id": 1,
                },
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "ssl",
                    "ssl_certificate_id": 1,
                    "username": "",
                    "password": "",
                },
                None,
            ),
            (
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "password",
                    "username": "foo",
                    "password": "bar",
                },
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "password",
                    "ssl_certificate_id": None,
                    "username": "foo",
                    "password": "bar",
                },
                None,
            ),
            (
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "ssl",
                    "username": "foo",
                    "password": "bar",
                },
                None,
                ValidationError,
            ),
            (
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "password",
                    "ssl_certificate_id": 1,
                    "username": "foo",
                    "password": "",
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate(self, data, expected, expected_error):
        slz = serializers.EtcdDiscoveryConfigSLZ(data=data)

        if not expected_error:
            assert slz.is_valid(raise_exception=True)
            assert slz.validated_data == expected
            return

        with pytest.raises(expected_error):
            slz.is_valid(raise_exception=True)

    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "secure_type": "",
                    "ssl_certificate_id": None,
                },
                None,
                None,
            ),
            (
                {
                    "secure_type": "password",
                    "ssl_certificate_id": None,
                },
                None,
                None,
            ),
            (
                {
                    "secure_type": "ssl",
                    "ssl_certificate_id": 1,
                },
                1,
                None,
            ),
            (
                {
                    "secure_type": "ssl",
                    "ssl_certificate_id": None,
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_ssl_certificate_id(self, data, expected, expected_error):
        slz = serializers.EtcdDiscoveryConfigSLZ()

        if not expected_error:
            assert slz._validate_ssl_certificate_id(**data) == expected
            return

        with pytest.raises(expected_error):
            slz._validate_ssl_certificate_id(**data)

    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "secure_type": "",
                    "username": None,
                    "password": None,
                },
                {
                    "username": "",
                    "password": "",
                },
                None,
            ),
            (
                {
                    "secure_type": "ssl",
                    "username": None,
                    "password": None,
                },
                {
                    "username": "",
                    "password": "",
                },
                None,
            ),
            (
                {
                    "secure_type": "password",
                    "username": "foo",
                    "password": "bar",
                },
                {
                    "username": "foo",
                    "password": "bar",
                },
                None,
            ),
            (
                {
                    "secure_type": "password",
                    "username": "foo",
                    "password": None,
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_password(self, data, expected, expected_error):
        slz = serializers.EtcdDiscoveryConfigSLZ()

        if not expected_error:
            assert slz._validate_password(**data) == expected
            return

        with pytest.raises(expected_error):
            slz._validate_password(**data)


class TestServiceDiscoverySLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "discovery_type": "go_micro_etcd",
                    "discovery_config": {
                        "addresses": ["1.0.0.1:8000"],
                        "secure_type": "",
                    },
                },
                {
                    "discovery_type": "go_micro_etcd",
                    "discovery_config": {
                        "addresses": ["1.0.0.1:8000"],
                        "secure_type": "",
                        "ssl_certificate_id": None,
                        "username": "",
                        "password": "",
                    },
                },
            )
        ],
    )
    def test_validate(self, data, expected):
        slz = serializers.ServiceDiscoverySLZ(data=data)
        assert slz.is_valid() is True
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "discovery_type": "go_micro_etcd",
                    "discovery_config": {
                        "addresses": ["1.0.0.1:8000"],
                        "secure_type": "",
                    },
                },
                {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "",
                    "ssl_certificate_id": None,
                    "username": "",
                    "password": "",
                },
                None,
            ),
            (
                {
                    "discovery_type": "go_micro_etcd",
                    "discovery_config": {
                        "addresses": ["1.0.0.1:8000"],
                        "secure_type": "password",
                    },
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_discovery_config(self, data, expected, expected_error):
        slz = serializers.ServiceDiscoverySLZ()

        if not expected_error:
            assert slz._validate_discovery_config(**data) == expected
            return

        with pytest.raises(expected_error):
            slz._validate_discovery_config(**data)


class TestStageItemConfigSLZ:
    @pytest.mark.parametrize(
        "stage_item_type, data, expected",
        [
            (
                "node",
                {
                    "config": {
                        "nodes": [
                            {
                                "host": "1.0.0.1:8000",
                                "weight": 100,
                            },
                        ]
                    },
                },
                {
                    "config": {
                        "nodes": [
                            {
                                "host": "1.0.0.1:8000",
                                "weight": 100,
                            },
                        ]
                    },
                },
            ),
            (
                "service_discovery",
                {
                    "type": "service_discovery",
                    "config": {
                        "discovery_type": "go_micro_etcd",
                        "discovery_config": {
                            "addresses": ["1.0.0.1:8000"],
                            "secure_type": "",
                        },
                    },
                },
                {
                    "config": {
                        "discovery_type": "go_micro_etcd",
                        "discovery_config": {
                            "addresses": ["1.0.0.1:8000"],
                            "secure_type": "",
                            "ssl_certificate_id": None,
                            "username": "",
                            "password": "",
                        },
                    },
                },
            ),
        ],
    )
    def test_validate(self, fake_stage_item, stage_item_type, data, expected):
        fake_stage_item.type = stage_item_type
        slz = serializers.StageItemConfigSLZ(
            data=data, context={"api": fake_stage_item.api, "stage_item": fake_stage_item}
        )
        assert slz.is_valid() is True
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "type, config, expected, expected_error",
        [
            (
                "node",
                {
                    "nodes": [
                        {
                            "host": "1.0.0.1:8000",
                            "weight": 100,
                        },
                    ]
                },
                {
                    "nodes": [
                        {
                            "host": "1.0.0.1:8000",
                            "weight": 100,
                        },
                    ]
                },
                None,
            ),
            (
                "node",
                {"nodes": []},
                None,
                ValidationError,
            ),
            (
                "service_discovery",
                {
                    "discovery_type": "go_micro_etcd",
                    "discovery_config": {
                        "addresses": ["1.0.0.1:8000"],
                        "secure_type": "",
                    },
                },
                {
                    "discovery_type": "go_micro_etcd",
                    "discovery_config": {
                        "addresses": ["1.0.0.1:8000"],
                        "secure_type": "",
                        "ssl_certificate_id": None,
                        "username": "",
                        "password": "",
                    },
                },
                None,
            ),
            (
                "service_discovery",
                {
                    "discovery_type": "go_micro_etcd",
                    "discovery_config": {
                        "addresses": ["1.0.0.1:8000"],
                        "secure_type": "password",
                    },
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_config(self, type, config, expected, expected_error):
        slz = serializers.StageItemConfigSLZ()
        if not expected_error:
            assert slz._validate_config(type, config) == expected
            return

        with pytest.raises(expected_error):
            slz._validate_config(type, config)

    def test_validate_ssl_certificate_id(self, fake_gateway):
        with pytest.raises(ValidationError):
            serializers.StageItemConfigSLZ()._validate_ssl_certificate_id(fake_gateway.id, 1)

        ssl = G(SslCertificate, api=fake_gateway)
        serializers.StageItemConfigSLZ()._validate_ssl_certificate_id(fake_gateway.id, ssl.id)

    def test_create(self, fake_stage_item):
        fake_stage_item.type = StageItemTypeEnum.SERVICE_DISCOVERY.value
        fake_stage_item.save()

        ssl_certificate = G(SslCertificate, api=fake_stage_item.api)
        stage = G(Stage, api=fake_stage_item.api)

        data = {
            "config": {
                "discovery_type": "go_micro_etcd",
                "discovery_config": {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "ssl",
                    "ssl_certificate_id": ssl_certificate.id,
                },
            },
        }

        slz = serializers.StageItemConfigSLZ(
            data=data, context={"api": fake_stage_item.api, "stage": stage, "stage_item": fake_stage_item}
        )
        slz.is_valid(raise_exception=True)
        slz.save()

        assert StageItemConfig.objects.filter(
            api=fake_stage_item.api, stage=stage, stage_item=fake_stage_item
        ).exists()
        assert SslCertificateBinding.objects.filter(
            api=fake_stage_item.api,
            scope_id=slz.instance.id,
            ssl_certificate_id=ssl_certificate.id,
        ).exists()

    def test_update(self, fake_stage_item_config):
        fake_stage_item = fake_stage_item_config.stage_item
        fake_stage_item.type = StageItemTypeEnum.SERVICE_DISCOVERY.value
        fake_stage_item.save()

        ssl_certificate = G(SslCertificate, api=fake_stage_item.api)
        data = {
            "config": {
                "discovery_type": "go_micro_etcd",
                "discovery_config": {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "ssl",
                    "ssl_certificate_id": ssl_certificate.id,
                },
            },
        }
        slz = serializers.StageItemConfigSLZ(
            fake_stage_item_config,
            data=data,
            context={"api": fake_stage_item.api, "stage_item": fake_stage_item},
        )
        slz.is_valid(raise_exception=True)
        slz.save()

        assert StageItemConfig.objects.filter(
            api=fake_stage_item.api, stage=fake_stage_item_config.stage, stage_item=fake_stage_item
        ).exists()
        assert SslCertificateBinding.objects.filter(
            api=fake_stage_item.api,
            scope_id=slz.instance.id,
            ssl_certificate_id=ssl_certificate.id,
        ).exists()
