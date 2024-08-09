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
from django.utils import timezone

from apigateway.apis.web.resource.views import (
    BackendHostIsEmpty,
    BackendPathCheckApi,
)
from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_label import ResourceLabelHandler
from apigateway.common.contexts import ResourceAuthContext
from apigateway.core import constants
from apigateway.core.models import Backend, BackendConfig, Context, Proxy, Resource, Stage


class TestResourceListCreateApi:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {},
                2,
            ),
            (
                {"path": "/echo/"},
                1,
            ),
            (
                {"method": "GET"},
                2,
            ),
            (
                {"keyword": "echo"},
                1,
            ),
        ],
    )
    def test_list(self, request_view, fake_gateway, fake_backend, data, expected):
        resource_1 = G(Resource, gateway=fake_gateway, path="/echo/", method="GET", name="echo")
        resource_2 = G(Resource, gateway=fake_gateway, path="/test/", method="GET", name="test")
        G(Proxy, resource=resource_1, backend=fake_backend)
        G(Proxy, resource=resource_2, backend=fake_backend)

        resp = request_view(
            method="GET",
            view_name="resource.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        result = resp.json()
        assert resp.status_code == 200
        assert len(result["data"]["results"]) == expected

    @pytest.mark.parametrize(
        "data",
        [
            {
                "name": "post_echo",
                "description": "desc",
                "is_public": True,
                "method": "POST",
                "path": "/echo/",
                "match_subpath": False,
                "label_ids": [],
                "backend": {
                    "config": {
                        "method": "GET",
                        "path": "/echo/",
                        "match_subpath": False,
                        "timeout": 30,
                    }
                },
                "auth_config": {
                    "auth_verified_required": False,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            },
        ],
    )
    def test_create(self, request_view, fake_gateway, data):
        backend = G(Backend, gateway=fake_gateway)
        data["backend"]["id"] = backend.id

        resp = request_view(
            method="POST",
            view_name="resource.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )

        assert resp.status_code == 201

        resource = Resource.objects.get(gateway=fake_gateway, method=data["method"], path=data["path"])
        assert resource.is_public == data["is_public"]
        assert resource.match_subpath == data["match_subpath"]

        proxy = Proxy.objects.get(resource=resource)
        assert proxy.backend_id == backend.id

        context = Context.objects.get(
            scope_type=constants.ContextScopeTypeEnum.RESOURCE.value,
            type=constants.ContextTypeEnum.RESOURCE_AUTH.value,
            scope_id=resource.id,
        )
        assert context.config == {
            "skip_auth_verification": False,
            "auth_verified_required": False,
            "app_verified_required": True,
            "resource_perm_required": True,
        }


class TestResourceRetrieveUpdateDestroyApi:
    def test_retrieve(self, fake_resource, request_view):
        fake_gateway = fake_resource.gateway

        resp = request_view(
            method="GET",
            view_name="resource.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "id": fake_resource.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == fake_resource.id

    def test_update(self, request_view, fake_resource):
        fake_gateway = fake_resource.gateway
        backend = Backend.objects.filter(gateway=fake_gateway).first()

        data = {
            "name": "post_echo",
            "description": "desc",
            "is_public": True,
            "method": "POST",
            "path": "/echo/",
            "label_ids": [],
            "backend": {
                "id": backend.id,
                "config": {
                    "method": "GET",
                    "path": "/echo/",
                    "timeout": 30,
                },
            },
            "auth_config": {
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
        }

        resp = request_view(
            method="PUT",
            view_name="resource.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "id": fake_resource.id},
            data=data,
        )

        assert resp.status_code == 204

        proxy = Proxy.objects.get(resource=fake_resource)
        assert proxy.backend_id == backend.id

        auth_config = ResourceAuthContext().get_config(fake_resource.id)
        assert auth_config == {
            "skip_auth_verification": False,
            "auth_verified_required": False,
            "app_verified_required": True,
            "resource_perm_required": True,
        }

    def test_destroy(self, request_view, fake_resource):
        fake_gateway = fake_resource.gateway

        resp = request_view(
            method="DELETE",
            view_name="resource.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "id": fake_resource.id},
        )
        assert resp.status_code == 204
        assert not Resource.objects.filter(id=fake_resource.id).exists()
        assert not Proxy.objects.filter(resource=fake_resource)
        assert not Context.objects.filter(type="resource", scope_id=fake_resource.id)


class TestResourceBatchUpdateDestroyApi:
    def test_update(self, request_view, fake_resource):
        data = {
            "ids": [fake_resource.id],
            "is_public": True,
            "allow_apply_permission": True,
        }

        resp = request_view(
            method="PUT",
            view_name="resource.batch_update_destroy",
            path_params={"gateway_id": fake_resource.gateway.id},
            data=data,
        )

        assert resp.status_code == 204

        resource = Resource.objects.get(id=fake_resource.id)
        assert resource.is_public == data["is_public"]
        assert resource.allow_apply_permission == data["allow_apply_permission"]

    def test_update_label_add(self, request_view, fake_resource, fake_resource1, fake_gateway):
        label_1 = G(APILabel, gateway=fake_gateway, name="test")
        label_2 = G(APILabel, gateway=fake_gateway, name="test1")
        data = {
            "ids": [fake_resource.id, fake_resource1.id],
            "is_public": True,
            "allow_apply_permission": True,
            "is_update_labels": True,
            "label_ids": [label_1.id, label_2.id],
        }

        resp = request_view(
            method="PUT",
            view_name="resource.batch_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )

        assert resp.status_code == 204

        resource = Resource.objects.get(id=fake_resource.id)
        assert resource.is_public == data["is_public"]
        assert resource.allow_apply_permission == data["allow_apply_permission"]
        label = ResourceLabelHandler.get_labels([fake_resource.id])
        assert label[fake_resource.id] == [
            {"id": label_1.id, "name": label_1.name},
            {"id": label_2.id, "name": label_2.name},
        ]

        resp = request_view(
            method="GET",
            view_name="resource.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        result = resp.json()
        assert resp.status_code == 200
        assert result["data"]["results"][0]["labels"] == [
            {"id": label_1.id, "name": label_1.name},
            {"id": label_2.id, "name": label_2.name},
        ]
        assert result["data"]["results"][1]["labels"] == [
            {"id": label_1.id, "name": label_1.name},
            {"id": label_2.id, "name": label_2.name},
        ]

    def test_update_label_delete(self, request_view, fake_resource, fake_resource1, fake_gateway):
        label_1 = G(APILabel, gateway=fake_gateway, name="test")
        label_2 = G(APILabel, gateway=fake_gateway, name="test1")
        # 将标签绑定上资源
        G(ResourceLabel, resource=fake_resource, api_label=label_1)
        G(ResourceLabel, resource=fake_resource, api_label=label_2)
        G(ResourceLabel, resource=fake_resource1, api_label=label_1)
        G(ResourceLabel, resource=fake_resource1, api_label=label_2)
        data = {
            "ids": [fake_resource.id, fake_resource1.id],
            "is_public": True,
            "allow_apply_permission": True,
            "is_update_labels": True,
            "label_ids": [],
        }

        resp = request_view(
            method="PUT",
            view_name="resource.batch_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )

        assert resp.status_code == 204

        resource = Resource.objects.get(id=fake_resource.id)
        assert resource.is_public == data["is_public"]
        assert resource.allow_apply_permission == data["allow_apply_permission"]
        label = ResourceLabelHandler.get_labels([fake_resource.id])
        assert label[fake_resource.id] == []

        resp = request_view(
            method="GET",
            view_name="resource.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        result = resp.json()
        assert resp.status_code == 200
        assert result["data"]["results"][0]["labels"] == []
        assert result["data"]["results"][1]["labels"] == []

    def test_destroy(self, request_view, fake_resource):
        data = {
            "ids": [fake_resource.id],
        }

        resp = request_view(
            method="DELETE",
            view_name="resource.batch_update_destroy",
            path_params={"gateway_id": fake_resource.gateway.id},
            data=data,
        )

        assert resp.status_code == 204
        assert not Resource.objects.filter(id__in=data["ids"]).exists()


class TestResourceLabelUpdateApi:
    def test_update(self, request_view, fake_resource):
        fake_gateway = fake_resource.gateway
        initial_updated_time = fake_resource.updated_time
        label_1 = G(APILabel, gateway=fake_gateway)
        label_2 = G(APILabel, gateway=fake_gateway)

        assert initial_updated_time is not None and initial_updated_time <= timezone.now()
        resp = request_view(
            method="PUT",
            view_name="resource.label.update",
            path_params={"gateway_id": fake_gateway.id, "resource_id": fake_resource.id},
            data={
                "label_ids": [label_1.id],
            },
        )
        assert resp.status_code == 204
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 1
        fake_resource.refresh_from_db()
        assert fake_resource.updated_time > initial_updated_time

        initial_updated_time = fake_resource.updated_time
        resp = request_view(
            method="PUT",
            view_name="resource.label.update",
            path_params={"gateway_id": fake_gateway.id, "resource_id": fake_resource.id},
            data={
                "label_ids": [label_1.id, label_2.id],
            },
        )
        assert resp.status_code == 204
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 2
        fake_resource.refresh_from_db()
        assert fake_resource.updated_time > initial_updated_time

        initial_updated_time = fake_resource.updated_time
        resp = request_view(
            method="PUT",
            view_name="resource.label.update",
            path_params={"gateway_id": fake_gateway.id, "resource_id": fake_resource.id},
            data={
                "label_ids": [label_2.id],
            },
        )
        assert resp.status_code == 204
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 1
        fake_resource.refresh_from_db()
        assert fake_resource.updated_time > initial_updated_time


class TestResourceImportCheckApi:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
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
                                        "operationId": "http_get_mapping_user_id",
                                        "description": "test",
                                        "parameters": [
                                            {
                                                "name": "userId",
                                                "in": "path",
                                                "description": "ID of User",
                                                "required": True,
                                                "type": "integer",
                                                "format": "int64",
                                            }
                                        ],
                                        "tags": ["pet"],
                                        "schemes": ["http"],
                                        "x-bk-apigateway-resource": {
                                            "isPublic": True,
                                            "allowApplyPermission": True,
                                            "matchSubpath": True,
                                            "backend": {
                                                "name": "default",
                                                "type": "HTTP",
                                                "method": "get",
                                                "path": "/hello/",
                                                "matchSubpath": True,
                                                "timeout": 30,
                                            },
                                        },
                                    },
                                }
                            },
                        }
                    ),
                },
                [
                    {
                        "id": None,
                        "name": "http_get_mapping_user_id",
                        "description": "test",
                        "description_en": None,
                        "method": "GET",
                        "path": "/http/get/mapping/{userId}/*",
                        "match_subpath": True,
                        "is_public": True,
                        "allow_apply_permission": True,
                        "doc": [],
                        "auth_config": {
                            "auth_verified_required": True,
                            "app_verified_required": True,
                            "resource_perm_required": True,
                        },
                        "backend": {
                            "name": "default",
                            "config": {"method": "GET", "path": "/hello/", "match_subpath": True, "timeout": 30},
                        },
                        "labels": ["pet"],
                        "openapi_schema": {
                            "parameters": [
                                {
                                    "name": "userId",
                                    "in": "path",
                                    "required": True,
                                    "description": "ID of User",
                                    "schema": {"type": "integer", "format": "int64"},
                                }
                            ]
                        },
                        "plugin_configs": None,
                    }
                ],
            ),
            (
                {
                    "doc_language": "zh",
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
                                        "operationId": "http_get_mapping_user_id",
                                        "description": "test",
                                        "tags": ["pet"],
                                        "schemes": ["http"],
                                        "x-bk-apigateway-resource": {
                                            "isPublic": True,
                                            "allowApplyPermission": True,
                                            "matchSubpath": False,
                                            "backend": {
                                                "name": "default",
                                                "type": "HTTP",
                                                "method": "get",
                                                "path": "/hello/",
                                                "matchSubpath": False,
                                                "timeout": 30,
                                            },
                                        },
                                    },
                                }
                            },
                        }
                    ),
                },
                [
                    {
                        "id": None,
                        "name": "http_get_mapping_user_id",
                        "description": "test",
                        "description_en": None,
                        "method": "GET",
                        "path": "/http/get/mapping/{userId}",
                        "match_subpath": False,
                        "is_public": True,
                        "allow_apply_permission": True,
                        "doc": [],
                        "auth_config": {
                            "auth_verified_required": True,
                            "app_verified_required": True,
                            "resource_perm_required": True,
                        },
                        "backend": {
                            "name": "default",
                            "config": {"method": "GET", "path": "/hello/", "match_subpath": False, "timeout": 30},
                        },
                        "labels": ["pet"],
                        "openapi_schema": {},
                        "plugin_configs": None,
                    }
                ],
            ),
        ],
    )
    def test_post(self, request_view, fake_gateway, data, expected):
        G(Backend, gateway=fake_gateway, name="default")
        resp = request_view(
            method="POST",
            view_name="resource.import.check",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"] == expected


class TestResourceImportApi:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "import_resources": [
                        {
                            "id": None,
                            "name": "import_r_user_2",
                            "description": "test",
                            "description_en": None,
                            "method": "GET",
                            "path": "/import/r/{user}/",
                            "match_subpath": False,
                            "is_public": True,
                            "allow_apply_permission": True,
                            "doc": [],
                            "auth_config": {
                                "auth_verified_required": True,
                                "app_verified_required": True,
                                "resource_perm_required": True,
                            },
                            "backend_name": "default",
                            "backend_config": {
                                "method": "GET",
                                "path": "/hello/",
                                "match_subpath": False,
                                "timeout": 30,
                            },
                            "labels": ["pet"],
                            "openapi_schema": {},
                            "plugin_configs": None,
                        },
                        {
                            "id": None,
                            "name": "import_any_user_2",
                            "description": "test",
                            "description_en": None,
                            "method": "ANY",
                            "path": "/import/any/{user}/2/",
                            "match_subpath": False,
                            "is_public": True,
                            "allow_apply_permission": True,
                            "doc": [],
                            "auth_config": {
                                "auth_verified_required": True,
                                "app_verified_required": True,
                                "resource_perm_required": True,
                            },
                            "backend_name": "default",
                            "backend_config": {
                                "method": "ANY",
                                "path": "/hello/",
                                "match_subpath": False,
                                "timeout": 30,
                            },
                            "labels": [],
                            "openapi_schema": {},
                            "plugin_configs": None,
                        },
                    ]
                },
                2,
            )
        ],
    )
    def test_post(self, request_view, fake_gateway, data, expected):
        G(Backend, gateway=fake_gateway, name="default")

        resp = request_view(
            method="POST",
            view_name="resource.import",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )

        assert resp.status_code == 204
        assert Resource.objects.filter(gateway=fake_gateway).count() == expected


