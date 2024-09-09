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

from apigateway.biz.constants import OpenAPIFormatEnum
from apigateway.biz.resource.importer.openapi import OpenAPIExportManager, OpenAPIImportManager
from apigateway.biz.resource.importer.parser import BaseExporter
from apigateway.core.models import Gateway
from apigateway.utils.yaml import yaml_loads


class TestOpenAPIManger:
    @pytest.mark.parametrize(
        "content, expected, error",
        [
            (
                "{test}",
                None,
                Exception,
            ),
            (
                '{"swagger": "2.0"}',
                {
                    "swagger": "2.0",
                },
                None,
            ),
            (
                'swagger: "2.0"',
                {
                    "swagger": "2.0",
                },
                None,
            ),
        ],
    )
    def test_load_from_openapi_content(self, content, expected, error):
        if not error:
            manager = OpenAPIImportManager.load_from_content(gateway=G(Gateway), content=content)
            assert manager.data == expected
            return

        with pytest.raises(error):
            OpenAPIImportManager.load_from_content(gateway=G(Gateway), content=content)

    @pytest.mark.parametrize(
        "swagger, expected",
        [
            ('{"swagger": "2.0"}', OpenAPIFormatEnum.JSON),
            ('swagger: "2.0"', OpenAPIFormatEnum.YAML),
        ],
    )
    def test_guess_openapi_format(self, swagger, expected):
        result = OpenAPIImportManager.guess_content_format(swagger)
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
            manager = OpenAPIImportManager.load_from_content(gateway=G(Gateway), content=content)

            if not will_error:
                validate_err_list = manager.validate()
                assert len(validate_err_list) == 0
                return

            validate_err_list = manager.validate()
            assert len(validate_err_list) > 0

        @pytest.mark.parametrize(
            "content, expected",
            [
                (
                    json.dumps(
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
                                            },
                                            "authConfig": {
                                                "userVerifiedRequired": False,
                                            },
                                        },
                                    },
                                }
                            },
                        }
                    ),
                    [
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
                            "backend_name": "default",
                            "backend_config": {
                                "path": "/hello/",
                                "method": "GET",
                                "match_subpath": True,
                                "timeout": 30,
                                "legacy_transform_headers": None,
                                "legacy_upstreams": None,
                            },
                            "auth_config": {
                                "auth_verified_required": False,
                                "app_verified_required": True,
                                "resource_perm_required": True,
                            },
                            "plugin_configs": None,
                        }
                    ],
                ),
                (
                    json.dumps(
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
                    [
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
                            "backend_name": "default",
                            "backend_config": {
                                "method": "ANY",
                                "path": "/echo/",
                                "match_subpath": False,
                                "timeout": 0,
                                "legacy_transform_headers": None,
                                "legacy_upstreams": None,
                            },
                            "auth_config": {
                                "auth_verified_required": True,
                                "app_verified_required": True,
                                "resource_perm_required": True,
                            },
                            "plugin_configs": None,
                        }
                    ],
                ),
                (
                    json.dumps(
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
                    [
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
                            "backend_name": "default",
                            "backend_config": {
                                "method": "ANY",
                                "path": "/echo/",
                                "match_subpath": False,
                                "timeout": 0,
                                "legacy_transform_headers": None,
                                "legacy_upstreams": None,
                            },
                            "auth_config": {
                                "auth_verified_required": True,
                                "app_verified_required": True,
                                "resource_perm_required": True,
                            },
                            "plugin_configs": None,
                        }
                    ],
                ),
            ],
        )
        def test_get_resources(self, content, expected):
            importer = OpenAPIImportManager.load_from_content(G(Gateway), content)
            resources = importer.get_resource_list(raw=True)
            assert resources == expected


