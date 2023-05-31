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
import json

import pytest
from ddf import G
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apigateway.apps.access_strategy.access_strategy import serializers
from apigateway.apps.access_strategy.models import AccessStrategy
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import dummy_time


class TestIPAccessControlSLZ(TestCase):
    def test_to_internal_value(self):
        data = [
            {
                "type": "allow",
                "ip_group_list": [],
            },
            {
                "type": "deny",
                "ip_group_list": [1, 2, 3],
            },
        ]
        for test in data:
            slz = serializers.IPAccessControlSLZ(data=test)
            slz.is_valid()
            self.assertEqual(slz.validated_data, test)


class TestCBWindowsSLZ:
    @pytest.mark.parametrize(
        "params, expected, will_error",
        [
            (
                {"duration": 10},
                {"duration": "10s", "buckets": 10},
                False,
            ),
            (
                {"duration": 10, "buckets": 20},
                {"duration": "10s", "buckets": 10},
                False,
            ),
            (
                {"duration": 0},
                None,
                True,
            ),
        ],
    )
    def test_validate(self, params, expected, will_error):
        slz = serializers.CBWindowSLZ(data=params)
        slz.is_valid()
        if will_error:
            assert slz.errors
            return

        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {"duration": "10s", "buckets": 10},
                {"duration": 10},
            ),
        ],
    )
    def test_to_representation(self, params, expected):
        slz = serializers.CBWindowSLZ(instance=params)
        assert slz.data == expected


class TestCBConditionsSLZ:
    @pytest.mark.parametrize(
        "params, expected, will_error",
        [
            (
                {"http_error": True, "status_code": [500], "timeout": True, "network_error": True},
                {"http_error": True, "status_code": [500], "timeout": True, "network_error": True},
                False,
            ),
            (
                {"http_error": False, "status_code": [], "timeout": False, "network_error": False},
                {"http_error": False, "status_code": [], "timeout": False, "network_error": False},
                False,
            ),
            (
                {"http_error": True, "status_code": []},
                None,
                True,
            ),
            (
                {"http_error": False, "status_code": [500]},
                None,
                True,
            ),
        ],
    )
    def test_validate(self, params, expected, will_error):
        slz = serializers.CBConditionsSLZ(data=params)
        slz.is_valid()

        if will_error:
            assert slz.errors
            return

        assert slz.validated_data == expected


class TestCBStrategySLZ:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {"type": "threshold", "options": {"threshold": 10, "rate": 1, "min_samples": 10}},
                {"type": "threshold", "options": {"threshold": 10, "rate": 0, "min_samples": 0}},
            ),
        ],
    )
    def test_validate(self, params, expected):
        slz = serializers.CBStrategySLZ(data=params)
        slz.is_valid()
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {"type": "threshold", "options": {"threshold": 10, "rate": 0, "min_samples": 0}},
                {"type": "threshold", "options": {"threshold": 10}},
            ),
        ],
    )
    def test_to_representation(self, params, expected):
        slz = serializers.CBStrategySLZ(instance=params)
        assert slz.data == expected


class TestCBBackOffSLZ:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {"type": "fixed", "options": {"interval": 10}},
                {"type": "fixed", "options": {"interval": "10s"}},
            ),
        ],
    )
    def test_validate(self, params, expected):
        slz = serializers.CBBackOffSLZ(data=params)
        slz.is_valid()
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {"type": "fixed", "options": {"interval": "10s"}},
                {"type": "fixed", "options": {"interval": 10}},
            ),
        ],
    )
    def test_to_representation(self, params, expected):
        slz = serializers.CBBackOffSLZ(instance=params)
        assert slz.data == expected


class TestCircuitBreakerSLZ:
    @pytest.mark.parametrize(
        "params,expected",
        [
            (
                {
                    "window": {"duration": 10},
                    "conditions": {
                        "http_error": True,
                        "status_code": [500, 502],
                        "timeout": True,
                        "network_error": True,
                    },
                    "strategy": {"type": "threshold", "options": {"threshold": 10}},
                    "back_off": {"type": "fixed", "options": {"interval": 10}},
                },
                {
                    "window": {"duration": "10s", "buckets": 10},
                    "conditions": {
                        "http_error": True,
                        "status_code": [500, 502],
                        "timeout": True,
                        "network_error": True,
                    },
                    "strategy": {"type": "threshold", "options": {"threshold": 10, "rate": 0, "min_samples": 0}},
                    "back_off": {"type": "fixed", "options": {"interval": "10s"}},
                },
            ),
        ],
    )
    def test_validate(self, params, expected):
        slz = serializers.CircuitBreakerSLZ(data=params)
        slz.is_valid()
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "params,expected",
        [
            (
                {
                    "window": {"duration": "10s", "buckets": 10},
                    "conditions": {
                        "http_error": True,
                        "status_code": [500, 502],
                        "timeout": True,
                        "network_error": True,
                    },
                    "strategy": {"type": "threshold", "options": {"threshold": 10, "rate": 0, "min_samples": 0}},
                    "back_off": {"type": "fixed", "options": {"interval": "10s"}},
                },
                {
                    "window": {"duration": 10},
                    "conditions": {
                        "http_error": True,
                        "status_code": [500, 502],
                        "timeout": True,
                        "network_error": True,
                    },
                    "strategy": {"type": "threshold", "options": {"threshold": 10}},
                    "back_off": {"type": "fixed", "options": {"interval": 10}},
                },
            ),
        ],
    )
    def test_to_representation(self, params, expected):
        slz = serializers.CircuitBreakerSLZ(instance=params)
        assert slz.data == expected


