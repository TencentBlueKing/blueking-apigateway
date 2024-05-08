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

from apigateway.core.models import Gateway
from apigateway.iam.constants import UserRoleEnum
from apigateway.iam.handlers.grade_manager import IAMGradeManagerHandler
from apigateway.iam.handlers.user_group import IAMUserGroupHandler


class GatewayMemberHandler:
    group_handler = IAMUserGroupHandler()
    grade_manager_handler = IAMGradeManagerHandler()

    def add_member(self, gateway: Gateway, role: UserRoleEnum, username: str):
        """
        添加网关成员

        :param gateway: 网关
        :param role: 角色
        :param username: 用户 ID
        """
        if role == UserRoleEnum.MANAGER:
            self.grade_manager_handler.add_grade_manager_members(gateway.id, [username])

            maintainers = gateway.maintainers
            if username not in maintainers:
                maintainers.append(username)
                gateway.maintainers = maintainers
                gateway.save()

        if role == UserRoleEnum.DEVELOPER:
            developers = gateway.developers
            if username not in developers:
                developers.append(username)
                gateway.developers = developers
                gateway.save()

        self.group_handler.add_user_group_members(gateway.id, role, [username])

    def delete_member(self, gateway: Gateway, role: UserRoleEnum, username: str):
        """
        删除网关成员

        :param gateway: 网关
        :param role: 角色
        :param username: 用户 ID
        """
        if role == UserRoleEnum.MANAGER:
            self.grade_manager_handler.delete_grade_manager_members(gateway.id, [username])

            maintainers = gateway.maintainers
            if username in maintainers:
                maintainers.remove(username)
                gateway.maintainers = maintainers
                gateway.save()

        if role == UserRoleEnum.DEVELOPER:
            developers = gateway.developers
            if username in developers:
                developers.remove(username)
                gateway.developers = developers
                gateway.save()

        self.group_handler.delete_user_group_members(gateway.id, role, [username])
