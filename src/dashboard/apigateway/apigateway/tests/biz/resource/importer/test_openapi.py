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
import json

import pytest
from ddf import G
from openapi_spec_validator.versions import get_spec_version

from apigateway.apps.support.constants import OpenAPIFormatEnum
from apigateway.biz.openapi import OpenAPIImportManager
from apigateway.biz.openapi.schema import openapi_validator_mapping
from apigateway.biz.resource.importer import sync_openapi_resources_from_content
from apigateway.core.constants import DEFAULT_BACKEND_NAME
from apigateway.core.models import Backend, Gateway
from apigateway.service.resource_version import BaseExporter, OpenAPIExportManager
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
                # not error, set websocket
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
                                            "enableWebsocket": True,
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
                # error, set websocket valid
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
                                            "enableWebsocket": 1,
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


class TestOpenAPIImportManagerParse:
    """Regression tests for OpenAPIImportManager.parse() — ensures dict data
    is serialized as valid JSON (not Python repr) before passing to ResolvingParser."""

    def _make_gateway_with_backend(self):
        gateway = G(Gateway)
        G(Backend, gateway=gateway, name=DEFAULT_BACKEND_NAME)
        return gateway

    def _make_manager(self, data):
        gateway = self._make_gateway_with_backend()
        manager = OpenAPIImportManager(gateway=gateway, data=data)
        manager.version = get_spec_version(data)
        return manager

    @pytest.mark.parametrize("openapi_version", ["2.0", "3.0.1", "3.1.0"])
    @pytest.mark.parametrize("resource_kind", [None, "standard"])
    def test_schema_rejects_name_only_backend_for_standard_resource(self, openapi_version, resource_kind):
        data = self._name_only_backend_document(openapi_version, resource_kind)

        errors = list(openapi_validator_mapping[get_spec_version(data)].cls(data).iter_errors())

        assert errors

    @pytest.mark.parametrize("openapi_version", ["2.0", "3.0.1", "3.1.0"])
    def test_schema_accepts_name_only_backend_for_ai_resource(self, openapi_version):
        data = self._name_only_backend_document(openapi_version, "ai")

        errors = list(openapi_validator_mapping[get_spec_version(data)].cls(data).iter_errors())

        assert not errors

    @staticmethod
    def _name_only_backend_document(openapi_version, resource_kind):
        extension = {"backend": {"name": "openai-primary"}}
        if resource_kind is not None:
            extension["kind"] = resource_kind

        version = {"swagger": openapi_version} if openapi_version == "2.0" else {"openapi": openapi_version}
        return {
            **version,
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/chat": {
                    "post": {
                        "operationId": "chat",
                        "responses": {"200": {"description": "OK"}},
                        "x-bk-apigateway-resource": extension,
                    }
                }
            },
        }

    def test_parse_swagger2_dict(self):
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "schemes": ["http"],
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "description": "test",
                        "tags": ["test"],
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {
                                "type": "HTTP",
                                "path": "/test/",
                                "method": "get",
                                "timeout": 30,
                            },
                        },
                    }
                }
            },
        }
        manager = self._make_manager(data)
        manager.parse()

        resources = manager.get_resource_list(raw=True)
        assert len(resources) == 1
        assert resources[0]["name"] == "get_test"
        assert resources[0]["method"] == "GET"
        assert resources[0]["path"] == "/test/"

    def test_parse_openapi3_dict(self):
        data = {
            "openapi": "3.0.1",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/test/": {
                    "post": {
                        "operationId": "post_test",
                        "description": "test post",
                        "tags": ["demo"],
                        "responses": {"200": {"description": "success"}},
                        "x-bk-apigateway-resource": {
                            "isPublic": False,
                            "backend": {
                                "type": "HTTP",
                                "path": "/backend/test/",
                                "method": "post",
                                "timeout": 10,
                            },
                        },
                    }
                }
            },
        }
        manager = self._make_manager(data)
        manager.parse()

        resources = manager.get_resource_list(raw=True)
        assert len(resources) == 1
        assert resources[0]["name"] == "post_test"
        assert resources[0]["is_public"] is False

    def test_parse_from_yaml_content(self):
        yaml_content = """\
swagger: "2.0"
basePath: /
info:
  version: "0.1"
  title: Test
schemes:
  - http
paths:
  /yaml-test/:
    get:
      operationId: yaml_test_get
      description: yaml originated
      tags:
        - yaml
      x-bk-apigateway-resource:
        isPublic: true
        backend:
          type: HTTP
          path: /yaml-test/
          method: get
          timeout: 30
"""
        gateway = self._make_gateway_with_backend()
        manager = OpenAPIImportManager.load_from_content(gateway=gateway, content=yaml_content)
        manager.version = get_spec_version(manager.data)
        manager.parse()

        resources = manager.get_resource_list(raw=True)
        assert len(resources) == 1
        assert resources[0]["name"] == "yaml_test_get"

    def test_parse_dict_with_boolean_and_none_values(self):
        """Python True/False/None would break str() but work with json.dumps()."""
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "schemes": ["http"],
            "paths": {
                "/bool-test/": {
                    "get": {
                        "operationId": "bool_test",
                        "description": "test booleans",
                        "tags": [],
                        "x-bk-apigateway-resource": {
                            "isPublic": False,
                            "allowApplyPermission": True,
                            "backend": {
                                "type": "HTTP",
                                "path": "/bool-test/",
                                "method": "get",
                                "timeout": 0,
                            },
                            "authConfig": {
                                "userVerifiedRequired": False,
                                "appVerifiedRequired": False,
                            },
                        },
                    }
                }
            },
        }
        manager = self._make_manager(data)
        manager.parse()

        resources = manager.get_resource_list(raw=True)
        assert len(resources) == 1
        assert resources[0]["name"] == "bool_test"
        assert resources[0]["is_public"] is False
        assert resources[0]["auth_config"]["auth_verified_required"] is False

    def test_validate_returns_schema_err_for_recursive_ref(self):
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "schemes": ["http"],
            "paths": {
                "/tree/": {
                    "get": {
                        "operationId": "get_tree",
                        "description": "test recursive ref",
                        "tags": [],
                        "responses": {
                            "200": {
                                "description": "success",
                                "schema": {"$ref": "#/definitions/v3TopoNodeInfo"},
                            },
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {
                                "type": "HTTP",
                                "path": "/tree/",
                                "method": "get",
                                "timeout": 30,
                            },
                        },
                    }
                }
            },
            "definitions": {
                "v3TopoNodeInfo": {
                    "type": "object",
                    "properties": {
                        "children": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/v3TopoNodeInfo"},
                        }
                    },
                }
            },
        }
        manager = self._make_manager(data)

        validate_err_list = manager.validate()

        assert len(validate_err_list) == 1
        assert "Recursion reached limit" in validate_err_list[0].message
        assert "#/definitions/v3TopoNodeInfo" in validate_err_list[0].message


