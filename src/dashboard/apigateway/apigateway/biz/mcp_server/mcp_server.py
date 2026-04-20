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
import json
import logging
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
from urllib.parse import quote

from django.conf import settings
from django.db import transaction
from django.db.models import Q, QuerySet
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from apigateway.apps.mcp_server.constants import (
    FEATURED_MCP_CATEGORY_NAME,
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerExtendTypeEnum,
    MCPServerLeastPrivilegeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermission,
    MCPServerCategory,
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
from apigateway.core.constants import GatewayStatusEnum, GatewayTypeEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, Resource, Stage
from apigateway.service.contexts import GatewayAuthContext
from apigateway.service.mcp.mcp_server import build_mcp_server_application_url, build_mcp_server_url
from apigateway.utils.time import NeverExpiresTime

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
    def save_mcp_servers(
        gateway_id: int,
        gateway_name: str,
        stage_id: int,
        stage_name: str,
        mcp_servers_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """批量创建或更新 MCP Server

        Args:
            gateway_id: 网关 ID
            gateway_name: 网关名称
            stage_id: 环境 ID
            stage_name: 环境名称
            mcp_servers_data: MCP Server 配置列表，每项包含 name, description, resource_names 等字段

        Returns:
            操作结果列表，每项包含 name, action, id
        """
        results = []
        for mcp_data in mcp_servers_data:
            mcp_data["gateway_id"] = gateway_id
            mcp_data["stage_id"] = stage_id

            name = mcp_data["name"]
            full_name = MCPServerHandler.get_mcp_server_name(
                gateway_name=gateway_name, stage_name=stage_name, name=name
            )
            mcp_data["name"] = full_name

            resource_names = mcp_data.pop("resource_names", [])
            tool_names = mcp_data.pop("tool_names", None) or resource_names
            target_app_codes = mcp_data.pop("target_app_codes", [])
            category_names = mcp_data.pop("category_names", None)

            instance = MCPServer.objects.filter(name=full_name, stage__name=stage_name, gateway_id=gateway_id).first()

            if instance:
                action = "updated"
                for field, value in mcp_data.items():
                    if hasattr(instance, field):
                        setattr(instance, field, value)
                instance.update_resource_names(resource_names, tool_names)
                instance.save()
            else:
                action = "created"
                instance = MCPServer(**mcp_data)
                instance.update_resource_names(resource_names, tool_names)
                instance.save()

            MCPServerHandler._sync_mcp_server_permissions(instance.id, target_app_codes)
            MCPServerHandler._sync_mcp_server_categories(instance, category_names)

            results.append({"name": instance.name, "action": action, "id": instance.id})

        return results

    @staticmethod
    def _sync_mcp_server_permissions(mcp_server_id: int, app_codes: List[str]):
        """同步 MCP Server 权限"""
        for app_code in app_codes:
            MCPServerAppPermission.objects.save_permission(
                mcp_server_id=mcp_server_id,
                bk_app_code=app_code,
                grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
                expire_days=None,
            )
        MCPServerHandler.sync_permissions(mcp_server_id)

    @staticmethod
    def _sync_mcp_server_categories(instance: MCPServer, category_names: Optional[List[str]]):
        """同步 MCP Server 分类，None 表示不操作，空列表表示清空"""
        if category_names is None:
            return

        if not category_names:
            instance.categories.clear()
            return

        existing_categories = MCPServerCategory.objects.filter(name__in=category_names)
        instance.categories.set(existing_categories)

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
        """同步 MCPServer 的权限，包括 OAuth2 权限（bk_app_code=public）
        Args:
            mcp_server_id (int): mcp_server 的 id
        """
        mcp_server = MCPServer.objects.get(id=mcp_server_id)

        # 同步 OAuth2 权限：根据 oauth2_public_client_enabled 开启/关闭 public app 权限
        public_app_code = settings.MCP_SERVER_OAUTH2_PUBLIC_CLIENT_APP_CODE
        if mcp_server.oauth2_public_client_enabled:
            MCPServerAppPermission.objects.save_permission(
                mcp_server_id=mcp_server_id,
                bk_app_code=public_app_code,
                grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
                expire_days=None,
            )
            logger.info(
                "sync oauth2 permissions for mcp_server %d, granted bk_app_code=%s",
                mcp_server_id,
                public_app_code,
            )
        else:
            deleted_count, _ = MCPServerAppPermission.objects.filter(
                mcp_server_id=mcp_server_id,
                bk_app_code=public_app_code,
            ).delete()
            if deleted_count:
                logger.info(
                    "sync oauth2 permissions for mcp_server %d, revoked bk_app_code=%s, deleted %d",
                    mcp_server_id,
                    public_app_code,
                    deleted_count,
                )

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
    def _get_releases_for_mcp_servers(mcp_servers) -> Dict[Tuple[int, int], Release]:
        """批量获取 MCP Server 列表对应的 Release 记录

        Args:
            mcp_servers: MCPServer 实例列表

        Returns:
            {(gateway_id, stage_id): Release} 映射
        """
        gateway_stage_pairs = {(mcp_server.gateway_id, mcp_server.stage_id) for mcp_server in mcp_servers}
        if not gateway_stage_pairs:
            return {}

        release_filters = Q()
        for gateway_id, stage_id in gateway_stage_pairs:
            release_filters |= Q(gateway_id=gateway_id, stage_id=stage_id)

        releases = Release.objects.filter(release_filters).select_related("resource_version")
        return {(r.gateway_id, r.stage_id): r for r in releases}

    @staticmethod
    def get_app_permission_risks(
        mcp_servers: Sequence,
        releases: Optional[Dict[Tuple[int, int], Release]] = None,
    ) -> Dict[int, List[str]]:
        """检测开启了 oauth2_public_client_enabled 的 MCPServer 是否存在应用态权限安全风险。

        当 oauth2_public_client_enabled=True 时，public 应用被自动授权；
        如果工具对应的 API 要求应用认证(verified_app_required)，则存在权限失效的安全风险。

        Args:
            mcp_servers: MCPServer 实例列表（需已 select_related gateway/stage）
            releases: 可选，预查询的 Release 映射，避免重复查询

        Returns:
            {mcp_server_id: [risk_tool_name, ...]} 映射，仅包含存在风险的 MCPServer
        """
        risk_mcp_servers = [m for m in mcp_servers if m.oauth2_public_client_enabled]
        if not risk_mcp_servers:
            return {}

        if releases is None:
            releases = MCPServerHandler._get_releases_for_mcp_servers(risk_mcp_servers)

        release_resource_auth: Dict[Tuple[int, int], Dict[str, bool]] = {}
        for key, release in releases.items():
            resource_auth: Dict[str, bool] = {}
            for resource in release.resource_version.data:
                auth_config = json.loads(resource.get("contexts", {}).get("resource_auth", {}).get("config", "{}"))
                resource_auth[resource["name"]] = bool(auth_config.get("app_verified_required", True))
            release_resource_auth[key] = resource_auth

        risks: Dict[int, List[str]] = {}
        for mcp_server in risk_mcp_servers:
            gateway_stage_key = (mcp_server.gateway_id, mcp_server.stage_id)
            resource_auth = release_resource_auth.get(gateway_stage_key, {})
            tool_name_map = mcp_server.gen_tool_name_map()
            risk_tools = [
                tool_name_map.get(resource_name, resource_name)
                for resource_name in mcp_server.resource_names
                if resource_auth.get(resource_name, False)
            ]
            if risk_tools:
                risks[mcp_server.id] = risk_tools

        return risks

    @staticmethod
    def get_least_privileges(
        mcp_servers,
        releases: Optional[Dict[Tuple[int, int], Release]] = None,
    ) -> Dict[Tuple[int, int], str]:
        """批量计算 MCP Server 的最低权限级别

        遍历每个 MCP Server 的 (gateway_id, stage_id) 对，检查 Release 中对应工具资源
        是否需要用户认证。如果所有工具都不需要用户认证，则为 APPLICATION；
        否则为 APPLICATION_AND_USER。

        Args:
            mcp_servers: MCPServer 实例列表（需已 select_related gateway/stage）
            releases: 可选，预查询的 Release 映射，避免重复查询

        Returns:
            {(gateway_id, stage_id): least_privilege} 映射
        """
        gateway_stage_tools: Dict[Tuple[int, int], List[str]] = {}
        for mcp_server in mcp_servers:
            gateway_stage_tools[(mcp_server.gateway_id, mcp_server.stage_id)] = mcp_server.resource_names

        if not gateway_stage_tools:
            return {}

        if releases is None:
            releases = MCPServerHandler._get_releases_for_mcp_servers(mcp_servers)

        least_privileges: Dict[Tuple[int, int], str] = {}
        for gateway_stage_key, release in releases.items():
            tool_names = gateway_stage_tools.get(gateway_stage_key, [])
            least_privilege = MCPServerLeastPrivilegeEnum.APPLICATION.value
            for resource in release.resource_version.data:
                if resource["name"] not in tool_names:
                    continue
                auth_config = json.loads(resource.get("contexts", {}).get("resource_auth", {}).get("config", "{}"))
                verified_user_required = not auth_config.get("skip_auth_verification", False) and bool(
                    auth_config.get("auth_verified_required", False)
                )
                if verified_user_required:
                    least_privilege = MCPServerLeastPrivilegeEnum.APPLICATION_AND_USER.value
                    break
            least_privileges[gateway_stage_key] = least_privilege

        return least_privileges

    @staticmethod
    def get_mcp_server_url(instance: MCPServer, least_privilege: str = "") -> str:
        """根据 MCP Server 的应用态条件返回合适的访问 URL

        当未开启公共客户端模式且所有工具都是应用态时，返回应用态 URL。

        Args:
            instance: MCPServer 实例
            least_privilege: 最低权限级别

        Returns:
            MCP Server 访问 URL
        """
        if (
            not instance.oauth2_public_client_enabled
            and least_privilege == MCPServerLeastPrivilegeEnum.APPLICATION.value
        ):
            return build_mcp_server_application_url(instance.name, instance.protocol_type)
        return build_mcp_server_url(instance.name, instance.protocol_type)

    # ========== 通用访问校验/查询构建方法 ==========

    @staticmethod
    def validate_access(
        instance: MCPServer,
        check_public: bool = False,
        username: Optional[str] = None,
    ) -> None:
        """校验 MCPServer 的访问权限

        检查 MCPServer 的状态、网关状态、环境状态，以及可选的公开性检查。

        Args:
            instance: MCPServer 实例
            check_public: 是否检查公开性
            username: 当前用户名，用于公开性检查时判断是否为维护者

        Raises:
            error_codes.NOT_FOUND: 当校验不通过时
        """
        if instance.status != MCPServerStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未启用，无法访问。"))
        if instance.gateway.status != GatewayStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关未启用，无法访问。"))
        if instance.stage.status != StageStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关对应的环境未启用，无法访问。"))

        if check_public and not instance.is_public and (not username or username not in instance.gateway.maintainers):
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未公开，无法访问。"))

    @staticmethod
    def build_guideline(
        instance: MCPServer,
        user_tenant_id: str = "",
        least_privilege: str = "",
    ) -> str:
        """构建 MCPServer 使用指南（Guideline）

        根据 MCPServer 实例和当前语言环境渲染 guideline 模板。

        Args:
            instance: MCPServer 实例
            user_tenant_id: 用户租户 ID
            least_privilege: 最低权限级别，用于确定 URL

        Returns:
            渲染后的 guideline 内容（Markdown 格式）
        """
        mcp_url = MCPServerHandler.get_mcp_server_url(instance, least_privilege)
        template_name = f"mcp_server/{get_current_language_code()}/guideline.md"
        return render_to_string(
            template_name,
            context={
                "name": instance.name,
                "url": mcp_url,
                "description": instance.description,
                "bk_login_ticket_key": settings.BK_LOGIN_TICKET_KEY,
                "bk_access_token_doc_url": settings.BK_ACCESS_TOKEN_DOC_URL,
                "enable_multi_tenant_mode": settings.ENABLE_MULTI_TENANT_MODE,
                "user_tenant_id": user_tenant_id,
                "protocol_type": instance.protocol_type,
            },
        )

    @staticmethod
    def apply_category_filter(queryset: QuerySet, categories: List[str]) -> QuerySet:
        """对 MCPServer queryset 应用分类筛选

        当选择的分类中包含 Official 或 Featured 时，使用 AND 逻辑（结果必须同时满足所有分类）；
        否则使用 OR 逻辑（属于任意一个分类即可）。

        Args:
            queryset: MCPServer 查询集
            categories: 分类名称列表

        Returns:
            应用分类筛选后的查询集
        """
        if not categories:
            return queryset

        special_categories = {OFFICIAL_MCP_CATEGORY_NAME, FEATURED_MCP_CATEGORY_NAME}
        if special_categories & set(categories):
            for category in categories:
                queryset = queryset.filter(categories__name=category, categories__is_active=True)
            queryset = queryset.distinct()
        else:
            queryset = queryset.filter(categories__name__in=categories, categories__is_active=True).distinct()

        return queryset

    @staticmethod
    def build_list_queryset(
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        categories: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        order_by: str = "-updated_time",
    ) -> QuerySet:
        """构建 MCPServer 列表的通用 queryset

        只返回 status=ACTIVE 且 gateway/stage 也是 ACTIVE 的记录。

        Args:
            keyword: 搜索关键词（名称/标题/描述模糊匹配）
            category: 单个分类名称筛选（兼容旧接口）
            categories: 多个分类名称列表筛选（支持 AND/OR 逻辑）
            is_public: 是否公开
            order_by: 排序字段

        Returns:
            构建好的 queryset
        """
        queryset = MCPServer.objects.filter(status=MCPServerStatusEnum.ACTIVE.value)
        queryset = queryset.filter(gateway__status=GatewayStatusEnum.ACTIVE.value)
        queryset = queryset.filter(stage__status=StageStatusEnum.ACTIVE.value)

        if is_public is not None:
            queryset = queryset.filter(is_public=is_public)

        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword) | Q(title__icontains=keyword) | Q(description__icontains=keyword)
            )

        # 兼容单分类筛选
        if category:
            queryset = queryset.filter(categories__name=category, categories__is_active=True)

        # 多分类筛选（AND/OR 逻辑）
        if categories:
            queryset = MCPServerHandler.apply_category_filter(queryset, categories)

        return queryset.select_related("gateway", "stage").order_by(order_by)

    @staticmethod
    def build_categories_map(mcp_server_ids: List[int]) -> Dict[int, List[Dict[str, str]]]:
        """批量查询 MCPServer 的分类信息，返回 {mcp_server_id: [{"name": ..., "display_name": ...}]} 映射

        使用单次查询替代 N+1 的 categories.filter() 调用。

        Args:
            mcp_server_ids: MCPServer ID 列表

        Returns:
            以 mcp_server_id 为 key 的分类字典映射
        """
        if not mcp_server_ids:
            return {}

        categories_qs = MCPServerCategory.objects.filter(
            mcp_servers__id__in=mcp_server_ids,
            is_active=True,
        ).values("mcp_servers__id", "name", "display_name")

        categories_map: Dict[int, List[Dict[str, str]]] = {}
        for cat in categories_qs:
            categories_map.setdefault(cat["mcp_servers__id"], []).append(
                {"name": cat["name"], "display_name": cat["display_name"]}
            )
        return categories_map

    @staticmethod
    def build_list_context(
        mcp_servers: Sequence,
        include_prompts_count: bool = False,
        include_least_privileges: bool = False,
        include_app_permission_risks: bool = False,
    ) -> Dict[str, Any]:
        """构建 MCPServer 列表序列化所需的上下文

        包括 gateways/stages 字典，以及可选的 prompts_count、least_privileges 等。

        Args:
            mcp_servers: MCPServer 实例列表
            include_prompts_count: 是否包含 prompts 数量
            include_least_privileges: 是否包含最低权限级别
            include_app_permission_risks: 是否包含应用态权限风险

        Returns:
            序列化所需的 context 字典
        """
        gateway_ids = list({ms.gateway.id for ms in mcp_servers})
        gateway_auth_configs = GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids)
        gateways = {
            gw.id: {
                "id": gw.id,
                "name": gw.name,
                "maintainers": gw.maintainers,
                "is_official": gateway_auth_configs[gw.id].gateway_type
                in (GatewayTypeEnum.SUPER_OFFICIAL_API.value, GatewayTypeEnum.OFFICIAL_API.value),
            }
            for gw in Gateway.objects.filter(id__in=gateway_ids)
        }

        stage_ids = [ms.stage.id for ms in mcp_servers]
        stages = {
            s.id: {
                "id": s.id,
                "name": s.name,
            }
            for s in Stage.objects.filter(id__in=stage_ids)
        }

        context: Dict[str, Any] = {"gateways": gateways, "stages": stages}

        mcp_server_ids = [ms.id for ms in mcp_servers]

        if include_prompts_count:
            context["prompts_count_map"] = MCPServerHandler.get_prompts_count_map(mcp_server_ids)

        releases = None
        if include_least_privileges or include_app_permission_risks:
            releases = MCPServerHandler._get_releases_for_mcp_servers(mcp_servers)

        if include_least_privileges:
            context["least_privileges"] = MCPServerHandler.get_least_privileges(mcp_servers, releases=releases)

        if include_app_permission_risks:
            context["app_permission_risks"] = MCPServerHandler.get_app_permission_risks(mcp_servers, releases=releases)

        return context

    @staticmethod
    def build_retrieve_context(
        instance: MCPServer,
        check_public: bool = False,
        username: Optional[str] = None,
        user_tenant_id: str = "",
    ) -> Dict[str, Any]:
        """校验 MCPServer 状态并构建 retrieve 所需的上下文数据

        整合访问校验、guideline 生成、工具资源获取、prompts 获取等逻辑。

        Args:
            instance: MCPServer 实例
            check_public: 是否检查公开性（open/marketplace 接口需要，inner 接口不需要）
            username: 当前用户名，用于公开性检查
            user_tenant_id: 用户租户 ID，用于 guideline 渲染

        Returns:
            序列化所需的 context 字典
        """
        MCPServerHandler.validate_access(instance, check_public=check_public, username=username)

        least_privileges = MCPServerHandler.get_least_privileges([instance])
        least_privilege = least_privileges.get((instance.gateway.id, instance.stage.id), "")

        guideline = MCPServerHandler.build_guideline(
            instance, user_tenant_id=user_tenant_id, least_privilege=least_privilege
        )
        instance.guideline = guideline

        tool_resources, labels = MCPServerHandler.get_tools_resources_and_labels(
            gateway_id=instance.gateway.id,
            stage_name=instance.stage.name,
            resource_names=instance.resource_names,
        )
        instance.tools = tool_resources
        instance.maintainers = instance.gateway.maintainers

        prompts_count_map = MCPServerHandler.get_prompts_count_map([instance.id])
        prompts = MCPServerHandler.get_prompts(instance.id)
        user_custom_doc = MCPServerHandler.get_user_custom_doc(instance.id)

        resource_schema_map: Dict[int, dict] = {}
        release = Release.objects.filter(
            gateway_id=instance.gateway.id,
            stage=instance.stage,
        ).first()
        if release:
            resource_schema_map = ResourceVersionHandler.get_resource_id_to_schema_by_resource_version(
                release.resource_version_id
            )

        categories = [
            {"name": cat.name, "display_name": cat.display_name} for cat in instance.categories.filter(is_active=True)
        ]

        # 构建 gateway/stage 上下文
        gateway_auth_configs = GatewayAuthContext().get_gateway_id_to_auth_config([instance.gateway.id])
        gateways = {
            instance.gateway.id: {
                "id": instance.gateway.id,
                "name": instance.gateway.name,
                "maintainers": instance.gateway.maintainers,
                "is_official": gateway_auth_configs[instance.gateway.id].gateway_type
                in (GatewayTypeEnum.SUPER_OFFICIAL_API.value, GatewayTypeEnum.OFFICIAL_API.value),
            }
        }
        stages = {
            instance.stage.id: {
                "id": instance.stage.id,
                "name": instance.stage.name,
            }
        }

        return {
            "gateways": gateways,
            "stages": stages,
            "labels": labels,
            "tool_name_map": instance.gen_tool_name_map(),
            "resource_schema_map": resource_schema_map,
            "categories": categories,
            "prompts_count_map": prompts_count_map,
            "prompts": prompts,
            "user_custom_doc": user_custom_doc,
            "least_privileges": least_privileges,
        }

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
    def _build_cursor_install_url(
        name: str, mcp_url: str, oauth2_public_client_enabled: bool = False, user_tenant_id: str = ""
    ) -> str:
        """
        生成 Cursor 一键配置 URL

        格式: cursor://anysphere.cursor-deeplink/mcp/install?name=<NAME>&config=<BASE64_CONFIG>
        """
        config: Dict[str, Any] = {
            "url": mcp_url,
        }
        headers: Dict[str, str] = {}
        if not oauth2_public_client_enabled:
            headers["X-Bkapi-Authorization"] = json.dumps(
                {
                    "bk_app_code": "your_app_code",
                    "bk_app_secret": "your_app_secret",
                    settings.BK_LOGIN_TICKET_KEY: "your_ticket",
                }
            )
        if settings.ENABLE_MULTI_TENANT_MODE and user_tenant_id:
            headers["X-Bk-Tenant-Id"] = user_tenant_id
            headers["X-Bkapi-Allowed-Headers"] = "X-Bk-Tenant-Id"
        if headers:
            config["headers"] = headers
        config_json = json.dumps(config)
        config_base64 = base64.b64encode(config_json.encode()).decode()
        return f"cursor://anysphere.cursor-deeplink/mcp/install?name={quote(name)}&config={quote(config_base64)}"

    @staticmethod
    def build_agent_client_configs(
        instance: MCPServer, least_privilege: str = "", user_tenant_id: str = ""
    ) -> List[Dict[str, Any]]:
        """
        构建 MCPServer 的 Agent 客户端配置列表

        Args:
            instance: MCPServer 实例
            least_privilege: 最低权限级别，用于判断是否使用应用态 URL
            user_tenant_id: 用户租户 ID（多租户模式下使用）

        Returns:
            配置列表，每个配置包含 name, display_name, content, install_url
        """
        language_code = get_current_language_code()
        mcp_url = MCPServerHandler.get_mcp_server_url(instance, least_privilege)
        enable_multi_tenant_mode = settings.ENABLE_MULTI_TENANT_MODE
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
                "oauth2_public_client_enabled": instance.oauth2_public_client_enabled,
                "enable_multi_tenant_mode": enable_multi_tenant_mode,
                "user_tenant_id": user_tenant_id,
            }

            # AIDev 需要额外的创建链接
            if client["name"] == "aidev":
                context["aidev_agent_create_url"] = settings.AIDEV_AGENT_CREATE_URL

            content = render_to_string(template_name, context=context)

            # 生成一键配置 URL（目前只有 Cursor 支持）
            install_url = ""
            if client["name"] == "cursor":
                install_url = MCPServerHandler._build_cursor_install_url(
                    instance.name, mcp_url, instance.oauth2_public_client_enabled, user_tenant_id
                )

            configs.append(
                {
                    "name": client["name"],
                    "display_name": client["display_name"],
                    "content": content,
                    "install_url": install_url,
                }
            )

        return configs

    @staticmethod
    def build_batch_agent_client_config(
        instances: List[MCPServer],
        client_type: str,
        least_privileges: Dict[Tuple[int, int], str],
        user_tenant_id: str = "",
    ) -> Dict[str, Any]:
        """
        批量构建指定客户端类型的 MCP Server 配置

        Args:
            instances: MCPServer 实例列表
            client_type: 客户端类型（cursor, codebuddy, claude, vscode, aidev 等）
            least_privileges: 最低权限字典，key 为 (gateway_id, stage_id)
            user_tenant_id: 用户租户 ID（多租户模式下使用）

        Returns:
            对应客户端类型的 JSON 配置，包含所有 mcpServers
        """
        if not instances:
            return {"mcpServers": {}}

        enable_multi_tenant_mode = settings.ENABLE_MULTI_TENANT_MODE
        mcp_servers_config = {}

        for instance in instances:
            mcp_url = MCPServerHandler.get_mcp_server_url(
                instance, least_privileges.get((instance.gateway.id, instance.stage.id), "")
            )

            # 根据 protocol_type 和客户端类型确定 transport_type
            if instance.protocol_type == "streamable_http":
                transport_type = "streamable-http" if client_type == "codebuddy" else "http"
            else:
                transport_type = "sse"

            # 构建单个 server 配置
            server_config: Dict[str, Any] = {
                "url": mcp_url,
            }

            # CodeBuddy 需要 transportType
            if client_type == "codebuddy":
                server_config["transportType"] = transport_type

            # 处理 headers
            headers = {}
            if not instance.oauth2_public_client_enabled:
                headers["X-Bkapi-Authorization"] = json.dumps(
                    {
                        "bk_app_code": "your_app_code",
                        "bk_app_secret": "your_app_secret",
                        settings.BK_LOGIN_TICKET_KEY: "your_ticket",
                    }
                )
            if enable_multi_tenant_mode and user_tenant_id:
                headers["X-Bk-Tenant-Id"] = user_tenant_id
                headers["X-Bkapi-Allowed-Headers"] = "X-Bk-Tenant-Id"

            if headers:
                server_config["headers"] = headers

            mcp_servers_config[instance.name] = server_config

        return {"mcpServers": mcp_servers_config}
