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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.biz.resource import ResourceHandler
from apigateway.core import models
from apigateway.core.constants import APIHostingTypeEnum, APIStatusEnum

pytestmark = pytest.mark.django_db


class TestAPI:
    @pytest.mark.parametrize(
        "status, is_public, expected",
        [
            (APIStatusEnum.ACTIVE.value, True, True),
            (APIStatusEnum.INACTIVE.value, True, False),
            (APIStatusEnum.ACTIVE.value, False, False),
            (APIStatusEnum.INACTIVE.value, False, False),
        ],
    )
    def test_is_active_and_public(self, status, is_public, expected):
        gateway = G(models.Gateway, status=status, is_public=is_public)
        assert gateway.is_active_and_public == expected

    @pytest.mark.parametrize(
        "hosting_type, expected",
        [
            (APIHostingTypeEnum.DEFAULT.value, False),
            (APIHostingTypeEnum.MICRO.value, True),
        ],
    )
    def test_is_micro_gateway(self, hosting_type, expected):
        gateway = G(models.Gateway, hosting_type=hosting_type)
        assert gateway.is_micro_gateway is expected


class TestResource(TestCase):
    def test_snapshot(self):
        gateway = G(
            models.Gateway,
        )

        resource = G(
            models.Resource,
            api=gateway,
            name="test",
            method="GET",
            path="/echo/",
        )

        stage_prod = G(models.Stage, api=gateway, name="prod")
        stage_test = G(models.Stage, api=gateway, name="test")

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
        self.assertTrue(snapshot["disabled_stages"], ["prod", "test"])
