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

from apigateway.apps.backend_service import serializers
from apigateway.core.models import BackendService, SslCertificate, SslCertificateBinding, StageItem

pytestmark = pytest.mark.django_db


class TestTimeoutSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_valid",
        [
            (
                {"connect": 1, "send": 1, "read": 1},
                {"connect": 1, "send": 1, "read": 1},
                True,
            ),
            (
                {"connect": 1, "send": 1, "read": 0},
                {},
                False,
            ),
            (
                {"connect": 1, "send": 1, "read": 24 * 60 * 60},
                {},
                False,
            ),
        ],
    )
    def test_validate(self, data, expected, expected_valid):
        slz = serializers.TimeoutSLZ(data=data)

        assert slz.is_valid() is expected_valid
        assert slz.validated_data == expected


class TestBackendServiceSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_valid",
        [
            # node ok
            (
                {
                    "name": "foo",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "node",
                    "stage_item_id": None,
                    "upstream_custom_config": {
                        "nodes": [
                            {
                                "host": "1.0.0.1:8000",
                                "weight": 100,
                            }
                        ]
                    },
                    "pass_host": "pass",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": False,
                },
                {
                    "name": "foo",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "node",
                    "stage_item_id": None,
                    "upstream_custom_config": {
                        "nodes": [
                            {
                                "host": "1.0.0.1:8000",
                                "weight": 100,
                            }
                        ]
                    },
                    "upstream_config": {},
                    "pass_host": "pass",
                    "upstream_host": "",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": False,
                },
                True,
            ),
            # service_discovery ok
            (
                {
                    "name": "foo",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "service_discovery",
                    "stage_item_id": None,
                    "upstream_custom_config": {
                        "discovery_type": "go_micro_etcd",
                        "discovery_config": {
                            "addresses": ["1.0.0.1:8000"],
                            "secure_type": "password",
                            "username": "foo",
                            "password": "bar",
                        },
                    },
                    "upstream_config": {
                        "service_name": "my-service",
                    },
                    "pass_host": "rewrite",
                    "upstream_host": "test.blueking.com",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": True,
                },
                {
                    "name": "foo",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "service_discovery",
                    "stage_item_id": None,
                    "upstream_custom_config": {
                        "discovery_type": "go_micro_etcd",
                        "discovery_config": {
                            "addresses": ["1.0.0.1:8000"],
                            "secure_type": "password",
                            "ssl_certificate_id": None,
                            "username": "foo",
                            "password": "bar",
                        },
                    },
                    "upstream_config": {
                        "service_name": "my-service",
                    },
                    "pass_host": "rewrite",
                    "upstream_host": "test.blueking.com",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": True,
                },
                True,
            ),
            # upstream_custom_config invalid
            (
                {
                    "name": "foo",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "node",
                    "stage_item_id": None,
                    "upstream_custom_config": {"nodes": []},  # type: ignore
                    "pass_host": "rewrite",
                    "upstream_host": "test.blueking.com",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": True,
                },
                {},
                False,
            ),
            # upstream_config invalid
            (
                {
                    "name": "foo",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "service_discovery",
                    "stage_item_id": None,
                    "upstream_custom_config": {
                        "discovery_type": "go_micro_etcd",
                        "discovery_config": {
                            "addresses": ["1.0.0.1:8000"],
                            "secure_type": "password",
                            "username": "foo",
                            "password": "bar",
                        },
                    },
                    "upstream_config": {},
                    "pass_host": "pass",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": True,
                },
                {},
                False,
            ),
            # upstream_host invalid
            (
                {
                    "name": "foo",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "node",
                    "stage_item_id": None,
                    "upstream_custom_config": {
                        "nodes": [
                            {
                                "host": "1.0.0.1:8000",
                                "weight": 100,
                            }
                        ]
                    },
                    "pass_host": "rewrite",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": True,
                },
                {},
                False,
            ),
        ],
    )
    def test_validate(self, fake_gateway, mocker, data, expected, expected_valid):
        slz = serializers.BackendServiceSLZ(data=data, context={"api": fake_gateway})

        mocker.patch.object(slz, "_validate_discovery_ssl_certificate_id", return_value=None)
        mocker.patch.object(slz, "_validate_stage_item_id", return_value=None)

        assert slz.is_valid() is expected_valid

        if not expected_valid:
            return

        expected["api"] = fake_gateway
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "stage_item_id": 1,
                    "upstream_type": "node",
                    "upstream_custom_config": {
                        "foo": "bar",
                    },
                },
                {},
                None,
            ),
            (
                {
                    "stage_item_id": None,
                    "upstream_type": "node",
                    "upstream_custom_config": {
                        "nodes": [
                            {
                                "host": "1.0.0.1:8000",
                                "weight": 100,
                            }
                        ]
                    },
                },
                {
                    "nodes": [
                        {
                            "host": "1.0.0.1:8000",
                            "weight": 100,
                        }
                    ]
                },
                None,
            ),
            (
                {
                    "stage_item_id": None,
                    "upstream_type": "service_discovery",
                    "upstream_custom_config": {
                        "discovery_type": "go_micro_etcd",
                        "discovery_config": {
                            "addresses": ["1.0.0.1:8000"],
                            "secure_type": "password",
                            "username": "foo",
                            "password": "bar",
                        },
                    },
                },
                {
                    "discovery_type": "go_micro_etcd",
                    "discovery_config": {
                        "addresses": ["1.0.0.1:8000"],
                        "secure_type": "password",
                        "ssl_certificate_id": None,
                        "username": "foo",
                        "password": "bar",
                    },
                },
                None,
            ),
            # invalid
            (
                {"stage_item_id": None, "upstream_type": "node", "upstream_custom_config": {"nodes": []}},
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_upstream_custom_config(self, data, expected, expected_error):
        slz = serializers.BackendServiceSLZ()

        if expected_error:
            with pytest.raises(expected_error):
                slz._validate_upstream_custom_config(**data)
            return

        assert slz._validate_upstream_custom_config(**data) == expected

    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "upstream_type": "node",
                    "upstream_config": {},
                },
                {},
                None,
            ),
            (
                {
                    "upstream_type": "service_discovery",
                    "upstream_config": {
                        "service_name": "my-service",
                    },
                },
                {
                    "service_name": "my-service",
                },
                None,
            ),
            (
                {
                    "upstream_type": "service_discovery",
                    "upstream_config": {},
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_upstream_config(self, data, expected, expected_error):
        slz = serializers.BackendServiceSLZ()

        if expected_error:
            with pytest.raises(expected_error):
                slz._validate_upstream_config(**data)
            return

        assert slz._validate_upstream_config(**data) == expected

    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            (
                {
                    "pass_host": "pass",
                    "upstream_host": "test.blueking.com",
                },
                "",
                None,
            ),
            (
                {
                    "pass_host": "node",
                    "upstream_host": "test.blueking.com",
                },
                "",
                None,
            ),
            (
                {
                    "pass_host": "rewrite",
                    "upstream_host": "test.blueking.com",
                },
                "test.blueking.com",
                None,
            ),
            (
                {
                    "pass_host": "rewrite",
                    "upstream_host": "",
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate_upstream_host(self, data, expected, expected_error):
        slz = serializers.BackendServiceSLZ()

        if expected_error:
            with pytest.raises(expected_error):
                slz._validate_upstream_host(**data)
            return

        assert slz._validate_upstream_host(**data) == expected

    def test_create(self, fake_gateway, unique_backend_service_name):
        ssl_certificate = G(SslCertificate, api=fake_gateway)

        data = {
            "name": unique_backend_service_name,
            "description": "this is a test",
            "loadbalance": "roundrobin",
            "upstream_type": "service_discovery",
            "stage_item_id": None,
            "upstream_custom_config": {
                "discovery_type": "go_micro_etcd",
                "discovery_config": {
                    "addresses": ["1.0.0.1:8000"],
                    "secure_type": "ssl",
                    "ssl_certificate_id": ssl_certificate.id,
                },
            },
            "upstream_config": {
                "service_name": "my-service",
            },
            "pass_host": "pass",
            "scheme": "http",
            "timeout": {"connect": 10, "send": 10, "read": 10},
            "ssl_enabled": False,
        }

        slz = serializers.BackendServiceSLZ(data=data, context={"api": fake_gateway})
        slz.is_valid(raise_exception=True)
        slz.save()

        assert BackendService.objects.filter(api=fake_gateway, id=slz.instance.id).exists()
        assert SslCertificateBinding.objects.filter(
            api=fake_gateway,
            scope_id=slz.instance.id,
            ssl_certificate_id=ssl_certificate.id,
        ).exists()

    def test_update(self, fake_gateway, faker, mocker):
        instance = G(BackendService, api=fake_gateway)
        ssl_certificate = G(SslCertificate, api=fake_gateway)

        slz = serializers.BackendServiceSLZ(instance, data={})

        mocker.patch.object(slz, "_get_discovery_ssl_certificate_id", return_value=ssl_certificate.id)
        slz.update(instance, {"api": fake_gateway})
        assert SslCertificateBinding.objects.filter(
            api=fake_gateway,
            scope_id=instance.id,
            ssl_certificate_id=ssl_certificate.id,
        ).exists()

        mocker.patch.object(slz, "_get_discovery_ssl_certificate_id", return_value=None)
        slz.update(instance, {"api": fake_gateway})
        assert not SslCertificateBinding.objects.filter(
            api=fake_gateway,
            scope_id=instance.id,
            ssl_certificate_id=ssl_certificate.id,
        ).exists()

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "upstream_type": "node",
                },
                None,
            ),
            (
                {
                    "upstream_type": "service_discovery",
                    "stage_item_id": 1,
                },
                None,
            ),
            (
                {
                    "upstream_type": "service_discovery",
                    "stage_item_id": None,
                    "upstream_custom_config": {"discovery_config": {"ssl_certificate_id": 1}},
                },
                1,
            ),
        ],
    )
    def test_get_discovery_ssl_certificate_id(self, data, expected):
        slz = serializers.BackendServiceSLZ()
        assert slz._get_discovery_ssl_certificate_id(data) == expected

    def test_validate_discovery_ssl_certificate_id(self, fake_gateway):
        slz = serializers.BackendServiceSLZ()

        assert slz._validate_discovery_ssl_certificate_id(fake_gateway.id, None) is None

        with pytest.raises(ValidationError):
            slz._validate_discovery_ssl_certificate_id(fake_gateway.id, 1)

        ssl_certificate = G(SslCertificate, api=fake_gateway)
        assert slz._validate_discovery_ssl_certificate_id(fake_gateway.id, ssl_certificate.id) is None

    def test_validate_stage_item_id(self, fake_gateway):
        slz = serializers.BackendServiceSLZ()

        assert slz._validate_stage_item_id(fake_gateway.id, None) is None

        with pytest.raises(ValidationError):
            slz._validate_stage_item_id(fake_gateway.id, 1)

        stage_item = G(StageItem, api=fake_gateway)
        assert slz._validate_stage_item_id(fake_gateway.id, stage_item.id) is None

    @pytest.mark.parametrize(
        "instance, expected",
        [
            (
                {
                    "name": "validate-node",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "service_discovery",
                    "stage_item_id": None,
                    "upstream_custom_config": {
                        "discovery_type": "go_micro_etcd",
                        "discovery_config": {
                            "addresses": ["1.0.0.1:8000"],
                            "secure_type": "tls",
                            "ssl_certificate_id": 10,
                        },
                    },
                    "upstream_config": {
                        "service_name": "my-service",
                    },
                    "pass_host": "pass",
                    "upstream_host": "",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": False,
                },
                {
                    "name": "validate-node",
                    "description": "this is a test",
                    "loadbalance": "roundrobin",
                    "upstream_type": "service_discovery",
                    "stage_item_id": None,
                    "upstream_custom_config": {
                        "discovery_type": "go_micro_etcd",
                        "discovery_config": {
                            "addresses": ["1.0.0.1:8000"],
                            "secure_type": "tls",
                            "ssl_certificate_id": 10,
                        },
                    },
                    "upstream_config": {
                        "service_name": "my-service",
                    },
                    "pass_host": "pass",
                    "upstream_host": "",
                    "scheme": "http",
                    "timeout": {"connect": 10, "send": 10, "read": 10},
                    "ssl_enabled": False,
                },
            ),
        ],
    )
    def test_to_representation(self, fake_gateway, instance, expected):
        service = G(BackendService, api=fake_gateway, **instance)

        slz = serializers.BackendServiceSLZ(service)

        expected.update(
            {
                "id": service.id,
            }
        )

        assert slz.data == expected
