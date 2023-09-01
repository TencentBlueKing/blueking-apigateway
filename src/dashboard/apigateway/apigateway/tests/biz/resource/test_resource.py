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
from django_dynamic_fixture import G

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.biz.resource import ResourceHandler
from apigateway.common.contexts import ResourceAuthContext
from apigateway.core.models import BackendService, Gateway, Proxy, Resource, Stage, StageResourceDisabled


class TestResourceHandler:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)

    def test_get_proxy_configs(self):
        backend_service = G(BackendService)
        resource = G(Resource)
        proxy_http = G(
            Proxy,
            resource=resource,
            type="http",
            _config='{"method": "GET"}',
            backend_service=backend_service,
            backend_config_type="existed",
        )
        proxy_mock = G(
            Proxy,
            resource=resource,
            type="mock",
            _config='{"code": 200}',
            backend_service=None,
            backend_config_type="default",
        )

        data = [
            {
                "proxy_id": proxy_http.id,
                "expected": {
                    "type": "http",
                    "backend_service_id": backend_service.id,
                    "backend_config_type": "existed",
                    "configs": {
                        "http": {"method": "GET"},
                        "mock": {"code": 200},
                    },
                },
            },
            {
                "proxy_id": proxy_mock.id,
                "expected": {
                    "type": "mock",
                    "backend_service_id": None,
                    "backend_config_type": "default",
                    "configs": {
                        "http": {"method": "GET"},
                        "mock": {"code": 200},
                    },
                },
            },
        ]

        for test in data:
            resource.proxy_id = test["proxy_id"]
            resource.save()

            result = ResourceHandler().get_proxy_configs(resource)
            assert result == test["expected"]

    def test_save_resource_labels(self, fake_resource):
        fake_gateway = fake_resource.api

        label_1 = G(APILabel, gateway=fake_gateway)
        label_2 = G(APILabel, gateway=fake_gateway)
        G(ResourceLabel, resource=fake_resource, api_label=label_1)

        # test save label
        ResourceHandler().save_resource_labels(fake_gateway, fake_resource, [label_2.id, label_1.id])
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 2

        # test delete invalid labels
        ResourceHandler().save_resource_labels(fake_gateway, fake_resource, [label_2.id])
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 1

    def test_save_disabled_stages(self):
        gateway = G(Gateway)
        resource = G(Resource, gateway=gateway)
        stage = G(Stage, gateway=gateway)
        invalid_stage = G(Stage, gateway=gateway)
        G(StageResourceDisabled, resource=resource, stage=invalid_stage)

        # test save disabled stages
        ResourceHandler().save_disabled_stages(gateway, resource, [stage.id])
        assert StageResourceDisabled.objects.filter(resource=resource).count() == 2

        # test delete invalid disabled_stages
        ResourceHandler().save_disabled_stages(gateway, resource, [stage.id], delete_unspecified=True)
        assert StageResourceDisabled.objects.filter(resource=resource).count() == 1

    def test_save_auth_config(self):
        resource = G(Resource)
        data = [
            {
                "config": {
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
                "expected": {
                    "skip_auth_verification": False,
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            },
            {
                "config": {
                    "skip_auth_verification": True,
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
                "expected": {
                    "skip_auth_verification": True,
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            },
        ]
        for test in data:
            ResourceHandler().save_auth_config(resource.id, test["config"])
            assert ResourceAuthContext().get_config(resource.id) == test["expected"]

        # test skip_auth_verification=True in database
        ResourceHandler().save_auth_config(
            resource.id,
            {
                "skip_auth_verification": True,
                "auth_verified_required": False,
                "app_verified_required": False,
                "resource_perm_required": False,
            },
        )
        data = [
            {
                "config": {
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
                "expected": {
                    "skip_auth_verification": True,
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
            },
            {
                "config": {
                    "skip_auth_verification": False,
                    "auth_verified_required": True,
                    "app_verified_required": False,
                    "resource_perm_required": True,
                },
                "expected": {
                    "skip_auth_verification": False,
                    "auth_verified_required": True,
                    "app_verified_required": False,
                    "resource_perm_required": True,
                },
            },
        ]
        for test in data:
            ResourceHandler().save_auth_config(resource.id, test["config"])
            assert ResourceAuthContext().get_config(resource.id) == test["expected"]

    def test_filter_resource(self):
        gateway = G(Gateway)
        G(Resource, gateway=gateway, path="/apis/", method="GET", name="search_apis")
        G(Resource, gateway=gateway, path="/resources/", method="POST", name="create_resource")
        resource = G(Resource, gateway=gateway, path="/labels/1/", method="DELETE", name="delete_label")

        api_label = G(APILabel, gateway=gateway, name="hello")
        G(ResourceLabel, resource=resource, api_label=api_label)

        data = [
            {
                "params": {"query": "/apis/"},
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {"query": "search_apis"},
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {"path": "/labels/"},
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {"method": "POST"},
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {"label_name": "hello"},
                "expected": {
                    "count": 1,
                },
            },
        ]
        for test in data:
            result = (
                ResourceHandler()
                .filter_resource(
                    gateway=gateway,
                    query=test["params"].get("query"),
                    path=test["params"].get("path"),
                    method=test["params"].get("method"),
                    label_name=test["params"].get("label_name"),
                )
                .count()
            )
            assert result == test["expected"]["count"]

    def test_snapshot(self, fake_resource):
        snapshot = ResourceHandler().snapshot(fake_resource, as_dict=True)
        assert snapshot
        assert isinstance(snapshot, dict)

    def test_filter_by_resource_filter_condition(self, fake_gateway):
        resource_1 = G(Resource, gateway=fake_gateway, name="test1", method="GET", path="/test")
        resource_2 = G(Resource, gateway=fake_gateway, name="test2", method="POST", path="/test")
        resource_3 = G(Resource, gateway=fake_gateway, name="color", method="PUT", path="/green")
        label = G(APILabel, gateway=fake_gateway)
        G(ResourceLabel, api_label=label, resource=resource_1)

        result = ResourceHandler.filter_by_resource_filter_condition(fake_gateway.id, {"name": "test1"})
        assert list(result) == [resource_1]

        result = ResourceHandler.filter_by_resource_filter_condition(fake_gateway.id, {"path": "/green"})
        assert list(result) == [resource_3]

        result = ResourceHandler.filter_by_resource_filter_condition(fake_gateway.id, {"method": "POST"})
        assert list(result) == [resource_2]

        result = ResourceHandler.filter_by_resource_filter_condition(fake_gateway.id, {"label_ids": [label.id]})
        assert list(result) == [resource_1]

        result = ResourceHandler.filter_by_resource_filter_condition(fake_gateway.id, {"query": "Test"})
        assert result.count() == 2

        result = ResourceHandler.filter_by_resource_filter_condition(fake_gateway.id, {})
        assert result.count() == 3
