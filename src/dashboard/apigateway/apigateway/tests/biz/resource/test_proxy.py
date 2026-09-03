# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
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

from apigateway.biz.resource import ProxyHandler
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Backend, Proxy, Release, Resource, ResourceVersion, Stage


class TestProxyHandler:
    def test_get_resource_count_by_backend_returns_empty_without_backend_ids(
        self, django_assert_num_queries, fake_gateway
    ):
        with django_assert_num_queries(0):
            result = ProxyHandler.get_resource_count_by_backend(fake_gateway.id, [])

        assert result == {}

    def test_get_resource_count_by_backend_combines_current_and_active_released_resources(self, fake_gateway):
        backend = G(Backend, gateway=fake_gateway)
        current_resource = G(Resource, gateway=fake_gateway)
        G(Proxy, resource=current_resource, backend=backend)

        released_only_resource_id = current_resource.id + 1_000_000
        active_resource_version = G(ResourceVersion, gateway=fake_gateway)
        active_resource_version.data = [
            {"id": current_resource.id, "proxy": {"backend_id": backend.id}},
            {"id": released_only_resource_id, "proxy": {"backend_id": backend.id}},
        ]
        active_resource_version.save()
        active_stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=fake_gateway, stage=active_stage, resource_version=active_resource_version)

        inactive_resource_version = G(ResourceVersion, gateway=fake_gateway)
        inactive_resource_version.data = [
            {"id": released_only_resource_id + 1, "proxy": {"backend_id": backend.id}},
        ]
        inactive_resource_version.save()
        inactive_stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.INACTIVE.value)
        G(Release, gateway=fake_gateway, stage=inactive_stage, resource_version=inactive_resource_version)

        result = ProxyHandler.get_resource_count_by_backend(fake_gateway.id, [backend.id])

        assert result == {backend.id: 2}

    def test_get_resource_count_by_backend_ignores_incomplete_released_resource_data(self, fake_gateway):
        backend = G(Backend, gateway=fake_gateway)
        other_backend = G(Backend, gateway=fake_gateway)
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        resource_version.data = [
            {"proxy": {"backend_id": backend.id}},
            {"id": 1},
            {"id": 2, "proxy": {}},
            {"id": 3, "proxy": {"backend_id": other_backend.id}},
            {"id": 4, "proxy": {"backend_id": backend.id}},
        ]
        resource_version.save()
        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        G(Release, gateway=fake_gateway, stage=stage, resource_version=resource_version)

        result = ProxyHandler.get_resource_count_by_backend(fake_gateway.id, [backend.id])

        assert result == {backend.id: 1}

    def test_get_resource_count_by_backend_loads_shared_resource_version_once(self, monkeypatch, fake_gateway):
        backend = G(Backend, gateway=fake_gateway)
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        resource_version.data = [{"id": 1, "proxy": {"backend_id": backend.id}}]
        resource_version.save()

        for name in ["stage-1", "stage-2"]:
            stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value, name=name)
            G(Release, gateway=fake_gateway, stage=stage, resource_version=resource_version)

        original_data_property = ResourceVersion.data
        data_load_count = 0

        def get_data(instance):
            nonlocal data_load_count
            data_load_count += 1
            return original_data_property.fget(instance)

        monkeypatch.setattr(
            ResourceVersion,
            "data",
            property(get_data, original_data_property.fset),
        )

        result = ProxyHandler.get_resource_count_by_backend(fake_gateway.id, [backend.id])

        assert result == {backend.id: 1}
        assert data_load_count == 1