class TestOpenAPIExporter:
    def test_generate_ai_resource_extension(self, fake_resource_dict):
        resource = dict(fake_resource_dict)
        resource.update(
            {
                "kind": "ai",
                "method": "POST",
                "backend": {"name": "openai-primary", "config": {}},
            }
        )

        operation = BaseExporter()._gen_swagger_paths([resource])[resource["path"]]["post"]
        extension = operation["x-bk-apigateway-resource"]

        assert extension["kind"] == "ai"
        assert extension["backend"] == {"name": "openai-primary"}

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

    def test_generate_paths__plugin_configs_dict(self, fake_resource_dict):
        """plugin_configs 为 dict 列表时（资源版本导出路径），pluginConfigs 应正确填充。"""
        resource = dict(
            fake_resource_dict,
            plugin_configs=[
                {
                    "type": "bk-header-rewrite",
                    "yaml": "remove:\n- X-Bar\nset:\n- key: X-Foo\n  value: test",
                },
            ],
        )
        exporter = BaseExporter()
        paths = exporter._gen_swagger_paths([resource])
        operation = paths[resource["path"]][resource["method"].lower()]

        plugin_configs = operation["x-bk-apigateway-resource"]["pluginConfigs"]
        assert len(plugin_configs) == 1
        assert plugin_configs[0]["type"] == "bk-header-rewrite"
        # yaml_dumps 输出末尾不应有多余换行
        assert not plugin_configs[0]["yaml"].endswith("\n")
        assert "remove:" in plugin_configs[0]["yaml"]

    def test_generate_paths__plugin_configs_orm_obj(self, fake_plugin_config):
        """plugin_configs 为 PluginConfig ORM 对象列表时（资源配置导出路径），应兼容。"""
        resource = {
            "method": "GET",
            "path": "/test",
            "name": "test_api",
            "description": "",
            "description_en": None,
            "labels": [],
            "is_public": True,
            "allow_apply_permission": True,
            "match_subpath": False,
            "enable_websocket": False,
            "backend": {
                "name": "default",
                "config": {"method": "GET", "path": "/test", "timeout": 0},
            },
            "auth_config": {"auth_verified_required": True},
            "plugin_configs": [fake_plugin_config],
        }
        exporter = BaseExporter()
        paths = exporter._gen_swagger_paths([resource])
        operation = paths["/test"]["get"]

        plugin_configs = operation["x-bk-apigateway-resource"]["pluginConfigs"]
        assert len(plugin_configs) == 1
        assert plugin_configs[0]["type"] == "bk-cors"
        assert "allow_origins" in plugin_configs[0]["yaml"]


