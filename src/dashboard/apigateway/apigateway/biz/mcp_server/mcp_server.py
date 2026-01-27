#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import base64
import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyExpireDaysEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerExtendTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermission,
    MCPServerAppPermissionApply,
    MCPServerExtend,
)
from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.biz.released_resource import ReleasedResourceData, ReleasedResourceHandler
from apigateway.biz.released_resource_doc import ReleasedResourceDocHandler
from apigateway.biz.released_resource_doc.generators import DocGenerator
from apigateway.biz.resource import ResourceLabelHandler
from apigateway.biz.resource_doc import ResourceDocHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.components import bkaidev
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, Resource
from apigateway.service.mcp.mcp_server import build_mcp_server_url
from apigateway.utils.time import NeverExpiresTime, now_datetime

logger = logging.getLogger(__name__)


class MCPServerHandler:
    @staticmethod
    def get_tools_resources_and_labels(
        gateway_id: int, stage_name: str, resource_names: List[str]
    ) -> Tuple[List[ReleasedResourceData], Dict[int, List]]:
        """获取工具资源列表、标签

        Args:
            gateway_id: 网关 ID
            stage_name: 环境名称
            resource_names: 资源名称列表，支持 resource_name@tool_name 格式

        Returns:
            (tool_resources, labels) 元组
            - tool_resources: 资源数据列表
            - labels: 资源标签映射
        """
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
    def get_valid_resource_names(gateway_id: int, stage_id: int) -> Set[str]:
        release = Release.objects.filter(
            gateway_id=gateway_id,
            stage_id=stage_id,
            stage__status=StageStatusEnum.ACTIVE.value,
        ).first()
        if not release:
            raise error_codes.FAILED_PRECONDITION.format(
                _("环境已下架或者未发布，请先发布资源到该环境，再更新 MCPServer。"), replace=True
            )
        return ResourceVersionHandler.get_resource_names_set(release.resource_version.id)

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
            with_common_request_params_part=False,
        )

        data = generator.get_doc()
        resource_version_id = (
            Release.objects.filter(
                gateway_id=gateway_id,
                stage__name=stage_name,
            )
            .values_list("resource_version_id", flat=True)
            .first()
        )
        # 查询哪些资源有配置对应的 schema
        schema = ResourceVersionHandler.get_resource_schema(
            resource_version_id,
            resource_data.id,
        )
        data["schema"] = schema

        return data

    @staticmethod
    def _virtual_app_code_prefix(mcp_server_id: int) -> str:
        return f"v_mcp_{mcp_server_id}_"

    @staticmethod
    def get_mcp_server_name(gateway_name: str, stage_name: str, name: str) -> str:
        return f"{gateway_name}-{stage_name}-{name}"

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

    @staticmethod
    def disable_servers(gateway_id: int, stage_id: int = 0) -> None:
        """set the status of the servers to inactive
        e.g. gateway inactivated, stage offline, etc.

        Args:
            gateway_id (int): the id of the gateway
            stage_id (int, optional): the id of the stage. Defaults to 0.
        """
        queryset = MCPServer.objects.filter(gateway_id=gateway_id)
        if stage_id:
            queryset = queryset.filter(stage_id=stage_id)

        queryset.update(status=MCPServerStatusEnum.INACTIVE.value)

    # ========== Prompts 相关方法 ==========

    @staticmethod
    def fetch_remote_prompts(user_credentials: UserCredentials) -> List[Dict[str, Any]]:
        """从 BKAIDev 平台获取 prompts 列表

        Args:
            user_credentials: 用于平台鉴权

        Returns:
            prompts 列表
        """
        return bkaidev.fetch_prompts_list(user_credentials=user_credentials)

    @staticmethod
    def get_prompts(mcp_server_id: int) -> List[Dict[str, Any]]:
        """获取 MCPServer 已关联的 prompts 配置

        Args:
            mcp_server_id: MCPServer ID

        Returns:
            prompts 列表
        """
        extend = MCPServerExtend.objects.filter(
            mcp_server_id=mcp_server_id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        ).first()

        if not extend or not extend.content:
            return []

        try:
            return json.loads(extend.content)
        except json.JSONDecodeError:
            logger.exception("Failed to parse prompts content for mcp_server_id=%s", mcp_server_id)
            return []

    @staticmethod
    def save_prompts(mcp_server_id: int, prompts: List[Dict[str, Any]], username: str) -> None:
        """保存 MCPServer 的 prompts 配置

        Args:
            mcp_server_id: MCPServer ID
            prompts: prompts 列表
            username: 操作用户名
        """
        content = json.dumps(prompts, ensure_ascii=False)

        extend, created = MCPServerExtend.objects.get_or_create(
            mcp_server_id=mcp_server_id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            defaults={
                "content": content,
                "created_by": username,
                "updated_by": username,
            },
        )

        if not created:
            extend.content = content
            extend.updated_by = username
            extend.save(update_fields=["content", "updated_by"])

    @staticmethod
    def delete_prompts(mcp_server_id: int) -> None:
        """删除 MCPServer 的 prompts 配置

        Args:
            mcp_server_id: MCPServer ID
        """
        MCPServerExtend.objects.filter(
            mcp_server_id=mcp_server_id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        ).delete()

    @staticmethod
    def get_prompts_count(mcp_server_id: int) -> int:
        """获取 MCPServer 已关联的 prompts 数量

        Args:
            mcp_server_id: MCPServer ID

        Returns:
            prompts 数量
        """
        prompts = MCPServerHandler.get_prompts(mcp_server_id)
        return len(prompts)

    @staticmethod
    def get_prompts_count_map(mcp_server_ids: List[int]) -> Dict[int, int]:
        """批量获取 MCPServer 的 prompts 数量

        Args:
            mcp_server_ids: MCPServer ID 列表

        Returns:
            {mcp_server_id: prompts_count} 映射
        """
        extends = MCPServerExtend.objects.filter(
            mcp_server_id__in=mcp_server_ids,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )

        prompts_count_map: Dict[int, int] = dict.fromkeys(mcp_server_ids, 0)
        for extend in extends:
            if extend.content:
                try:
                    prompts = json.loads(extend.content)
                    prompts_count_map[extend.mcp_server_id] = len(prompts)
                except json.JSONDecodeError:
                    logger.exception("Failed to parse prompts content for mcp_server_id=%s", extend.mcp_server_id)

        return prompts_count_map

    @staticmethod
    def get_user_custom_doc(mcp_server_id: int) -> str:
        """获取 MCPServer 的用户自定义文档

        Args:
            mcp_server_id: MCPServer ID

        Returns:
            用户自定义文档内容，如果不存在则返回空字符串
        """
        extend = MCPServerExtend.objects.filter(
            mcp_server_id=mcp_server_id,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
        ).first()

        if not extend or not extend.content:
            return ""

        return extend.content

    @staticmethod
    def _build_cursor_install_url(name: str, mcp_url: str) -> str:
        """
        生成 Cursor 一键配置 URL

        格式: cursor://anysphere.cursor-deeplink/mcp/install?name=<NAME>&config=<BASE64_CONFIG>
        """
        config = {
            "url": mcp_url,
            "headers": {
                "X-Bkapi-Authorization": json.dumps(
                    {
                        "bk_app_code": "your_app_code",
                        "bk_app_secret": "your_app_secret",
                        settings.BK_LOGIN_TICKET_KEY: "your_ticket",
                    }
                )
            },
        }
        config_json = json.dumps(config)
        config_base64 = base64.b64encode(config_json.encode()).decode()
        return f"cursor://anysphere.cursor-deeplink/mcp/install?name={quote(name)}&config={quote(config_base64)}"

    @staticmethod
    def build_agent_client_configs(instance: MCPServer) -> List[Dict[str, Any]]:
        """
        构建 MCPServer 的 Agent 客户端配置列表

        Args:
            instance: MCPServer 实例

        Returns:
            配置列表，每个配置包含 name, display_name, content, install_url
        """
        language_code = get_current_language_code()
        mcp_url = build_mcp_server_url(instance.name, instance.protocol_type)
        configs = []

        for client in settings.MCP_CONFIG_AGENT_CLIENTS:
            template_name = f"mcp_server/{language_code}/config/{client['name']}.md"

            # 根据 protocol_type 和客户端类型确定 transport_type
            if instance.protocol_type == "streamable_http":
                transport_type = "streamable-http" if client["name"] == "codebuddy" else "http"
            else:
                transport_type = "sse"

            # 构建模板上下文
            context = {
                "name": instance.name,
                "url": mcp_url,
                "description": instance.description,
                "bk_login_ticket_key": settings.BK_LOGIN_TICKET_KEY,
                "transport_type": transport_type,
            }

            # AIDev 需要额外的创建链接
            if client["name"] == "aidev":
                context["aidev_agent_create_url"] = settings.AIDEV_AGENT_CREATE_URL

            content = render_to_string(template_name, context=context)

            # 生成一键配置 URL（目前只有 Cursor 支持）
            install_url = ""
            if client["name"] == "cursor":
                install_url = MCPServerHandler._build_cursor_install_url(instance.name, mcp_url)

            configs.append(
                {
                    "name": client["name"],
                    "display_name": client["display_name"],
                    "content": content,
                    "install_url": install_url,
                }
            )

        return configs


