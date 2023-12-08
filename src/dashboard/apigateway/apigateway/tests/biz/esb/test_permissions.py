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

import pytest
from ddf import G

from apigateway.apps.esb.bkcore.models import (
    AppComponentPermission,
    AppPermissionApplyRecord,
    ComponentResourceBinding,
)
from apigateway.biz.esb.permissions import (
    AppComponentPermissionData,
    ComponentPermission,
    ComponentPermissionByEsbManager,
)
from apigateway.utils.time import to_datetime_from_now


class TestComponentPermissionByEsbManager:
    def test_create_apply_record(self, unique_id, fake_system, fake_channel):
        manager = ComponentPermissionByEsbManager()
        record = manager.create_apply_record(
            bk_app_code=unique_id,
            system=fake_system,
            component_ids=[fake_channel.id],
            reason="",
            expire_days=180,
            username="admin",
        )

        assert AppPermissionApplyRecord.objects.filter(id=record.id).exists()

    def test_renew_permission(self, unique_id, fake_channel):
        perm = G(
            AppComponentPermission,
            bk_app_code=unique_id,
            component_id=fake_channel.id,
            expires=to_datetime_from_now(days=10),
        )

        manager = ComponentPermissionByEsbManager()
        manager.renew_permission(unique_id, [fake_channel.id], 180)

        perm.refresh_from_db()

        assert to_datetime_from_now(days=170) < perm.expires < to_datetime_from_now(days=190)

    def test_list_permissions(self, mocker, fake_system, fake_channel):
        mocker.patch(
            "apigateway.biz.esb.permissions.get_component_doc_link",
            return_value="",
        )
        mocker.patch(
            "apigateway.biz.esb.permissions.ComponentPermission.expires_in",
            new_callable=mocker.PropertyMock(return_value=-math.inf),
        )
        mocker.patch(
            "apigateway.biz.esb.permissions.ComponentPermission.permission_status",
            new_callable=mocker.PropertyMock(return_value="need_apply"),
        )

        components = [
            {
                "id": fake_channel.id,
                "board": fake_channel.board or "",
                "name": fake_channel.name,
                "description": fake_channel.description,
                "description_en": fake_channel.description_en,
                "system_name": fake_system.name,
                "permission_level": fake_channel.permission_level,
            }
        ]

        manager = ComponentPermissionByEsbManager()
        result = manager.list_permissions("test", components)
        assert result == [
            {
                "id": fake_channel.id,
                "board": fake_channel.board or "",
                "name": fake_channel.name,
                "description": fake_channel.description,
                "description_en": fake_channel.description_en,
                "system_name": fake_system.name,
                "permission_level": fake_channel.permission_level,
                "permission_status": "need_apply",
                "expires_in": -math.inf,
                "doc_link": "",
            }
        ]

    def test_get_component_id_to_resource_id(self, fake_channel, faker):
        if not ComponentResourceBinding:
            return

        resource_id = faker.pyint()

        G(ComponentResourceBinding, component_id=fake_channel.id, resource_id=resource_id)

        manager = ComponentPermissionByEsbManager()
        result = manager._get_component_id_to_resource_id([fake_channel.id])
        assert result == {fake_channel.id: resource_id}


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
            "apigateway.biz.esb.permissions.get_component_doc_link",
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
                "unlimited",
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
            "apigateway.biz.esb.permissions.ComponentPermission.component_perm_required",
            new_callable=mocker.PropertyMock(return_value=params["component_perm_required"]),
        )
        if "expires_in" in params:
            mocker.patch(
                "apigateway.biz.esb.permissions.ComponentPermission.expires_in",
                new_callable=mocker.PropertyMock(return_value=params["expires_in"]),
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
            "apigateway.biz.esb.permissions.ComponentPermission.component_perm_required",
            new_callable=mocker.PropertyMock(return_value=params["component_perm_required"]),
        )

        if "component_permission_expires_in" in params:
            params["component_permission"] = AppComponentPermissionData(
                expires_in=params["component_permission_expires_in"]
            )

        mocked_component.update(params)

        perm = ComponentPermission.parse_obj(mocked_component)
        assert perm.expires_in == expected
