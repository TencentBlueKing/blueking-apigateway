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
from unittest import mock

import pytest
from ddf import G

from components.bk.apis.esb.get_components import GetComponents
from esb.bkcore.constants import PermissionLevelEnum
from esb.bkcore.models import ESBChannel, System

pytestmark = pytest.mark.django_db


class TestGetComponents:
    def test_handle(self, faker):
        system = G(System)
        channel = G(
            ESBChannel,
            system=system,
            is_public=True,
            permission_level=PermissionLevelEnum.UNLIMITED.value,
        )

        component = GetComponents()
        result = component.invoke(
            kwargs={
                "system_name": system.name,
                "searched_app_code": faker.unique.pystr(),
            }
        )
        assert len(result["data"]) == 1

    @pytest.mark.parametrize(
        "mock_component_permission_required, mock_has_permission, bk_app_code, expected",
        [
            (
                False,
                None,
                "",
                True,
            ),
            (
                True,
                True,
                "test",
                True,
            ),
            (
                True,
                False,
                "test",
                False,
            ),
            (
                True,
                None,
                "",
                False,
            ),
        ],
    )
    def test_has_component_permission(
        self,
        mocker,
        mock_component_permission_required,
        mock_has_permission,
        bk_app_code,
        expected,
    ):
        channel = G(ESBChannel)

        mocker.patch(
            "components.bk.apis.esb.get_components.ESBChannel.component_permission_required",
            new_callable=mock.PropertyMock(return_value=mock_component_permission_required),
        )
        mocker.patch(
            "components.bk.apis.esb.get_components.AppComponentPermission.objects.has_permission",
            return_value=mock_has_permission,
        )

        component = GetComponents()
        result = component._has_component_permission(channel, bk_app_code)
        assert result == expected
