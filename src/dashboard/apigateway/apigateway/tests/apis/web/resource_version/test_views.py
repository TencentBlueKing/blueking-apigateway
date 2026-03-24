# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import datetime
import json
import operator

from django_dynamic_fixture import G

from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion, OpenAPIResourceSchemaVersion
from apigateway.apps.support.models import GatewaySDK, ReleasedResourceDoc, ResourceDoc, ResourceDocVersion
from apigateway.core.models import Proxy, Release, ReleasedResource, Resource, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_gateway, dummy_time


class TestResourceVersionListCreateApi:
    def test_create(self, request_view, fake_gateway, fake_resource1):
        data = {"comment": "test", "version": "1.1.0"}

        resp = request_view(
            method="POST",
            view_name="gateway.resource_version.list_create",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        assert resp.status_code == 201
        assert ResourceVersion.objects.filter(gateway=fake_gateway).count() > 0

    def test_list(self, request_view, fake_gateway):
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1.0.1",
            created_time=dummy_time.time,
        )
        stage_prod = G(Stage, gateway=fake_gateway, status=1)
        stage_test = G(Stage, gateway=fake_gateway, status=1)
        G(Release, gateway=fake_gateway, stage=stage_prod, resource_version=resource_version)
        G(Release, gateway=fake_gateway, stage=stage_test, resource_version=resource_version)
        G(GatewaySDK, gateway=fake_gateway, resource_version=resource_version)

        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.list_create",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
        )

        result = resp.json()
        assert resp.status_code == 200

        results = result["data"]["results"]

        released_stages = results[0].pop("released_stages")

        assert results == [
            {
                "id": resource_version.id,
                "version": resource_version.version,
                "schema_version": resource_version.schema_version,
                "comment": resource_version.comment,
                "sdk_count": 1,
                "created_time": dummy_time.str,
                "created_by": resource_version.created_by,
                "deletable": False,
            },
        ]
        expected_release_stages = [
            {
                "id": stage_prod.id,
                "name": stage_prod.name,
            },
            {
                "id": stage_test.id,
                "name": stage_test.name,
            },
        ]
        released_stages.sort(key=operator.itemgetter("name"))
        expected_release_stages.sort(key=operator.itemgetter("name"))
        assert released_stages == expected_release_stages

    def test_list_deletable_true(self, request_view, fake_gateway):
        """When no release and no SDK, deletable should be True."""
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="2.0.0",
            created_time=dummy_time.time,
        )

        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.list_create",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
        )

        result = resp.json()
        assert resp.status_code == 200

        results = result["data"]["results"]
        assert results[0]["deletable"] is True
        assert results[0]["sdk_count"] == 0
        assert results[0]["released_stages"] == []


class TestResourceVersionRetrieveDestroyApi:
    def test_retrieve(
        self, request_view, fake_backend, fake_stage, fake_gateway, fake_resource_version_v2, echo_plugin_stage_binding
    ):
        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.retrieve_destroy",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id, "id": fake_resource_version_v2.id},
        )

        assert resp.status_code == 200

        result = resp.json()
        assert result["data"] == {
            "id": fake_resource_version_v2.id,
            "version": fake_resource_version_v2.version,
            "comment": fake_resource_version_v2.comment,
            "schema_version": fake_resource_version_v2.schema_version,
            "resources": [
                {
                    "id": fake_resource_version_v2.data[0]["id"],
                    "name": fake_resource_version_v2.data[0]["name"],
                    "method": fake_resource_version_v2.data[0]["method"],
                    "path": fake_resource_version_v2.data[0]["path"],
                    "description": fake_resource_version_v2.data[0]["description"],
                    "description_en": fake_resource_version_v2.data[0]["description_en"],
                    "gateway_label_ids": fake_resource_version_v2.data[0]["api_labels"],
                    "match_subpath": fake_resource_version_v2.data[0]["match_subpath"],
                    "is_public": fake_resource_version_v2.data[0]["is_public"],
                    "allow_apply_permission": fake_resource_version_v2.data[0]["allow_apply_permission"],
                    "doc_updated_time": "",
                    "enable_websocket": False,
                    "proxy": {
                        "config": fake_resource_version_v2.data[0]["proxy"]["config"],
                        "backend": {
                            "id": fake_backend.id,
                            "name": fake_backend.name,
                        },
                    },
                    "contexts": fake_resource_version_v2.data[0]["contexts"],
                    "plugins": [],
                    "has_openapi_schema": False,
                    "openapi_schema": {},
                }
            ],
            "created_time": fake_resource_version_v2.created_time,
            "created_by": fake_resource_version_v2.created_by,
        }

    def test_destroy(self, request_view, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        rv_id = rv.id

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.retrieve_destroy",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id, "id": rv_id},
        )
        assert resp.status_code == 204
        assert not ResourceVersion.objects.filter(id=rv_id).exists()

    def test_destroy_referenced_by_release(self, request_view, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        stage = G(Stage, gateway=fake_gateway, status=1)
        G(Release, gateway=fake_gateway, stage=stage, resource_version=rv)

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.retrieve_destroy",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id, "id": rv.id},
        )
        assert resp.status_code == 400
        assert ResourceVersion.objects.filter(id=rv.id).exists()

    def test_destroy_referenced_by_sdk(self, request_view, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        G(GatewaySDK, gateway=fake_gateway, resource_version=rv)

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.retrieve_destroy",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id, "id": rv.id},
        )
        assert resp.status_code == 400
        assert ResourceVersion.objects.filter(id=rv.id).exists()

    def test_destroy_cleans_related_records(self, request_view, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        rv_id = rv.id
        G(ReleasedResourceDoc, gateway=fake_gateway, resource_version_id=rv_id, resource_id=1, language="zh")
        G(
            ReleasedResource,
            gateway=fake_gateway,
            resource_version_id=rv_id,
            resource_id=1,
            resource_name="r",
            resource_method="GET",
            resource_path="/r",
        )
        G(ResourceDocVersion, gateway=fake_gateway, resource_version=rv)
        G(OpenAPIResourceSchemaVersion, resource_version=rv, schema=[])
        G(OpenAPIFileResourceSchemaVersion, gateway=fake_gateway, resource_version=rv, schema="")

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.retrieve_destroy",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id, "id": rv_id},
        )
        assert resp.status_code == 204
        assert not ResourceVersion.objects.filter(id=rv_id).exists()
        assert not ReleasedResourceDoc.objects.filter(resource_version_id=rv_id).exists()
        assert not ReleasedResource.objects.filter(resource_version_id=rv_id).exists()
        assert not ResourceDocVersion.objects.filter(resource_version_id=rv_id).exists()
        assert not OpenAPIResourceSchemaVersion.objects.filter(resource_version_id=rv_id).exists()
        assert not OpenAPIFileResourceSchemaVersion.objects.filter(resource_version_id=rv_id).exists()


