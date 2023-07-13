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
import uuid

import pytest
from ddf import G
from django.test import TestCase
from rest_framework.serializers import ValidationError

from apigateway.apps.stage import serializers
from apigateway.biz.stage import StageHandler
from apigateway.common.contexts import StageProxyHTTPContext, StageRateLimitContext
from apigateway.core import constants
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Context, Gateway, MicroGateway, Release, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_request, dummy_time


class TestHostSLZ(TestCase):
    def test_to_internal_value(self):
        data = [
            # host, weight ok
            {
                "host": "http://www.a.com",
                "weight": 100,
                "will_error": False,
                "expected": {
                    "host": "http://www.a.com",
                    "weight": 100,
                },
            },
            # only has host
            {
                "host": "http://www.a.com",
                "will_error": False,
                "expected": {
                    "host": "http://www.a.com",
                },
            },
            # host is empty
            {
                "host": "",
                "weight": 100,
                "will_error": True,
            },
            # weight invalid
            {
                "host": "http://www.a.com",
                "weight": -1,
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.HostSLZ(data=test)
            slz.is_valid()
            if test["will_error"]:
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data, test["expected"])


class TestUpstreamsSLZ(TestCase):
    def test_to_internal_value(self):
        data = [
            # weighted-rr, ok
            {
                "loadbalance": "weighted-roundrobin",
                "hosts": [
                    {
                        "host": "http://www.a.com",
                        "weight": 100,
                    }
                ],
                "will_error": False,
                "expected": {
                    "loadbalance": "weighted-roundrobin",
                    "hosts": [
                        {
                            "host": "http://www.a.com",
                            "weight": 100,
                        }
                    ],
                },
            },
            # rr, ok
            {
                "loadbalance": "roundrobin",
                "hosts": [
                    {
                        "host": "http://www.a.com",
                    }
                ],
                "will_error": False,
                "expected": {
                    "loadbalance": "roundrobin",
                    "hosts": [
                        {
                            "host": "http://www.a.com",
                            "weight": 100,
                        }
                    ],
                },
            },
            # only roundrobin, error
            {
                "loadbalance": "roundrobin",
                "will_error": True,
            },
            # only hosts, error
            {
                "hosts": [
                    {
                        "host": "http://www.a.com",
                    }
                ],
                "will_error": True,
            },
            # wrr, host weight is required, error
            {
                "loadbalance": "weighted-roundrobin",
                "hosts": [
                    {
                        "host": "http://www.a.com",
                    }
                ],
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.UpstreamsSLZ(data=test)
            slz.is_valid()
            if test["will_error"]:
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data, test["expected"])


class TestTransformHeadersSLZ(TestCase):
    def test_to_internal_value(self):
        data = [
            {
                # 'add': {'k1': 'v1', 'k2': 'v2'},
                # 'append': {'k1': 'v1', 'k2': 'v2'},
                # 'replace': {'k1': 'v1', 'k2': 'v2'},
                "set": {"k1": "v1", "k2": "v2"},
                "delete": ["k1", "k2"],
            },
        ]
        for test in data:
            slz = serializers.TransformHeadersSLZ(data=test)
            slz.is_valid()
            self.assertEqual(slz.validated_data, test)

    def test_validate(self):
        data = [
            # error, header key include '_'
            {
                "set": {"X_Token": "test"},
                "will_error": True,
            },
            {
                "delete": ["X_Token"],
                "will_error": True,
            },
            # error, header key is blank
            {
                "set": {"": "test"},
                "will_error": True,
            },
            # error, length > 100
            {
                "set": {"a" * 101: "test"},
                "will_error": True,
            },
            # ok
            {
                "set": {"X-Token": "test"},
                "will_error": False,
            },
        ]
        for test in data:
            slz = serializers.TransformHeadersSLZ(data=test)
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertFalse(slz.errors)


class TestStageSLZ:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.gateway = G(Gateway)
        self.request = create_request()
        self.request.gateway = self.gateway

    @pytest.mark.parametrize(
        "data, will_error, expected",
        [
            # ok
            (
                {
                    "name": "prod",
                    "description": "test",
                    "vars": {"test": 123},
                    "proxy_http": {
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {"k1": "v1"},
                        },
                    },
                    "rate_limit": {
                        "enabled": True,
                        "rate": {
                            "tokens": 100,
                            "period": 60,
                        },
                    },
                },
                False,
                {
                    "name": "prod",
                    "description": "test",
                    "vars": {"test": "123"},
                    "proxy_http": {
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {"k1": "v1"},
                        },
                    },
                    "rate_limit": {
                        "enabled": True,
                        "rate": {
                            "tokens": 100,
                            "period": 60,
                        },
                    },
                },
            ),
            # rate-limit not exist
            (
                {
                    "name": "prod",
                    "description": "test",
                    "vars": {"test": 123},
                    "proxy_http": {
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {"k1": "v1"},
                        },
                    },
                },
                False,
                {
                    "name": "prod",
                    "description": "test",
                    "vars": {"test": "123"},
                    "proxy_http": {
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {"k1": "v1"},
                        },
                    },
                },
            ),
        ],
    )
    def test_to_internal_value(self, data, will_error, expected):
        slz = serializers.StageSLZ(data=data, context={"request": self.request})
        if will_error:
            with pytest.raises(ValidationError):
                slz.is_valid(raise_exception=True)
            return

        slz.is_valid(raise_exception=True)
        expected["api"] = self.gateway
        assert slz.validated_data == expected

    def test_to_representation(self):
        unique_id = uuid.uuid4()
        micro_gateway = G(MicroGateway, api=self.gateway, id=unique_id)
        stage = G(Stage, _vars='{"test": "123"}', status=0, micro_gateway=micro_gateway, api=self.gateway)
        G(
            Context,
            scope_type=constants.ContextScopeTypeEnum.STAGE.value,
            scope_id=stage.id,
            type=constants.ContextTypeEnum.STAGE_PROXY_HTTP.value,
            _config=json.dumps(
                {
                    "timeout": 30,
                    "upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {
                                "host": "http://www.a.com",
                            }
                        ],
                    },
                    "transform_headers": {
                        "set": {"k1": "v1"},
                    },
                }
            ),
        )
        G(
            Context,
            scope_type=constants.ContextScopeTypeEnum.STAGE.value,
            scope_id=stage.id,
            type=constants.ContextTypeEnum.STAGE_RATE_LIMIT.value,
            _config=json.dumps(
                {
                    "enabled": True,
                    "rate": {
                        "tokens": 100,
                        "period": 60,
                    },
                }
            ),
        )
        expected = {
            "id": stage.id,
            "name": stage.name,
            "status": stage.status,
            "description": stage.description,
            "description_en": stage.description_en,
            "vars": {
                "test": "123",
            },
            "proxy_http": {
                "timeout": 30,
                "upstreams": {
                    "loadbalance": "roundrobin",
                    "hosts": [
                        {
                            "host": "http://www.a.com",
                        }
                    ],
                },
                "transform_headers": {
                    "set": {"k1": "v1"},
                },
            },
            "rate_limit": {
                "enabled": True,
                "rate": {
                    "tokens": 100,
                    "period": 60,
                },
            },
            "micro_gateway_id": str(micro_gateway.id),
        }
        slz = serializers.StageSLZ(instance=stage)
        assert slz.data == expected

    def test_validate_vars(self, mocker):
        stage = G(Stage, api=self.gateway, status=1)
        resource_version = G(ResourceVersion, api=self.gateway)
        G(Release, api=self.gateway, stage=stage, resource_version=resource_version)

        stage_data = {
            "name": "prod",
            "description": "",
            "proxy_http": {
                "timeout": 30,
                "upstreams": {
                    "loadbalance": "roundrobin",
                    "hosts": [
                        {
                            "host": "http://www.a.com",
                        }
                    ],
                },
                "transform_headers": {},
            },
            "rate_limit": {
                "enabled": True,
                "rate": {
                    "tokens": 100,
                    "period": 60,
                },
            },
        }

        data = [
            # ok
            {
                "vars": {
                    "prefix": "/o",
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": False,
            },
            # key error, first is not char
            {
                "vars": {
                    "12345": "a",
                },
                "mock_used_stage_vars": {},
                "will_error": True,
            },
            # value error, var in path not exist
            {
                "vars": {
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
        ]
        for test in data:
            stage_data.update(vars=test["vars"])
            slz = serializers.StageSLZ(instance=stage, data=stage_data, context={"request": self.request})
            mocker.patch(
                "apigateway.apps.stage.validators.ResourceVersion.objects.get_used_stage_vars",
                return_value=test["mock_used_stage_vars"],
            )
            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors, test["params"]
            else:
                assert not slz.errors, test["params"]

    @pytest.mark.parametrize(
        "data, will_error",
        [
            (
                {
                    "name": "prod",
                    "description": "test",
                    "vars": {
                        "test": "123",
                    },
                    "proxy_http": {
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {"k1": "v1"},
                        },
                    },
                    "rate_limit": {
                        "enabled": True,
                        "rate": {
                            "tokens": 100,
                            "period": 60,
                        },
                    },
                },
                False,
            ),
            (
                {
                    "name": "test",
                    "description": "test",
                    "vars": {
                        "test": "123",
                    },
                    "proxy_http": {
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {"k1": "v1"},
                        },
                    },
                },
                False,
            ),
        ],
    )
    def test_create(self, data, will_error, fake_gateway, fake_request):
        fake_request.gateway = fake_gateway
        micro_gateway = G(MicroGateway, api=fake_gateway)
        data["api"] = fake_gateway
        data["micro_gateway_id"] = micro_gateway.id
        slz = serializers.StageSLZ(data=data, context={"request": fake_request})
        slz.is_valid()
        if will_error:
            assert slz.errors
            return

        slz.save(created_by="", status=StageStatusEnum.INACTIVE.value)
        stage = Stage.objects.get(api=fake_gateway, name=data["name"])
        assert stage.description == data["description"]
        assert stage.vars == data["vars"]
        assert stage.status == constants.StageStatusEnum.INACTIVE.value
        assert stage.micro_gateway.id == micro_gateway.id
        assert StageProxyHTTPContext().filter_contexts(scope_ids=[stage.id]).exists()
        assert StageRateLimitContext().filter_contexts(scope_ids=[stage.id]).exists()

    @pytest.mark.parametrize(
        "data, will_error",
        [
            (
                {
                    "name": "test-05",
                    "description": "t2",
                    "status": 1,
                    "vars": {
                        "test": "test",
                    },
                    "proxy_http": {
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "weighted-roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.b.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {"k2": "v2"},
                        },
                    },
                    "rate_limit": {
                        "enabled": True,
                        "rate": {
                            "tokens": 200,
                            "period": 3600,
                        },
                    },
                },
                False,
            ),
            (
                {
                    "name": "test-05",
                    "description": "t2",
                    "status": 1,
                    "vars": {
                        "test": "test",
                    },
                    "proxy_http": {
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "weighted-roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.b.com",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {"k2": "v2"},
                        },
                    },
                },
                False,
            ),
        ],
    )
    def test_update(self, data, will_error, fake_gateway, fake_request):
        micro_gateway = G(MicroGateway, api=fake_gateway)
        stage = G(
            Stage, api=fake_gateway, name="test-03", status=0, description="t1", _vars=json.dumps({"test": "123"})
        )

        fake_request.gateway = fake_gateway
        data["micro_gateway_id"] = str(micro_gateway.id)
        slz = serializers.StageSLZ(
            stage,
            data=data,
            context={
                "request": fake_request,
            },
        )
        slz.is_valid()

        slz.save(status=1)

        stage = Stage.objects.get(api=fake_gateway, name="test-03")
        assert stage.status == 0
        assert stage.vars == data["vars"]
        assert stage.micro_gateway.id == micro_gateway.id
        assert StageProxyHTTPContext().get_config(stage.id) == data["proxy_http"]
        if data.get("rate_limit"):
            assert StageRateLimitContext().get_config(stage.id) == data["rate_limit"]
        else:
            assert not StageRateLimitContext().filter_contexts(scope_ids=[stage.id]).exists()

    def test_validate_micro_gateway_id(self, fake_gateway, fake_request):
        unique_id = uuid.uuid4()
        fake_request.gateway = fake_gateway

        micro_gateway = G(MicroGateway, api=fake_gateway)

        slz = serializers.StageSLZ({}, context={"request": fake_request})
        assert slz.validate_micro_gateway_id(None) is None
        assert slz.validate_micro_gateway_id(micro_gateway.id) == micro_gateway.id

        with pytest.raises(ValidationError):
            slz.validate_micro_gateway_id(unique_id)

    def test_validate_micro_gateway_stage_unique(self, fake_gateway, fake_request):
        fake_request.gateway = fake_gateway

        micro_gateway = G(MicroGateway, api=fake_gateway)
        s1 = G(Stage, api=fake_gateway, micro_gateway=micro_gateway)
        s2 = G(Stage, api=fake_gateway)

        slz = serializers.StageSLZ({}, context={"request": fake_request})
        assert slz._validate_micro_gateway_stage_unique(None) is None

        slz = serializers.StageSLZ(instance=s1, context={"request": fake_request})
        assert slz._validate_micro_gateway_stage_unique(micro_gateway.id) is None

        # micro-gateway has related to s1
        slz = serializers.StageSLZ(instance=s2, context={"request": fake_request})
        with pytest.raises(ValidationError):
            slz._validate_micro_gateway_stage_unique(micro_gateway.id)


