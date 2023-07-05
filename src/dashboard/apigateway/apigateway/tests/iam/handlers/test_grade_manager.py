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

from apigateway.iam.exceptions import IAMGradeManagerExistError
from apigateway.iam.handlers.grade_manager import IAMGradeManagerHandler
from apigateway.iam.models import IAMGradeManager


class TestIAMGradeManagerHandler:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.handler = IAMGradeManagerHandler()

    def test_create_grade_manager(self, mocker, faker, fake_gateway):
        grade_manager_id = faker.pyint()
        mock_create_grade_manager = mocker.patch.object(
            self.handler._bk_iam_client,
            "create_grade_manager",
            return_value={"id": grade_manager_id},
        )

        self.handler.create_grade_manager(fake_gateway.id, fake_gateway.name, [])
        mock_create_grade_manager.assert_called_once()

        assert IAMGradeManager.objects.filter(gateway=fake_gateway, grade_manager_id=grade_manager_id).count() == 1

        # 分级管理员已创建
        with pytest.raises(IAMGradeManagerExistError):
            self.handler.create_grade_manager(fake_gateway.id, fake_gateway.name, [])

    def test_delete_grade_manager(self, mocker, faker, fake_gateway):
        mock_delete_grade_manager = mocker.patch.object(
            self.handler._bk_iam_client,
            "delete_grade_manager",
        )
        grade_manager = G(IAMGradeManager, gateway=fake_gateway, grade_manager_id=faker.pyint())

        self.handler.delete_grade_manager(fake_gateway.id)
        mock_delete_grade_manager.assert_called_once_with(grade_manager.grade_manager_id)
        assert IAMGradeManager.objects.filter(gateway=fake_gateway).exists() is False

        self.handler.delete_grade_manager(fake_gateway.id)
        mock_delete_grade_manager.assert_called_once()

    def test_sync_grade_manager_members(self, mocker, faker, fake_gateway):
        mocker.patch.object(
            self.handler._bk_iam_client,
            "fetch_grade_manager_members",
            return_value=["user1", "user2"],
        )
        mock_add_grade_manager_members = mocker.patch.object(self.handler._bk_iam_client, "add_grade_manager_members")
        mock_delete_grade_manager_members = mocker.patch.object(
            self.handler._bk_iam_client, "delete_grade_manager_members"
        )
        grade_manager = G(IAMGradeManager, gateway=fake_gateway, grade_manager_id=faker.pyint())

        self.handler.sync_grade_manager_members(fake_gateway.id, ["user2", "user3"])

        mock_add_grade_manager_members.assert_called_once_with(grade_manager.grade_manager_id, ["user3"])
        mock_delete_grade_manager_members.assert_called_once_with(grade_manager.grade_manager_id, ["user1"])

    def test_add_grade_manager_members(self, mocker, faker, fake_gateway):
        mock_add_grade_manager_members = mocker.patch.object(self.handler._bk_iam_client, "add_grade_manager_members")
        grade_manager = G(IAMGradeManager, gateway=fake_gateway, grade_manager_id=faker.pyint())

        self.handler.add_grade_manager_members(fake_gateway.id, [])
        mock_add_grade_manager_members.assert_not_called()

        self.handler.add_grade_manager_members(fake_gateway.id, ["user1", "user2"])
        mock_add_grade_manager_members.assert_called_once_with(grade_manager.grade_manager_id, ["user1", "user2"])

    def test_delete_grade_manager_members(self, mocker, faker, fake_gateway):
        mock_delete_grade_manager_members = mocker.patch.object(
            self.handler._bk_iam_client, "delete_grade_manager_members"
        )
        grade_manager = G(IAMGradeManager, gateway=fake_gateway, grade_manager_id=faker.pyint())

        self.handler.delete_grade_manager_members(fake_gateway.id, [])
        mock_delete_grade_manager_members.assert_not_called()

        self.handler.delete_grade_manager_members(fake_gateway.id, ["user1", "user2"])
        mock_delete_grade_manager_members.assert_called_once_with(grade_manager.grade_manager_id, ["user1", "user2"])
