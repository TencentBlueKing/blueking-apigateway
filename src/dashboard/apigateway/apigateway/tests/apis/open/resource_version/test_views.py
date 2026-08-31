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

from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum, ResourceKindEnum
from apigateway.core.models import Proxy, ResourceVersion, Stage
from apigateway.tests.utils.testing import get_response_json
from apigateway.utils.yaml import yaml_loads

pytestmark = pytest.mark.django_db


class TestResourceVersionListCreateApi:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mocker):
        mocker.patch(
            "apigateway.apis.open.resource_version.views.OpenAPIGatewayRelatedAppPermission.has_permission",
            return_value=True,
        )

    def test_list(self, request_view, fake_resource_version):
        fake_gateway = fake_resource_version.gateway
        response = request_view(
            "GET",
            "openapi.resource_versions.list_create",
            gateway=fake_gateway,
            path_params={
                "gateway_name": fake_gateway.name,
            },
            data={
                "version": fake_resource_version.version,
            },
        )
        result = response.json()

        assert result["data"]["count"] == 1

        response = request_view(
            "GET",
            "openapi.resource_versions.list_create",
            gateway=fake_gateway,
            path_params={
                "gateway_name": fake_gateway.name,
            },
            data={
                "version": fake_resource_version.version + "-not-exists",
            },
        )
        result = response.json()
        assert result["data"]["count"] == 0

    def test_create(self, request_view, fake_gateway, fake_resource, fake_resource_version, mocker):
        resp = request_view(
            method="POST",
            view_name="openapi.resource_versions.list_create",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "version": "1.1.0",
            },
            gateway=fake_gateway,
        )
        result = resp.json()
        assert result["code"] == 0

    def test_create_ai_resource_version(self, request_view, fake_gateway, fake_backend, fake_resource):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        fake_backend.kind = BackendKindEnum.AI.value
        fake_backend.save()
        fake_resource.kind = ResourceKindEnum.AI.value
        fake_resource.method = "POST"
        fake_resource.match_subpath = False
        fake_resource.enable_websocket = False
        fake_resource.save()
        proxy = Proxy.objects.get(resource=fake_resource)
        Proxy.objects.filter(id=proxy.id).update(_config="{}")

        response = request_view(
            method="POST",
            view_name="openapi.resource_versions.list_create",
            path_params={"gateway_name": fake_gateway.name},
            data={"version": "1.2.0"},
            gateway=fake_gateway,
        )

        assert response.status_code == 200
        resource_version = ResourceVersion.objects.get(gateway=fake_gateway, version="1.2.0")
        resource = resource_version.data[0]
        assert resource["kind"] == ResourceKindEnum.AI.value
        assert resource["proxy"]["backend_id"] == fake_backend.id
        assert json.loads(resource["proxy"]["config"]) == {}
        artifact = OpenAPIFileResourceSchemaVersion.objects.get(resource_version=resource_version)
        operation = yaml_loads(artifact.schema)["paths"][fake_resource.path]["post"]
        assert operation["x-bk-apigateway-resource"]["kind"] == ResourceKindEnum.AI.value


class TestResourceVersionReleaseApi:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mocker):
        mocker.patch(
            "apigateway.apis.open.resource_version.views.OpenAPIGatewayRelatedAppPermission.has_permission",
            return_value=True,
        )

    def test_release(self, faker, request_view, fake_admin_user, fake_gateway, mocker):
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        stage_1 = G(Stage, gateway=fake_gateway)
        stage_2 = G(Stage, gateway=fake_gateway)
        release_to_stages = mocker.patch(
            "apigateway.apis.open.resource_version.views.ReleaseHandler.release_to_stages"
        )
        release_to_stages.return_value = (True, "")
        mocker.patch(
            "apigateway.apis.open.resource_version.serializers.ReleaseV1InputSLZ.to_internal_value",
            return_value={
                "gateway": fake_gateway,
                "stage_ids": [stage_2.id, stage_1.id],
                "resource_version_id": resource_version.id,
                "comment": "",
            },
        )
        mocker.patch(
            "apigateway.apis.open.resource_version.views.ResourceVersion.objects.get_object_fields",
            return_value={
                "id": faker.pyint(),
                "name": faker.pystr(),
                "title": faker.pystr(),
                "version": faker.pystr(),
            },
        )

        response = request_view(
            "POST",
            "openapi.resource_version.release",
            gateway=fake_gateway,
            path_params={
                "gateway_name": fake_gateway.name,
            },
            data={
                "stage_name": ["prod"],
                "resource_version_name": "test",
            },
            user=fake_admin_user,
        )

        result = get_response_json(response)
        assert result["code"] == 0
        release_to_stages.assert_called_once()
        assert release_to_stages.call_args.kwargs["stage_ids"] == [stage_2.id, stage_1.id]
