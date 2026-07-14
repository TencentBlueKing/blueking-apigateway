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
from unittest import mock

import pytest
from ddf import G

from apigateway.apis.open.stage import views
from apigateway.biz.plugin import PluginBindingHandler
from apigateway.core.backend_config import decrypt_ai_backend_config
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum, StageStatusEnum
from apigateway.core.models import Backend, BackendConfig, Gateway, Stage
from apigateway.tests.utils.testing import get_response_json
from apigateway.utils.yaml import yaml_dumps

pytestmark = pytest.mark.django_db


def _model_backend():
    return {
        "name": "openai-primary",
        "config": {
            "timeout": 30000,
            "instances": [
                {
                    "name": "primary",
                    "provider": "openai",
                    "weight": 1,
                    "auth": {"header": {"Authorization": "Bearer secret"}},
                    "options": {"model": "gpt-4o", "temperature": 0.7},
                }
            ],
        },
    }


class TestStageListViewSet:
    def test_list_by_gateway_name(self, request_to_view, request_factory, fake_gateway):
        request = request_factory.get("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        stage = G(Stage, name="prod", gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)

        response = request_to_view(
            request, view_name="openapi.stage.list_by_gateway_name", path_params={"gateway_name": fake_gateway.name}
        )

        result = get_response_json(response)

        assert response.status_code == 200
        assert result["code"] == 0
        assert result["data"] == [
            {
                "id": stage.id,
                "name": stage.name,
                "description": stage.description,
            },
        ]


class TestStageV1ViewSet:
    def list_stages_with_resource_version(self, request_to_view, request_factory, fake_release):
        request = request_factory.get("")
        request.gateway = fake_release.gateway

        G(Stage, name="test", gateway=request.gateway, status=StageStatusEnum.ACTIVE.value)

        response = request_to_view(
            request,
            view_name="openapi.stage.list_stages_with_resource_version",
            path_params={"gateway_name": request.gateway.name},
        )

        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == [
            {
                "name": fake_release.stage.name,
                "released": True,
                "resource_version": {
                    "version": fake_release.resource_version.version,
                },
            },
            {
                "name": "test",
                "released": False,
                "resource_version": None,
            },
        ]


class TestStageSyncViewSet:
    def test_sync_ai_gateway_with_model_backends(self, mocker, unique_gateway_name, request_factory):
        mocker.patch(
            "apigateway.apis.open.stage.views.OpenAPIGatewayRelatedAppPermission.has_permission",
            return_value=True,
        )
        gateway = G(Gateway, name=unique_gateway_name, is_public=False, kind=GatewayKindEnum.AI.value)
        request = request_factory.post(
            f"/api/v1/apis/{unique_gateway_name}/stages/sync/",
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "modelBackends": [_model_backend()],
            },
        )
        request.gateway = gateway

        response = views.StageSyncViewSet.as_view({"post": "sync"})(request, gateway_name=unique_gateway_name)

        result = get_response_json(response)
        assert response.status_code == 200, result
        backend = Backend.objects.get(gateway=gateway, name="openai-primary")
        assert backend.kind == BackendKindEnum.AI.value
        backend_config = BackendConfig.objects.get(backend=backend, stage__name="prod")
        decrypted_config = decrypt_ai_backend_config(backend_config.config)
        assert decrypted_config["instances"][0]["auth"]["header"]["Authorization"] == "Bearer secret"
        assert decrypted_config["instances"][0]["options"] == {"model": "gpt-4o", "temperature": 0.7}

    def test_sync(self, mocker, unique_gateway_name, request_factory):
        mocker.patch(
            "apigateway.apis.open.stage.views.OpenAPIGatewayRelatedAppPermission.has_permission",
            return_value=True,
        )

        mocker.patch(
            "apigateway.service.plugin.HeaderRewriteConvertor.sync_plugins",
            return_value=True,
        )

        gateway = G(Gateway, name=unique_gateway_name, is_public=False)

        request = request_factory.post(
            f"/api/v1/apis/{unique_gateway_name}/stages/sync/",
            data={
                "name": "prod",
                "description": "desc",
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
                    "transform_headers": {
                        "set": {"k1": "v1"},
                    },
                },
            },
        )
        request.gateway = gateway

        view = views.StageSyncViewSet.as_view({"post": "sync"})
        response = view(request, gateway_name=unique_gateway_name)

        result = get_response_json(response)
        stage = Stage.objects.get(gateway=gateway, name="prod")
        assert result["code"] == 0
        assert stage.status == 0

    def test_sync_with_empty_backends_returns_error(self, mocker, unique_gateway_name, request_factory):
        mocker.patch(
            "apigateway.apis.open.stage.views.OpenAPIGatewayRelatedAppPermission.has_permission",
            return_value=True,
        )

        gateway = G(Gateway, name=unique_gateway_name, is_public=False)
        request = request_factory.post(
            f"/api/v1/apis/{unique_gateway_name}/stages/sync/",
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "backends": [],
            },
        )
        request.gateway = gateway

        view = views.StageSyncViewSet.as_view({"post": "sync"})
        response = view(request, gateway_name=unique_gateway_name)
        result = get_response_json(response)

        assert response.status_code == 400
        assert "backends" in str(result)

    def test_sync_backends(self, fake_plugin_type_bk_header_rewrite, mocker, unique_gateway_name, request_factory):
        mocker.patch(
            "apigateway.apis.open.stage.views.OpenAPIGatewayRelatedAppPermission.has_permission",
            return_value=True,
        )

        mocker.patch(
            "apigateway.service.plugin.HeaderRewriteConvertor.sync_plugins",
            return_value=True,
        )

        gateway = G(Gateway, name=unique_gateway_name, is_public=False)
        omitted_backend = G(Backend, gateway=gateway, name="service2")

        request = request_factory.post(
            f"/api/v1/apis/{unique_gateway_name}/stages/sync/",
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "backends": [
                    {
                        "name": "default",
                        "config": {
                            "timeout": 60,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                }
                            ],
                        },
                    },
                    {
                        "name": "service1",
                        "config": {
                            "timeout": 60,
                            "loadbalance": "roundrobin",
                            "hosts": [
                                {
                                    "host": "http://www.a.com",
                                }
                            ],
                        },
                    },
                ],
                "plugin_configs": [
                    {
                        "type": "bk-header-rewrite",
                        "yaml": yaml_dumps(
                            {
                                "set": [{"key": "foo", "value": "bar"}],
                                "remove": [],
                            }
                        ),
                    }
                ],
            },
        )
        request.gateway = gateway

        view = views.StageSyncViewSet.as_view({"post": "sync"})
        response = view(request, gateway_name=unique_gateway_name)

        result = get_response_json(response)
        stage = Stage.objects.get(gateway=gateway, name="prod")

        assert result["code"] == 0
        assert stage.status == 0
        assert len(Backend.objects.filter(gateway=gateway, name__in=["default", "service1"])) == 2
        assert len(BackendConfig.objects.filter(backend__name__in=["default", "service1"])) == 2
        assert not BackendConfig.objects.filter(backend=omitted_backend, stage=stage).exists()
        assert BackendConfig.objects.get(backend__name="default").config == {
            "type": "node",
            "timeout": 60,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.a.com", "weight": 100}],
        }
        assert len(PluginBindingHandler.get_stage_plugin_bindings(gateway.id, stage.id)) == 1
