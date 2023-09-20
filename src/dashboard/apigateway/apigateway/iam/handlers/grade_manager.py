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
from typing import List

from apigateway.components.bk_iam_bkapi import BKIAMClient
from apigateway.iam.constants import UserRoleEnum
from apigateway.iam.exceptions import IAMGradeManagerExistError, IAMGradeManagerNotExist
from apigateway.iam.handlers.authorization_scopes import AuthorizationScopes
from apigateway.iam.models import IAMGradeManager


class IAMGradeManagerHandler:
    def __init__(self):
        self._bk_iam_client = BKIAMClient()

    def create_grade_manager(self, gateway_id: int, gateway_name: str, members: List[str]):
        """
        在权限中心上为网关注册分级管理员，并保存网关和分级管理员的对应关系

        :param gateway_id: 网关 ID
        :param gateway_name: 网关名称
        :param members: 分级管理员成员列表
        """
        if IAMGradeManager.objects.filter(gateway_id=gateway_id).exists():
            raise IAMGradeManagerExistError(gateway_id=gateway_id)

        grade_manager_id = self._create_grade_manager(gateway_id, gateway_name, members)

        IAMGradeManager.objects.create(gateway_id=gateway_id, grade_manager_id=grade_manager_id)

    def _create_grade_manager(self, gateway_id: int, gateway_name: str, members: List[str]) -> int:
        name = f"API网关-{gateway_name}"
        description = f"API网关 ({gateway_name}) 分级管理员，拥有审批用户加入网关管理员/开发者/运营者用户组的权限。"

        authorization_scopes = AuthorizationScopes.get_scopes(UserRoleEnum.MANAGER, gateway_id, gateway_name)

        result = self._bk_iam_client.create_grade_manager(
            name=name,
            description=description,
            members=members,
            authorization_scopes=authorization_scopes,
        )
        return result["id"]

    def delete_grade_manager(self, gateway_id: int):
        """
        删除注册到权限中心的分级管理员，并删除网关和分级管理员的对应关系

        :param gateway_id: 网关 ID
        """
        grade_manager = IAMGradeManager.objects.filter(gateway_id=gateway_id).first()
        if not grade_manager:
            return

        self._bk_iam_client.delete_grade_manager(grade_manager.grade_manager_id)
        IAMGradeManager.objects.filter(gateway_id=gateway_id).delete()

    def sync_grade_manager_members(self, gateway_id: int, members: List[str]):
        """
        同步分级管理员成员，在指定成员列表中的人员将被添加，不在列表中的人员将被删除

        :param gateway_id: 网关 ID
        :param members: 待同步的成员列表
        """
        grade_manager_id = self._get_grade_manager_id(gateway_id)

        existed_members = self._bk_iam_client.fetch_grade_manager_members(grade_manager_id)
        add_members = set(members) - set(existed_members)
        delete_members = set(existed_members) - set(members)

        if add_members:
            self._bk_iam_client.add_grade_manager_members(grade_manager_id, list(add_members))

        if delete_members:
            self._bk_iam_client.delete_grade_manager_members(grade_manager_id, list(delete_members))

    def add_grade_manager_members(self, gateway_id: int, members: List[str]):
        """
        向某个分级管理员添加成员（分级管理员没有过期时间）

        :param gateway_id: 网关 ID
        :param members: 待添加成员名称列表
        """
        if not members:
            return

        grade_manager_id = self._get_grade_manager_id(gateway_id)

        self._bk_iam_client.add_grade_manager_members(grade_manager_id, members)

    def delete_grade_manager_members(self, gateway_id: int, members: List[str]):
        """
        删除某个分级管理员的成员

        :param gateway_id: 网关 ID
        :param members: 待删除的成员名称列表
        """
        if not members:
            return

        grade_manager_id = self._get_grade_manager_id(gateway_id)

        self._bk_iam_client.delete_grade_manager_members(grade_manager_id, members)

    def _get_grade_manager_id(self, gateway_id: int) -> int:
        try:
            grade_manager = IAMGradeManager.objects.get(gateway_id=gateway_id)
        except IAMGradeManager.DoesNotExist:
            raise IAMGradeManagerNotExist(gateway_id=gateway_id)

        return grade_manager.grade_manager_id
