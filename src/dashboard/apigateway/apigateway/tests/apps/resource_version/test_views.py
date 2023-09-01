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
import datetime
import json
import operator
from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import G
from pydantic import BaseModel

from apigateway.apps.resource_version.diff_helpers import DiffMixin
from apigateway.apps.resource_version.views import ResourceVersionDiffViewSet, ResourceVersionViewSet
from apigateway.apps.support.models import APISDK, ResourceDoc, ResourceDocVersion
from apigateway.core.models import Release, Resource, ResourceVersion, Stage
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, dummy_time, get_response_json


class TestResourceVersionViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    # def test_create(self, fake_resource):
    #     gateway = create_gateway()
    #     resource = G(Resource, =gateway)
    #     ResourceHandler().save_related_data(
    #         self.gateway,
    #         resource,
    #         proxy_type="mock",
    #         proxy_config={
    #             "code": 200,
    #             "body": "test",
    #             "headers": {},
    #         },
    #         auth_config={"auth_verified_required": True},
    #         label_ids=[],
    #         disabled_stage_ids=[],
    #     )

    #     data = {
    #         "comment": "test",
    #     }
    #     request = self.factory.post(f"/apis/{gateway.id}/resource_versions/", data=data)

    #     view = ResourceVersionViewSet.as_view({"post": "create"})
    #     response = view(request, gateway_id=gateway.id)

    #     result = get_response_json(response)
    #     self.assertEqual(response.status_code, 200, result)

    #     self.assertTrue(ResourceVersion.objects.filter(gateway=gateway).count() > 0)

    def test_list(self):
        resource_version = G(
            ResourceVersion,
            gateway=self.gateway,
            version="1.0.1",
            title="test",
            created_time=dummy_time.time,
        )
        stage_prod = G(Stage, gateway=self.gateway, status=1)
        stage_test = G(Stage, gateway=self.gateway, status=1)
        G(Release, gateway=self.gateway, stage=stage_prod, resource_version=resource_version)
        G(Release, gateway=self.gateway, stage=stage_test, resource_version=resource_version)
        G(APISDK, gateway=self.gateway, resource_version=resource_version)

        request = self.factory.get(f"/apis/{self.gateway.id}/resource_versions/")

        view = ResourceVersionViewSet.as_view({"get": "list"})
        response = view(request, gateway_id=self.gateway.id)

        result = get_response_json(response)
        self.assertEqual(response.status_code, 200)

        results = result["data"]["results"]

        released_stages = results[0].pop("released_stages")

        self.assertEqual(
            results,
            [
                {
                    "id": resource_version.id,
                    "version": resource_version.version,
                    "name": resource_version.name,
                    "title": resource_version.title,
                    "comment": resource_version.comment,
                    "resource_version_display": "1.0.1(test)",
                    "has_sdk": True,
                    "created_time": dummy_time.str,
                },
            ],
        )
        expected_release_stages = [
            {
                "id": stage_prod.id,
                "name": stage_prod.name,
            },
            {
                "id": stage_test.id,
                "name": stage_test.name,
            },
        ]
        released_stages.sort(key=operator.itemgetter("name"))
        expected_release_stages.sort(key=operator.itemgetter("name"))

        self.assertEqual(
            released_stages,
            expected_release_stages,
        )

    def test_retrieve(self):
        resource_version = G(
            ResourceVersion,
            gateway=self.gateway,
            version="1.0.1",
            title="test",
            created_time=dummy_time.time,
            _data=json.dumps(
                [
                    {
                        "id": 1,
                        "name": "test",
                        "path": "/echo",
                        "proxy": {
                            "type": "mock",
                        },
                    }
                ]
            ),
        )
        request = self.factory.get(f"/apis/{self.gateway.id}/resource_versions/{resource_version.id}/")

        view = ResourceVersionViewSet.as_view({"get": "retrieve"})
        response = view(request, gateway_id=self.gateway.id, id=resource_version.id)

        result = get_response_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            result["data"],
            {
                "id": resource_version.id,
                "version": resource_version.version,
                "name": resource_version.name,
                "title": resource_version.title,
                "comment": resource_version.comment,
                "data": [
                    {
                        "id": 1,
                        "name": "test",
                        "path": "/echo",
                        "proxy": {
                            "type": "mock",
                        },
                        "doc_updated_time": {},
                    }
                ],
                "created_by": resource_version.created_by,
                "created_time": dummy_time.str,
            },
        )

    def test_update(self):
        gateway = create_gateway()

        rv = G(ResourceVersion, gateway=gateway)

        data = [
            {
                "title": "test",
                "comment": "comment",
            }
        ]
        for test in data:
            request = self.factory.put(f"/apis/{gateway.id}/resource_versions/{rv.id}/", data=test)

            view = ResourceVersionViewSet.as_view({"put": "update"})
            response = view(request, gateway_id=gateway.id, id=rv.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200, result)

            rv = ResourceVersion.objects.get(id=rv.id)
            self.assertEqual(rv.title, test["title"])
            self.assertEqual(rv.comment, test["comment"])

    def test_need_new_version(self):
        gateway_1 = create_gateway()

        gateway_2 = create_gateway()
        G(Resource, gateway=gateway_2)

        gateway_3 = create_gateway()
        G(Resource, gateway=gateway_3, updated_time=dummy_time.time + datetime.timedelta(seconds=10))
        G(ResourceVersion, gateway=gateway_3, created_time=dummy_time.time)

        gateway_4 = create_gateway()
        G(Resource, gateway=gateway_4, updated_time=dummy_time.time)
        G(
            ResourceVersion,
            gateway=gateway_4,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )

        gateway_5 = create_gateway()
        G(Resource, gateway=gateway_5, updated_time=dummy_time.time)
        G(
            ResourceVersion,
            gateway=gateway_5,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )
        G(ResourceDoc, gateway=gateway_5, updated_time=dummy_time.time + datetime.timedelta(seconds=20))
        G(
            ResourceDocVersion,
            gateway=gateway_5,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )

        data = [
            {
                "api": gateway_1,
                "will_error": True,
            },
            {
                "api": gateway_2,
                "expected": {
                    "need_new_version": True,
                },
            },
            {
                "api": gateway_3,
                "expected": {
                    "need_new_version": True,
                },
            },
            {
                "api": gateway_4,
                "expected": {
                    "need_new_version": False,
                },
            },
            # resource doc has updated
            {
                "api": gateway_5,
                "expected": {
                    "need_new_version": True,
                },
            },
        ]

        for test in data:
            api = test["api"]
            request = self.factory.get(f"/apis/{api.id}/resource_versions/need_new_version/")

            view = ResourceVersionViewSet.as_view({"get": "need_new_version"})
            response = view(request, gateway_id=api.id)
            result = get_response_json(response)

            if test.get("will_error"):
                self.assertNotEqual(result["code"], 0)
                continue

            self.assertEqual(response.status_code, 200, result)
            self.assertEqual(result["data"], test["expected"])


class TestResourceVersionDiffViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def setUp(self):
        patcher = mock.patch("apigateway.apps.resource_version.views.ResourceDiffer")
        self.ResourceDiffer = patcher.start()

        class ResourceDifferMock(BaseModel, DiffMixin):
            id: int
            name: str
            method: str
            path: str

        self.ResourceDiffer.parse_obj.side_effect = lambda x: ResourceDifferMock.parse_obj(x)

        self.addCleanup(patcher.stop)

    def test_diff_resource_version_data(self):
        source_data = [
            {"id": 1, "name": "n1", "method": "GET", "path": "/p1"},
            {"id": 3, "name": "n3", "method": "POST", "path": "/p3"},
        ]
        target_data = [
            {"id": 2, "name": "n2", "method": "POST", "path": "/p2"},
            {"id": 3, "name": "nn", "method": "GET", "path": "/p3"},
        ]
        view = ResourceVersionDiffViewSet()
        result = view._diff_resource_version_data(source_data, target_data, {}, {})

        self.assertEqual(
            result,
            {
                "add": [{"id": 2, "name": "n2", "method": "POST", "path": "/p2"}],
                "delete": [{"id": 1, "name": "n1", "method": "GET", "path": "/p1"}],
                "update": [
                    {
                        "source": {
                            "id": 3,
                            "name": "n3",
                            "method": "POST",
                            "path": "/p3",
                            "diff": {"name": "n3", "method": "POST"},
                        },
                        "target": {
                            "id": 3,
                            "name": "nn",
                            "method": "GET",
                            "path": "/p3",
                            "diff": {"name": "nn", "method": "GET"},
                        },
                    }
                ],
            },
        )
