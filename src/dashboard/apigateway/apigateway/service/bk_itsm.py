# -*- coding: utf-8 -*-
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
import logging
import secrets
from typing import Any, Dict, List, Optional

from django.conf import settings

from apigateway.apps.bk_itsm.models import ItsmSystemConfig
from apigateway.common.error_codes import error_codes
from apigateway.components.bkitsm import create_ticket
from apigateway.utils.url import url_join

logger = logging.getLogger(__name__)


class ItsmPermissionApplyHelper:
    """
    ITSM 权限申请辅助类
    用于在权限申请时创建 ITSM 工单
    """

    def __init__(self, system_code: str = "bk_apigateway"):
        self.system_code = system_code
        self._config: Optional[ItsmSystemConfig] = None

    @property
    def config(self) -> ItsmSystemConfig:
        if self._config is None:
            try:
                self._config = ItsmSystemConfig.objects.get(system_code=self.system_code)
            except ItsmSystemConfig.DoesNotExist:
                raise error_codes.FAILED_PRECONDITION.format(
                    f"ITSM system config not found for {self.system_code}, please run register_to_itsm command first."
                )
        return self._config

    def is_ready(self) -> bool:
        """检查 ITSM 集成是否已就绪"""
        try:
            cfg = self.config
            workflow_key_map = cfg.workflow_key_map or {}
            return (
                cfg.is_registered and bool(workflow_key_map.get("gateway")) and bool(workflow_key_map.get("resource"))
            )
        except Exception:
            return False

    @staticmethod
    def generate_callback_token() -> str:
        """生成高熵回调 token"""
        return secrets.token_urlsafe(24)

    def create_permission_apply_ticket(
        self,
        bk_app_code: str,
        gateway_name: str,
        grant_dimension: str,
        apply_resource_names: List[str],
        applied_by: str = "",
        apply_record_id: int = 0,
        approvers: Optional[List[str]] = None,
        callback_token: str = "",
    ) -> Dict[str, Any]:
        """
        创建网关权限申请 ITSM 工单

        :param bk_app_code: 申请权限的应用代码
        :param gateway_name: 网关名称
        :param grant_dimension: 授权维度 (gateway/resource/mcp_server)
        :param apply_resource_names: 申请的资源名称列表
        :param applied_by: 申请人（必填且不能为空）
        :param apply_record_id: 权限申请记录 ID
        :param approvers: 审批人列表（必填且不能为空）
        :return: ITSM 工单创建响应
        """
        if not self.is_ready():
            raise error_codes.FAILED_PRECONDITION.format(
                "ITSM integration is not ready, please check system registration."
            )

        normalized_applied_by = str(applied_by).strip()
        if not normalized_applied_by:
            raise error_codes.FAILED_PRECONDITION.format("ITSM applied_by is required and cannot be empty.")

        normalized_approvers = [str(username).strip() for username in (approvers or []) if str(username).strip()]
        if not normalized_approvers:
            raise error_codes.FAILED_PRECONDITION.format("ITSM approvers is required and cannot be empty.")

        apply_resources = self._build_apply_resources_display(
            grant_dimension=grant_dimension,
            gateway_name=gateway_name,
            apply_resource_names=apply_resource_names,
        )

        form_data = {
            "ticket__title": f"网关权限申请-{gateway_name}-{bk_app_code}",
            "gateway_name": gateway_name,
            "grant_dimension": grant_dimension,
            "apply_resources": apply_resources,
            "bk_app_code": bk_app_code,
            "apply_record_id": apply_record_id,
            "instance_approvers": normalized_approvers,
        }

        callback_url = self._build_callback_url()
        callback_token = callback_token or self.generate_callback_token()
        options = self._build_form_options(grant_dimension)

        workflow_key = self._get_workflow_key(grant_dimension)
        if not workflow_key:
            raise error_codes.FAILED_PRECONDITION.format(
                f"ITSM workflow key not configured for grant_dimension={grant_dimension}."
            )

        logger.info(
            "Creating ITSM ticket for permission apply: gateway=%s, app=%s, record_id=%s, grant_dimension=%s, workflow_key=%s",
            gateway_name,
            bk_app_code,
            apply_record_id,
            grant_dimension,
            workflow_key,
        )

        return create_ticket(
            workflow_key=workflow_key,
            form_data=form_data,
            operator=applied_by,
            callback_url=callback_url,
            callback_token=callback_token,
            system_id=self.config.itsm_system_id,
            system_token=self.config.system_token,
            options=options,
        )

    def _get_workflow_key(self, grant_dimension: str) -> str:
        workflow_key_map = self.config.workflow_key_map or {}
        workflow_key = str(workflow_key_map.get(grant_dimension, "")).strip()
        return self._normalize_workflow_key(workflow_key)

    @staticmethod
    def _normalize_workflow_key(workflow_key: str) -> str:
        workflow_key = str(workflow_key or "").strip()
        if workflow_key.startswith("$Workflow"):
            return workflow_key[len("$Workflow") :]
        return workflow_key

    @staticmethod
    def _build_form_options(grant_dimension: str) -> Dict[str, List[Dict[str, Optional[str]]]]:
        """构建 ITSM ticket_create 所需 options（选项型字段明细）"""
        grant_dimension_option_name_map = {
            "gateway": "gateway",
            "resource": "resource",
            "mcp_server": "MCP Server",
        }
        return {
            "grant_dimension": [
                {
                    "name": grant_dimension_option_name_map.get(grant_dimension, grant_dimension),
                    "key": grant_dimension,
                    "parent": None,
                }
            ]
        }

    def _build_apply_resources_display(
        self,
        grant_dimension: str,
        gateway_name: str,
        apply_resource_names: List[str],
    ) -> str:
        """构建申请资源的展示文本"""
        if grant_dimension == "gateway":
            return gateway_name

        normalized_names = [str(name).strip() for name in (apply_resource_names or []) if str(name).strip()]
        if normalized_names:
            return ", ".join(normalized_names)

        return gateway_name

    def _build_callback_url(self) -> str:
        """构建 ITSM 回调 URL"""
        bk_api_url_tmpl = getattr(settings, "BK_API_URL_TMPL", "")
        if not bk_api_url_tmpl:
            raise error_codes.FAILED_PRECONDITION.format(
                "BK_API_URL_TMPL is not configured, unable to build ITSM callback URL."
            )

        callback_path = getattr(settings, "BK_ITSM4_CALLBACK_PATH", "")
        if not callback_path:
            raise error_codes.FAILED_PRECONDITION.format(
                "BK_ITSM4_CALLBACK_PATH is not configured, unable to build ITSM callback URL."
            )

        try:
            bk_apigateway_url = bk_api_url_tmpl.format(api_name="bk-apigateway")
        except Exception:
            raise error_codes.FAILED_PRECONDITION.format(
                "BK_API_URL_TMPL is invalid, unable to build ITSM callback URL."
            )

        if not bk_apigateway_url.startswith(("http://", "https://")):
            raise error_codes.FAILED_PRECONDITION.format(
                "BK_API_URL_TMPL must render absolute URL, unable to build ITSM callback URL."
            )

        return url_join(bk_apigateway_url, callback_path)