class TestUpdateStageStatusSLZ(TestCase):
    def test(self):
        data = [
            # ok
            {
                "status": 0,
                "will_error": False,
                "expected": {
                    "status": 0,
                },
            },
            # ok, input parameters include is_public
            {
                "status": 0,
                "other_parameter": "test",
                "will_error": False,
                "expected": {
                    "status": 0,
                },
            },
            {
                "status": 100,
                "will_error": True,
            },
        ]

        stage = G(Stage)

        for test in data:
            slz = serializers.UpdateStageStatusSLZ(instance=stage, data=test)
            slz.is_valid()
            if test["will_error"]:
                self.assertTrue(slz.errors)
                continue
            self.assertEqual(slz.validated_data, test["expected"])


class TestListStageSLZ:
    def test_to_representation(self, fake_gateway):
        micro_gateway = G(MicroGateway, api=fake_gateway)

        stage_prod = G(Stage, api=fake_gateway, name="prod", status=0)
        stage_test = G(Stage, api=fake_gateway, name="test", status=0, micro_gateway=micro_gateway)

        expected = [
            {
                "id": stage_prod.id,
                "name": stage_prod.name,
                "description": stage_prod.description,
                "description_en": stage_prod.description_en,
                "status": stage_prod.status,
                "deletable": False,
                "release_status": True,
                "release_time": dummy_time.str,
                "resource_version_name": "test-01",
                "resource_version_title": "test",
                "resource_version_display": "1.0.0(test)",
                "access_strategies": [],
                "plugins": [],
                "micro_gateway_id": None,
                "micro_gateway_name": "",
            },
            {
                "id": stage_test.id,
                "name": stage_test.name,
                "description": stage_test.description,
                "description_en": stage_test.description_en,
                "status": stage_prod.status,
                "deletable": True,
                "release_status": False,
                "release_time": None,
                "resource_version_name": "",
                "resource_version_title": "",
                "resource_version_display": "",
                "access_strategies": [],
                "plugins": [],
                "micro_gateway_id": micro_gateway.id,
                "micro_gateway_name": micro_gateway.name,
            },
        ]

        slz = serializers.ListStageSLZ(
            [stage_prod, stage_test],
            many=True,
            context={
                "stage_release": {
                    stage_test.id: {
                        "release_status": False,
                        "release_time": None,
                        "resource_version_name": "",
                        "resource_version_title": "",
                        "resource_version_display": "",
                    },
                    stage_prod.id: {
                        "release_status": True,
                        "release_time": dummy_time.time,
                        "resource_version_name": "test-01",
                        "resource_version_title": "test",
                        "resource_version_display": "1.0.0(test)",
                    },
                },
                "scope_bindings": {},
                "scope_bound_plugins": {},
                "stage_id_to_micro_gateway_fields": StageHandler().get_id_to_micro_gateway_fields(fake_gateway.id),
            },
        )
        assert slz.data == expected
