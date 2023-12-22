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
import math
from unittest import mock

import pytest
from ddf import G

from apigateway.apis.open.permission.helpers import AppPermissionBuilder, ResourcePermission
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import AppAPIPermission, AppPermissionApplyStatus, AppResourcePermission
from apigateway.core.models import Resource
from apigateway.utils.time import to_datetime_from_now

pytestmark = pytest.mark.django_db


class TestResourcePermission:
    @pytest.fixture
    def mocked_resource(self):
        return {
            "id": 1,
            "name": "test",
            "api_name": "test",
            "description": "desc",
            "description_en": "desc_en",
            "resource_perm_required": True,
            "api_permission": None,
            "resource_permission": None,
            "api_permission_apply_status": "",
            "resource_permission_apply_status": "",
            "doc_link": "",
        }

    @pytest.mark.parametrize(
        "resource, expected",
        [
            (
                {
                    "id": 1,
                    "name": "test",
                    "api_name": "test",
                    "description": "desc",
                    "description_en": "desc_en",
                    "doc_link": "",
                    "resource_perm_required": True,
                    "api_permission": None,
                    "resource_permission": None,
                    "api_permission_apply_status": "",
                    "resource_permission_apply_status": "pending",
                },
                {
                    "id": 1,
                    "name": "test",
                    "api_name": "test",
                    "doc_link": "",
                    "description": "desc",
                    "description_en": "desc_en",
                    "permission_status": "pending",
                    "permission_level": "normal",
                    "expires_in": -math.inf,
                },
            ),
        ],
    )
    def test_as_dict(self, resource, expected):
        perm = ResourcePermission.parse_obj(resource)
        assert perm.as_dict() == expected

    @pytest.mark.parametrize(
        "resource_perm_required, expected",
        [
            (True, "normal"),
            (False, "unlimited"),
        ],
    )
    def test_permission_level(self, mocked_resource, resource_perm_required, expected):
        mocked_resource["resource_perm_required"] = resource_perm_required

        perm = ResourcePermission.parse_obj(mocked_resource)
        assert perm.permission_level == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "resource_perm_required": False,
                },
                "unlimited",
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": None,
                },
                "owned",
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_apply_status": "pending",
                },
                "pending",
            ),
            (
                {
                    "resource_perm_required": True,
                    "resource_permission_apply_status": "pending",
                },
                "pending",
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": 10,
                },
                "owned",
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": -10,
                },
                "expired",
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": -math.inf,
                },
                "need_apply",
            ),
        ],
    )
    def test_permission_status(self, mocker, mocked_resource, params, expected):
        if "api_permission_expires_in" in params:
            params["api_permission"] = G(AppAPIPermission)
            mocker.patch(
                "apigateway.apps.permission.models.AppAPIPermission.expires_in",
                new_callable=mock.PropertyMock(return_value=params["api_permission_expires_in"]),
            )

        mocked_resource.update(params)

        perm = ResourcePermission.parse_obj(mocked_resource)
        assert perm.permission_status == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "resource_perm_required": False,
                },
                math.inf,
            ),
            (
                {
                    "resource_perm_required": True,
                },
                -math.inf,
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": None,
                },
                math.inf,
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": 10,
                },
                10,
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": -10,
                },
                -10,
            ),
            (
                {
                    "resource_perm_required": True,
                    "resource_permission_expires_in": 10,
                },
                10,
            ),
            (
                {
                    "resource_perm_required": True,
                    "resource_permission_expires_in": -10,
                },
                -10,
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": 10,
                    "resource_permission_expires_in": 30,
                },
                30,
            ),
            (
                {
                    "resource_perm_required": True,
                    "api_permission_expires_in": 30,
                    "resource_permission_expires_in": 10,
                },
                30,
            ),
        ],
    )
    def test_expires_in(self, mocker, mocked_resource, params, expected):
        if "api_permission_expires_in" in params:
            params["api_permission"] = G(AppAPIPermission)
            mocker.patch(
                "apigateway.apps.permission.models.AppAPIPermission.expires_in",
                new_callable=mock.PropertyMock(return_value=params["api_permission_expires_in"]),
            )

        if "resource_permission_expires_in" in params:
            params["resource_permission"] = G(AppResourcePermission)
            mocker.patch(
                "apigateway.apps.permission.models.AppResourcePermission.expires_in",
                new_callable=mock.PropertyMock(return_value=params["resource_permission_expires_in"]),
            )

        mocked_resource.update(params)

        perm = ResourcePermission.parse_obj(mocked_resource)
        assert perm.expires_in == expected


