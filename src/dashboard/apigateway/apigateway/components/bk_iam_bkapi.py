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
import logging
from operator import itemgetter
from typing import Any, Dict, List

from bkapi_client_core.apigateway.django_helper import get_client_by_username
from django.conf import settings

from apigateway.components.bkapi_client.bk_iam import Client
from apigateway.components.handler import RequestAPIHandler
from apigateway.components.utils import inject_accept_language

logger = logging.getLogger(__name__)


class BKIAMClient:
    """API 网关 bk-iam(权限中心) 相关接口"""

    def __init__(self):
        self._client = get_client_by_username(Client, username="admin")
        self._client.session.register_hook("request", inject_accept_language)
        self._request_handler = RequestAPIHandler("bk-iam")

    def create_grade_manager(
        self,
        name: str,
        description: str,
        members: List[str],
        authorization_scopes: List[dict],
    ) -> Dict[str, Any]:
        """
        在权限中心上为网关注册分级管理员

        :param name: 分级管理员名称
        :param description: 分级管理员描述
        :param members: 分级管理员成员列表
        :param authorization_scopes: 分级管理员可授权范围
        :returns: 分级管理员信息，例如：{"id": 12345}
        """
        data = {
            "name": name,
            "description": description,
            "members": members,
            "authorization_scopes": authorization_scopes,
            # 可授权的人员范围为公司任意人
            "subject_scopes": [
                {
                    "type": "*",
                    "id": "*",
                }
            ],
        }
        api_result, response = self._request_handler.call_api(
            self._client.api.v2_management_grade_manager_create,
            path_params={"system_id": settings.BK_IAM_SYSTEM_ID},
            data=data,
        )
        return self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def delete_grade_manager(self, grade_manager_id: int):
        """
        删除注册到权限中心的分级管理员

        :param grade_manager_id: 分级管理员 ID
        """
        api_result, response = self._request_handler.call_api(
            self._client.api.v2_management_delete_grade_manager,
            path_params={"system_id": settings.BK_IAM_SYSTEM_ID, "id": grade_manager_id},
        )
        return self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def fetch_grade_manager_members(self, grade_manager_id: int) -> List[str]:
        """
        获取某个分级管理员的成员列表

        :param grade_manager_id: 分级管理员 ID
        :returns: 分级管理员成员列表，例如：["user1", "user2"]
        """
        api_result, response = self._request_handler.call_api(
            self._client.api.management_grade_manager_members,
            path_params={"id": grade_manager_id},
        )
        return self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def add_grade_manager_members(self, grade_manager_id: int, members: List[str]):
        """
        向某个分级管理员添加成员（分级管理员没有过期时间）

        :param grade_manager_id: 分级管理员 ID
        :param members: 待添加成员名称列表
        """
        if not members:
            return None

        api_result, response = self._request_handler.call_api(
            self._client.api.management_add_grade_manager_members,
            path_params={"id": grade_manager_id},
            data={"members": members},
        )
        return self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def delete_grade_manager_members(self, grade_manager_id: int, members: List[str]):
        """
        删除某个分级管理员的成员

        :param grade_manager_id: 分级管理员 ID
        :param members: 待删除的成员名称列表
        """
        if not members:
            return None

        api_result, response = self._request_handler.call_api(
            self._client.api.management_delete_grade_manager_members,
            path_params={"id": grade_manager_id},
            params={"members": ",".join(members)},
        )
        return self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def create_user_groups(self, grade_manager_id: int, user_groups: List[dict]) -> List[int]:
        """
        创建用户组

        :param grade_manager_id: 分级管理员 ID
        :param groups: 需要创建的用户组列表
        :returns: 用户组 ID 列表，例如：[15, 16, 17]
        """
        api_result, response = self._request_handler.call_api(
            self._client.api.v2_management_grade_manager_create_groups,
            path_params={"system_id": settings.BK_IAM_SYSTEM_ID, "id": grade_manager_id},
            data={"groups": user_groups},
        )
        return self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def delete_user_groups(self, user_group_ids: List[int]):
        """
        删除指定的用户组

        :param user_group_ids: 用户组 ID 列表
        """
        for group_id in user_group_ids:
            api_result, response = self._request_handler.call_api(
                self._client.api.v2_management_grade_manager_delete_group,
                path_params={"system_id": settings.BK_IAM_SYSTEM_ID, "id": group_id},
                data={},
            )
            self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def fetch_user_group_members(self, user_group_id: int) -> List[int]:
        """
        获取某个用户组成员信息

        :param user_group_id: 用户组 ID
        :returns: 用户组成员列表，例如：["username1", "username2"]
        """
        api_result, response = self._request_handler.call_api(
            self._client.api.v2_management_group_members,
            path_params={"system_id": settings.BK_IAM_SYSTEM_ID, "id": user_group_id},
            # 全量查询；page 从 1 开始，page_size 设置一个较大数字，以便获取全量数据
            params={"page": 1, "page_size": 10000},
        )
        result_data = self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))
        return [user["id"] for user in result_data["results"]]

    def add_user_group_members(self, user_group_id: int, members: List[str], expired_at: int):
        """
        向某个用户组添加成员

        :param user_group_id: 用户组 ID
        :param members: 待添加成员名称列表
        :param expired_at: 过期时间，时间戳，单位秒
        """
        if not members:
            return None

        api_result, response = self._request_handler.call_api(
            self._client.api.v2_management_add_group_members,
            path_params={"system_id": settings.BK_IAM_SYSTEM_ID, "id": user_group_id},
            data={
                "members": [{"type": "user", "id": member} for member in members],
                "expired_at": expired_at,
            },
        )
        return self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def delete_user_group_members(self, user_group_id: int, members: List[str]):
        """
        删除某个用户组的成员

        :param user_group_id: 用户组 ID
        :param members: 待删除的成员名称列表
        """
        api_result, response = self._request_handler.call_api(
            self._client.api.v2_management_delete_group_members,
            path_params={"system_id": settings.BK_IAM_SYSTEM_ID, "id": user_group_id},
            params={
                "type": "user",
                "ids": ",".join(members),
            },
        )
        return self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))

    def grant_user_group_policies(self, user_group_id: int, authorization_scopes: List[Dict]):
        """
        为指定的用户组授权

        :param user_group_id: 用户组 ID
        :param authorization_scopes: 授权范围
        """
        for policies in authorization_scopes:
            api_result, response = self._request_handler.call_api(
                self._client.api.v2_management_groups_policies_grant,
                path_params={"system_id": settings.BK_IAM_SYSTEM_ID, "id": user_group_id},
                data=policies,
            )
            self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))
