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

from apigateway.apps.gateway.serializers import GatewayDetailSLZ
from apigateway.apps.gateway.views import GatewayViewSet
from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.biz.gateway import GatewayHandler
from apigateway.core import constants
from apigateway.core.models import JWT, Context, Gateway, Release, Resource, ResourceVersion, Stage
from apigateway.tests.conftest import FAKE_USERNAME
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json

pytestmark = pytest.mark.django_db(transaction=True)


class TestAPI:
    def test_api(self, fake_gateway):
        assert fake_gateway.maintainers == [FAKE_USERNAME]


class TestAPIViewSet:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "name": "api-create-test-01",
                    "description": "test",
                    "maintainers": ["admin1", "admin2"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "default",
                },
                {
                    "maintainers": ["admin1", "admin2", "admin"],
                },
            ),
            (
                {
                    "name": "api-create-test-02",
                    "description": "test",
                    "maintainers": ["admin", "admin2"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "default",
                },
                {
                    "maintainers": ["admin", "admin2"],
                },
            ),
        ],
    )
    def test_create(self, settings, request_factory, params, expected):
        settings.DEFAULT_GATEWAY_HOSTING_TYPE = 0
        settings.USE_BK_IAM_PERMISSION = False

        request = request_factory.post("/apis/", data=params)

        view = GatewayViewSet.as_view({"post": "create"})
        response = view(request)

        result = get_response_json(response)
        gateway = Gateway.objects.get(name=params["name"])

        assert result["code"] == 0
        assert result["data"]["id"] == gateway.id

        # check api
        assert gateway.maintainers == expected["maintainers"]
        assert gateway.status == 1
        assert gateway.is_public
        assert gateway.hosting_type == 0

        # check context
        assert (
            Context.objects.filter(
                scope_type=constants.ContextScopeTypeEnum.API.value,
                scope_id=gateway.id,
                type=constants.ContextTypeEnum.API_AUTH.value,
            ).count()
            == 1
        )

        # check jwt
        assert JWT.objects.filter(api=gateway).count() == 1

        # check default stage
        assert Stage.objects.filter(api=gateway, name="prod").count() == 1

        # check default alarm-strategy
        assert AlarmStrategy.objects.filter(api=gateway).count() == 3

    def test_list(self, request_factory):
        request = request_factory.get("/apis/", data={})

        view = GatewayViewSet.as_view({"get": "list"})
        response = view(request)

        result = get_response_json(response)
        assert result["code"] == 0

    @pytest.mark.parametrize(
        "status, target",
        [
            [1, "apigateway.apps.gateway.views.rolling_update_release"],
            [0, "apigateway.apps.gateway.views.revoke_release"],
        ],
    )
    def test_update_status_for_micro_gateway(
        self, status, target, mocker, request_view, fake_gateway_for_micro_gateway
    ):
        task = mocker.patch(target)

        response = request_view(
            "PUT",
            "apigateway.apps.gateway.update_status",
            gateway=fake_gateway_for_micro_gateway,
            path_params={"id": fake_gateway_for_micro_gateway.pk},
            data={"status": status},
        )

        assert response.status_code == 200
        assert task.apply_async.call_count == 1


class TestAPIViewSetCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway(name="api-viewset-test")
        cls.stage_prod = G(Stage, api=cls.gateway, name="prod")
        cls.resource = G(Resource, api=cls.gateway)
        cls.resource_version = G(ResourceVersion, gateway=cls.gateway)
        cls.release = G(Release, gateway=cls.gateway, stage=cls.stage_prod, resource_version=cls.resource_version)
        cls.stage_test = G(Stage, api=cls.gateway, name="test")

        G(Gateway, name="api-viewset-test-2", created_by="test")

    def test_update(self):
        gateway = create_gateway(
            name="api-update-test",
            description="t1",
            _maintainers="admin",
            is_public=True,
            status=0,
        )

        data = [
            {
                "name": "api-update-test-2",
                "description": "t2",
                "maintainers": ["admin1", "admin2"],
                "is_public": False,
                "status": 1,
            }
        ]
        for test in data:
            request = self.factory.put(f"/apis/{gateway.id}/", data=test)

            view = GatewayViewSet.as_view({"put": "update"})
            response = view(request, id=gateway.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0, result)
            self.assertEqual(response.status_code, 200, result)

            self.assertFalse(Gateway.objects.filter(name=test["name"]).exists())

            gateway = Gateway.objects.get(name="api-update-test")
            self.assertEqual(gateway.description, test["description"])
            self.assertEqual(gateway.maintainers, test["maintainers"])
            self.assertEqual(gateway.is_public, test["is_public"])
            self.assertEqual(gateway.status, 0)

    def test_retrieve(self):
        gateway = create_gateway()
        JWT.objects.create_jwt(gateway)
        GatewayHandler().save_auth_config(gateway.id, "default")

        data = [
            {
                "api_id": gateway.id,
            },
        ]
        for test in data:
            request = self.factory.get(f"/apis/{gateway.id}/", data=test)

            view = GatewayViewSet.as_view({"get": "retrieve"})
            response = view(request, id=gateway.id)

            slz = GatewayDetailSLZ.from_instance(gateway)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(result["data"], slz.data)

    def test_destroy(self):
        data = [
            {
                "name": "api-destroy-test-1",
                "status": 1,
                "will_error": True,
            },
            {
                "name": "api-destroy-test-2",
                "status": 0,
                "will_error": False,
            },
        ]
        for test in data:
            gateway = create_gateway(name=test["name"], status=test["status"])
            self.assertTrue(Gateway.objects.filter(name=test["name"]).exists())

            request = self.factory.delete(f"/apis/{gateway.id}/")

            view = GatewayViewSet.as_view({"delete": "destroy"})
            response = view(request, id=gateway.id)

            # result = get_response_json(response)

            if test["will_error"]:
                # self.assertNotEqual(result["code"], 0)
                self.assertNotEqual(response.status_code, 200, "")
                self.assertTrue(Gateway.objects.filter(name=test["name"]).exists())
            else:
                # self.assertEqual(result["code"], 0)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(Gateway.objects.filter(name=test["name"]).exists())

    def test_update_status(self):
        gateway = create_gateway(
            name="api-update-status-test",
            description="t1",
            _maintainers="admin;admin1",
            is_public=True,
            status=0,
        )
        data = [
            {
                "name": "api-update-status-test-2",
                "description": "t2",
                "maintainers": ["admin1", "admin2"],
                "is_public": False,
                "status": 1,
            }
        ]
        for test in data:
            request = self.factory.put(f"/apis/{gateway.id}/status/", data=test)

            view = GatewayViewSet.as_view({"put": "update_status"})
            response = view(request, id=gateway.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0)
            self.assertEqual(response.status_code, 200)

            self.assertFalse(Gateway.objects.filter(name=test["name"]).exists())

            gateway = Gateway.objects.get(name="api-update-status-test")
            self.assertEqual(gateway.description, "t1")
            self.assertEqual(gateway.maintainers, ["admin", "admin1"])
            self.assertEqual(gateway.is_public, True)
            self.assertEqual(gateway.status, 1)
