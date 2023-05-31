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

from apigateway.apps.resource.swagger.swagger import ResourceSwaggerExporter, ResourceSwaggerImporter, SwaggerManager
from apigateway.core.constants import SwaggerFormatEnum


class TestSwaggerManager:
    @pytest.mark.parametrize(
        "content, will_error, expected",
        [
            (
                "{test}",
                True,
                None,
            ),
            (
                '{"swagger": "2.0"}',
                False,
                {
                    "swagger": "2.0",
                },
            ),
            (
                'swagger: "2.0"',
                False,
                {
                    "swagger": "2.0",
                },
            ),
        ],
    )
    def test_load_from_swagger(self, content, will_error, expected):
        if will_error:
            with pytest.raises(Exception):
                SwaggerManager.load_from_swagger(content)
            return

        manager = SwaggerManager.load_from_swagger(content)
        assert manager.content == expected

    @pytest.mark.parametrize(
        "swagger, expected",
        [
            ('{"swagger": "2.0"}', SwaggerFormatEnum.JSON),
            ('swagger: "2.0"', SwaggerFormatEnum.YAML),
        ],
    )
    def test_guess_swagger_format(self, swagger, expected):
        result = SwaggerManager.guess_swagger_format(swagger)
        assert result == expected

    @pytest.mark.parametrize(
        "content, expected",
        [
            (
                {
                    "basePath": "/",
                    "paths": {
                        "/user": {
                            "get": {
                                "operationId": "get_user",
                            }
                        },
                    },
                },
                {
                    "/user": {
                        "get": {
                            "operationId": "get_user",
                        }
                    }
                },
            ),
        ],
    )
    def test_get_paths(self, content, expected):
        manager = SwaggerManager(content=content)
        result = manager.get_paths()
        assert result == expected

    def test_to_swagger(self):
        paths = {
            "/user": {
                "get": {
                    "operationId": "get_user",
                },
            }
        }

        result = SwaggerManager.to_swagger(paths=paths, swagger_format=SwaggerFormatEnum.YAML)
        assert not result.startswith("{")

        result = SwaggerManager.to_swagger(paths=paths, swagger_format=SwaggerFormatEnum.JSON)
        assert result.startswith("{")

    @pytest.mark.parametrize(
        "base_path, paths, expected",
        [
            (
                "/",
                {
                    "/users/": {
                        "get": {},
                    }
                },
                {
                    "/users/": {
                        "get": {},
                    }
                },
            ),
            (
                "/v2/",
                {
                    "/users/": {
                        "get": {},
                    }
                },
                {
                    "/v2/users/": {
                        "get": {},
                    }
                },
            ),
        ],
    )
    def test_add_base_path_to_path(self, base_path, paths, expected):
        manager = SwaggerManager(content={})
        result = manager._add_base_path_to_path(base_path, paths)
        assert result == expected

    @pytest.mark.parametrize(
        "paths, expected",
        [
            (
                {
                    "/user": {
                        "get": {},
                        "post": {},
                    },
                    "/user/1": {
                        "invalid": {},
                    },
                    "/user/2": {
                        "delete": {},
                        "invalid": {},
                    },
                },
                {
                    "/user": {
                        "get": {},
                        "post": {},
                    },
                    "/user/2": {
                        "delete": {},
                    },
                },
            )
        ],
    )
    def test_remove_invalid_method(self, paths, expected):
        manager = SwaggerManager(content={})
        result = manager._remove_invalid_method(paths)
        assert result == expected

    @pytest.mark.parametrize(
        "content, will_error",
        [
            # content is not valid swagger
            (
                "test",
                True,
            ),
            # swaager 1.0, error
            (
                json.dumps(
                    {
                        "swagger": "1.0",
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
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                }
                            }
                        },
                    }
                ),
                True,
            ),
            # error, x-bk-apigateway-is-public is not a boolean
            (
                json.dumps(
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
                                        "isPublic": "a",
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                }
                            }
                        },
                    }
                ),
                True,
            ),
            # error, userVerifiedRequired is not valid
            (
                json.dumps(
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
                                        "isPublic": False,
                                        "authConfig": {
                                            "userVerifiedRequired": "a",
                                        },
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                }
                            }
                        },
                    }
                ),
                True,
            ),
            # error, additional properties of x-bk-apigateway-resource authConfig are not allowed
            (
                json.dumps(
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
                                        "authConfig": {
                                            "userVerifiedRequired": True,
                                            "test": False,
                                        },
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                },
                            }
                        },
                    }
                ),
                True,
            ),
            # error, disabled-stages invalid
            (
                json.dumps(
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
                                        "authConfig": {
                                            "userVerifiedRequired": True,
                                        },
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                        "disabledStages": [{"test": 1}],
                                    },
                                }
                            }
                        },
                    }
                ),
                True,
            ),
            # error, x-bk-apigateway-backend type invalid
            (
                json.dumps(
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
                                        "authConfig": {
                                            "userVerifiedRequired": True,
                                        },
                                        "disabledStages": [{"test": 1}],
                                        "backend": {
                                            "type": "test",
                                            "path": "/hello/",
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                }
                            }
                        },
                    }
                ),
                True,
            ),
            # ok, responses is empty
            (
                json.dumps(
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
                                    "responses": {},
                                    "x-bk-apigateway-resource": {
                                        "isPublic": True,
                                        "backend": {
                                            "type": "MOCK",
                                            "statusCode": 200,
                                            "responseBody": "test",
                                            "headers": {
                                                "X-Token": "token",
                                            },
                                        },
                                    },
                                }
                            }
                        },
                    }
                ),
                False,
            ),
            # ok, backend http, json
            (
                json.dumps(
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
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
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
                                            "transformHeaders": {
                                                "set": {"X-Token": "test"},
                                                "delete": ["delete-token"],
                                            },
                                        },
                                    },
                                }
                            }
                        },
                    }
                ),
                False,
            ),
            # ok, backend mock
            (
                json.dumps(
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
                                        "backend": {
                                            "type": "MOCK",
                                            "statusCode": 200,
                                            "responseBody": "test",
                                            "headers": {
                                                "X-Token": "token",
                                            },
                                        },
                                    },
                                }
                            }
                        },
                    }
                ),
                False,
            ),
            # ok, yaml
            (
                """\
!!omap
- swagger: "2.0"
- basePath: /
- info:
    version: "0.1"
    title: API Gateway Resources
- schemes:
  - http
- paths: !!omap
  - /echo/:
      get:
        operationId: get_echo
        description: desc
        tags:
        - test
        x-bk-apigateway-resource:
          isPublic: true
          backend:
            type: HTTP
            method: get
            path: /echo/
            timeout: 30
            upstreams:
              loadbalance: roundrobin
              hosts:
              - host: http://0.0.0.1
                weight: 100
            transformHeaders:
              set:
                X-Token: test
              delete:
              - delete-token
          authConfig:
            userVerifiedRequired: false
          disabledStages:
          - prod
      post:
        operationId: post_echo
        description: desc
        tags: []
        x-bk-apigateway-resource:
          isPublic: true
          backend:
            type: MOCK
            statusCode: 200
            responseBody: test
            headers:
              X-Token: test
          authConfig:
            userVerifiedRequired: true
          disabledStages: []""",
                False,
            ),
        ],
    )
    def test_validate(self, content, will_error):
        manager = SwaggerManager.load_from_swagger(content)

        if will_error:
            with pytest.raises(Exception):
                manager.validate()
            return

        result = manager.validate()
        assert result is None

    @pytest.mark.parametrize(
        "base_path, path, expected",
        [
            ("/", "/user", "/user"),
            ("/v2", "/user", "/v2/user"),
            ("/v2/", "/user", "/v2/user"),
        ],
    )
    def test_join_path(self, base_path, path, expected):
        manager = SwaggerManager(content={})
        result = manager._join_path(base_path, path)
        assert result == expected