class TestResourceExportApi:
    @pytest.mark.parametrize(
        "data",
        [
            {"export_type": "all", "file_type": "yaml"},
            {"export_type": "filtered", "file_type": "json"},
            {"export_type": "selected", "file_type": "yaml"},
        ],
    )
    def test_post(self, request_view, fake_resource, data):
        fake_gateway = fake_resource.gateway
        label = G(APILabel, gateway=fake_gateway)
        G(ResourceLabel, resource=fake_resource, api_label=label)

        resp = request_view(
            method="POST",
            view_name="resource.export",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )

        assert resp.status_code == 200


class TestBackendPathCheckApi:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                # ok, no vars
                {
                    "path": "/echo/",
                    "backend_path": "/echo/",
                },
                200,
            ),
            (
                # ok, have same vars
                {
                    "path": "/echo/{cmd}/",
                    "backend_path": "/echo/{cmd}/",
                },
                200,
            ),
            (
                # ok, have same vars or env vars
                {
                    "path": "/echo/{cmd}/",
                    "backend_path": "/echo/{cmd}/{env.k1}/",
                },
                200,
            ),
            (
                # fail, proxy-path vars not exist in path
                {
                    "path": "/echo/",
                    "backend_path": "/echo/{cmd}/",
                },
                400,
            ),
            (
                # fail, proxy-path vars not exist in path
                {
                    "path": "/echo/{cmd}/",
                    "backend_path": "/echo/{cmd2}/",
                },
                400,
            ),
            (
                # fail, proxy-path env vars not exist in stage vars
                {
                    "path": "/echo/{cmd}/",
                    "backend_path": "/echo/{cmd}/{env.k2}/",
                },
                400,
            ),
        ],
    )
    def test_get(self, request_view, fake_gateway, fake_stage, fake_backend, data, expected):
        fake_stage.vars = {"k1": "v1"}
        fake_stage.save()

        data["backend_id"] = fake_backend.id

        resp = request_view(
            method="GET",
            view_name="resource.backend_path.check",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )

        assert resp.status_code == expected

    def test_get__data(self, request_view, fake_gateway):
        stage = G(Stage, gateway=fake_gateway, name="prod", _vars='{"k1": "v1"}')
        backend = G(Backend, gateway=fake_gateway, name="default")
        G(
            BackendConfig,
            gateway=fake_gateway,
            stage=stage,
            backend=backend,
            config={"type": "node", "hosts": [{"host": "api.demo.com", "scheme": "http"}]},
        )

        data = {
            "backend_id": backend.id,
            "path": "/echo/{cmd}/",
            "backend_path": "/echo/{cmd}/{env.k1}/",
        }

        resp = request_view(
            method="GET",
            view_name="resource.backend_path.check",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"] == [
            {
                "stage": {"id": stage.id, "name": stage.name},
                "backend_urls": ["http://api.demo.com/echo/{cmd}/v1/"],
            }
        ]

    def test_get_backend_hosts(self, fake_gateway, fake_request):
        stage = G(Stage, gateway=fake_gateway, _vars='{"k1": "v1"}')
        backend = G(Backend, gateway=fake_gateway, name="default")
        backend_config = G(
            BackendConfig,
            gateway=fake_gateway,
            stage=stage,
            backend=backend,
            config={"type": "node", "hosts": [{"host": "api.demo.com", "scheme": "http"}]},
        )

        view = BackendPathCheckApi()
        fake_request.gateway = fake_gateway
        view.request = fake_request

        result = view._get_backend_hosts(None)
        assert result == {}

        result = view._get_backend_hosts(backend.id)
        assert result == {stage.id: ["http://api.demo.com"]}

        backend_config.config = {"type": "node", "hosts": [{"host": "", "scheme": "http"}]}
        backend_config.save()

        with pytest.raises(BackendHostIsEmpty):
            view._get_backend_hosts(backend.id)

    @pytest.mark.parametrize(
        "host, path, vars, expected",
        [
            ("http://api.demo.com", "/color/", {}, "http://api.demo.com/color/"),
            ("http://api.demo.com", "/color/{color}", {}, "http://api.demo.com/color/{color}"),
            ("http://api.demo.com", "/color/{env.color}", {}, "http://api.demo.com/color/{env.color}"),
            ("http://api.demo.com", "/color/{env.color}", {"color": "green"}, "http://api.demo.com/color/green"),
        ],
    )
    def test_get_backend_url(self, host, path, vars, expected):
        view = BackendPathCheckApi()

        result = view._get_backend_url(host, path, vars)
        assert result == expected


class TestResourcesWithVerifiedUserRequiredApi:
    def test_list(self, request_view, fake_gateway):
        resource_1 = G(Resource, gateway=fake_gateway)
        resource_2 = G(Resource, gateway=fake_gateway)

        auth_config = ResourceHandler.get_default_auth_config()
        ResourceAuthContext().save(resource_1.id, dict(auth_config, auth_verified_required=True))
        ResourceAuthContext().save(resource_2.id, dict(auth_config, auth_verified_required=False))

        resp = request_view(
            method="GET",
            view_name="resource.list_with_verified_user_required",
            path_params={"gateway_id": fake_gateway.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1
