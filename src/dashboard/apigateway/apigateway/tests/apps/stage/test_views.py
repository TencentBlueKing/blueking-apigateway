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
from unittest.mock import patch

from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding
from apigateway.apps.stage.views import StageViewSet
from apigateway.common.contexts import StageProxyHTTPContext, StageRateLimitContext
from apigateway.core import constants
from apigateway.core.models import Context, Release, ResourceVersion, Stage
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, dummy_time, get_response_json


def mock_alter_plugin(*args, **kwargs):
    return None


class TestStageViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    @patch("apigateway.common.plugin.header_rewrite.HeaderRewriteConvertor.alter_plugin", mock_alter_plugin)
    def test_create(self):
        data = [
            # ok
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
            # error, name exist
            {
                "name": "prod",
                "description": "test",
                "vars": {},
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
                    "enabled": False,
                },
                "will_error": True,
            },
        ]

        for test in data:
            request = self.factory.post(f"/apis/{self.gateway.id}/stages/", data=test)

            view = StageViewSet.as_view({"post": "create"})
            response = view(request, gateway_id=self.gateway.id)

            # result = get_response_json(response)

            if test.get("will_error"):
                self.assertNotEqual(response.status_code, 200, "")
            else:
                self.assertEqual(response.status_code, 200, "")

                # check stage
                stage = Stage.objects.get(api=self.gateway, name=test["name"])
                self.assertEqual(stage.description, test["description"])
                self.assertEqual(stage.vars, test["vars"])
                self.assertEqual(stage.status, constants.StageStatusEnum.INACTIVE.value)

    def test_list(self):
        stage_prod = G(Stage, api=self.gateway, name="prod-01", status=1)
        stage_test = G(Stage, api=self.gateway, name="test-01", status=1)

        resource_version = G(ResourceVersion, api=self.gateway, name="test-01", title="test", version="1.0.1")
        G(Release, api=self.gateway, stage=stage_prod, resource_version=resource_version, updated_time=dummy_time.time)

        access_strategy = G(AccessStrategy, api=self.gateway)
        G(
            AccessStrategyBinding,
            scope_type="stage",
            scope_id=stage_test.id,
            type="ip_access_control",
            access_strategy=access_strategy,
        )

        data = [
            {
                "order_by": "-name",
                "expected": [
                    {
                        "id": stage_test.id,
                        "name": stage_test.name,
                        "description": stage_test.description,
                        "description_en": stage_test.description_en,
                        "status": stage_test.status,
                        "deletable": False,
                        "release_status": False,
                        "release_time": None,
                        "resource_version_name": "",
                        "resource_version_title": "",
                        "resource_version_display": "",
                        "access_strategies": [
                            {
                                "access_strategy_id": access_strategy.id,
                                "access_strategy_name": access_strategy.name,
                            }
                        ],
                        "plugins": [],
                        "micro_gateway_id": None,
                        "micro_gateway_name": "",
                    },
                    {
                        "id": stage_prod.id,
                        "name": stage_prod.name,
                        "description": stage_prod.description,
                        "description_en": stage_prod.description_en,
                        "status": stage_prod.status,
                        "deletable": False,
                        "release_status": True,
                        "release_time": "2019-01-01 20:30:00",
                        "resource_version_name": "test-01",
                        "resource_version_title": "test",
                        "resource_version_display": "1.0.1(test)",
                        "access_strategies": [],
                        "plugins": [],
                        "micro_gateway_id": None,
                        "micro_gateway_name": "",
                    },
                ],
            },
            {
                "name": "prod",
                "expected": [
                    {
                        "id": stage_prod.id,
                        "name": stage_prod.name,
                        "description": stage_prod.description,
                        "description_en": stage_prod.description,
                        "status": stage_prod.status,
                        "deletable": False,
                        "release_status": True,
                        "release_time": "2019-01-01 20:30:00",
                        "resource_version_name": "test-01",
                        "resource_version_title": "test",
                        "resource_version_display": "1.0.1(test)",
                        "access_strategies": [],
                        "plugins": [],
                        "micro_gateway_id": None,
                        "micro_gateway_name": "",
                    },
                ],
            },
        ]
        for test in data:
            request = self.factory.get(f"/apis/{self.gateway.id}/stages/", data=test)

            view = StageViewSet.as_view({"get": "list"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(result["data"]["results"], test["expected"])

    def test_list_release(self):
        gateway = create_gateway()
        stage_prod = G(Stage, api=gateway, name="prod-01", status=1)
        stage_test = G(Stage, api=gateway, name="test-01", status=1)

        resource_version = G(ResourceVersion, api=gateway, name="test-01", title="test", version="1.0.2")
        G(Release, api=gateway, stage=stage_prod, resource_version=resource_version, updated_time=dummy_time.time)

        data = [
            {
                "ids": [stage_prod.id, stage_test.id],
                "expected": [
                    {
                        "id": stage_prod.id,
                        "name": stage_prod.name,
                        "release_status": True,
                        "release_time": "2019-01-01 20:30:00",
                        "resource_version_id": resource_version.id,
                        "resource_version_name": "test-01",
                        "resource_version_title": "test",
                        "resource_version_display": "1.0.2(test)",
                    },
                    {
                        "id": stage_test.id,
                        "name": stage_test.name,
                        "release_status": False,
                        "release_time": None,
                        "resource_version_id": None,
                        "resource_version_name": "",
                        "resource_version_title": "",
                        "resource_version_display": "",
                    },
                ],
            },
            {
                "ids": [stage_prod.id],
                "expected": [
                    {
                        "id": stage_prod.id,
                        "name": stage_prod.name,
                        "release_status": True,
                        "release_time": "2019-01-01 20:30:00",
                        "resource_version_id": resource_version.id,
                        "resource_version_name": "test-01",
                        "resource_version_title": "test",
                        "resource_version_display": "1.0.2(test)",
                    },
                ],
            },
        ]
        for test in data:
            request = self.factory.post(f"/apis/{gateway.id}/stages/releases/", data=test)

            view = StageViewSet.as_view({"post": "list_release"})
            response = view(request, gateway_id=gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(result["data"], test["expected"])

    def test_list_basic(self):
        gateway = create_gateway()
        stage_prod = G(Stage, api=gateway, name="prod", _vars=json.dumps({"k1": "v1"}))

        StageProxyHTTPContext().save(
            stage_prod.id,
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
                    "delete": ["k2"],
                },
            },
        )

        data = [
            {
                "expected": [
                    {
                        "id": stage_prod.id,
                        "name": stage_prod.name,
                        "description": stage_prod.description,
                        "description_en": stage_prod.description_en,
                        "status": stage_prod.status,
                        "vars": stage_prod.vars,
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
                                "delete": ["k2"],
                            },
                        },
                    },
                ]
            },
        ]
        for test in data:
            request = self.factory.get(f"/apis/{gateway.id}/stages/basic/")

            view = StageViewSet.as_view({"get": "list_basic"})
            response = view(request, gateway_id=gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(result["data"]["results"], test["expected"])

    @patch("apigateway.common.plugin.header_rewrite.HeaderRewriteConvertor.alter_plugin", mock_alter_plugin)
    def test_update(self):
        stage = G(
            Stage, api=self.gateway, name="test-03", status=0, description="t1", _vars=json.dumps({"test": "123"})
        )
        StageProxyHTTPContext().save(
            stage.id,
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
            },
        )
        StageRateLimitContext().save(
            stage.id,
            {
                "enabled": True,
                "rate": {
                    "tokens": 100,
                    "period": 60,
                },
            },
        )
        data = [
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
            }
        ]
        for test in data:
            request = self.factory.put(f"/apis/{self.gateway.id}/stages/{stage.id}/", data=test)

            view = StageViewSet.as_view({"put": "update"})
            response = view(request, gateway_id=self.gateway.id, id=stage.id)

            self.assertEqual(response.status_code, 200)

            self.assertTrue(Stage.objects.filter(api=self.gateway, name="test-03").exists())

            stage = Stage.objects.get(name="test-03")
            self.assertEqual(stage.description, test["description"])
            self.assertEqual(stage.status, 0)
            self.assertEqual(stage.vars, test["vars"])

            self.assertEqual(
                StageProxyHTTPContext().get_config(stage.id),
                {
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
            )
            self.assertEqual(
                StageRateLimitContext().get_config(stage.id),
                {
                    "enabled": True,
                    "rate": {
                        "tokens": 200,
                        "period": 3600,
                    },
                },
            )

    def test_retrieve(self):
        stage = G(Stage, api=self.gateway, _vars='{"test": "123"}')
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

        request = self.factory.get(f"/apis/{self.gateway.id}/stages/{stage.id}/")

        view = StageViewSet.as_view({"get": "retrieve"})
        response = view(request, gateway_id=self.gateway.id, id=stage.id)

        result = get_response_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            result["data"],
            {
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
                "micro_gateway_id": None,
            },
        )

    def test_destroy(self):
        stage = G(Stage, api=self.gateway)

        request = self.factory.delete(f"/apis/{self.gateway.id}/stages/{stage.id}/")

        view = StageViewSet.as_view({"delete": "destroy"})
        response = view(request, gateway_id=self.gateway.id, id=stage.id)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Stage.objects.filter(api=self.gateway, name=stage.name).exists())

    def test_update_status(self):
        stage = G(Stage, api=self.gateway, name="prod", status=0, _vars='{"test": 123}')
        data = [
            {
                "name": "test",
                "description": "t2",
                "status": 1,
                "vars": {
                    "test": "test",
                },
            }
        ]
        for test in data:
            request = self.factory.put(f"/apis/{self.gateway.id}/stages/{stage.id}/status/", data=test)

            view = StageViewSet.as_view({"put": "update_status"})
            response = view(request, gateway_id=self.gateway.id, id=stage.id)

            self.assertEqual(response.status_code, 200)

            stage = Stage.objects.get(api=self.gateway, name="prod")
            self.assertEqual(stage.status, 1)
            self.assertEqual(stage.vars, {"test": 123})
