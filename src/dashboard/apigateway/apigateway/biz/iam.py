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


class IAMHandler:
    @classmethod
    def register_grade_manager_and_builtin_user_groups(cls, gateway: Gateway):
        """
        在权限中心上为网关注册分级管理员，并创建 3 个用户组（管理员、开发者、运营者）
        - 网关创建者，将添加到分级管理员及管理员用户组中
        """
        grade_manager_handler = IAMGradeManagerHandler()
        members = gateway.maintainers

        # 1. 创建分级管理员，创建者为分级管理员的成员
        grade_manager_handler.create_grade_manager(gateway.id, gateway.name, members)

        # 2. 创建 3 个用户组
        user_group_handler = IAMUserGroupHandler()
        user_group_handler.create_builtin_user_groups(gateway.id, gateway.name)

        # 3. 为网关下的用户组授权
        user_group_handler.grant_user_group_policies(gateway.id, gateway.name)

        # 4. 将创建者添加为“管理员”用户组成员
        user_group_handler.add_user_group_members(gateway.id, UserRoleEnum.MANAGER, members)

    @classmethod
    def delete_grade_manager_and_builtin_user_groups(cls, gateway_id: int):
        """在权限中心上，删除网关的分级管理员及内建的 3 个用户组"""
        # 1. 删除用户组
        user_group_handler = IAMUserGroupHandler()
        user_group_handler.delete_user_groups(gateway_id)

        # 2. 删除分级管理员
        grade_manager_handler = IAMGradeManagerHandler()
        grade_manager_handler.delete_grade_manager(gateway_id)
