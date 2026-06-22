#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from collections import defaultdict
from typing import Any, Dict, List, Optional

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.biz.audit import Auditor
from apigateway.utils.django import get_model_dict

from .mcp_server import MCPServerHandler


def get_mcp_server_sync_data_before_map(
    gateway_id: int,
    gateway_name: str,
    stage_name: str,
    mcp_servers_data: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    full_names = [
        MCPServerHandler.get_mcp_server_name(
            gateway_name=gateway_name,
            stage_name=stage_name,
            name=mcp_data["name"],
        )
        for mcp_data in mcp_servers_data
    ]
    instances = MCPServer.objects.filter(gateway_id=gateway_id, name__in=full_names)
    return {instance.name: get_model_dict(instance) for instance in instances}


def get_mcp_server_permission_sync_data_before_map(
    gateway_id: int,
    gateway_name: str,
    stage_name: str,
    mcp_servers_data: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    full_names = [
        MCPServerHandler.get_mcp_server_name(
            gateway_name=gateway_name,
            stage_name=stage_name,
            name=mcp_data["name"],
        )
        for mcp_data in mcp_servers_data
        if mcp_data.get("target_app_codes")
    ]
    if not full_names:
        return {}

    permissions = MCPServerAppPermission.objects.filter(
        mcp_server__gateway_id=gateway_id,
        mcp_server__name__in=full_names,
    ).select_related("mcp_server")
    data_before_map: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for permission in permissions:
        data_before_map.setdefault(permission.mcp_server.name, {})[permission.bk_app_code] = get_model_dict(permission)

    return data_before_map


def record_mcp_server_sync_audits(
    username: str,
    gateway_id: int,
    results: List[Dict[str, Any]],
    data_before_map: Dict[str, Dict[str, Any]],
) -> None:
    instance_ids = [result["id"] for result in results if result.get("id")]
    instances = {instance.id: instance for instance in MCPServer.objects.filter(id__in=instance_ids)}

    for result in results:
        action = result.get("action")
        if action not in {"created", "updated"}:
            continue

        instance = instances.get(result["id"])
        if not instance:
            continue

        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.CREATE if action == "created" else OpTypeEnum.MODIFY,
            username=username,
            gateway_id=gateway_id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before_map.get(instance.name, {}),
            data_after=get_model_dict(instance),
        )


def record_mcp_server_permission_sync_audits(
    username: str,
    gateway_id: int,
    results: List[Dict[str, Any]],
    mcp_servers_data: List[Dict[str, Any]],
    data_before_map: Dict[str, Dict[str, Dict[str, Any]]],
) -> None:
    app_codes_by_name = {
        result["name"]: mcp_data.get("target_app_codes", [])
        for result, mcp_data in zip(results, mcp_servers_data)
        if result.get("id") and mcp_data.get("target_app_codes")
    }
    if not app_codes_by_name:
        return

    instances = {
        instance.name: instance
        for instance in MCPServer.objects.filter(gateway_id=gateway_id, name__in=app_codes_by_name.keys())
    }

    for instance_name, app_codes in app_codes_by_name.items():
        instance = instances.get(instance_name)
        if not instance:
            continue

        permissions = {
            permission.bk_app_code: permission
            for permission in MCPServerAppPermission.objects.filter(
                mcp_server_id=instance.id,
                bk_app_code__in=app_codes,
            )
        }
        for app_code in app_codes:
            permission = permissions.get(app_code)
            if not permission:
                continue

            data_before = data_before_map.get(instance.name, {}).get(app_code, {})
            Auditor.record_permission_op_success(
                op_type=OpTypeEnum.MODIFY if data_before else OpTypeEnum.CREATE,
                username=username,
                gateway_id=gateway_id,
                instance_id=permission.id,
                instance_name=app_code,
                data_before=data_before,
                data_after=get_model_dict(permission),
            )


def record_mcp_server_permission_apply_audits(
    username: str,
    instance_name: str,
    applies: List[MCPServerAppPermissionApply],
) -> None:
    apply_ids = [apply.id for apply in applies if apply.id]
    if not apply_ids:
        return

    applies_by_gateway_id = defaultdict(list)
    for apply in MCPServerAppPermissionApply.objects.filter(id__in=apply_ids).select_related("mcp_server"):
        applies_by_gateway_id[apply.mcp_server.gateway_id].append(apply)

    for gateway_id, gateway_applies in applies_by_gateway_id.items():
        Auditor.record_permission_op_success(
            op_type=OpTypeEnum.CREATE,
            username=username,
            gateway_id=gateway_id,
            instance_id=gateway_applies[0].id,
            instance_name=instance_name,
            data_before={},
            data_after=[get_model_dict(apply) for apply in gateway_applies],
            comment="MCPServer 权限申请",
        )


def get_active_mcp_server_data_before_map(gateway_id: int, stage_id: int = 0) -> Dict[int, Dict[str, Any]]:
    queryset = MCPServer.objects.filter(gateway_id=gateway_id, status=MCPServerStatusEnum.ACTIVE.value)
    if stage_id:
        queryset = queryset.filter(stage_id=stage_id)

    return {instance.id: get_model_dict(instance) for instance in queryset}


def record_mcp_server_disable_audits(
    username: str,
    gateway_id: int,
    data_before_map: Dict[int, Dict[str, Any]],
    comment: Optional[str] = None,
) -> None:
    if not data_before_map:
        return

    instances = MCPServer.objects.filter(id__in=data_before_map.keys())
    for instance in instances:
        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=username,
            gateway_id=gateway_id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before_map.get(instance.id, {}),
            data_after=get_model_dict(instance),
            comment=comment,
        )
