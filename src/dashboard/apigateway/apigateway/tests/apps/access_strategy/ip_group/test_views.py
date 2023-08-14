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
import json

import pytest
from django_dynamic_fixture import G

from apigateway.apps.access_strategy.ip_group.views import IPGroupViewSet
from apigateway.apps.access_strategy.models import AccessStrategy, IPGroup
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json


class TestIPGroupViewSet:
    @pytest.fixture(autouse=True)
    def setup(self, patch_redis):
        self.factory = APIRequestFactory()
        self.gateway = create_gateway()
        self.ip_group = G(IPGroup, api=self.gateway, name="unique-name")

    def test_create(self):
        data = {
            "name": "ipgroups-create-test",
            "ips": "1.0.0.1",
            "comment": "comment",
        }
        request = self.factory.post(f"/apis/{self.gateway.id}/access_strategies/ip_groups/", data=data)

        view = IPGroupViewSet.as_view({"post": "create"})
        response = view(request, gateway_id=self.gateway.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert IPGroup.objects.filter(api=self.gateway, name="ipgroups-create-test").count() == 1

    def test_list(self):
        params = {
            "query": "unique-name",
        }
        request = self.factory.get(f"/apis/{self.gateway.id}/access_strategies/ip_groups/", data=params)

        view = IPGroupViewSet.as_view({"get": "list"})
        response = view(request, gateway_id=self.gateway.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"]["count"] == 1
        assert len(result["data"]["results"]) == 1

    def test_update(self):
        ip_group = G(IPGroup, api=self.gateway)
        data = {
            "name": "ipgroups-update-test",
            "ips": "1.0.0.1",
            "comment": "comment",
        }

        request = self.factory.put(f"/apis/{self.gateway.id}/access_strategies/ip_groups/{ip_group.id}/", data=data)

        view = IPGroupViewSet.as_view({"put": "update"})
        response = view(request, gateway_id=self.gateway.id, id=ip_group.id)

        result = get_response_json(response)
        assert result["code"] == 0, result["message"]

        ip_group = IPGroup.objects.get(api=self.gateway, name=data["name"])

        assert ip_group._ips == data["ips"]
        assert ip_group.comment == data["comment"]

    def test_retrieve(self):
        request = self.factory.get(f"/apis/{self.gateway.id}/access_strategies/ip_groups/{self.ip_group.id}/")

        view = IPGroupViewSet.as_view({"get": "retrieve"})
        response = view(request, gateway_id=self.gateway.id, id=self.ip_group.id)

        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"]["name"] == "unique-name"

    def test_destroy(self):
        gateway = create_gateway()
        ip_group = G(IPGroup, api=gateway)

        ip_group_2 = G(IPGroup, api=gateway)
        G(
            AccessStrategy,
            api=gateway,
            type="ip_access_control",
            _config=json.dumps(
                {
                    "type": "allow",
                    "ip_group_list": [ip_group_2.id],
                }
            ),
        )

        data = [
            {
                "ip_group_id": ip_group.id,
                "expected": {
                    "code": 0,
                    "exists": False,
                },
            },
            {
                "ip_group_id": ip_group_2.id,
                "expected": {
                    "code": 40403,
                    "exists": True,
                },
            },
        ]
        for test in data:
            ip_group_id = test["ip_group_id"]
            request = self.factory.delete(f"/apis/{gateway.id}/access_strategies/ip_groups/{ip_group_id}/")

            view = IPGroupViewSet.as_view({"delete": "destroy"})
            response = view(request, gateway_id=gateway.id, id=ip_group_id)

            # result = get_response_json(response)
            _ = get_response_json(response)

            # assert result["code"] == test["expected"]["code"]
            # TODO: fix the assert according to the response here!!!!
            assert IPGroup.objects.filter(id=ip_group_id).exists() == test["expected"]["exists"]