class TestResourceVersionNeedNewVersionRetrieveApi:
    def test_get(self, request_view):
        gateway_1 = create_gateway()

        gateway_2 = create_gateway()
        G(Resource, gateway=gateway_2)

        gateway_3 = create_gateway()
        G(Resource, gateway=gateway_3, updated_time=dummy_time.time + datetime.timedelta(seconds=10))
        G(ResourceVersion, gateway=gateway_3, created_time=dummy_time.time)

        gateway_4 = create_gateway()
        G(Resource, gateway=gateway_4, updated_time=dummy_time.time)
        G(
            ResourceVersion,
            gateway=gateway_4,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )

        gateway_5 = create_gateway()
        G(Resource, gateway=gateway_5, updated_time=dummy_time.time)
        G(
            ResourceVersion,
            gateway=gateway_5,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )
        G(ResourceDoc, gateway=gateway_5, updated_time=dummy_time.time + datetime.timedelta(seconds=20))
        G(
            ResourceDocVersion,
            gateway=gateway_5,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )

        data = [
            {
                "gateway": gateway_1,
                "will_error": True,
            },
            {
                "gateway": gateway_2,
                "expected": {
                    "need_new_version": True,
                },
            },
            {
                "gateway": gateway_3,
                "expected": {
                    "need_new_version": True,
                },
            },
            {
                "gateway": gateway_4,
                "expected": {
                    "need_new_version": False,
                },
            },
            # resource doc has updated
            {
                "gateway": gateway_5,
                "expected": {
                    "need_new_version": True,
                },
            },
        ]

        for test in data:
            gateway = test["gateway"]

            resp = request_view(
                method="GET",
                view_name="gateway.resource_version.need_new_version",
                path_params={"gateway_id": gateway.id},
            )

            result = resp.json()
            if test.get("will_error"):
                assert result["error"] is not None
                continue

            assert resp.status_code == 200
            assert result["data"]["need_new_version"] == test["expected"]["need_new_version"]


