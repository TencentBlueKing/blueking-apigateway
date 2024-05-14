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

from apigateway.biz.resource.importer.parser import BaseParser, ResourceDataConvertor
from apigateway.core.models import Backend, Resource


class TestResourceDataConvertor:
    def test_convert(self, fake_gateway, faker):
        resource_1 = G(Resource, gateway=fake_gateway, name="test1", method="GET", path="/test1")
        resource_2 = G(Resource, gateway=fake_gateway, name="test2", method="POST", path="/test2")

        backend_1 = G(Backend, gateway=fake_gateway, name="foo")
        backend_2 = G(Backend, gateway=fake_gateway, name="default")

        resources = [
            {
                "id": resource_1.id,
                "name": "test1",
                "method": "GET",
                "path": "/test1",
                "backend_name": "foo",
                "backend_config": {
                    "method": "GET",
                    "path": "/backend/test1",
                },
            },
            {
                "name": "test2_1",
                "method": "POST",
                "path": "/test2",
                "backend_config": {
                    "method": "POST",
                    "path": "/backend/test2",
                },
            },
        ]
        convertor = ResourceDataConvertor(fake_gateway, resources)
        result = convertor.convert()

        assert result[0].resource == resource_1
        assert result[0].backend == backend_1
        assert result[0].backend_config.path == "/backend/test1"

        assert result[1].resource == resource_2
        assert result[1].backend == backend_2
        assert result[1].backend_config.path == "/backend/test2"

    def test_convert__error(self, fake_resource):
        resources = [
            {
                "id": fake_resource.id,
                "name": "test1",
                "method": "GET",
                "path": "/test1",
                "backend_name": "not_exist",
                "backend_config": {
                    "method": "GET",
                    "path": "/backend/test1",
                },
            },
        ]

        convertor = ResourceDataConvertor(fake_resource.gateway, resources)
        with pytest.raises(ValueError):
            convertor.convert()

    def test_get_resource_obj(self, fake_resource):
        resource_id_to_obj = {fake_resource.id: fake_resource}
        resource_key_to_resource_obj = {f"{fake_resource.method}:{fake_resource.path}": fake_resource}

        convertor = ResourceDataConvertor(fake_resource.gateway, [])

        resource_obj = convertor._get_resource_obj(
            {"id": fake_resource.id}, resource_id_to_obj, resource_key_to_resource_obj
        )
        assert resource_obj == fake_resource

        resource_obj = convertor._get_resource_obj(
            {"method": fake_resource.method, "path": fake_resource.path},
            resource_id_to_obj,
            resource_key_to_resource_obj,
        )
        assert resource_obj == fake_resource

        with pytest.raises(ValueError):
            convertor._get_resource_obj({"id": 0}, resource_id_to_obj, resource_key_to_resource_obj)


class TestBaseParser:
    @pytest.mark.parametrize(
        "swagger_data, expected",
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
    def test_get_paths(self, swagger_data, expected):
        manager = BaseParser(_openapi_data=swagger_data)
        result = manager.get_paths()
        assert result == expected

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
        manager = BaseParser(_openapi_data={})
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
        manager = BaseParser(_openapi_data={})
        result = manager._remove_invalid_method(paths)
        assert result == expected

    @pytest.mark.parametrize(
        "base_path, path, expected",
        [
            ("/", "/user", "/user"),
            ("/v2", "/user", "/v2/user"),
            ("/v2/", "/user", "/v2/user"),
        ],
    )
    def test_join_path(self, base_path, path, expected):
        manager = BaseParser(_openapi_data={})
        result = manager._join_path(base_path, path)
        assert result == expected

    def test_adapt_method(self, fake_openapi_content):
        importer = BaseParser(fake_openapi_content)
        assert importer._adapt_method("get") == "GET"
        assert importer._adapt_method("x-bk-apigateway-method-any") == "ANY"

    def test_adapt_backend__error(self, fake_openapi_content):
        importer = BaseParser(fake_openapi_content)

        with pytest.raises(ValueError):
            importer._adapt_backend({"type": "MOCK"})

    @pytest.mark.parametrize(
        "backend, expected",
        [
            (
                {
                    "type": "HTTP",
                    "method": "get",
                    "path": "/foo",
                    "matchSubpath": True,
                },
                {
                    "method": "GET",
                    "path": "/foo",
                    "match_subpath": True,
                    "timeout": 0,
                    "legacy_upstreams": None,
                    "legacy_transform_headers": None,
                },
            ),
            (
                {
                    "type": "HTTP",
                    "method": "get",
                    "path": "/foo",
                    "matchSubpath": True,
                    "upstreams": {"loadbalance": "roundrobin", "hosts": [{"host": "http://foo.com", "weight": 100}]},
                    "transformHeaders": {"set": {"x-token": "test"}, "delete": ["x-token"]},
                },
                {
                    "method": "GET",
                    "path": "/foo",
                    "match_subpath": True,
                    "timeout": 0,
                    "legacy_upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [{"host": "http://foo.com", "weight": 100}],
                    },
                    "legacy_transform_headers": {"set": {"x-token": "test"}, "delete": ["x-token"]},
                },
            ),
        ],
    )
    def test_adapt_backend(self, fake_openapi_content, backend, expected):
        importer = BaseParser(fake_openapi_content)
        result = importer._adapt_backend(backend)
        assert result == expected

    @pytest.mark.parametrize(
        "auth_config, expected",
        [
            (
                {
                    "userVerifiedRequired": True,
                    "appVerifiedRequired": True,
                    "resourcePermissionRequired": True,
                },
                {
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            ),
            (
                {
                    "userVerifiedRequired": False,
                    "appVerifiedRequired": False,
                    "resourcePermissionRequired": False,
                },
                {
                    "auth_verified_required": False,
                    "app_verified_required": False,
                    "resource_perm_required": False,
                },
            ),
            (
                {
                    "userVerifiedRequired": False,
                    "appVerifiedRequired": False,
                    "resourcePermissionRequired": True,
                },
                {
                    "auth_verified_required": False,
                    "app_verified_required": False,
                    "resource_perm_required": False,
                },
            ),
        ],
    )
    def test_adapt_auth_config(self, fake_openapi_content, auth_config, expected):
        importer = BaseParser(fake_openapi_content)
        result = importer._adapt_auth_config(auth_config)
        assert result == expected
