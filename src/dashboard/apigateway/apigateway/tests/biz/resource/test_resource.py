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
from apigateway.core.models import Gateway, Resource


class TestResourceHandler:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)

    def test_save_resource_labels(self, fake_resource):
        fake_gateway = fake_resource.gateway

        label_1 = G(APILabel, gateway=fake_gateway)
        label_2 = G(APILabel, gateway=fake_gateway)
        G(ResourceLabel, resource=fake_resource, api_label=label_1)

        # test save label
        ResourceHandler().save_resource_labels(fake_gateway, fake_resource, [label_2.id, label_1.id])
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 2

        # test delete invalid labels
        ResourceHandler().save_resource_labels(fake_gateway, fake_resource, [label_2.id])
        assert ResourceLabel.objects.filter(resource=fake_resource).count() == 1

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
            ResourceHandler.save_auth_config(resource.id, test["config"])
            assert ResourceAuthContext().get_config(resource.id) == test["expected"]

        # test skip_auth_verification=True in database
        ResourceHandler.save_auth_config(
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
            ResourceHandler.save_auth_config(resource.id, test["config"])
            assert ResourceAuthContext().get_config(resource.id) == test["expected"]

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

        result = ResourceHandler.filter_by_resource_filter_condition(fake_gateway.id, {"keyword": "Test"})
        assert result.count() == 2

        result = ResourceHandler.filter_by_resource_filter_condition(fake_gateway.id, {})
        assert result.count() == 3

    def test_group_by_gateway_id(self):
        gateway_1 = G(Gateway)
        gateway_2 = G(Gateway)

        r1 = G(Resource, gateway=gateway_1)
        r2 = G(Resource, gateway=gateway_2)
        r3 = G(Resource, gateway=gateway_1)

        result = ResourceHandler.group_by_gateway_id([r1.id, r2.id, r3.id])
        assert result == {
            gateway_1.id: [r1.id, r3.id],
            gateway_2.id: [r2.id],
        }
