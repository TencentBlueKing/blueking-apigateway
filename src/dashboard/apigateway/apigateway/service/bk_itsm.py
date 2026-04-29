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

    _TICKET_ID_KEYS = ("id", "ticket_id", "ticketId")

    @classmethod
    def _extract_id_from_dict(cls, data: Optional[Dict[str, Any]]) -> str:
        if not isinstance(data, dict):
            return ""

        for key in cls._TICKET_ID_KEYS:
            value = data.get(key)
            if value not in (None, ""):
                return str(value)

        return ""

    @classmethod
    def extract_ticket_id(cls, resp: Optional[Dict[str, Any]]) -> str:
        """从 ticket_create 响应中提取工单 ID，兼容不同返回结构"""
        if not isinstance(resp, dict):
            return ""

        for candidate in (resp, resp.get("ticket"), resp.get("data")):
            ticket_id = cls._extract_id_from_dict(candidate)
            if ticket_id:
                return ticket_id

            if isinstance(candidate, dict):
                ticket_id = cls._extract_id_from_dict(candidate.get("ticket"))
                if ticket_id:
                    return ticket_id

        return ""

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
                    f"ITSM system config not found for {self.system_code}, please run init_bk_itsm command first."
                )
        return self._config

    def is_ready(self) -> bool:
        """检查 ITSM 集成是否已就绪"""
        try:
            cfg = self.config
            return cfg.is_registered and bool(cfg.workflow_key)
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
        reason: str = "",
        expire_days: int = 0,
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
        :param reason: 申请理由
        :param expire_days: 过期天数
        :param applied_by: 申请人
        :param apply_record_id: 权限申请记录 ID
        :param approvers: 审批人列表
        :return: ITSM 工单创建响应
        """
        if not self.is_ready():
            raise error_codes.FAILED_PRECONDITION.format(
                "ITSM integration is not ready, please check system registration."
            )

        # 构建权限对象描述
        apply_resources = self._build_apply_resources_display(grant_dimension, apply_resource_names)

        # 构建表单数据
        form_data = {
            "ticket__title": f"网关权限申请-{gateway_name}-{bk_app_code}",
            "gateway_name": gateway_name,
            "grant_dimension": grant_dimension,
            "apply_resources": apply_resources,
            "bk_app_code": bk_app_code,
            "apply_record_id": apply_record_id,
            "reason": reason,
            "expire_days": expire_days,
        }

        if approvers:
            form_data["approvers"] = approvers

        # 构建回调 URL
        callback_url = self._build_callback_url()
        callback_token = callback_token or self.generate_callback_token()

        logger.info(
            "Creating ITSM ticket for permission apply: gateway=%s, app=%s, record_id=%s, workflow_key=%s",
            gateway_name,
            bk_app_code,
            apply_record_id,
            self.config.workflow_key,
        )

        return create_ticket(
            workflow_key=self.config.workflow_key,
            form_data=form_data,
            operator=applied_by,
            callback_url=callback_url,
            callback_token=callback_token,
            system_id=self.config.itsm_system_id,
            system_token=self.config.system_token,
        )

    def _build_apply_resources_display(
        self,
        grant_dimension: str,
        apply_resource_names: List[str],
    ) -> str:
        """构建申请资源的展示文本"""
        if grant_dimension == "gateway":
            return "该网关所有资源"

        if apply_resource_names:
            return ", ".join(apply_resource_names)

        return "该网关所有资源"

    def _build_callback_url(self) -> str:
        """构建 ITSM 回调 URL"""
        bk_apigateway_url = getattr(settings, "BK_API_URL_TMPL", "").format(api_name="bk-apigateway")
        if not bk_apigateway_url:
            return ""
        return url_join(bk_apigateway_url, "/prod/api/v2/open/itsm/callback/")
