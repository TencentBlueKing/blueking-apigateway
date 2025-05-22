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
from typing import Dict, List, Tuple

from django.db import transaction

from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission
from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import NeverExpiresTime

from .released_resource import ReleasedResourceData, ReleasedResourceHandler
from .released_resource_doc import ReleasedResourceDocHandler
from .released_resource_doc.generators import DocGenerator
from .resource_doc import ResourceDocHandler
from .resource_label import ResourceLabelHandler

logger = logging.getLogger(__name__)


class MCPServerHandler:
    @staticmethod
    def get_tools_resources_and_labels(
        gateway_id: int, stage_name: str, resource_names: List[str]
    ) -> Tuple[List[ReleasedResourceData], Dict[int, List]]:
        tool_resource_names = set(resource_names)

        stage_released_resources = ReleasedResourceHandler.get_public_released_resource_data_list(
            gateway_id,
            stage_name,
            False,
        )

        # only need the resources in the resource_names
        tool_resources: List[ReleasedResourceData] = [
            r for r in stage_released_resources if r.name in tool_resource_names
        ]

        label_ids = list({label_id for resource in tool_resources for label_id in resource.gateway_labels})
        labels = ResourceLabelHandler.get_labels_by_ids(label_ids)

        return tool_resources, labels

    @staticmethod
    def get_tool_doc(gateway_id: int, stage_name: str, tool_name: str) -> Dict:
        resource_data, doc_data = ReleasedResourceDocHandler.get_released_resource_doc_data(
            gateway_id=gateway_id,
            stage_name=stage_name,
            resource_name=tool_name,
            language=ResourceDocHandler.get_doc_language(get_current_language_code()),
        )
        if not (resource_data and doc_data):
            raise error_codes.NOT_FOUND

        gateway = Gateway.objects.get(id=gateway_id)

        generator = DocGenerator(
            gateway=gateway,
            stage_name=stage_name,
            resource_data=resource_data,
            doc_data=doc_data,
            language=ResourceDocHandler.get_doc_language(get_current_language_code()),
        )

        return generator.get_doc()

    @staticmethod
    def _virtual_app_code_prefix(mcp_server_id: int) -> str:
        return f"v_mcp_{mcp_server_id}_"

    @staticmethod
    def _virtual_app_code(mcp_server_id: int, app_code: str) -> str:
        return f"v_mcp_{mcp_server_id}_{app_code}"

    @staticmethod
    def _cleanup_all_resource_permissions(gateway_id: int, mcp_server_id: int):
        """清理 mcp_server 的所有权限
        特征：bk_app_code 以 v_mcp_{mcp_server_id}_ 开头
        只有虚拟 app_code 能带下划线

        Args:
            mcp_server_id (int): mcp_server 的 id
        """
        AppResourcePermission.objects.filter(
            gateway_id=gateway_id, bk_app_code__startswith=MCPServerHandler._virtual_app_code_prefix(mcp_server_id)
        ).delete()

    @staticmethod
    @transaction.atomic
    def sync_permissions(mcp_server_id: int) -> None:
        """同步 MCPServer 的权限
        Args:
            mcp_server_id (int): mcp_server 的 id
        """
        mcp_server = MCPServer.objects.get(id=mcp_server_id)

        # 1. fetch the app codes in mcp_server_app_permission
        app_codes = MCPServerAppPermission.objects.filter(mcp_server=mcp_server).values_list("bk_app_code", flat=True)
        if not app_codes:
            logger.debug("no app_codes, cleanup the permissions of the mcp_server %d", mcp_server_id)
            # if no app_codes, cleanup the permissions of the mcp_server
            MCPServerHandler._cleanup_all_resource_permissions(
                gateway_id=mcp_server.gateway_id,
                mcp_server_id=mcp_server_id,
            )
            return

        # 2. check the resource names, and get the resource_ids
        resource_names = mcp_server.resource_names
        if not resource_names:
            logger.debug("no resource_names, skip sync the permissions of the mcp_server %d", mcp_server_id)
            return
        resource_ids = Resource.objects.filter(gateway_id=mcp_server.gateway_id, name__in=resource_names).values_list(
            "id", flat=True
        )

        # 3. sync the permission
        newest_virtual_app_code_resource_id_set = {
            (
                MCPServerHandler._virtual_app_code(mcp_server_id, app_code),
                resource_id,
            )
            for app_code in app_codes
            for resource_id in resource_ids
        }

        # sync the permission
        current_permissions = AppResourcePermission.objects.filter(
            bk_app_code__startswith=MCPServerHandler._virtual_app_code_prefix(mcp_server_id)
        )
        current_virtual_app_code_resource_id_set = {
            (permission.bk_app_code, permission.resource_id) for permission in current_permissions
        }

        # 3.1 if no change, return
        if newest_virtual_app_code_resource_id_set == current_virtual_app_code_resource_id_set:
            logger.debug("no change, skip sync the permissions of the mcp_server %d", mcp_server_id)
            return

        # 3.2 check to add
        to_add_virtual_app_code_resource_id_set = (
            newest_virtual_app_code_resource_id_set - current_virtual_app_code_resource_id_set
        )
        to_add: List[AppResourcePermission] = []
        for virtual_app_code, resource_id in to_add_virtual_app_code_resource_id_set:
            to_add.append(
                AppResourcePermission(
                    bk_app_code=virtual_app_code,
                    gateway=mcp_server.gateway,
                    resource_id=resource_id,
                    expires=NeverExpiresTime.time,
                    grant_type=GrantTypeEnum.SYNC.value,
                )
            )

        # 3.3 check to delete
        to_delete_virtual_app_code_resource_id_set = (
            current_virtual_app_code_resource_id_set - newest_virtual_app_code_resource_id_set
        )
        to_delete: List[int] = []
        for permission in current_permissions:
            if (permission.bk_app_code, permission.resource_id) in to_delete_virtual_app_code_resource_id_set:
                to_delete.append(permission.id)
                continue

        # 3.4 add and delete
        logger.debug("add %d permissions, delete %d permissions", len(to_add), len(to_delete))
        if to_add:
            AppResourcePermission.objects.bulk_create(to_add)
        if to_delete:
            AppResourcePermission.objects.filter(id__in=to_delete).delete()
