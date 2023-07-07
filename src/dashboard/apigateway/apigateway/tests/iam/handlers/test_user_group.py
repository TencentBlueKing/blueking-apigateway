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
from ddf import G

from apigateway.iam.constants import GATEWAY_DEFAULT_ROLES, NEVER_EXPIRE_TIMESTAMP, UserRoleEnum
from apigateway.iam.handlers.user_group import IAMUserGroupHandler
from apigateway.iam.models import IAMGradeManager, IAMUserGroup


class TestIAMUserGroupHandler:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.handler = IAMUserGroupHandler()

    def test_create_builtin_user_groups(self, mocker, fake_gateway):
        G(IAMGradeManager, gateway=fake_gateway)
        mock_create_user_groups = mocker.patch.object(
            self.handler._bk_iam_client,
            "create_user_groups",
            return_value=list(range(len(GATEWAY_DEFAULT_ROLES))),
        )

        self.handler.create_builtin_user_groups(fake_gateway.id, fake_gateway.name)
        mock_create_user_groups.assert_called_once()

        assert IAMUserGroup.objects.filter(gateway=fake_gateway).count() == len(GATEWAY_DEFAULT_ROLES)

    def test_delete_user_groups(self, mocker, fake_gateway):
        mock_delete_user_groups = mocker.patch.object(
            self.handler._bk_iam_client,
            "delete_user_groups",
        )

        self.handler.delete_user_groups(fake_gateway.id)
        mock_delete_user_groups.assert_not_called()

        user_group = G(IAMUserGroup, gateway=fake_gateway)
        self.handler.delete_user_groups(fake_gateway.id)
        mock_delete_user_groups.assert_called_once_with([user_group.id])

    def test_sync_user_group_members(self, mocker, fake_gateway):
        mocker.patch.object(
            self.handler._bk_iam_client,
            "fetch_user_group_members",
            return_value=["user1", "user2"],
        )
        mock_add_user_group_members = mocker.patch.object(self.handler._bk_iam_client, "add_user_group_members")
        mock_delete_user_group_members = mocker.patch.object(self.handler._bk_iam_client, "delete_user_group_members")
        user_group = G(IAMUserGroup, gateway=fake_gateway, role=UserRoleEnum.MANAGER.value)

        self.handler.sync_user_group_members(fake_gateway.id, UserRoleEnum.MANAGER, ["user2", "user3"])

        mock_add_user_group_members.assert_called_once_with(
            user_group.user_group_id, ["user3"], NEVER_EXPIRE_TIMESTAMP
        )
        mock_delete_user_group_members.assert_called_once_with(user_group.user_group_id, ["user1"])

    def test_fetch_user_group_members(self, mocker, fake_gateway):
        mocker.patch.object(
            self.handler._bk_iam_client,
            "fetch_user_group_members",
            return_value=["user1", "user2"],
        )

        G(IAMUserGroup, gateway=fake_gateway, role=UserRoleEnum.MANAGER.value)
        result = self.handler.fetch_user_group_members(fake_gateway.id, UserRoleEnum.MANAGER)
        assert result == ["user1", "user2"]

    def test_add_user_group_members(self, mocker, fake_gateway):
        mock_add_user_group_members = mocker.patch.object(self.handler._bk_iam_client, "add_user_group_members")
        user_group = G(IAMUserGroup, gateway=fake_gateway, role=UserRoleEnum.MANAGER.value)

        self.handler.add_user_group_members(fake_gateway.id, UserRoleEnum.MANAGER, [])
        mock_add_user_group_members.assert_not_called()

        self.handler.add_user_group_members(fake_gateway.id, UserRoleEnum.MANAGER, ["user1", "user2"])
        mock_add_user_group_members.assert_called_once_with(
            user_group.user_group_id, ["user1", "user2"], NEVER_EXPIRE_TIMESTAMP
        )

    def test_delete_user_group_members(self, mocker, fake_gateway):
        mock_delete_user_group_members = mocker.patch.object(self.handler._bk_iam_client, "delete_user_group_members")
        user_group = G(IAMUserGroup, gateway=fake_gateway, role=UserRoleEnum.MANAGER.value)

        self.handler.delete_user_group_members(fake_gateway.id, UserRoleEnum.MANAGER, [])
        mock_delete_user_group_members.assert_not_called()

        self.handler.delete_user_group_members(fake_gateway.id, UserRoleEnum.MANAGER, ["user1", "user2"])
        mock_delete_user_group_members.assert_called_once_with(user_group.user_group_id, ["user1", "user2"])

    def test_grant_user_group_policies(self, mocker, fake_gateway):
        mock_grant_user_group_policies = mocker.patch.object(self.handler._bk_iam_client, "grant_user_group_policies")
        G(IAMUserGroup, gateway=fake_gateway, role=UserRoleEnum.MANAGER.value)
        G(IAMUserGroup, gateway=fake_gateway, role=UserRoleEnum.DEVELOPER.value)

        self.handler.grant_user_group_policies(fake_gateway.id, fake_gateway.name)
        assert mock_grant_user_group_policies.call_count == 2
