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

from apigateway.apis.open.esb.permission.helpers import ComponentPermission, ComponentPermissionBuilder
from apigateway.apps.esb.bkcore.models import AppComponentPermission, ComponentSystem, ESBChannel

pytestmark = pytest.mark.django_db


class TestComponentPermission:
    @pytest.fixture
    def mocked_component(self):
        return {
            "id": 1,
            "board": "test",
            "name": "test",
            "description": "test",
            "system_name": "test",
            "permission_level": "normal",
            "component_permission": None,
            "component_permission_apply_status": "",
        }

    @pytest.mark.parametrize(
        "component, expected",
        [
            (
                {
                    "id": 1,
                    "board": "test",
                    "name": "test",
                    "description": "test",
                    "system_name": "test",
                    "permission_level": "normal",
                    "component_permission": None,
                    "component_permission_apply_status": "",
                },
                {
                    "id": 1,
                    "board": "test",
                    "name": "test",
                    "description": "test",
                    "description_en": None,
                    "system_name": "test",
                    "permission_level": "normal",
                    "permission_status": "need_apply",
                    "expires_in": -math.inf,
                    "doc_link": "",
                },
            ),
        ],
    )
    def test_as_dict(self, mocker, component, expected):
        mocker.patch(
            "apigateway.apis.open.esb.permission.helpers.get_component_doc_link",
            return_value="",
        )
        perm = ComponentPermission.parse_obj(component)
        assert perm.as_dict() == expected

    @pytest.mark.parametrize(
        "permission_level, expected",
        [
            ("unlimited", False),
            ("normal", True),
            ("sensitive", True),
            ("special", True),
        ],
    )
    def test_component_perm_required(self, mocked_component, permission_level, expected):
        mocked_component["permission_level"] = permission_level

        perm = ComponentPermission.parse_obj(mocked_component)
        assert perm.component_perm_required == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "component_perm_required": False,
                },
                "owned",
            ),
            (
                {
                    "component_perm_required": True,
                    "expires_in": math.inf,
                },
                "owned",
            ),
            (
                {
                    "component_perm_required": True,
                    "expires_in": 0,
                    "component_permission_apply_status": "pending",
                },
                "pending",
            ),
            (
                {
                    "component_perm_required": True,
                    "expires_in": 10,
                    "component_permission_apply_status": "",
                },
                "owned",
            ),
            (
                {
                    "component_perm_required": True,
                    "expires_in": -10,
                    "component_permission_apply_status": "",
                },
                "expired",
            ),
            (
                {
                    "component_perm_required": True,
                    "expires_in": -math.inf,
                    "component_permission_apply_status": "",
                },
                "need_apply",
            ),
        ],
    )
    def test_permission_status(self, mocker, mocked_component, params, expected):
        mocker.patch(
            "apigateway.apis.open.esb.permission.helpers.ComponentPermission.component_perm_required",
            new_callable=mock.PropertyMock(return_value=params["component_perm_required"]),
        )
        if "expires_in" in params:
            mocker.patch(
                "apigateway.apis.open.esb.permission.helpers.ComponentPermission.expires_in",
                new_callable=mock.PropertyMock(return_value=params["expires_in"]),
            )

        mocked_component.update(params)

        perm = ComponentPermission.parse_obj(mocked_component)
        assert perm.permission_status == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "component_perm_required": False,
                },
                math.inf,
            ),
            (
                {
                    "component_perm_required": True,
                },
                -math.inf,
            ),
            (
                {
                    "component_perm_required": True,
                    "component_permission_expires_in": None,
                },
                math.inf,
            ),
            (
                {
                    "component_perm_required": True,
                    "component_permission_expires_in": 10,
                },
                10,
            ),
            (
                {
                    "component_perm_required": True,
                    "component_permission_expires_in": -10,
                },
                -10,
            ),
        ],
    )
    def test_expires_in(self, mocker, mocked_component, params, expected):
        mocker.patch(
            "apigateway.apis.open.esb.permission.helpers.ComponentPermission.component_perm_required",
            new_callable=mock.PropertyMock(return_value=params["component_perm_required"]),
        )

        if "component_permission_expires_in" in params:
            params["component_permission"] = G(AppComponentPermission)
            mocker.patch(
                "apigateway.apps.esb.bkcore.models.AppComponentPermission.expires_in",
                new_callable=mock.PropertyMock(return_value=params["component_permission_expires_in"]),
            )

        mocked_component.update(params)

        perm = ComponentPermission.parse_obj(mocked_component)
        assert perm.expires_in == expected


class TestComponentPermissionBuilder:
    def test_build(self, mocker):
        mocker.patch(
            "apigateway.apis.open.esb.permission.helpers.get_component_doc_link",
            return_value="",
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.helpers.ComponentPermission.expires_in",
            new_callable=mock.PropertyMock(return_value=-math.inf),
        )
        mocker.patch(
            "apigateway.apis.open.esb.permission.helpers.ComponentPermission.permission_status",
            new_callable=mock.PropertyMock(return_value="need_apply"),
        )
        system = G(ComponentSystem)
        component = G(ESBChannel, system=system)

        components = [
            {
                "id": component.id,
                "board": component.board or "",
                "name": component.name,
                "description": component.description,
                "description_en": component.description_en,
                "system_name": system.name,
                "permission_level": component.permission_level,
            }
        ]

        result = ComponentPermissionBuilder(system.id, target_app_code="test").build(components)
        assert result == [
            {
                "id": component.id,
                "board": component.board or "",
                "name": component.name,
                "description": component.description,
                "description_en": component.description_en,
                "system_name": system.name,
                "permission_level": component.permission_level,
                "permission_status": "need_apply",
                "expires_in": -math.inf,
                "doc_link": "",
            }
        ]
