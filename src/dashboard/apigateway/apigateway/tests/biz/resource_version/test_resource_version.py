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

import pytest
from django_dynamic_fixture import G

from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion, OpenAPIResourceSchemaVersion
from apigateway.apps.support.models import GatewaySDK, ReleasedResourceDoc, ResourceDocVersion
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage
from apigateway.utils.time import now_datetime


class TestResourceVersionHandler:
    def test_make_version(self, fake_gateway, fake_resource):
        ResourceHandler.save_auth_config(
            fake_resource.id,
            {
                "skip_auth_verification": False,
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
        )

        data = ResourceVersionHandler.make_version(fake_gateway)
        assert data[0]["id"] == fake_resource.id
        assert data[0]["method"] == fake_resource.method
        assert data[0]["path"] == fake_resource.path
        assert data[0]["proxy"]["type"] == "http"
        assert data[0]["proxy"]["config"]
        assert data[0]["contexts"]["resource_auth"]["config"] == json.dumps(
            {
                "skip_auth_verification": False,
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
            separators=(",", ":"),
        )

    def test_create_resource_version(self, fake_resource):
        gateway = fake_resource.gateway

        ResourceVersionHandler.create_resource_version(gateway, {"comment": "test", "version": "1.1.0"}, "admin")
        assert ResourceVersion.objects.filter(gateway=gateway).count() == 1

    @pytest.mark.parametrize(
        "gateway_id, stage_name, mocked_released_resource_version_ids, mocked_resources, expected",
        [
            (
                1,
                None,
                [1, 2],
                {
                    1: {"id": 1, "is_public": True, "disabled_stages": []},
                    2: {"id": 2, "is_public": False, "disabled_stages": []},
                },
                [{"id": 1, "is_public": True, "disabled_stages": []}],
            ),
            (
                1,
                "prod",
                [1],
                {
                    1: {"id": 1, "is_public": False, "disabled_stages": []},
                    2: {"id": 2, "is_public": False, "disabled_stages": []},
                },
                [],
            ),
            (
                1,
                None,
                [1],
                {
                    1: {"id": 1, "is_public": True, "disabled_stages": ["prod"]},
                },
                [{"id": 1, "is_public": True, "disabled_stages": ["prod"]}],
            ),
            (
                1,
                "prod",
                [1],
                {
                    1: {"id": 1, "is_public": True, "disabled_stages": ["prod"]},
                },
                [],
            ),
            (
                1,
                None,
                [1],
                {
                    1: {"id": 1, "is_public": True, "disabled_stages": ["test"]},
                },
                [],
            ),
        ],
    )
    def test_get_released_public_resources(
        self,
        mocker,
        gateway_id,
        stage_name,
        mocked_released_resource_version_ids,
        mocked_resources,
        expected,
    ):
        get_released_resource_version_ids_mock = mocker.patch(
            "apigateway.core.models.Release.objects.get_released_resource_version_ids",
            return_value=mocked_released_resource_version_ids,
        )
        get_resources_mock = mocker.patch.object(
            ResourceVersion.objects,
            "get_resources",
            return_value=mocked_resources,
        )
        mocker.patch.object(
            Stage.objects,
            "get_names",
            return_value=["test"],
        )

        result = ResourceVersionHandler.get_released_public_resources(gateway_id, stage_name)
        assert expected == result

        get_released_resource_version_ids_mock.assert_called_once_with(gateway_id, stage_name)
        get_resources_mock.assert_called()

    def test_get_latest_created_time(self, fake_gateway):
        result = ResourceVersionHandler.get_latest_created_time(fake_gateway.id)
        assert result is None

        G(ResourceVersion, gateway=fake_gateway, created_time=now_datetime())
        result = ResourceVersionHandler.get_latest_created_time(fake_gateway.id)
        assert isinstance(result, datetime.datetime)

    def test_get_latest_version_by_gateway(self, fake_gateway):
        resource_version_1 = G(ResourceVersion, gateway=fake_gateway, version="1.0.1", created_time=now_datetime())
        resource_version_2 = G(ResourceVersion, gateway=fake_gateway, version="1.1.1", created_time=now_datetime())
        resource_version_3 = G(ResourceVersion, gateway=fake_gateway, version="2.0.0", created_time=now_datetime())
        result = ResourceVersionHandler.get_latest_version_by_gateway(fake_gateway.id)
        assert result == resource_version_3.version

    def test_get_used_stage_vars(self):
        gateway = G(Gateway)

        data = [
            # resource version not exist
            {
                "resource_version": None,
                "expected": None,
            },
            # proxy type is mock
            {
                "resource_version": G(
                    ResourceVersion,
                    gateway=gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "mock",
                                }
                            }
                        ]
                    ),
                ),
                "expected": {
                    "in_path": [],
                    "in_host": [],
                },
            },
            # vars in path/host
            {
                "resource_version": G(
                    ResourceVersion,
                    gateway=gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "http",
                                    "config": json.dumps(
                                        {
                                            "path": "/hello/{env.region}/",
                                            "upstreams": {
                                                "hosts": [
                                                    {"host": "https://{env.domain}"},
                                                ]
                                            },
                                        }
                                    ),
                                }
                            }
                        ]
                    ),
                ),
                "expected": {
                    "in_path": ["region"],
                    "in_host": ["domain"],
                },
            },
            # vars in path/host
            {
                "resource_version": G(
                    ResourceVersion,
                    gateway=gateway,
                    _data=json.dumps(
                        [
                            {
                                "proxy": {
                                    "type": "http",
                                    "config": json.dumps(
                                        {
                                            "path": "/hello/{env.region}/",
                                            "upstreams": {},
                                        }
                                    ),
                                }
                            }
                        ]
                    ),
                ),
                "expected": {
                    "in_path": ["region"],
                    "in_host": [],
                },
            },
        ]
        for test in data:
            result = ResourceVersionHandler.get_used_stage_vars(
                gateway_id=gateway.id,
                id=test["resource_version"].id if test["resource_version"] else 0,
            )
            assert result == test["expected"]

    def test_get_resource_schema(self, fake_resource, fake_resource_version, fake_resource_schema_with_body):
        openapi_schema_version = G(
            OpenAPIResourceSchemaVersion,
            resource_version=fake_resource_version,
            schema=[
                {
                    "resource_id": fake_resource.id,
                    "schema": fake_resource_schema_with_body.schema,
                }
            ],
        )
        resource_schema = ResourceVersionHandler.get_resource_schema(fake_resource_version.id, fake_resource.id)
        assert resource_schema["requestBody"] == fake_resource_schema_with_body.schema["requestBody"]

    def test_is_resource_version_referenced_by_release(self, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        assert ResourceVersionHandler.is_resource_version_referenced(rv.id) is False

        stage = G(Stage, gateway=fake_gateway, status=1)
        G(Release, gateway=fake_gateway, stage=stage, resource_version=rv)
        assert ResourceVersionHandler.is_resource_version_referenced(rv.id) is True

    def test_is_resource_version_referenced_by_sdk(self, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="2.0.0")
        assert ResourceVersionHandler.is_resource_version_referenced(rv.id) is False

        G(GatewaySDK, gateway=fake_gateway, resource_version=rv)
        assert ResourceVersionHandler.is_resource_version_referenced(rv.id) is True

    def test_is_resource_version_referenced_not_referenced(self, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="3.0.0")
        assert ResourceVersionHandler.is_resource_version_referenced(rv.id) is False

    def test_delete_resource_version(self, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        rv_id = rv.id

        G(ReleasedResourceDoc, gateway=fake_gateway, resource_version_id=rv_id, resource_id=1, language="zh")
        G(
            ReleasedResource,
            gateway=fake_gateway,
            resource_version_id=rv_id,
            resource_id=1,
            resource_name="test",
            resource_method="GET",
            resource_path="/test",
        )
        G(ResourceDocVersion, gateway=fake_gateway, resource_version=rv)
        G(OpenAPIResourceSchemaVersion, resource_version=rv, schema=[])
        G(OpenAPIFileResourceSchemaVersion, gateway=fake_gateway, resource_version=rv, schema="")

        assert ResourceVersion.objects.filter(id=rv_id).exists()
        assert ReleasedResourceDoc.objects.filter(resource_version_id=rv_id).exists()
        assert ReleasedResource.objects.filter(resource_version_id=rv_id).exists()
        assert ResourceDocVersion.objects.filter(resource_version_id=rv_id).exists()
        assert OpenAPIResourceSchemaVersion.objects.filter(resource_version_id=rv_id).exists()
        assert OpenAPIFileResourceSchemaVersion.objects.filter(resource_version_id=rv_id).exists()

        ResourceVersionHandler.delete_resource_version(rv_id)

        assert not ResourceVersion.objects.filter(id=rv_id).exists()
        assert not ReleasedResourceDoc.objects.filter(resource_version_id=rv_id).exists()
        assert not ReleasedResource.objects.filter(resource_version_id=rv_id).exists()
        assert not ResourceDocVersion.objects.filter(resource_version_id=rv_id).exists()
        assert not OpenAPIResourceSchemaVersion.objects.filter(resource_version_id=rv_id).exists()
        assert not OpenAPIFileResourceSchemaVersion.objects.filter(resource_version_id=rv_id).exists()