class TestOpenAPIExporter:
    def test_get_swagger_by_paths(self):
        paths = {
            "/user": {
                "get": {
                    "operationId": "get_user",
                },
            }
        }

        result = OpenAPIExportManager().get_swagger_by_paths(paths=paths, openapi_format=OpenAPIFormatEnum.YAML)
        assert not result.startswith("{")

        result = OpenAPIExportManager().get_swagger_by_paths(paths=paths, openapi_format=OpenAPIFormatEnum.JSON)
        assert result.startswith("{")

    def test_get_swagger_by_resources(self, fake_resource_dict):
        exporter = OpenAPIExportManager()

        content = exporter.get_swagger_by_resources([fake_resource_dict], "json")
        assert json.loads(content)["paths"]

        content = exporter.get_swagger_by_resources([fake_resource_dict], "yaml")
        assert yaml_loads(content)["paths"]

    def test_generate_paths(self, fake_resource_dict):
        exporter = BaseExporter()
        paths = exporter._gen_swagger_paths([fake_resource_dict])
        operation = paths[fake_resource_dict["path"]][fake_resource_dict["method"].lower()]

        assert operation == {
            "operationId": fake_resource_dict["name"],
            "description": fake_resource_dict["description"],
            "tags": fake_resource_dict["labels"],
            "x-bk-apigateway-resource": {
                "descriptionEn": fake_resource_dict["description_en"],
                "isPublic": fake_resource_dict["is_public"],
                "allowApplyPermission": fake_resource_dict["allow_apply_permission"],
                "matchSubpath": fake_resource_dict["match_subpath"],
                "enableWebsocket": fake_resource_dict["enable_websocket"],
                "backend": {
                    "name": fake_resource_dict["backend"]["name"],
                    "method": fake_resource_dict["backend"]["config"]["method"].lower(),
                    "path": fake_resource_dict["backend"]["config"]["path"],
                    "matchSubpath": fake_resource_dict["backend"]["config"]["match_subpath"],
                    "timeout": fake_resource_dict["backend"]["config"]["timeout"],
                },
                "authConfig": {
                    "userVerifiedRequired": fake_resource_dict["auth_config"]["auth_verified_required"],
                    "appVerifiedRequired": True,
                    "resourcePermissionRequired": True,
                },
                "pluginConfigs": [],
            },
            "responses": {"default": {"description": ""}},
        }

    def test_generate_paths__exclude_bk_apigateway_resource(self, fake_resource_dict):
        exporter = BaseExporter(include_bk_apigateway_resource=False)
        paths = exporter._gen_swagger_paths([fake_resource_dict])
        operation = paths[fake_resource_dict["path"]][fake_resource_dict["method"].lower()]

        assert "x-bk-apigateway-resource" not in operation

    def test_adapt_method(self):
        exporter = BaseExporter()

        result = exporter._adapt_method("ANY")
        assert result == "x-bk-apigateway-method-any"

        result = exporter._adapt_method("POST")
        assert result == "post"

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "backend": {
                        "name": "foo",
                        "config": {"method": "GET", "path": "/foo"},
                    },
                    "proxy_type": "http",
                    "proxy_configs": {},
                },
                {
                    "name": "foo",
                    "type": "HTTP",
                    "method": "get",
                    "path": "/foo",
                    "matchSubpath": False,
                    "timeout": 0,
                },
            ),
            (
                {
                    "backend": {},
                    "proxy_type": "http",
                    "proxy_configs": {
                        "http": {
                            "method": "GET",
                            "path": "/bar",
                            "match_subpath": False,
                            "timeout": 30,
                        }
                    },
                },
                {
                    "type": "HTTP",
                    "method": "get",
                    "path": "/bar",
                    "matchSubpath": False,
                    "timeout": 30,
                    "upstreams": {},
                    "transformHeaders": {},
                },
            ),
        ],
    )
    def test_adapt_backend(self, data, expected):
        exporter = BaseExporter()

        result = exporter._adapt_backend(**data)
        assert result == expected

    def test_adapt_backend__error(self):
        data = {
            "backend": {},
            "proxy_type": "mock",
            "proxy_configs": {},
        }

        exporter = BaseExporter()
        with pytest.raises(ValueError):
            exporter._adapt_backend(**data)

    @pytest.mark.parametrize(
        "auth_config, expected",
        [
            (
                {
                    "auth_verified_required": True,
                },
                {
                    "userVerifiedRequired": True,
                    "appVerifiedRequired": True,
                    "resourcePermissionRequired": True,
                },
            ),
            (
                {
                    "auth_verified_required": False,
                    "app_verified_required": False,
                    "resource_perm_required": False,
                },
                {
                    "userVerifiedRequired": False,
                    "appVerifiedRequired": False,
                    "resourcePermissionRequired": False,
                },
            ),
            (
                {
                    "auth_verified_required": False,
                    "app_verified_required": False,
                    "resource_perm_required": True,
                },
                {
                    "userVerifiedRequired": False,
                    "appVerifiedRequired": False,
                    "resourcePermissionRequired": False,
                },
            ),
        ],
    )
    def test_adapt_auth_config(self, auth_config, expected):
        exporter = BaseExporter()
        result = exporter._adapt_auth_config(auth_config)
        assert result == expected