class TestResourceSwaggerImporter(TestCase):
    def test_get_resources(self):
        data = [
            {
                "content": json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "paths": {
                            "/http/get/mapping/{userId}": {
                                "get": {
                                    "operationId": "http_get_mapping_userid",
                                    "description": "test",
                                    "tags": ["pet"],
                                    "x-bk-apigateway-resource": {
                                        "descriptionEn": "test_en",
                                        "isPublic": False,
                                        "allowApplyPermission": False,
                                        "matchSubpath": True,
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "method": "get",
                                            "matchSubpath": True,
                                            "timeout": 30,
                                            "upstreams": [
                                                {
                                                    "loadbalance": "roundrobin",
                                                    "hosts": [
                                                        {
                                                            "host": "bking.com",
                                                        },
                                                        {
                                                            "host": "test.bking.com",
                                                        },
                                                    ],
                                                }
                                            ],
                                            "transformHeaders": {
                                                "set": {"X-Token": "test"},
                                                "delete": ["X-Token2"],
                                            },
                                        },
                                        "authConfig": {
                                            "userVerifiedRequired": False,
                                        },
                                        "disabledStages": ["prod", "test"],
                                    },
                                },
                            }
                        },
                    }
                ),
                "expected": [
                    {
                        "method": "GET",
                        "path": "/http/get/mapping/{userId}",
                        "name": "http_get_mapping_userid",
                        "description": "test",
                        "description_en": "test_en",
                        "labels": ["pet"],
                        "is_public": False,
                        "allow_apply_permission": False,
                        "match_subpath": True,
                        "proxy_type": "http",
                        "proxy_configs": {
                            "http": {
                                "path": "/hello/",
                                "method": "GET",
                                "match_subpath": True,
                                "timeout": 30,
                                "upstreams": [
                                    {
                                        "loadbalance": "roundrobin",
                                        "hosts": [
                                            {
                                                "host": "bking.com",
                                            },
                                            {
                                                "host": "test.bking.com",
                                            },
                                        ],
                                    }
                                ],
                                "transform_headers": {
                                    "set": {"X-Token": "test"},
                                    "delete": ["X-Token2"],
                                },
                            }
                        },
                        "auth_config": {
                            "auth_verified_required": False,
                        },
                        "disabled_stages": ["prod", "test"],
                    }
                ],
            },
            # ok, proxy-type mock
            {
                "content": json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "paths": {
                            "/http/get/mapping/{userId}": {
                                "get": {
                                    "description": "中文",
                                    "operationId": "http_get_mapping_userid",
                                    "x-bk-apigateway-resource": {
                                        "descriptionEn": "English",
                                        "backend": {
                                            "type": "MOCK",
                                            "statusCode": 200,
                                            "responseBody": "test",
                                            "headers": {
                                                "X-Token": "test",
                                            },
                                        },
                                    },
                                },
                            }
                        },
                    }
                ),
                "expected": [
                    {
                        "method": "GET",
                        "path": "/http/get/mapping/{userId}",
                        "name": "http_get_mapping_userid",
                        "description": "中文",
                        "description_en": "English",
                        "labels": [],
                        "is_public": True,
                        "allow_apply_permission": True,
                        "match_subpath": False,
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
                        "disabled_stages": [],
                    }
                ],
            },
            # ok, any method
            {
                "content": json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "paths": {
                            "/http/get/mapping/{userId}": {
                                "x-bk-apigateway-method-any": {
                                    "operationId": "http_get_mapping_userid",
                                    "x-bk-apigateway-resource": {
                                        "backend": {
                                            "type": "HTTP",
                                            "method": "ANY",
                                            "path": "/echo/",
                                        },
                                    },
                                },
                            }
                        },
                    }
                ),
                "expected": [
                    {
                        "method": "ANY",
                        "path": "/http/get/mapping/{userId}",
                        "name": "http_get_mapping_userid",
                        "description": "",
                        "description_en": None,
                        "labels": [],
                        "is_public": True,
                        "allow_apply_permission": True,
                        "match_subpath": False,
                        "proxy_type": "http",
                        "proxy_configs": {
                            "http": {
                                "method": "ANY",
                                "path": "/echo/",
                                "match_subpath": False,
                                "timeout": 0,
                                "upstreams": {},
                                "transform_headers": {},
                            }
                        },
                        "auth_config": {
                            "auth_verified_required": True,
                        },
                        "disabled_stages": [],
                    }
                ],
            },
            # ok, basePath not /
            {
                "content": json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/api/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "paths": {
                            "/echo/": {
                                "x-bk-apigateway-method-any": {
                                    "operationId": "get_echo",
                                    "x-bk-apigateway-resource": {
                                        "backend": {
                                            "type": "HTTP",
                                            "method": "ANY",
                                            "path": "/echo/",
                                        }
                                    },
                                },
                            }
                        },
                    }
                ),
                "expected": [
                    {
                        "method": "ANY",
                        "path": "/api/echo/",
                        "name": "get_echo",
                        "description": "",
                        "description_en": None,
                        "labels": [],
                        "is_public": True,
                        "allow_apply_permission": True,
                        "match_subpath": False,
                        "proxy_type": "http",
                        "proxy_configs": {
                            "http": {
                                "method": "ANY",
                                "path": "/echo/",
                                "match_subpath": False,
                                "timeout": 0,
                                "upstreams": {},
                                "transform_headers": {},
                            }
                        },
                        "auth_config": {
                            "auth_verified_required": True,
                        },
                        "disabled_stages": [],
                    }
                ],
            },
        ]
        for test in data:
            importer = ResourceSwaggerImporter(test["content"])
            result = importer.get_resources()
            self.assertEqual(result, test["expected"])


