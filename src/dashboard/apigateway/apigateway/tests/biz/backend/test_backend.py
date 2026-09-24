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

import pytest
from django_dynamic_fixture import G

from apigateway.biz.backend import BackendHandler
from apigateway.core.constants import DEFAULT_BACKEND_NAME, BackendKindEnum, PublishSourceEnum
from apigateway.core.models import Backend, BackendConfig, Proxy, Release, Resource, ResourceVersion, Stage
from apigateway.service.resource import delete_resources


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

    def test_update(self, mocker, fake_stage):
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

        publish = mocker.patch("apigateway.biz.backend.backend.trigger_gateway_publish")
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

        assert list(updated_stage_ids) == []
        publish.assert_not_called()
        assert backend.name == "backend-update"
        assert backend.description == "update"

        backend_config = BackendConfig.objects.get(backend=backend)
        assert backend_config.config == {
            "type": "node",
            "timeout": 10,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "https", "host": "www.example.com", "weight": 1}],
        }

    @pytest.mark.parametrize(
        "draft_reference, released_reference, gateway_status, stage_status, changed, expected_publish",
        [
            (False, True, 1, 1, True, True),
            (True, True, 1, 1, True, True),
            (False, False, 1, 1, True, False),
            (True, False, 1, 1, True, False),
            (False, True, 0, 1, True, False),
            (False, True, 1, 0, True, False),
            (False, True, 1, 1, False, False),
        ],
        ids=[
            "released-only",
            "draft-and-released",
            "unreferenced",
            "draft-only",
            "gateway-inactive",
            "stage-inactive",
            "unchanged",
        ],
    )
    def test_update_publishes_changed_released_backend(
        self,
        mocker,
        fake_backend,
        fake_release_v2,
        draft_reference,
        released_reference,
        gateway_status,
        stage_status,
        changed,
        expected_publish,
    ):
        gateway = fake_backend.gateway
        stage = fake_release_v2.stage
        gateway.status = gateway_status
        gateway.save(update_fields=["status"])
        stage.status = stage_status
        stage.save(update_fields=["status"])
        if not draft_reference:
            other_backend = G(Backend, gateway=gateway)
            Proxy.objects.filter(backend=fake_backend).update(backend=other_backend)
        if not released_reference:
            resource_version = fake_release_v2.resource_version
            resource_version.data = []
            resource_version.save(update_fields=["_data"])

        backend_config = BackendConfig.objects.get(backend=fake_backend, stage=stage)
        config = backend_config.config
        config["timeout"] = 60 if changed else 30
        publish = mocker.patch("apigateway.biz.backend.backend.trigger_gateway_publish")
        _, stage_ids = BackendHandler.update(
            fake_backend,
            {
                "name": fake_backend.name,
                "description": fake_backend.description,
                "type": fake_backend.type,
                "configs": [{**config, "stage_id": stage.id}],
            },
            "admin",
        )

        backend_config.refresh_from_db()
        assert backend_config.config["timeout"] == (60 if changed else 30)
        assert list(stage_ids) == ([stage.id] if expected_publish else [])
        if expected_publish:
            publish.assert_called_once_with(PublishSourceEnum.BACKEND_UPDATE, "admin", gateway.id, stage.id)
        else:
            publish.assert_not_called()

    def test_update_default_backend_publishes_only_affected_stages(self, mocker, fake_backend, fake_release_v2):
        fake_backend.name = DEFAULT_BACKEND_NAME
        fake_backend.save(update_fields=["name"])
        gateway = fake_backend.gateway
        changed_stage = fake_release_v2.stage
        unchanged_stage = G(Stage, gateway=gateway, status=1)
        other_backend_stage = G(Stage, gateway=gateway, status=1)
        unpublished_stage = G(Stage, gateway=gateway, status=1)
        G(Release, gateway=gateway, stage=unchanged_stage, resource_version=fake_release_v2.resource_version)
        other_backend = G(Backend, gateway=gateway)
        other_version = G(
            ResourceVersion, gateway=gateway, schema_version=fake_release_v2.resource_version.schema_version
        )
        resources = fake_release_v2.resource_version.data
        for resource in resources:
            resource["proxy"]["backend_id"] = other_backend.id
        other_version.data = resources
        other_version.save()
        G(Release, gateway=gateway, stage=other_backend_stage, resource_version=other_version)
        resource_ids = list(Proxy.objects.filter(backend=fake_backend).values_list("resource_id", flat=True))
        delete_resources(resource_ids)
        config = BackendConfig.objects.get(backend=fake_backend, stage=changed_stage).config
        for stage in [unchanged_stage, other_backend_stage, unpublished_stage]:
            G(BackendConfig, gateway=gateway, backend=fake_backend, stage=stage, _config=config)
        publish = mocker.patch("apigateway.biz.backend.backend.trigger_gateway_publish")

        _, stage_ids = BackendHandler.update(
            fake_backend,
            {
                "name": fake_backend.name,
                "description": fake_backend.description,
                "type": fake_backend.type,
                "configs": [
                    {**config, "stage_id": stage.id, "timeout": timeout}
                    for stage, timeout in [
                        (changed_stage, 60),
                        (unchanged_stage, 30),
                        (other_backend_stage, 60),
                        (unpublished_stage, 60),
                    ]
                ],
            },
            "admin",
        )

        assert list(stage_ids) == [changed_stage.id]
        publish.assert_called_once_with(PublishSourceEnum.BACKEND_UPDATE, "admin", gateway.id, changed_stage.id)
        assert BackendConfig.objects.get(backend=fake_backend, stage=other_backend_stage).config["timeout"] == 60
        assert BackendConfig.objects.get(backend=fake_backend, stage=unpublished_stage).config["timeout"] == 60

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
                        "timeout": 300,
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
