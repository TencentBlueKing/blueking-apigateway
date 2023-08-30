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

from django_dynamic_fixture import G

from apigateway.apps.support.models import APISDK, ResourceDoc, ResourceDocVersion
from apigateway.biz.resource import ResourceHandler
from apigateway.core.models import Release, Resource, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_gateway, dummy_time


class TestResourceVersionListCreateApi:
    def test_create(self, request_view, fake_gateway, fake_resource1):
        ResourceHandler().save_related_data(
            fake_gateway,
            fake_resource1,
            proxy_type="mock",
            proxy_config={
                "code": 200,
                "body": "test",
                "headers": {},
            },
            auth_config={"auth_verified_required": True},
            label_ids=[],
            disabled_stage_ids=[],
        )

        data = {
            "comment": "test",
        }

        resp = request_view(
            method="POST",
            view_name="gateway.resource_version.list_create",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        assert resp.status_code == 200
        assert ResourceVersion.objects.filter(gateway=fake_gateway).count() > 0

    def test_list(self, request_view, fake_gateway):
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1.0.1",
            title="test",
            created_time=dummy_time.time,
        )
        stage_prod = G(Stage, api=fake_gateway, status=1)
        stage_test = G(Stage, api=fake_gateway, status=1)
        G(Release, gateway=fake_gateway, stage=stage_prod, resource_version=resource_version)
        G(Release, gateway=fake_gateway, stage=stage_test, resource_version=resource_version)
        G(APISDK, gateway=fake_gateway, resource_version=resource_version)

        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.list_create",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
        )

        result = resp.json()
        assert resp.status_code == 200

        results = result["data"]["results"]

        released_stages = results[0].pop("released_stages")

        assert results == [
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
        ]
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
        assert released_stages == expected_release_stages


class TestResourceVersionRetrieveApi:
    def test_retrieve(self, request_view, fake_gateway):
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
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
        resp = request_view(
            method="GET",
            view_name="gateway.resource_version.retrieve",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id, "id": resource_version.id},
        )

        assert resp.status_code == 200

        result = resp.json()

        assert result["data"] == {
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
        }


class TestResourceVersionNeedNewVersionRetrieveApi:
    def test_get(self, request_view):
        gateway_1 = create_gateway()

        gateway_2 = create_gateway()
        G(Resource, api=gateway_2)

        gateway_3 = create_gateway()
        G(Resource, api=gateway_3, updated_time=dummy_time.time + datetime.timedelta(seconds=10))
        G(ResourceVersion, gateway=gateway_3, created_time=dummy_time.time)

        gateway_4 = create_gateway()
        G(Resource, api=gateway_4, updated_time=dummy_time.time)
        G(
            ResourceVersion,
            gateway=gateway_4,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )

        gateway_5 = create_gateway()
        G(Resource, api=gateway_5, updated_time=dummy_time.time)
        G(
            ResourceVersion,
            gateway=gateway_5,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )
        G(ResourceDoc, api=gateway_5, updated_time=dummy_time.time + datetime.timedelta(seconds=20))
        G(
            ResourceDocVersion,
            gateway=gateway_5,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
            _data=json.dumps([{"id": 1}]),
        )

        data = [
            {
                "gateway": gateway_1,
                "will_error": True,
            },
            {
                "gateway": gateway_2,
                "expected": {
                    "need_new_version": True,
                },
            },
            {
                "gateway": gateway_3,
                "expected": {
                    "need_new_version": True,
                },
            },
            {
                "gateway": gateway_4,
                "expected": {
                    "need_new_version": False,
                },
            },
            # resource doc has updated
            {
                "gateway": gateway_5,
                "expected": {
                    "need_new_version": True,
                },
            },
        ]

        for test in data:
            gateway = test["gateway"]

            resp = request_view(
                method="GET",
                view_name="gateway.resource_version.need_new_version",
                path_params={"gateway_id": gateway.id},
            )

            result = resp.json()
            print(result)
            if test.get("will_error"):
                assert result["error"] is not None
                continue

            assert resp.status_code == 200
            assert result["data"]["need_new_version"] == test["expected"]["need_new_version"]
