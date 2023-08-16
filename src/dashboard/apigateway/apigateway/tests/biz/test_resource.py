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

    def test_save_related_data(self):
        gateway = G(Gateway)
        resource = G(Resource)
        stage_prod = G(Stage, api=gateway, name="prod")
        label = G(APILabel, api=gateway)

        data = {
            "proxy_type": "http",
            "proxy_configs": {
                "http": {
                    "method": "GET",
                    "path": "/echo/",
                    "timeout": 10,
                    "upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {
                                "host": "www.a.com",
                                "weight": 100,
                            }
                        ],
                    },
                    "transform_headers": {
                        "replace": {"k1": "v1", "k2": "v2"},
                    },
                }
            },
            "auth_config": {
                "skip_auth_verification": False,
                "auth_verified_required": True,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
            "label_ids": [label.id],
            "disabled_stage_ids": [stage_prod.id],
        }
        ResourceHandler().save_related_data(
            gateway,
            resource,
            proxy_type=data["proxy_type"],
            proxy_config=data["proxy_configs"][data["proxy_type"]],
            auth_config=data["auth_config"],
            label_ids=data.get("label_ids", []),
            disabled_stage_ids=data.get("disabled_stage_ids", []),
        )

        assert Proxy.objects.filter(resource=resource, type="http").count() == 1
        assert Resource.objects.get(id=resource.id).proxy_id == Proxy.objects.get(resource=resource, type="http").id
        assert ResourceLabel.objects.filter(resource=resource).count() == 1
        assert StageResourceDisabled.objects.filter(resource=resource).count() == 1

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

    def test_save_labels(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)

        label = G(APILabel, api=gateway)
        invalid_label = G(APILabel, api=gateway)
        G(ResourceLabel, resource=resource, api_label=invalid_label)

        # test save label
        ResourceHandler().save_labels(gateway, resource, [label.id])
        assert ResourceLabel.objects.filter(resource=resource).count() == 2

        # test delete invalid labels
        ResourceHandler().save_labels(gateway, resource, [label.id], delete_unspecified=True)
        assert ResourceLabel.objects.filter(resource=resource).count() == 1

    def test_save_disabled_stages(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)
        stage = G(Stage, api=gateway)
        invalid_stage = G(Stage, api=gateway)
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
        G(Resource, api=gateway, path="/apis/", method="GET", name="search_apis")
        G(Resource, api=gateway, path="/resources/", method="POST", name="create_resource")
        resource = G(Resource, api=gateway, path="/labels/1/", method="DELETE", name="delete_label")

        api_label = G(APILabel, api=gateway, name="hello")
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

    def test_snapshot(self):
        gateway = G(Gateway)

        resource = G(
            Resource,
            api=gateway,
            name="test",
            method="GET",
            path="/echo/",
        )

        stage_prod = G(Stage, api=gateway, name="prod")
        stage_test = G(Stage, api=gateway, name="test")

        data = {
            "proxy_type": "http",
            "proxy_configs": {
                "http": {
                    "method": "GET",
                    "path": "/echo/",
                    "timeout": 10,
                    "upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {
                                "host": "www.a.com",
                                "weight": 100,
                            }
                        ],
                    },
                    "transform_headers": {
                        "replace": {"k1": "v1", "k2": "v2"},
                    },
                }
            },
            "auth_config": {
                "skip_auth_verification": False,
                "auth_verified_required": True,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
            "disabled_stage_ids": [stage_prod.id, stage_test.id],
        }
        ResourceHandler().save_related_data(
            gateway,
            resource,
            proxy_type=data["proxy_type"],
            proxy_config=data["proxy_configs"][data["proxy_type"]],
            auth_config=data["auth_config"],
            label_ids=data.get("label_ids", []),
            disabled_stage_ids=data.get("disabled_stage_ids", []),
        )

        snapshot = ResourceHandler().snapshot(resource, as_dict=True)
        assert snapshot["disabled_stages"] == ["prod", "test"]