class TestResourceSwaggerExporter:
    @pytest.fixture(autouse=True)
    def setup_imported(self):
        self.imported = {
            "method": "POST",
            "path": "/users",
            "match_subpath": False,
            "name": "add_user",
            "description": "创建新用户",
            "description_en": "Adds a new user",
            "labels": ["testing"],
            "is_public": True,
            "allow_apply_permission": True,
            "proxy_type": "http",
            "proxy_configs": {
                "http": {
                    "method": "POST",
                    "path": "/users",
                    "match_subpath": False,
                    "timeout": 0,
                    "upstreams": {},
                    "transform_headers": {},
                }
            },
            "auth_config": {"auth_verified_required": True},
            "disabled_stages": ["prod"],
        }

    def do_export(self, exporter, resources):
        swagger = exporter.to_swagger(resources, "json")
        exported = json.loads(swagger)
        return exported["paths"][self.imported["path"]][self.imported["method"].lower()]

    def test_export(self):
        exporter = ResourceSwaggerExporter()
        operation = self.do_export(exporter, [self.imported])

        http_config = self.imported["proxy_configs"][self.imported["proxy_type"]]

        assert operation == {
            "operationId": self.imported["name"],
            "description": self.imported["description"],
            "tags": self.imported["labels"],
            "x-bk-apigateway-resource": {
                "descriptionEn": self.imported["description_en"],
                "isPublic": self.imported["is_public"],
                "allowApplyPermission": self.imported["allow_apply_permission"],
                "matchSubpath": self.imported["match_subpath"],
                "backend": {
                    "type": self.imported["proxy_type"].upper(),
                    "method": http_config["method"].lower(),
                    "path": http_config["path"],
                    "matchSubpath": http_config["match_subpath"],
                    "timeout": http_config["timeout"],
                    "upstreams": http_config["upstreams"],
                    "transformHeaders": http_config["transform_headers"],
                },
                "authConfig": {"userVerifiedRequired": self.imported["auth_config"]["auth_verified_required"]},
                "disabledStages": self.imported["disabled_stages"],
            },
            "responses": {"default": {"description": ""}},
        }

    def test_export_exclude_bk_apigateway_resource(self):
        exporter = ResourceSwaggerExporter(include_bk_apigateway_resource=False)
        operation = self.do_export(exporter, [self.imported])

        assert "x-bk-apigateway-resource" not in operation

    def test_export_without_description_en(self):
        self.imported.pop("description_en")

        exporter = ResourceSwaggerExporter()
        operation = self.do_export(exporter, [self.imported])

        assert operation["x-bk-apigateway-resource"]["descriptionEn"] is None


