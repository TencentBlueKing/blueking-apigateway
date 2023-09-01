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

import pytest
from django_dynamic_fixture import G

from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.core.models import Gateway, Resource, ResourceVersion, Stage
from apigateway.tests.utils.testing import dummy_time
from apigateway.utils.time import now_datetime


class TestResourceVersionHandler:
    def test_make_version(self):
        gateway = G(Gateway)
        resource = G(Resource, gateway=gateway, created_time=dummy_time.time, updated_time=dummy_time.time)

        ResourceHandler().save_auth_config(
            resource.id,
            {
                "skip_auth_verification": False,
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
        )

        ResourceHandler().save_proxy_config(
            resource,
            "mock",
            {
                "code": 200,
                "body": "test",
                "headers": {},
            },
        )

        data = ResourceVersionHandler().make_version(gateway)
        assert data[0]["id"] == resource.id
        assert data[0]["method"] == resource.method
        assert data[0]["path"] == resource.path
        assert data[0]["proxy"]["id"] == resource.proxy_id
        assert data[0]["proxy"]["type"] == "mock"
        assert data[0]["proxy"]["config"] == json.dumps(
            {
                "code": 200,
                "body": "test",
                "headers": {},
            },
            separators=(",", ":"),
        )
        assert data[0]["contexts"]["resource_auth"]["config"] == json.dumps(
            {
                "skip_auth_verification": False,
                "auth_verified_required": False,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
            separators=(",", ":"),
        )

    def test_create_resource_version(self, fake_resource):
        gateway = fake_resource.api

        ResourceVersionHandler().create_resource_version(gateway, {"comment": "test"}, "admin")
        assert ResourceVersion.objects.filter(gateway=gateway).count() == 1

    @pytest.mark.parametrize(
        "api_id, stage_name, mocked_released_resource_version_ids, mocked_resources, expected",
        [
            (
                1,
                None,
                [1, 2],
                {
                    1: {"id": 1, "is_public": True, "disabled_stages": []},
                    2: {"id": 2, "is_public": False, "disabled_stages": []},
                },
                [{"id": 1, "is_public": True, "disabled_stages": []}],
            ),
            (
                1,
                "prod",
                [1],
                {
                    1: {"id": 1, "is_public": False, "disabled_stages": []},
                    2: {"id": 2, "is_public": False, "disabled_stages": []},
                },
                [],
            ),
            (
                1,
                None,
                [1],
                {
                    1: {"id": 1, "is_public": True, "disabled_stages": ["prod"]},
                },
                [{"id": 1, "is_public": True, "disabled_stages": ["prod"]}],
            ),
            (
                1,
                "prod",
                [1],
                {
                    1: {"id": 1, "is_public": True, "disabled_stages": ["prod"]},
                },
                [],
            ),
            (
                1,
                None,
                [1],
                {
                    1: {"id": 1, "is_public": True, "disabled_stages": ["test"]},
                },
                [],
            ),
        ],
    )
    def test_get_released_public_resources(
        self,
        mocker,
        api_id,
        stage_name,
        mocked_released_resource_version_ids,
        mocked_resources,
        expected,
    ):
        get_released_resource_version_ids_mock = mocker.patch(
            "apigateway.core.models.Release.objects.get_released_resource_version_ids",
            return_value=mocked_released_resource_version_ids,
        )
        get_resources_mock = mocker.patch.object(
            ResourceVersion.objects,
            "get_resources",
            return_value=mocked_resources,
        )
        mocker.patch.object(
            Stage.objects,
            "get_names",
            return_value=["test"],
        )

        result = ResourceVersionHandler().get_released_public_resources(api_id, stage_name)
        assert expected == result

        get_released_resource_version_ids_mock.assert_called_once_with(api_id, stage_name)
        get_resources_mock.assert_called()

    def test_get_latest_created_time(self, fake_gateway):
        result = ResourceVersionHandler.get_latest_created_time(fake_gateway.id)
        assert result is None

        G(ResourceVersion, gateway=fake_gateway, created_time=now_datetime())
        result = ResourceVersionHandler.get_latest_created_time(fake_gateway.id)
        assert isinstance(result, datetime.datetime)
