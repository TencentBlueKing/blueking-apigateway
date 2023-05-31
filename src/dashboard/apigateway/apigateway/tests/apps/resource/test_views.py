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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.apps.resource.views import (
    ProxyPathViewSet,
    ResourceBatchViewSet,
    ResourceImportExportViewSet,
    ResourceURLViewSet,
    ResourceViewSet,
)
from apigateway.biz.resource import ResourceHandler
from apigateway.core import constants
from apigateway.core.models import Context, Proxy, Resource, Stage, StageResourceDisabled
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json

pytestmark = pytest.mark.django_db


class TestResourceViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()
        cls.stage = G(Stage, api=cls.gateway)
        cls.label = G(APILabel, api=cls.gateway)

    def test_create(self):
        data = [
            {
                "name": "post_echo",
                "description": "desc",
                "is_public": True,
                "method": "POST",
                "path": "/echo/",
                "match_subpath": True,
                "label_ids": [self.label.id],
                "proxy_type": "http",
                "proxy_configs": {
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "match_subpath": True,
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
                        "transform_headers": {},
                    }
                },
                "auth_config": {
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
                "disabled_stage_ids": [self.stage.id],
            },
            # ok, proxy-config 不覆盖环境配置
            {
                "name": "get_echo_2",
                "description": "desc",
                "is_public": True,
                "method": "GET",
                "path": "/echo/2/",
                "match_subpath": False,
                "label_ids": [self.label.id],
                "proxy_type": "http",
                "proxy_configs": {
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "match_subpath": False,
                        "timeout": 0,
                        "upstreams": {},
                        "transform_headers": {},
                    }
                },
                "auth_config": {
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
                "disabled_stage_ids": [self.stage.id],
            },
        ]
        for test in data:
            request = self.factory.post(f"/apis/{self.gateway.id}/resources/", data=test)

            view = ResourceViewSet.as_view({"post": "create"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(result["code"], 0)

            # check resource
            resource = Resource.objects.get(api=self.gateway, method=test["method"], path=test["path"])
            self.assertEqual(resource.is_public, test["is_public"])
            self.assertEqual(resource.match_subpath, test["match_subpath"])

            # check resource proxy
            proxy = Proxy.objects.get(type=test["proxy_type"], resource=resource)
            self.assertEqual(resource.proxy_id, proxy.id)
            self.assertEqual(proxy.config, test["proxy_configs"][test["proxy_type"]])

            # check resource auth config
            context = Context.objects.get(
                scope_type=constants.ContextScopeTypeEnum.RESOURCE.value,
                scope_id=resource.id,
                type=constants.ContextTypeEnum.RESOURCE_AUTH.value,
            )
            self.assertEqual(
                context.config,
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            )

            # check resource label
            self.assertEqual(ResourceLabel.objects.filter(resource=resource, api_label=self.label).count(), 1)

            # check resource disabled stage resource
            self.assertEqual(StageResourceDisabled.objects.filter(resource=resource, stage=self.stage).count(), 1)

    def test_list(self):
        G(Resource, api=self.gateway, path="/echo/", method="GET", name="echo")
        G(Resource, api=self.gateway, path="/test/", method="GET", name="test")

        data = [
            {
                "expected": 2,
            },
            {
                "path": "echo",
                "expected": 1,
            },
            {
                "method": "GET",
                "expected": 2,
            },
            {
                "query": "echo",
                "expected": 1,
            },
        ]

        for test in data:
            request = self.factory.get(f"/apis/{self.gateway.id}/resources/", data=test)

            view = ResourceViewSet.as_view({"get": "list"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(result["code"], 0)
            self.assertEqual(len(result["data"]["results"]), test["expected"])

    def test_retrieve(self):
        resource = G(
            Resource,
            api=self.gateway,
        )
        data = {
            "label_ids": [],
            "proxy_type": "http",
            "proxy_configs": {
                "backend_config_type": "default",
                "backend_service_id": None,
                "http": {
                    "method": "GET",
                    "path": "/echo/",
                    "timeout": 0,
                    "upstreams": {},
                    "transform_headers": {},
                },
            },
            "auth_config": {
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
            "disabled_stage_ids": [],
        }
        ResourceHandler().save_related_data(
            self.gateway,
            resource,
            proxy_type=data["proxy_type"],
            proxy_config=data["proxy_configs"][data["proxy_type"]],
            auth_config=data["auth_config"],
            label_ids=data.get("label_ids", []),
            disabled_stage_ids=data.get("disabled_stage_ids", []),
        )

        request = self.factory.get(f"/apis/{self.gateway.id}/resources/{resource.id}/")

        view = ResourceViewSet.as_view({"get": "retrieve"})
        response = view(request, gateway_id=self.gateway.id, id=resource.id)

        result = get_response_json(response)
        self.assertEqual(result["code"], 0, result)
        self.assertEqual(result["data"]["proxy_configs"], data["proxy_configs"])

    def test_update(self):
        resource = G(Resource, api=self.gateway)
        ResourceHandler().save_auth_config(
            resource.id,
            {
                "skip_auth_verification": False,
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
        )

        data = [
            {
                "name": "post_echo",
                "description": "desc",
                "is_public": True,
                "method": "POST",
                "path": "/echo/",
                "label_ids": [self.label.id],
                "proxy_type": "http",
                "proxy_configs": {
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 30,
                        "upstreams": {"loadbalance": "roundrobin", "hosts": [{"host": "http://www.a.com"}]},
                        "transform_headers": {},
                    }
                },
                "auth_config": {
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
                "disabled_stage_ids": [self.stage.id],
            },
            # resource label_id exceed the maximum
            {
                "name": "post_echo",
                "description": "desc",
                "is_public": True,
                "method": "POST",
                "path": "/echo/",
                "label_ids": list(range(11)),
                "proxy_type": "http",
                "proxy_configs": {
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 30,
                        "upstreams": {"loadbalance": "roundrobin", "hosts": [{"host": "http://www.a.com"}]},
                        "transform_headers": {},
                    }
                },
                "auth_config": {
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
                "disabled_stage_ids": [self.stage.id],
                "will_error": True,
            },
        ]
        for test in data:
            request = self.factory.put(f"/apis/{self.gateway.id}/resources/{resource.id}/", data=test)

            view = ResourceViewSet.as_view({"put": "update"})
            response = view(request, gateway_id=self.gateway.id, id=resource.id)

            result = get_response_json(response)

            if test.get("will_error"):
                self.assertNotEqual(result["code"], 0, result)
                continue

            self.assertEqual(result["code"], 0, result)

            # check resource
            resource = Resource.objects.get(api=self.gateway, method=test["method"], path=test["path"])
            self.assertEqual(resource.is_public, test["is_public"])

            # check resource proxy
            proxy = Proxy.objects.get(type="http", resource=resource)
            self.assertEqual(resource.proxy_id, proxy.id)
            self.assertEqual(
                proxy.config,
                {
                    "method": "GET",
                    "path": "/echo/",
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
                    "transform_headers": {},
                },
            )

            # check resource auth config
            context = Context.objects.get(
                scope_type=constants.ContextScopeTypeEnum.RESOURCE.value,
                scope_id=resource.id,
                type=constants.ContextTypeEnum.RESOURCE_AUTH.value,
            )
            self.assertEqual(
                context.config,
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            )

            # check resource label
            self.assertEqual(ResourceLabel.objects.filter(resource=resource, api_label=self.label).count(), 1)

            # check resource disabled stage resource
            self.assertEqual(StageResourceDisabled.objects.filter(resource=resource, stage=self.stage).count(), 1)

    def test_destroy(self):
        resource = G(Resource, api=self.gateway)

        request = self.factory.delete(f"/apis/{self.gateway.id}/resource/{resource.id}/")

        view = ResourceViewSet.as_view({"delete": "destroy"})
        response = view(request, gateway_id=self.gateway.id, id=resource.id)

        result = get_response_json(response)
        self.assertEqual(result["code"], 0)
        self.assertFalse(Resource.objects.filter(id=resource.id).exists())


class TestResourceBatchViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_update(self):
        resource_1 = G(Resource, api=self.gateway, is_public=False, allow_apply_permission=False)
        resource_2 = G(Resource, api=self.gateway, is_public=False, allow_apply_permission=False)

        data = [
            {
                "ids": [resource_1.id, resource_2.id],
                "is_public": True,
                "allow_apply_permission": True,
                "expected": {
                    "is_public": True,
                    "allow_apply_permission": True,
                },
            }
        ]
        for test in data:
            request = self.factory.put(f"/apis/{self.gateway.id}/resource/batch/", data=test)

            view = ResourceBatchViewSet.as_view({"put": "update"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(result["code"], 0)

            for resource in Resource.objects.filter(id__in=test["ids"]):
                for attr, value in test["expected"].items():
                    self.assertEqual(getattr(resource, attr), value)

    def test_destroy(self):
        resource_1 = G(Resource, api=self.gateway)
        resource_2 = G(Resource, api=self.gateway)

        data = [
            {
                "ids": [resource_1.id, resource_2.id],
            }
        ]
        for test in data:
            request = self.factory.delete(f"/apis/{self.gateway.id}/resource/batch/", data=test)

            view = ResourceBatchViewSet.as_view({"delete": "destroy"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(result["code"], 0)

            self.assertFalse(Resource.objects.filter(id__in=test["ids"]).exists())


class TestResourceURLViewSet:
    def test_get(self, request_factory, fake_gateway, settings):
        settings.API_RESOURCE_URL_TMPL = "http://bking.com/{stage_name}/{resource_path}"

        G(Stage, api=fake_gateway, name="prod")
        G(Stage, api=fake_gateway, name="test")
        resource = G(Resource, api=fake_gateway, path="/echo/")

        request = request_factory.get(f"/apis/{fake_gateway.id}/resource/{resource.id}/urls/")

        view = ResourceURLViewSet.as_view({"get": "get"})
        response = view(request, gateway_id=fake_gateway.id, id=resource.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"] == [
            {
                "stage_name": "prod",
                "url": "http://bking.com/prod/echo/",
            },
            {
                "stage_name": "test",
                "url": "http://bking.com/test/echo/",
            },
        ]


class TestProxyPathViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_get(self):
        G(Stage, api=self.gateway, name="prod", _vars='{"k1": "v1"}')

        data = [
            # ok, no vars
            {
                "path": "/echo/",
                "proxy_path": "/echo/",
                "will_error": False,
            },
            # ok, have same vars
            {
                "path": "/echo/{cmd}/",
                "proxy_path": "/echo/{cmd}/",
                "will_error": False,
            },
            # ok, have same vars or env vars
            {
                "path": "/echo/{cmd}/",
                "proxy_path": "/echo/{cmd}/{env.k1}/",
                "will_error": False,
            },
            # fail, proxy-path vars not exist in path
            {
                "path": "/echo/",
                "proxy_path": "/echo/{cmd}/",
                "will_error": True,
            },
            # fail, proxy-path vars not exist in path
            {
                "path": "/echo/{cmd}/",
                "proxy_path": "/echo/{cmd2}/",
                "will_error": True,
            },
            # fail, proxy-path env vars not exist in stage vars
            {
                "path": "/echo/{cmd}/",
                "proxy_path": "/echo/{cmd}/{env.k2}/",
                "will_error": True,
            },
        ]
        for test in data:
            request = self.factory.get(f"/apis/{self.gateway.id}/resource/proxy_path/check/", data=test)

            view = ProxyPathViewSet.as_view({"get": "check"})
            response = view(request, gateway_id=self.gateway.id)
            result = get_response_json(response)

            if test["will_error"]:
                self.assertNotEqual(result["code"], 0, result)
            else:
                self.assertEqual(result["code"], 0, result)


class TestResourceImportExportViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.factory = APIRequestFactory()
        self.gateway = create_gateway()

    def test_import_resources_check(self):
        data = [
            # ok, no vars
            {
                "content": json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "schemes": ["http"],
                        "paths": {
                            "/http/get/mapping/{userId}": {
                                "get": {
                                    "operationId": "http_get_mapping_userid",
                                    "description": "test",
                                    "tags": ["pet"],
                                    "schemes": ["http"],
                                    "x-bk-apigateway-resource": {
                                        "isPublic": True,
                                        "allowApplyPermission": True,
                                        "matchSubpath": True,
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "matchSubpath": True,
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                },
                            }
                        },
                    }
                ),
                "allow_overwrite": True,
                "expected": [
                    {
                        "id": None,
                        "method": "GET",
                        "path": "/http/get/mapping/{userId}",
                        "match_subpath": True,
                        "name": "http_get_mapping_userid",
                        "description": "test",
                        "description_en": None,
                        "labels": ["pet"],
                        "is_public": True,
                        "allow_apply_permission": True,
                        "proxy_type": "http",
                        "proxy_configs": {
                            "backend_config_type": "default",
                            "backend_service_id": None,
                            "http": {
                                "method": "GET",
                                "path": "/hello/",
                                "match_subpath": True,
                                "timeout": 30,
                                "upstreams": {},
                                "transform_headers": {},
                            },
                        },
                        "auth_config": {
                            "auth_verified_required": True,
                        },
                        "disabled_stages": [],
                        "resource_doc_id": None,
                        "resource_doc_language": "",
                    }
                ],
            },
            {
                "content": json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "schemes": ["http"],
                        "paths": {
                            "/http/get/mapping/{userId}": {
                                "get": {
                                    "operationId": "http_get_mapping_userid",
                                    "description": "test",
                                    "tags": ["pet"],
                                    "schemes": ["http"],
                                    "x-bk-apigateway-resource": {
                                        "isPublic": True,
                                        "allowApplyPermission": True,
                                        "backend": {
                                            "type": "MOCK",
                                            "statusCode": 200,
                                            "responseBody": "test",
                                            "headers": {
                                                "X-Token": "token",
                                            },
                                        },
                                    },
                                },
                            }
                        },
                    }
                ),
                "allow_overwrite": True,
                "expected": [
                    {
                        "id": None,
                        "method": "GET",
                        "path": "/http/get/mapping/{userId}",
                        "name": "http_get_mapping_userid",
                        "description": "test",
                        "description_en": None,
                        "labels": ["pet"],
                        "is_public": True,
                        "allow_apply_permission": True,
                        "match_subpath": False,
                        "proxy_type": "mock",
                        "proxy_configs": {
                            "backend_config_type": "default",
                            "backend_service_id": None,
                            "mock": {
                                "code": 200,
                                "body": "test",
                                "headers": {
                                    "X-Token": "token",
                                },
                            },
                        },
                        "auth_config": {
                            "auth_verified_required": True,
                        },
                        "disabled_stages": [],
                        "resource_doc_id": None,
                        "resource_doc_language": "",
                    }
                ],
            },
        ]
        for test in data:
            request = self.factory.post(f"/apis/{self.gateway.id}/resource/import/check/", data=test)

            view = ResourceImportExportViewSet.as_view({"post": "import_resources_check"})
            response = view(request, gateway_id=self.gateway.id)
            result = get_response_json(response)
            assert result["code"] == 0
            assert result["data"] == test["expected"], result

    def test_import_resources(self):
        data = [
            # ok, no vars
            {
                "content": json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "schemes": ["http"],
                        "paths": {
                            "/import/r/{user}/": {
                                "get": {
                                    "operationId": "import_r_user",
                                    "description": "test",
                                    "tags": ["pet"],
                                    "schemes": ["http"],
                                    "x-bk-apigateway-resource": {
                                        "isPublic": True,
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                },
                            },
                            "/import/any/{user}/": {
                                "x-bk-apigateway-method-any": {
                                    "operationId": "import_any_user",
                                    "description": "test",
                                    "schemes": ["http"],
                                    "x-bk-apigateway-resource": {
                                        "backend": {
                                            "type": "MOCK",
                                            "statusCode": 200,
                                            "responseBody": "test",
                                            "headers": {"X-Token": "test"},
                                        }
                                    },
                                },
                            },
                        },
                    }
                ),
                "allow_overwrite": True,
                "expected": [
                    {
                        "path": "/import/r/{user}/",
                        "method": "GET",
                        "name": "import_r_user",
                    },
                    {
                        "path": "/import/any/{user}/",
                        "method": "ANY",
                        "name": "import_any_user",
                    },
                ],
            },
            {
                "content": json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "schemes": ["http"],
                        "paths": {
                            "/import/r/{user}/": {
                                "get": {
                                    "operationId": "import_r_user_2",
                                    "description": "test",
                                    "tags": ["pet"],
                                    "schemes": ["http"],
                                    "x-bk-apigateway-resource": {
                                        "isPublic": True,
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                },
                            },
                            "/import/any/{user}/2/": {
                                "get": {
                                    "operationId": "import_any_user_2",
                                    "description": "test",
                                    "schemes": ["http"],
                                    "x-bk-apigateway-resource": {
                                        "backend": {
                                            "type": "MOCK",
                                            "statusCode": 200,
                                            "responseBody": "test",
                                            "headers": {"X-Token": "test"},
                                        }
                                    },
                                },
                            },
                        },
                    }
                ),
                "allow_overwrite": True,
                "selected_resources": [
                    {
                        "name": "import_any_user_2",
                    }
                ],
                "expected": [
                    {
                        "path": "/import/r/{user}/",
                        "method": "GET",
                        "name": "import_r_user",
                    },
                    {
                        "path": "/import/any/{user}/2/",
                        "method": "GET",
                        "name": "import_any_user_2",
                    },
                ],
            },
        ]
        for test in data:
            request = self.factory.post(f"/apis/{self.gateway.id}/resource/import/", data=test)

            view = ResourceImportExportViewSet.as_view({"post": "import_resources"})
            response = view(request, gateway_id=self.gateway.id)
            result = get_response_json(response)
            assert result["code"] == 0, json.dumps(result)

            for expected in test["expected"]:
                resource = Resource.objects.get(api=self.gateway, path=expected["path"], method=expected["method"])
                assert resource.name == expected["name"]

    def test_export_resources(self):
        stage = G(Stage, api=self.gateway, name="prod")
        resource1 = G(Resource, api=self.gateway, path="/echo/", method="GET", name="get_echo", description="desc")
        resource2 = G(Resource, api=self.gateway, path="/echo/2/", method="ANY", name="any_echo", description="desc")
        resource3 = G(
            Resource, api=self.gateway, path="/users/", method="GET", name="get_users", description="get users"
        )
        resource4 = G(
            Resource,
            api=self.gateway,
            path="/users/",
            method="POST",
            name="create_users",
            description="create users",
        )

        api_label = G(APILabel, api=self.gateway, name="test")
        G(ResourceLabel, resource=resource1, api_label=api_label)
        G(ResourceLabel, resource=resource3, api_label=api_label)

        data = [
            {
                "resource": resource1,
                "label_ids": [api_label.id],
                "proxy_type": "http",
                "proxy_configs": {
                    "http": {
                        "method": "GET",
                        "path": "/echo/",
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://0.0.0.1",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {
                                "X-Token": "test",
                            },
                            "delete": ["delete-token"],
                        },
                    }
                },
                "auth_config": {
                    "auth_verified_required": False,
                },
                "disabled_stage_ids": [stage.id],
            },
            {
                "resource": resource2,
                "label_ids": [],
                "proxy_type": "mock",
                "proxy_configs": {
                    "mock": {
                        "code": 200,
                        "body": "test",
                        "headers": {
                            "X-Token": "test",
                        },
                    }
                },
                "auth_config": {
                    "auth_verified_required": True,
                },
                "disabled_stage_ids": [],
            },
            {
                "resource": resource3,
                "label_ids": [api_label.id],
                "proxy_type": "http",
                "proxy_configs": {
                    "http": {
                        "method": "GET",
                        "path": "/users/",
                        "timeout": 30,
                        "upstreams": {
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://0.0.0.1",
                                    "weight": 100,
                                }
                            ],
                        },
                        "transform_headers": {
                            "set": {
                                "X-Token": "token",
                            },
                            "delete": ["delete-token"],
                        },
                    }
                },
                "auth_config": {
                    "auth_verified_required": False,
                },
                "disabled_stage_ids": [stage.id],
            },
            {
                "resource": resource4,
                "label_ids": [],
                "proxy_type": "mock",
                "proxy_configs": {
                    "mock": {
                        "code": 200,
                        "body": "test",
                        "headers": {
                            "X-Token": "token",
                        },
                    }
                },
                "auth_config": {
                    "auth_verified_required": True,
                },
                "disabled_stage_ids": [],
            },
        ]
        for item in data:
            ResourceHandler().save_related_data(
                self.gateway,
                item["resource"],
                proxy_type=item["proxy_type"],
                proxy_config=item["proxy_configs"][item["proxy_type"]],
                auth_config=item["auth_config"],
                label_ids=item.get("label_ids", []),
                disabled_stage_ids=item.get("disabled_stage_ids", []),
            )

        data = [
            {
                "export_type": "selected",
                "resource_ids": [resource1.id, resource2.id],
            },
            {
                "export_type": "selected",
                "resource_ids": [resource3.id, resource4.id],
            },
        ]
        for test in data:
            request = self.factory.post(f"/apis/{self.gateway.id}/resource/export/", data=test)

            view = ResourceImportExportViewSet.as_view({"post": "export_resources"})
            response = view(request, gateway_id=self.gateway.id)
            assert response.status_code == 200, response


class TestResourceLabelViewSet:
    def test_update(self, fake_resource, request_to_view, request_factory):
        fake_gateway = fake_resource.api
        l1 = G(APILabel, api=fake_gateway)
        l2 = G(APILabel, api=fake_gateway)

        # create labels
        request = request_factory.put("", {"label_ids": [l1.id, l2.id]})
        request.gateway = fake_gateway

        response = request_to_view(
            request=request,
            view_name="apigateway.apps.resource.update.labels",
            path_params={"id": fake_resource.id, "gateway_id": fake_gateway.id},
        )
        result = get_response_json(response)
        assert result["code"] == 0
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 2

        # update labels, same resource, will delete unspecified labels
        request = request_factory.put("", {"label_ids": [l1.id]})
        request.gateway = fake_gateway

        response = request_to_view(
            request=request,
            view_name="apigateway.apps.resource.update.labels",
            path_params={"id": fake_resource.id, "gateway_id": fake_gateway.id},
        )
        result = get_response_json(response)
        assert result["code"] == 0
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 1