class TestOpenAPIImportManagerValidateRefs:
    """Tests for _validate_refs — ensures external $ref values are rejected."""

    @pytest.mark.parametrize("ref_value", ["#/definitions/User", "#User", "#"])
    def test_internal_ref_allowed(self, ref_value):
        """Pure internal fragment refs should pass validation."""
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "definitions": {
                "User": {"type": "object", "properties": {"name": {"type": "string"}}},
            },
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "responses": {
                            "200": {"schema": {"$ref": ref_value}},
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }
        OpenAPIImportManager._validate_refs(data)

    def test_openapi_31_anchor_ref_allowed(self):
        data = {
            "openapi": "3.1.0",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#userSchema"},
                                    }
                                }
                            },
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }

        OpenAPIImportManager._validate_refs(data)

    def test_external_url_ref_rejected(self):
        """HTTP(S) URL $ref should be rejected to prevent SSRF."""
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "responses": {
                            "200": {"schema": {"$ref": "http://evil.com/schema.json#/definitions/User"}},
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }
        with pytest.raises(ValueError, match="external \\$ref"):
            OpenAPIImportManager._validate_refs(data)

    def test_local_file_ref_rejected(self):
        """Local file path $ref should be rejected to prevent file read."""
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "responses": {
                            "200": {"schema": {"$ref": "/etc/passwd"}},
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }
        with pytest.raises(ValueError, match="external \\$ref"):
            OpenAPIImportManager._validate_refs(data)

    def test_relative_file_ref_rejected(self):
        """Relative file path $ref should be rejected."""
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "responses": {
                            "200": {"schema": {"$ref": "../common/models.yaml#/User"}},
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }
        with pytest.raises(ValueError, match="external \\$ref"):
            OpenAPIImportManager._validate_refs(data)

    def test_validate_returns_schema_err_for_unsafe_ref(self):
        """validate() should return SchemaValidateErr when $ref is external, not raise."""
        gateway = G(Gateway)
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "schemes": ["http"],
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "description": "test",
                        "tags": ["test"],
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                        "responses": {
                            "200": {"schema": {"$ref": "http://internal-service.local/schema.json"}},
                        },
                    }
                }
            },
        }
        manager = OpenAPIImportManager(gateway=gateway, data=data)
        validate_err_list = manager.validate()
        assert len(validate_err_list) > 0
        assert "external $ref" in validate_err_list[0].message
        assert "http://internal-service.local/schema.json" not in validate_err_list[0].message

    def test_validate_and_parse_use_same_unsafe_ref_message(self):
        gateway = G(Gateway)
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "schemes": ["http"],
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "description": "test",
                        "tags": ["test"],
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                        "responses": {
                            "200": {"schema": {"$ref": "http://internal-service.local/schema.json"}},
                        },
                    }
                }
            },
        }
        manager = OpenAPIImportManager(gateway=gateway, data=data)

        validate_err_list = manager.validate()

        with pytest.raises(ValueError) as err:
            manager.parse()

        assert validate_err_list[0].message == str(err.value)

    def test_literal_ref_text_in_description_is_not_misclassified(self):
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "description": 'example text with {"$ref": "http://evil.com/schema.json"}',
                        "responses": {
                            "200": {"description": "success"},
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }

        OpenAPIImportManager._validate_refs(data)

    def test_xss_like_ref_value_is_not_echoed_in_error_message(self):
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "responses": {
                            "200": {"schema": {"$ref": "<img src=x onerror=alert(1)>"}},
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }

        with pytest.raises(ValueError) as err:
            OpenAPIImportManager._validate_refs(data)

        assert "<img src=x onerror=alert(1)>" not in str(err.value)

    def test_xss_like_key_is_not_echoed_in_error_message(self):
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/<img src=x onerror=alert(1)>/": {
                    "get": {
                        "operationId": "get_test",
                        "responses": {
                            "200": {"schema": {"$ref": "http://evil.com/schema.json#/definitions/User"}},
                        },
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }

        with pytest.raises(ValueError) as err:
            OpenAPIImportManager._validate_refs(data)

        assert "/<img src=x onerror=alert(1)>/" not in str(err.value)
        assert "http://evil.com/schema.json" not in str(err.value)

    def test_no_ref_passes(self):
        """Document with no $ref at all should pass validation."""
        data = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {"version": "0.1", "title": "Test"},
            "paths": {
                "/test/": {
                    "get": {
                        "operationId": "get_test",
                        "responses": {"200": {"description": "success"}},
                        "x-bk-apigateway-resource": {
                            "isPublic": True,
                            "backend": {"type": "HTTP", "path": "/test/", "method": "get", "timeout": 30},
                        },
                    }
                }
            },
        }
        OpenAPIImportManager._validate_refs(data)

    def test_has_unsafe_refs(self):
        data = {
            "paths": {
                "/test/": {
                    "get": {
                        "responses": {
                            "200": {
                                "schema": {
                                    "$ref": "http://evil.com/schema.json#/definitions/User",
                                }
                            }
                        }
                    }
                }
            }
        }

        assert OpenAPIImportManager._has_unsafe_refs(data) is True

    def test_has_unsafe_refs_all_internal(self):
        data = {
            "paths": {
                "/test/": {
                    "get": {
                        "responses": {
                            "200": {
                                "schema": {
                                    "$ref": "#/definitions/User",
                                }
                            }
                        }
                    }
                }
            }
        }

        assert OpenAPIImportManager._has_unsafe_refs(data) is False


