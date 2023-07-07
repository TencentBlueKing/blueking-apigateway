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

from django.utils.translation import gettext as _

from apigateway.components.bk_iam_bkapi import BKIAMClient
from apigateway.iam.constants import GATEWAY_DEFAULT_ROLES, NEVER_EXPIRE_TIMESTAMP, UserRoleEnum
from apigateway.iam.exceptions import IAMGradeManagerNotExist, IAMUserRoleNotExist
from apigateway.iam.handlers.authorization_scopes import AuthorizationScopes
from apigateway.iam.models import IAMGradeManager, IAMUserGroup


class IAMUserGroupHandler:
    def __init__(self):
        self._bk_iam_client = BKIAMClient()

    def create_builtin_user_groups(self, gateway_id: int, gateway_name: str):
        """
        为网关创建内建用户组（默认 3 个：管理员，开发者，运营者），并记录网关和用户组的对应关系

        :param gateway_id: 网关 ID
        :param gateway_name: 网关名称
        """
        grade_manager_id = self._get_grade_manager_id(gateway_id)

        user_groups = [
            {
                "name": self._generate_user_group_name(role, gateway_name),
                "description": self._generate_user_group_description(role, gateway_name),
                # 只读用户组，设置为 True 后，分级管理员无法在权限中心产品上删除该用户组
                "readonly": True,
            }
            for role in GATEWAY_DEFAULT_ROLES
        ]
        result = self._bk_iam_client.create_user_groups(grade_manager_id, user_groups)

        # 记录用户分组信息
        IAMUserGroup.objects.bulk_create(
            [
                IAMUserGroup(gateway_id=gateway_id, role=role.value, user_group_id=user_group_id)
                for user_group_id, role in zip(result, GATEWAY_DEFAULT_ROLES)
            ]
        )

    def _generate_user_group_name(self, role: UserRoleEnum, gateway_name: str) -> str:
        if role == UserRoleEnum.MANAGER:
            return _("API网关-{gateway_name}-管理员").format(gateway_name=gateway_name)
        elif role == UserRoleEnum.DEVELOPER:
            return _("API网关-{gateway_name}-开发者").format(gateway_name=gateway_name)
        elif role == UserRoleEnum.OPERATOR:
            return _("API网关-{gateway_name}-运营者").format(gateway_name=gateway_name)

        raise ValueError(f"unsupported role: {role.value}")

    def _generate_user_group_description(self, role: UserRoleEnum, gateway_name: str) -> str:
        if role == UserRoleEnum.MANAGER:
            return _("API网关 ({gateway_name}) 管理员，拥有网关的全部权限。").format(gateway_name=gateway_name)
        elif role == UserRoleEnum.DEVELOPER:
            return _("API网关 ({gateway_name}) 开发者，拥有网关的开发权限，如管理资源，查看日志，在线测试等。").format(gateway_name=gateway_name)
        elif role == UserRoleEnum.OPERATOR:
            return _("API网关 ({gateway_name}) 运营者，拥有网关的运营权限，如管理权限，查看日志等。").format(gateway_name=gateway_name)

        raise ValueError(f"unsupported role: {role.value}")

    def delete_user_groups(self, gateway_id: int):
        """
        删除注册到权限中心的用户组，并删除网关和用户组的对应关系

        :param gateway_id: 网关 ID
        """
        user_group_ids = IAMUserGroup.objects.filter(gateway_id=gateway_id).values_list("user_group_id", flat=True)
        if not user_group_ids:
            return

        self._bk_iam_client.delete_user_groups(list(user_group_ids))

        IAMUserGroup.objects.filter(gateway_id=gateway_id).delete()

    def sync_user_group_members(self, gateway_id: int, role: UserRoleEnum, members: List[str]):
        """
        同步网关指定角色的用户组成员，在指定成员列表中的人员将被添加，不在列表中的人员将被删除

        :param gateway_id: 网关 ID
        :param role: 用户组角色
        :param members: 用户组成员
        """
        user_group_id = self._get_user_group_id(gateway_id, role)

        existed_members = self._bk_iam_client.fetch_user_group_members(user_group_id)
        add_members = set(members) - set(existed_members)
        delete_members = set(existed_members) - set(members)

        if add_members:
            self._bk_iam_client.add_user_group_members(user_group_id, list(add_members), NEVER_EXPIRE_TIMESTAMP)

        if delete_members:
            self._bk_iam_client.delete_user_group_members(user_group_id, list(delete_members))

    def fetch_user_group_members(self, gateway_id: int, role: UserRoleEnum):
        """
        获取网关指定角色的用户组成员列表

        :param gateway_id: 网关 ID
        :param role: 用户组角色
        :returns: 用户组成员列表，例如：["username1", "username2"]
        """
        user_group_id = self._get_user_group_id(gateway_id, role)
        return self._bk_iam_client.fetch_user_group_members(user_group_id)

    def add_user_group_members(self, gateway_id: int, role: UserRoleEnum, members: List[str]):
        """
        添加网关指定角色的用户组成员

        :param gateway_id: 网关 ID
        :param role: 用户组角色
        :param members: 用户组成员
        """
        if not members:
            return

        user_group_id = self._get_user_group_id(gateway_id, role)
        return self._bk_iam_client.add_user_group_members(user_group_id, members, NEVER_EXPIRE_TIMESTAMP)

    def delete_user_group_members(self, gateway_id: int, role: UserRoleEnum, members: List[str]):
        """
        删除网关指定角色的用户组成员

        :param gateway_id: 网关 ID
        :param role: 用户组角色
        :param members: 用户组成员
        """
        if not members:
            return

        user_group_id = self._get_user_group_id(gateway_id, role)
        self._bk_iam_client.delete_user_group_members(user_group_id, members)

    def grant_user_group_policies(self, gateway_id: int, gateway_name: str):
        """
        为网关下所有用户组添加授权

        :param gateway_id: 网关 ID
        :param gateway_name: 网关名称
        """
        for user_group in IAMUserGroup.objects.filter(gateway_id=gateway_id):
            authorization_scopes = AuthorizationScopes.get_scopes(
                UserRoleEnum(user_group.role), gateway_id, gateway_name
            )
            self._bk_iam_client.grant_user_group_policies(user_group.user_group_id, authorization_scopes)

    def _get_grade_manager_id(self, gateway_id: int) -> int:
        try:
            grade_manager = IAMGradeManager.objects.get(gateway_id=gateway_id)
        except IAMGradeManager.DoesNotExist:
            raise IAMGradeManagerNotExist(gateway_id)

        return grade_manager.grade_manager_id

    def _get_user_group_id(self, gateway_id: int, role: UserRoleEnum) -> int:
        try:
            user_group = IAMUserGroup.objects.get(gateway_id=gateway_id, role=role.value)
        except IAMUserGroup.DoesNotExist:
            raise IAMUserRoleNotExist(gateway_id, role)

        return user_group.user_group_id
