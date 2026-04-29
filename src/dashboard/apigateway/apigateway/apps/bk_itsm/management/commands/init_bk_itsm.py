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

from django.core.management.base import BaseCommand

from apigateway.apps.bk_itsm.models import ItsmSystemConfig
from apigateway.components.bkitsm import create_system, create_system_workflow

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Initialize bk-itsm4 resources for API Gateway permission apply"

    def add_arguments(self, parser):
        parser.add_argument(
            "--system-code",
            type=str,
            default="bk_apigateway",
            help="System code identifier",
        )
        parser.add_argument(
            "--system-name",
            type=str,
            default="API Gateway",
            help="System display name",
        )
        parser.add_argument(
            "--system-desc",
            type=str,
            default="API Gateway permission apply system",
            help="System description",
        )
        parser.add_argument(
            "--workflow-name",
            type=str,
            default="网关权限申请",
            help="Workflow name",
        )
        parser.add_argument(
            "--portal-id",
            type=str,
            default="DEFAULT",
            help="Portal ID",
        )
        parser.add_argument(
            "--workflow-category",
            type=str,
            default="",
            help="Workflow category",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode, do not actually call API",
        )

    def handle(self, *args, **options):
        system_code = options["system_code"]
        system_name = options["system_name"]
        system_desc = options["system_desc"]
        workflow_name = options["workflow_name"]
        portal_id = options["portal_id"]
        workflow_category = options["workflow_category"]
        dry_run = options["dry_run"]

        self.stdout.write(f"Start initializing bk-itsm4 resources for system: {system_code}")

        # 1. 创建或获取系统配置记录
        config = self._get_or_create_config(
            system_code, system_name, system_desc, portal_id, workflow_name, workflow_category
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run mode, skip API calls"))
            return

        # 2. 注册系统
        if not self._register_system(config, system_name, system_code, system_desc):
            return

        # 3. 注册流程
        if not self._register_workflow(config, workflow_name, portal_id, workflow_category):
            return

        config.is_registered = True
        config.save()

        self.stdout.write(self.style.SUCCESS("bk-itsm4 resources initialized successfully"))

    def _get_or_create_config(
        self,
        system_code: str,
        system_name: str,
        system_desc: str,
        portal_id: str,
        workflow_name: str,
        workflow_category: str,
    ) -> ItsmSystemConfig:
        """创建或获取系统配置记录"""
        config, created = ItsmSystemConfig.objects.get_or_create(
            system_code=system_code,
            defaults={
                "system_name": system_name,
                "system_desc": system_desc,
                "portal_id": portal_id,
                "workflow_name": workflow_name,
                "workflow_category": workflow_category,
            },
        )
        if not created:
            config.system_name = system_name
            config.system_desc = system_desc
            config.portal_id = portal_id
            config.workflow_name = workflow_name
            config.workflow_category = workflow_category
            config.save()
        return config

    def _register_system(self, config: ItsmSystemConfig, system_name: str, system_code: str, system_desc: str) -> bool:
        """调用 system_create 创建系统，返回是否成功"""
        if config.itsm_system_id:
            if not config.system_token:
                config.system_token = system_code
                config.save(update_fields=["system_token", "updated_time"])
            self.stdout.write(f"System already exists: {config.itsm_system_id}")
            return True

        self.stdout.write(f"Creating ITSM system: {system_code}")
        try:
            resp = create_system(
                name=system_name,
                code=system_code,
                token=system_code,
                desc=system_desc,
            )
            config.itsm_system_id = self._extract_system_id(resp, default=system_code)
            config.system_token = self._extract_system_token(resp, default=system_code)
            config.save(update_fields=["itsm_system_id", "system_token", "updated_time"])
            self.stdout.write(self.style.SUCCESS(f"System created: {config.itsm_system_id}"))
            return True
        except Exception as e:
            logger.exception("Failed to create ITSM system")
            self.stdout.write(self.style.ERROR(f"Failed to create system: {e}"))
            return False

    def _register_workflow(
        self,
        config: ItsmSystemConfig,
        workflow_name: str,
        portal_id: str,
        workflow_category: str,
    ) -> bool:
        """调用 system_workflow_create 创建流程，返回是否成功"""
        if config.workflow_key:
            self.stdout.write(f"Workflow already exists: {config.workflow_key}")
            return True

        self.stdout.write(f"Creating ITSM workflow: {workflow_name}")

        # 构建表单 schema，使用代码内置默认定义
        form_schema = self._build_form_schema()

        try:
            resp = create_system_workflow(
                system_id=config.itsm_system_id,
                name=workflow_name,
                form_schema=form_schema,
                portal_id=portal_id,
                desc="网关权限申请流程",
                workflow_category=workflow_category,
                predefined_approver={
                    "type": "Variable",
                    "id": ["approvers"],
                },
                system_token=config.system_token,
            )
            config.workflow_key = str(resp.get("key") or resp.get("workflow_key") or resp.get("id") or "")
            self.stdout.write(self.style.SUCCESS(f"Workflow created: {config.workflow_key}"))
            return True
        except Exception as e:
            logger.exception("Failed to create ITSM workflow")
            self.stdout.write(self.style.ERROR(f"Failed to create workflow: {e}"))
            return False

    def _build_form_schema(self) -> dict:
        """
        构建网关权限申请流程的默认表单 schema
        支持 gateway、resource、mcp_server 三种权限维度
        """
        return {
            "type": "object",
            "required": ["ticket__title", "apply_resources", "bk_app_code"],
            "properties": {
                "ticket__title": {
                    "title": "标题",
                    "type": "string",
                },
                "gateway_name": {
                    "title": "网关名",
                    "type": "string",
                },
                "grant_dimension": {
                    "title": "权限维度",
                    "type": "string",
                    "enum": ["gateway", "resource", "mcp_server"],
                },
                "apply_resources": {
                    "title": "权限对象",
                    "type": "string",
                    "format": "textarea",
                },
                "bk_app_code": {
                    "title": "申请的应用",
                    "type": "string",
                },
                "approvers": {
                    "title": "权限对象审批人",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "user",
                    },
                },
                "apply_record_id": {
                    "title": "网关申请单据ID",
                    "type": "number",
                },
                "reason": {
                    "title": "申请理由",
                    "type": "string",
                },
                "expire_days": {
                    "title": "过期天数",
                    "type": "number",
                },
            },
        }