class TestResourceSwagger:
    @pytest.fixture(autouse=True)
    def setup_exported(self):
        self.exported = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "API Gateway Resources", "description": ""},
            "schemes": ["http"],
            "paths": {
                "/users": {
                    "post": {
                        "operationId": "add_user",
                        "description": "创建新用户",
                        "tags": [],
                        "x-bk-apigateway-resource": {
                            "descriptionEn": "Adds a new user",
                            "isPublic": True,
                            "allowApplyPermission": True,
                            "matchSubpath": False,
                            "backend": {
                                "type": "HTTP",
                                "method": "post",
                                "path": "/users",
                                "matchSubpath": False,
                                "timeout": 0,
                                "upstreams": {},
                                "transformHeaders": {},
                            },
                            "authConfig": {"userVerifiedRequired": True},
                            "disabledStages": [],
                        },
                        "responses": {"default": {"description": ""}},
                    }
                }
            },
        }

    @pytest.fixture(autouse=True)
    def setup_exported_swagger(self):
        self.exported_swagger = json.dumps(self.exported)

    def do_import_resources(self, swagger):
        importer = ResourceSwaggerImporter(swagger)
        importer.validate()

        return importer.get_resources()

    def do_export_resources(self, exporter, resources):
        exported = exporter.to_swagger(resources, "json")
        return exported, json.loads(exported)

    def test_usage(self):
        imported_resources = self.do_import_resources(self.exported_swagger)

        _, exported = self.do_export_resources(
            ResourceSwaggerExporter(
                api_version=self.exported["info"]["version"],
                include_bk_apigateway_resource=True,
                title=self.exported["info"]["title"],
                description=self.exported["info"]["description"],
            ),
            imported_resources,
        )

        assert exported == self.exported

        exported_swagger, _ = self.do_export_resources(
            ResourceSwaggerExporter(
                api_version=self.exported["info"]["version"],
                include_bk_apigateway_resource=True,
                title=self.exported["info"]["title"],
                description=self.exported["info"]["description"],
            ),
            imported_resources,
        )

        assert imported_resources == self.do_import_resources(exported_swagger)