class TestSyncOpenAPIResourcesFromContent:
    PATCH_PREFIX = "apigateway.biz.resource.importer.sync"

    def _mock_sync_deps(self, mocker):
        mgr = mocker.patch(f"{self.PATCH_PREFIX}.OpenAPIImportManager.load_from_content").return_value
        mgr.validate.return_value = []
        mgr.get_resource_list.return_value = []

        imp_cls = mocker.patch(f"{self.PATCH_PREFIX}.ResourcesImporter")
        imp = imp_cls.from_resources.return_value
        imp.get_selected_resource_data_list.return_value = []
        imp.get_deleted_resources.return_value = []
        return mgr, imp

    def test_returns_diff(self, fake_gateway, mocker):
        self._mock_sync_deps(mocker)

        ok, message, data = sync_openapi_resources_from_content(
            gateway=fake_gateway,
            username="admin",
            content='{"swagger": "2.0", "paths": {}}',
            delete_missing_resources=False,
            doc_language="",
        )

        assert ok is True
        assert message == ""
        assert data["added"] == []
        assert data["updated"] == []
        assert data["deleted"] == []

    def test_invalid_content_returns_not_ok(self, fake_gateway, mocker):
        mocker.patch(
            f"{self.PATCH_PREFIX}.OpenAPIImportManager.load_from_content",
            side_effect=ValueError("bad yaml"),
        )

        ok, message, data = sync_openapi_resources_from_content(
            gateway=fake_gateway,
            username="admin",
            content="not valid",
            delete_missing_resources=False,
        )

        assert ok is False
        assert "json/yaml" in message
        assert "bad yaml" in message
        assert data == {}

    def test_validation_error_returns_not_ok(self, fake_gateway, mocker):
        mgr, _ = self._mock_sync_deps(mocker)
        mock_err = mocker.MagicMock()
        mock_err.to_dict.return_value = {"message": "bad"}
        mgr.validate.return_value = [mock_err]

        ok, message, data = sync_openapi_resources_from_content(
            gateway=fake_gateway,
            username="admin",
            content='{"swagger": "2.0", "paths": {}}',
            delete_missing_resources=False,
        )

        assert ok is False
        assert "bad" in message
        assert data == {}

    def test_with_doc_language(self, fake_gateway, mocker):
        self._mock_sync_deps(mocker)

        mock_parser = mocker.patch(f"{self.PATCH_PREFIX}.OpenAPIParser").return_value
        mock_parser.parse.return_value = []
        mock_doc_importer = mocker.patch(f"{self.PATCH_PREFIX}.DocImporter").return_value

        ok, message, data = sync_openapi_resources_from_content(
            gateway=fake_gateway,
            username="admin",
            content='{"swagger": "2.0", "paths": {}}',
            delete_missing_resources=False,
            doc_language="zh",
        )

        mock_parser.parse.assert_called_once()
        mock_doc_importer.import_docs.assert_called_once()
        assert ok is True
        assert message == ""

    def test_added_and_updated_classification(self, fake_gateway, mocker):
        _, imp = self._mock_sync_deps(mocker)

        created_rd = mocker.MagicMock()
        created_rd.metadata = {"is_created": True}
        created_rd.resource.id = 1

        updated_rd = mocker.MagicMock()
        updated_rd.metadata = {}
        updated_rd.resource.id = 2

        imp.get_selected_resource_data_list.return_value = [created_rd, updated_rd]
        imp.get_deleted_resources.return_value = [{"id": 3}]

        ok, message, data = sync_openapi_resources_from_content(
            gateway=fake_gateway,
            username="admin",
            content='{"swagger": "2.0", "paths": {}}',
            delete_missing_resources=True,
        )

        assert ok is True
        assert message == ""
        assert data["added"] == [{"id": 1}]
        assert data["updated"] == [{"id": 2}]
        assert data["deleted"] == [{"id": 3}]