class TestAppPermissionBuilder:
    def test_build(self, mocker, fake_gateway, unique_id):
        r = G(Resource, api=fake_gateway)
        G(AppAPIPermission, api=fake_gateway, bk_app_code=unique_id, expires=None)
        G(AppResourcePermission, api=fake_gateway, bk_app_code=unique_id, resource_id=r.id)

        mocker.patch(
            "apigateway.apis.open.permission.helpers.ResourceVersionHandler.get_released_public_resources",
            return_value=[
                {
                    "id": r.id,
                    "name": "test1-1",
                    "description": "desc",
                    "description_en": "desc_en",
                    "resource_perm_required": True,
                },
            ],
        )
        mocker.patch(
            "apigateway.apis.open.permission.helpers.ReleasedResource.objects.filter_latest_released_resources",
            return_value=[
                {
                    "id": r.id,
                    "name": "test1-2",
                    "description": "desc",
                    "description_en": "desc_en",
                    "resource_perm_required": True,
                },
            ],
        )
        mocker.patch(
            "apigateway.apis.open.permission.helpers.Resource.objects.get_id_to_fields_map",
            return_value={
                r.id: {
                    "api_name": "test",
                    "api_id": fake_gateway.id,
                },
            },
        )
        mocker.patch(
            "apigateway.apis.open.permission.helpers.ReleasedResource.objects.get_latest_doc_link",
            return_value={
                r.id: "test",
            },
        )

        result = AppPermissionBuilder(unique_id).build()
        assert result == [
            {
                "id": r.id,
                "name": "test1-2",
                "api_name": "test",
                "description": "desc",
                "description_en": "desc_en",
                "permission_status": "owned",
                "permission_level": "normal",
                "expires_in": math.inf,
                "doc_link": "test",
            },
        ]

    def test_build_with_apply_status(self, mocker, fake_gateway, fake_resource, unique_id):
        G(
            AppResourcePermission,
            api=fake_gateway,
            bk_app_code=unique_id,
            resource_id=fake_resource.id,
            expires=to_datetime_from_now(days=-10),
        )
        G(
            AppPermissionApplyStatus,
            api=fake_gateway,
            bk_app_code=unique_id,
            resource=fake_resource.id,
            status=ApplyStatusEnum.PENDING.value,
        )

        mocker.patch(
            "apigateway.apis.open.permission.helpers.ResourceVersionHandler.get_released_public_resources",
            return_value=[
                {
                    "id": fake_resource.id,
                    "name": "test1-1",
                    "description": "desc",
                    "description_en": "desc_en",
                    "resource_perm_required": True,
                },
            ],
        )
        mocker.patch(
            "apigateway.apis.open.permission.helpers.ReleasedResource.objects.filter_latest_released_resources",
            return_value=[
                {
                    "id": fake_resource.id,
                    "name": "test1-2",
                    "description": "desc",
                    "description_en": "desc_en",
                    "resource_perm_required": True,
                },
            ],
        )
        mocker.patch(
            "apigateway.apis.open.permission.helpers.Resource.objects.get_id_to_fields_map",
            return_value={
                fake_resource.id: {
                    "api_name": "test",
                    "api_id": fake_gateway.id,
                },
            },
        )
        mocker.patch(
            "apigateway.apis.open.permission.helpers.ReleasedResource.objects.get_latest_doc_link",
            return_value={
                fake_resource.id: "test",
            },
        )

        result = AppPermissionBuilder(unique_id).build()
        assert result[0]["expires_in"] < 0

        result[0]["expires_in"] = -10
        assert result == [
            {
                "id": fake_resource.id,
                "name": "test1-2",
                "api_name": "test",
                "description": "desc",
                "description_en": "desc_en",
                "permission_status": "pending",
                "permission_level": "normal",
                "expires_in": -10,
                "doc_link": "test",
            },
        ]

    def test_get_gateway_id_to_permission_apply_status(self, fake_gateway, unique_id):
        G(
            AppPermissionApplyStatus,
            bk_app_code=unique_id,
            api=fake_gateway,
            grant_dimension=GrantDimensionEnum.API.value,
            status=ApplyStatusEnum.PENDING.value,
        )

        builder = AppPermissionBuilder(unique_id)
        result = builder._get_gateway_id_to_permission_apply_status()
        assert result == {fake_gateway.id: "pending"}

    def test_get_resource_id_to_permission_apply_status(self, fake_gateway, fake_resource, unique_id):
        G(
            AppPermissionApplyStatus,
            bk_app_code=unique_id,
            api=fake_gateway,
            resource=fake_resource,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            status=ApplyStatusEnum.PENDING.value,
        )

        builder = AppPermissionBuilder(unique_id)
        result = builder._get_resource_id_to_permission_apply_status()
        assert result == {fake_resource.id: "pending"}
