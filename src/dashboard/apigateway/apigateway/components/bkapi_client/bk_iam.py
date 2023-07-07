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
from bkapi_client_core.apigateway import APIGatewayClient, Operation, OperationGroup, bind_property


class Group(OperationGroup):
    # bkapi resource management_grade_managers_list
    # 查询分级管理员列表
    management_grade_managers_list = bind_property(
        Operation,
        name="management_grade_managers_list",
        method="GET",
        path="/api/v1/open/management/grade_managers/",
    )

    # bkapi resource v2_management_grade_manager_create
    # 创建分级管理员
    v2_management_grade_manager_create = bind_property(
        Operation,
        name="v2_management_grade_manager_create",
        method="POST",
        path="/api/v2/open/management/systems/{system_id}/grade_managers/",
    )

    # bkapi resource v2_management_delete_grade_manager
    # 删除分级管理员
    v2_management_delete_grade_manager = bind_property(
        Operation,
        name="v2_management_delete_grade_manager",
        method="DELETE",
        path="/api/v2/open/management/systems/{system_id}/grade_managers/{id}/",
    )

    # bkapi resource management_grade_manager_members
    # 分级管理员成员列表
    management_grade_manager_members = bind_property(
        Operation,
        name="management_grade_manager_members",
        method="GET",
        path="/api/v1/open/management/grade_managers/{id}/members/",
    )

    # bkapi resource management_add_grade_manager_members
    # 批量添加分级管理员成员
    management_add_grade_manager_members = bind_property(
        Operation,
        name="management_add_grade_manager_members",
        method="POST",
        path="/api/v1/open/management/grade_managers/{id}/members/",
    )

    # bkapi resource management_delete_grade_manager_members
    # 批量删除分级管理员成员
    management_delete_grade_manager_members = bind_property(
        Operation,
        name="management_delete_grade_manager_members",
        method="DELETE",
        path="/api/v1/open/management/grade_managers/{id}/members/",
    )

    # bkapi resource v2_management_grade_manager_create_groups
    # 分级管理员批量创建用户组
    v2_management_grade_manager_create_groups = bind_property(
        Operation,
        name="v2_management_grade_manager_create_groups",
        method="POST",
        path="/api/v2/open/management/systems/{system_id}/grade_managers/{id}/groups/",
    )

    # bkapi resource v2_management_grade_manager_delete_group
    # 分级管理员删除用户组
    v2_management_grade_manager_delete_group = bind_property(
        Operation,
        name="v2_management_grade_manager_delete_group",
        method="DELETE",
        path="/api/v2/open/management/systems/{system_id}/groups/{id}/",
    )

    # bkapi resource v2_management_group_members
    # 用户组成员列表
    v2_management_group_members = bind_property(
        Operation,
        name="v2_management_group_members",
        method="GET",
        path="/api/v2/open/management/systems/{system_id}/groups/{id}/members/",
    )

    # bkapi resource v2_management_add_group_members
    # 用户组添加成员
    v2_management_add_group_members = bind_property(
        Operation,
        name="v2_management_add_group_members",
        method="POST",
        path="/api/v2/open/management/systems/{system_id}/groups/{id}/members/",
    )

    # bkapi resource v2_management_delete_group_members
    # 用户组删除成员
    v2_management_delete_group_members = bind_property(
        Operation,
        name="v2_management_delete_group_members",
        method="DELETE",
        path="/api/v2/open/management/systems/{system_id}/groups/{id}/members/",
    )

    # bkapi resource v2_management_groups_policies_grant
    # 用户组授权
    v2_management_groups_policies_grant = bind_property(
        Operation,
        name="v2_management_groups_policies_grant",
        method="POST",
        path="/api/v2/open/management/systems/{system_id}/groups/{id}/policies/",
    )


class Client(APIGatewayClient):
    """Bkapi bk_iam client"""

    _api_name = "bk-iam"

    api = bind_property(Group, name="api")