class TestResourceVersionDiffApi:
    def test_resource_version_diff_without_resource_version(
        self,
        request_view,
        fake_backend,
        fake_stage,
        fake_gateway,
        fake_resource,
        echo_plugin_stage_binding,
    ):
        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.diff",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
            },
            data={"source_resource_version_id": "", "target_resource_version_id": ""},
        )
        assert resp.status_code == 200
        result = resp.json()

        proxy = Proxy.objects.get(resource_id=fake_resource.id)
        assert result == {
            "data": {
                "add": [
                    {
                        "id": fake_resource.id,
                        "name": fake_resource.name,
                        "description": fake_resource.description,
                        "method": fake_resource.method,
                        "path": fake_resource.path,
                        "match_subpath": fake_resource.match_subpath,
                        "enable_websocket": fake_resource.enable_websocket,
                        "is_public": fake_resource.is_public,
                        "allow_apply_permission": fake_resource.allow_apply_permission,
                        "proxy": {
                            "type": "http",
                            "backend_id": fake_backend.id,
                            "config": {
                                "method": proxy.config.get("method"),
                                "path": proxy.config.get("path"),
                                "match_subpath": proxy.config.get("match_subpath"),
                                "timeout": proxy.config.get("timeout"),
                                "upstreams": {},
                                "transform_headers": {},
                            },
                        },
                        "api_labels": [],
                        "contexts": {
                            "resource_auth": {
                                "config": {
                                    "auth_verified_required": True,
                                    "app_verified_required": True,
                                    "resource_perm_required": True,
                                }
                            }
                        },
                        "disabled_stages": [],
                        "plugins": [],
                        "doc_updated_time": {},
                        "openapi_schema": {},
                    }
                ],
                "delete": [],
                "update": [],
            }
        }

    def test_resource_version_diff_with_resource_version(
        self,
        request_view,
        fake_backend,
        fake_stage,
        fake_gateway,
        fake_resource_version_v2,
        echo_plugin_stage_binding,
    ):
        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.diff",
            gateway=fake_gateway,
            path_params={
                "gateway_id": fake_gateway.id,
            },
            data={"source_resource_version_id": fake_resource_version_v2.id, "target_resource_version_id": ""},
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result == {
            "data": {
                "add": [],
                "delete": [],
                "update": [],
            }
        }


class TestResourceVersionGetApi:
    def test_resource_version_get(self, request_view):
        gateway_1 = create_gateway()
        G(ResourceVersion, gateway=gateway_1, version="1.0.1", created_time=dummy_time.time)
        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.next_version",
            gateway=gateway_1,
            path_params={"gateway_id": gateway_1.id},
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result == {"data": {"version": "1.0.2"}}

        gateway_2 = create_gateway()
        G(ResourceVersion, gateway=gateway_2, version="1.0.0-alpha+001", created_time=dummy_time.time)
        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.next_version",
            gateway=gateway_2,
            path_params={"gateway_id": gateway_2.id},
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result == {"data": {"version": "1.0.1"}}

        gateway_3 = create_gateway()
        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.next_version",
            gateway=gateway_3,
            path_params={"gateway_id": gateway_3.id},
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result == {"data": {"version": "1.0.0"}}


class TestResourceVersionBatchDeleteApi:
    def test_batch_delete(self, request_view, fake_gateway):
        rv1 = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        rv2 = G(ResourceVersion, gateway=fake_gateway, version="2.0.0")

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.batch_delete",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"ids": [rv1.id, rv2.id]},
        )
        assert resp.status_code == 204
        assert not ResourceVersion.objects.filter(id=rv1.id).exists()
        assert not ResourceVersion.objects.filter(id=rv2.id).exists()

    def test_batch_delete_empty_ids(self, request_view, fake_gateway):
        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.batch_delete",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"ids": []},
        )
        assert resp.status_code == 400

    def test_batch_delete_duplicate_ids(self, request_view, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.batch_delete",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"ids": [rv.id, rv.id]},
        )
        assert resp.status_code == 204
        assert not ResourceVersion.objects.filter(id=rv.id).exists()

    def test_batch_delete_not_exist(self, request_view, fake_gateway):
        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.batch_delete",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"ids": [99999]},
        )
        assert resp.status_code == 400

    def test_batch_delete_some_referenced(self, request_view, fake_gateway):
        rv1 = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        rv2 = G(ResourceVersion, gateway=fake_gateway, version="2.0.0")
        stage = G(Stage, gateway=fake_gateway, status=1)
        G(Release, gateway=fake_gateway, stage=stage, resource_version=rv2)

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.batch_delete",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"ids": [rv1.id, rv2.id]},
        )
        assert resp.status_code == 400
        # neither should be deleted since the operation is atomic
        assert ResourceVersion.objects.filter(id=rv1.id).exists()
        assert ResourceVersion.objects.filter(id=rv2.id).exists()

    def test_batch_delete_all_referenced(self, request_view, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        G(GatewaySDK, gateway=fake_gateway, resource_version=rv)

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.batch_delete",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"ids": [rv.id]},
        )
        assert resp.status_code == 400
        assert ResourceVersion.objects.filter(id=rv.id).exists()

    def test_batch_delete_cleans_related_records(self, request_view, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        rv_id = rv.id
        G(ReleasedResourceDoc, gateway=fake_gateway, resource_version_id=rv_id, resource_id=1, language="zh")
        G(
            ReleasedResource,
            gateway=fake_gateway,
            resource_version_id=rv_id,
            resource_id=1,
            resource_name="r",
            resource_method="GET",
            resource_path="/r",
        )

        resp = request_view(
            method="DELETE",
            view_name="gateway.resource_version.batch_delete",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"ids": [rv_id]},
        )
        assert resp.status_code == 204
        assert not ResourceVersion.objects.filter(id=rv_id).exists()
        assert not ReleasedResourceDoc.objects.filter(resource_version_id=rv_id).exists()
        assert not ReleasedResource.objects.filter(resource_version_id=rv_id).exists()
