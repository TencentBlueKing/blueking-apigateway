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

from django_dynamic_fixture import G

from apigateway.biz.backend import BackendHandler
from apigateway.core.constants import BackendKindEnum
from apigateway.core.models import Backend, BackendConfig, Proxy, Release, Resource, Stage


class TestBackendHandler:
    def test_create(self, fake_stage):
        BackendHandler.create(
            {
                "gateway": fake_stage.gateway,
                "name": "backend-test",
                "description": "test",
                "type": "http",
                "configs": [
                    {
                        "stage_id": fake_stage.id,
                        "type": "node",
                        "timeout": 1,
                        "loadbalance": "roundrobin",
                        "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                    }
                ],
            },
            "admin",
        )

        backend = Backend.objects.filter(gateway=fake_stage.gateway, name="backend-test").first()
        assert backend

        backend_config = BackendConfig.objects.get(backend=backend)
        assert backend_config.stage_id == fake_stage.id
        assert backend_config.gateway_id == fake_stage.gateway.id
        assert backend_config.config == {
            "type": "node",
            "timeout": 1,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
        }

    def test_update(self, fake_stage):
        BackendHandler.create(
            {
                "gateway": fake_stage.gateway,
                "name": "backend-test",
                "description": "test",
                "type": "http",
                "configs": [
                    {
                        "stage_id": fake_stage.id,
                        "type": "node",
                        "timeout": 1,
                        "loadbalance": "roundrobin",
                        "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                    }
                ],
            },
            "admin",
        )

        backend = Backend.objects.filter(gateway=fake_stage.gateway, name="backend-test").first()

        r = G(Resource, name="backend-test", gateway=fake_stage.gateway, method="/test/", path="/test/")

        G(Proxy, resource=r, backend=backend)

        assert backend

        backend, updated_stage_ids = BackendHandler.update(
            backend,
            {
                "gateway": fake_stage.gateway,
                "name": "backend-update",
                "description": "update",
                "type": "http",
                "configs": [
                    {
                        "stage_id": fake_stage.id,
                        "type": "node",
                        "timeout": 10,
                        "loadbalance": "roundrobin",
                        "hosts": [{"scheme": "https", "host": "www.example.com", "weight": 1}],
                    }
                ],
            },
            "admin",
        )

        assert updated_stage_ids != []
        assert backend.name == "backend-update"
        assert backend.description == "update"

        backend_config = BackendConfig.objects.get(backend=backend)
        assert backend_config.config == {
            "type": "node",
            "timeout": 10,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "https", "host": "www.example.com", "weight": 1}],
        }

    def test_update_ai_backend_ignores_unchanged_config(self, mocker, fake_stage):
        backend = BackendHandler.create(
            {
                "gateway": fake_stage.gateway,
                "kind": BackendKindEnum.AI.value,
                "name": "openai-primary",
                "description": "test",
                "type": "http",
                "configs": [
                    {
                        "stage_id": fake_stage.id,
                        "timeout": 30000,
                        "instances": [
                            {
                                "name": "primary",
                                "provider": "openai",
                                "weight": 1,
                                "auth": {"header": {"Authorization": "Bearer secret"}},
                                "options": {"model": "gpt-4o"},
                            }
                        ],
                    }
                ],
            },
            "admin",
        )
        resource = G(Resource, gateway=fake_stage.gateway, method="POST", path="/chat")
        G(Proxy, resource=resource, backend=backend)
        backend_config = BackendConfig.objects.get(backend=backend, stage=fake_stage)
        previous_updated_time = backend_config.updated_time
        config = backend_config.config
        config["stage_id"] = fake_stage.id
        trigger_gateway_publish = mocker.patch("apigateway.biz.backend.backend.trigger_gateway_publish")

        _, updated_stage_ids = BackendHandler.update(
            backend,
            {
                "gateway": fake_stage.gateway,
                "name": backend.name,
                "description": backend.description,
                "type": backend.type,
                "configs": [config],
            },
            "admin",
        )

        backend_config.refresh_from_db()
        assert list(updated_stage_ids) == []
        assert backend_config.updated_time == previous_updated_time
        trigger_gateway_publish.assert_not_called()

    def test_get_resource_version_released_stage_names(self, fake_gateway, fake_backend, fake_resource_version):
        stage1 = G(Stage, gateway=fake_gateway, status=1, name="stage1")
        stage2 = G(Stage, gateway=fake_gateway, status=1, name="stage2")

        G(Release, gateway=fake_gateway, stage=stage1, resource_version=fake_resource_version)
        G(Release, gateway=fake_gateway, stage=stage2, resource_version=fake_resource_version)

        result = BackendHandler.get_resource_version_released_stage_names(fake_backend)

        assert len(result) == 2

    def test_get_resource_version_released_stage_names_with_inactive_stage(
        self, fake_gateway, fake_backend, fake_resource_version
    ):
        stage1 = G(Stage, gateway=fake_gateway, status=0, name="stage1")
        stage2 = G(Stage, gateway=fake_gateway, status=0, name="stage2")

        G(Release, gateway=fake_gateway, stage=stage1, resource_version=fake_resource_version)
        G(Release, gateway=fake_gateway, stage=stage2, resource_version=fake_resource_version)

        result = BackendHandler.get_resource_version_released_stage_names(fake_backend)

        assert len(result) == 0