class MCPServerPermissionHandler:
    @staticmethod
    def create_apply(bk_app_code: str, mcp_server_ids: List[int], reason: str, applied_by: str):
        queryset = MCPServer.objects.filter(
            id__in=mcp_server_ids,
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            gateway__status=GatewayStatusEnum.ACTIVE.value,
            stage__status=StageStatusEnum.ACTIVE.value,
        )

        selected_mcp_server_ids = list(queryset.values_list("id", flat=True))
        existing_permissions = MCPServerAppPermissionApply.objects.filter(
            bk_app_code=bk_app_code,
            mcp_server_id__in=selected_mcp_server_ids,
            status__in=[
                MCPServerAppPermissionApplyStatusEnum.PENDING.value,
                MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            ],
        ).order_by("-applied_time")

        if existing_permissions:
            existing_names = ", ".join([obj.mcp_server.name for obj in existing_permissions])
            raise error_codes.INVALID_ARGUMENT.format(
                _(f"mcp server name：{existing_names} 已经存在待审批或已审批的记录")
            )

        add_app_permissions_apply_list = [
            MCPServerAppPermissionApply(
                bk_app_code=bk_app_code,
                mcp_server=obj,
                reason=reason,
                applied_by=applied_by,
                applied_time=now_datetime(),
                expire_days=MCPServerAppPermissionApplyExpireDaysEnum.FOREVER.value,
                status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            )
            for obj in queryset
        ]

        MCPServerAppPermissionApply.objects.bulk_create(add_app_permissions_apply_list)

    @staticmethod
    def filter_records(
        bk_app_code: str,
        applied_by: str,
        apply_status: str,
        query: str,
        applied_time_start: Optional[datetime.datetime] = None,
        applied_time_end: Optional[datetime.datetime] = None,
    ):
        queryset = MCPServerAppPermissionApply.objects.filter(bk_app_code=bk_app_code).order_by("-applied_time")

        if applied_by:
            queryset = queryset.filter(applied_by=applied_by)

        if applied_time_start and applied_time_end:
            queryset = queryset.filter(applied_time__range=(applied_time_start, applied_time_end))

        if apply_status:
            queryset = queryset.filter(status=apply_status)

        if query:
            queryset = queryset.filter(Q(mcp_server__name__icontains=query) | Q(mcp_server__title__icontains=query))

        return queryset