class TestAccessStrategySLZ:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, fake_gateway, request_factory, fake_request):
        self.gateway = fake_gateway
        self.factory = request_factory
        self.request = fake_request
        self.request.gateway = fake_gateway

    def test_validate(self):
        data = [
            # ok, ip_access_control
            {
                "ip_access_control": {
                    "type": "allow",
                    "ip_group_list": [1, 2, 3],
                },
                "rate_limit": None,
                "name": "test",
                "type": "ip_access_control",
                "comment": "comment",
                "expected": {
                    "api": self.gateway,
                    "ip_access_control": {
                        "type": "allow",
                        "ip_group_list": [1, 2, 3],
                    },
                    "rate_limit": None,
                    "name": "test",
                    "type": "ip_access_control",
                    "comment": "comment",
                    "config": {
                        "type": "allow",
                        "ip_group_list": [1, 2, 3],
                    },
                },
            },
            # ok, rate_limit -> rates_config
            {
                "rate_limit": {
                    "rates_config": [
                        {
                            "tokens": 100,
                            "period": 60,
                        }
                    ]
                },
                "type": "rate_limit",
                "name": "test",
                "comment": "comment",
                "expected": {
                    "api": self.gateway,
                    "rate_limit": {
                        "rates": {
                            "__default": [
                                {
                                    "tokens": 100,
                                    "period": 60,
                                }
                            ]
                        }
                    },
                    "name": "test",
                    "type": "rate_limit",
                    "comment": "comment",
                    "config": {
                        "rates": {
                            "__default": [
                                {
                                    "tokens": 100,
                                    "period": 60,
                                }
                            ]
                        }
                    },
                },
            },
            # ok, rate_limit -> rates
            {
                "rate_limit": {
                    "rates": {
                        "__default": [
                            {
                                "tokens": 100,
                                "period": 60,
                            }
                        ]
                    }
                },
                "type": "rate_limit",
                "name": "test",
                "comment": "comment",
                "expected": {
                    "api": self.gateway,
                    "rate_limit": {
                        "rates": {
                            "__default": [
                                {
                                    "tokens": 100,
                                    "period": 60,
                                }
                            ]
                        }
                    },
                    "name": "test",
                    "type": "rate_limit",
                    "comment": "comment",
                    "config": {
                        "rates": {
                            "__default": [
                                {
                                    "tokens": 100,
                                    "period": 60,
                                }
                            ]
                        }
                    },
                },
            },
            # error, ip_access_control is None
            {
                "ip_access_control": None,
                "rate_limit": None,
                "name": "test",
                "type": "ip_access_control",
                "comment": "comment",
                "will_error": True,
            },
            # error, instance.type != type
            {
                "instance": G(AccessStrategy, type="rate_limit", _config=json.dumps({"rates": {}})),
                "ip_access_control": {
                    "type": "allow",
                    "ip_group_list": [],
                },
                "rate_limit": None,
                "name": "test",
                "type": "ip_access_control",
                "comment": "comment",
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.AccessStrategySLZ(
                instance=test.get("instance"), data=test, context={"request": self.request}
            )
            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors
            else:
                assert not slz.errors
                assert slz.validated_data == test["expected"]

    def test_to_representation(self):
        access_strategy = G(
            AccessStrategy,
            api=self.gateway,
            name="test",
            comment="comment",
            type="ip_access_control",
            _config=json.dumps(
                {
                    "type": "allow",
                    "ip_group_list": [],
                }
            ),
        )
        slz = serializers.AccessStrategySLZ(instance=access_strategy)
        assert slz.data == {
            "id": access_strategy.id,
            "name": "test",
            "type": "ip_access_control",
            "comment": "comment",
            "ip_access_control": {
                "type": "allow",
                "ip_group_list": [],
            },
            "rate_limit": None,
            "user_verified_unrequired_apps": None,
            "error_status_code_200": None,
            "cors": None,
            "circuit_breaker": None,
        }

    def _mock_slz_data(self):
        return {
            "rate_limit": {
                "rates": {
                    "__default": [
                        {
                            "tokens": 100,
                            "period": 60,
                        }
                    ]
                }
            },
            "type": "rate_limit",
            "name": "test",
            "comment": "comment",
        }

    def test_save(self, fake_gateway, fake_request):
        fake_request.gateway = fake_gateway

        slz = serializers.AccessStrategySLZ(
            data=self._mock_slz_data(),
            context={
                "request": fake_request,
            },
        )
        slz.is_valid()
        assert not slz.errors
        slz.save()

        assert AccessStrategy.objects.filter(api=fake_gateway, name="test", type="rate_limit").exists()

    def test_update(self, patch_redis, fake_gateway, fake_request, mocker):
        mocker.patch(
            "apigateway.apps.access_strategy.access_strategy.serializers.reversion_update_signal.send",
            return_value=None,
        )
        fake_request.gateway = fake_gateway

        # 创建一个策略
        slz = serializers.AccessStrategySLZ(
            data=self._mock_slz_data(),
            context={
                "request": fake_request,
            },
        )
        slz.is_valid(raise_exception=True)
        slz.save()

        # 测试更新
        slz = serializers.AccessStrategySLZ(
            instance=slz.instance,
            data=self._mock_slz_data(),
            context={
                "request": fake_request,
            },
        )
        slz.is_valid()
        assert not slz.errors
        slz.save()

        assert AccessStrategy.objects.filter(api=fake_gateway, name="test", type="rate_limit").exists()


class TestAccessStrategyListSLZ(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway)

    def test_to_representation(self):
        access_strategy = G(
            AccessStrategy,
            api=self.gateway,
            name="test",
            comment="comment",
            type="ip_access_control",
            _config=json.dumps(
                {
                    "type": "allow",
                    "ip_group_list": [],
                }
            ),
            created_by="admin",
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
        )

        slz = serializers.AccessStrategyListSLZ(instance=[access_strategy], many=True)

        self.assertEqual(
            slz.data,
            [
                {
                    "id": access_strategy.id,
                    "name": "test",
                    "type": "ip_access_control",
                    "comment": "comment",
                    "created_by": "admin",
                    "created_time": dummy_time.str,
                    "updated_time": dummy_time.str,
                }
            ],
        )


class TestAccessStrategyCORSSLZ:
    @pytest.mark.parametrize(
        "data, expected, expected_error",
        [
            # ok
            (
                {
                    "allowed_origins": ["http://test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                    "exposed_headers": [],
                    "max_age": 0,
                    "allow_credentials": True,
                    "option_passthrough": False,
                },
                {
                    "allowed_origins": ["http://test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                    "exposed_headers": [],
                    "max_age": 0,
                    "allow_credentials": True,
                    "option_passthrough": False,
                },
                None,
            ),
            # ok, some optional field not exist
            (
                {
                    "allowed_origins": ["http://test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                },
                {
                    "allowed_origins": ["http://test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                    "option_passthrough": False,
                },
                None,
            ),
            # ok, option_passthrough=True
            (
                {
                    "allowed_origins": ["http://test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                    "option_passthrough": True,
                },
                {
                    "allowed_origins": ["http://test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                    "option_passthrough": False,
                },
                None,
            ),
            # ok, max_age is empty
            (
                {
                    "allowed_origins": ["http://test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                    "max_age": "",
                },
                {
                    "allowed_origins": ["http://test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                    "option_passthrough": False,
                },
                None,
            ),
            # error, allowed_origins invalid
            (
                {
                    "allowed_origins": ["test.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["Origin"],
                    "exposed_headers": [],
                    "max_age": 0,
                    "allow_credentials": True,
                    "option_passthrough": False,
                },
                None,
                ValidationError,
            ),
        ],
    )
    def test_validate(self, data, expected, expected_error):
        slz = serializers.AccessStrategyCORSSLZ(data=data)

        if not expected_error:
            slz.is_valid(raise_exception=True)
            assert slz.validated_data == expected
            return

        with pytest.raises(expected_error):
            slz.is_valid(raise_exception=True)


class TestAccessStrategyRateLimitSLZ:
    @pytest.mark.parametrize(
        "data, expected, will_error",
        [
            (
                {
                    "rates": {
                        "__default": [
                            {
                                "tokens": 1,
                                "period": 1,
                            },
                        ],
                    },
                },
                {
                    "rates": {
                        "__default": [
                            {
                                "tokens": 1,
                                "period": 1,
                            },
                        ],
                    },
                },
                False,
            ),
            (
                {
                    "rates_config": [
                        {
                            "tokens": 1,
                            "period": 1,
                        },
                    ],
                },
                {
                    "rates": {
                        "__default": [
                            {
                                "tokens": 1,
                                "period": 1,
                            },
                        ],
                    },
                },
                False,
            ),
            (
                {
                    "rates_config": [
                        {
                            "bk_app_code": "test",
                            "tokens": 1,
                            "period": 1,
                        },
                    ],
                },
                {
                    "rates": {
                        "test": [
                            {
                                "tokens": 1,
                                "period": 1,
                            },
                        ],
                    },
                },
                False,
            ),
            (
                {
                    "rates_config": [
                        {
                            "bk_app_code": "test",
                            "tokens": 1,
                            "period": 1,
                        },
                        {
                            "bk_app_code": "test",
                            "tokens": 1,
                            "period": 1,
                        },
                    ],
                },
                None,
                True,
            ),
        ],
    )
    def test_validate(self, data, expected, will_error):
        slz = serializers.AccessStrategyRateLimitSLZ(data=data)
        slz.is_valid()

        if will_error:
            assert slz.errors
            return

        assert not slz.errors
        assert slz.validated_data == expected
