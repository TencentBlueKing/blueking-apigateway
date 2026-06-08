# -*- coding: utf-8 -*-
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
import json
import logging
import os

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError, ProgrammingError

from apigateway.apps.bk_itsm.models import ItsmSystemConfig
from apigateway.components.bkitsm import system_migrate, system_workflow_list

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Register API Gateway approval workflow to bk-itsm4 via system_migrate"

    def add_arguments(self, parser):
        parser.add_argument(
            "--template-file",
            type=str,
            default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_bk-apigateway.json"),
            help="ITSM workflow template json file path",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            default=False,
            help="Strict mode: fail fast on migrate errors instead of idempotent fallback",
        )

    def handle(self, *args, **options):
        template_file = options["template_file"]
        strict_mode = options["strict"]

        template_data = self._load_template(template_file)
        template_data = self._normalize_template_for_migrate(template_data)
        template_defaults = self._extract_defaults_from_template(template_data)

        system_code = template_defaults["system_code"]

        self.stdout.write(f"Start register_to_itsm, system_code={system_code}")

        # 先查询 ITSM 侧该系统是否已注册过流程，避免重复 migrate 导致 400 报错
        if self._is_system_registered_in_itsm(system_code):
            self.stdout.write(f"System {system_code} already registered in ITSM, skip migrate")
            self._ensure_config_from_template(system_code, template_data)
            return

        try:
            system_migrate(template_data)
        except Exception as err:
            if not strict_mode and self._is_idempotent_migrate_error(err):
                self.stdout.write(self.style.WARNING(f"system_migrate skipped by idempotent fallback: {err}"))
                self._ensure_config_from_template(system_code, template_data)
                return
            raise

        # ITSM system_migrate 是异步接口，不会返回 system_id / workflow_keys，
        # 直接从模板配置中提取并写入本地配置表
        self._ensure_config_from_template(system_code, template_data)

    @staticmethod
    def _is_system_registered_in_itsm(system_code: str) -> bool:
        """通过 system_workflow_list 接口查询系统是否已在 ITSM 注册"""
        try:
            resp = system_workflow_list(system_id=system_code)
        except Exception:
            logger.warning("failed to query system_workflow_list, assume not registered", exc_info=True)
            return False

        return resp.get("count", 0) > 0

    def _ensure_config_from_template(self, system_code: str, template_data):
        """确保配置表有完整数据，有则复用，无则从模板写入"""
        existing_config = self._load_existing_config(system_code)
        if existing_config and self._can_fallback_to_existing_config(existing_config):
            self.stdout.write(
                self.style.SUCCESS(
                    f"register_to_itsm success(reuse): system_id={existing_config.itsm_system_id}, "
                    f"workflow_key_map={existing_config.workflow_key_map}"
                )
            )
            return

        workflow_keys = self._extract_workflow_keys_from_template(template_data)
        workflow_key_map = self._build_workflow_key_map(template_data, workflow_keys)

        config, _ = ItsmSystemConfig.objects.get_or_create(system_code=system_code)
        config.itsm_system_id = system_code
        config.workflow_key_map = workflow_key_map
        config.is_registered = True
        config.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"register_to_itsm success(from template): system_id={config.itsm_system_id}, "
                f"workflow_key_map={config.workflow_key_map}"
            )
        )

    @staticmethod
    def _load_template(template_file: str):
        if not os.path.exists(template_file):
            raise RuntimeError(f"template file not found: {template_file}")

        with open(template_file, "r", encoding="utf-8") as fp:
            return json.load(fp)

    @staticmethod
    def _normalize_template_for_migrate(template_data):
        form_models = template_data.get("form_models", [])
        if not form_models:
            raise RuntimeError("invalid template: form_models is required")

        default_form_model_key = str(form_models[0].get("key", "")).strip()
        if not default_form_model_key:
            raise RuntimeError("invalid template: form_models[0].key is required")

        workflows = template_data.get("workflows", [])
        if not isinstance(workflows, list) or not workflows:
            raise RuntimeError("invalid template: workflows is required")

        for workflow_item in workflows:
            workflow = workflow_item.get("workflow", {})
            form_model_key = str(workflow.get("form_model_key") or "").strip()
            if not form_model_key:
                workflow["form_model_key"] = default_form_model_key

        return template_data

    @staticmethod
    def _extract_defaults_from_template(template_data):
        system_data = template_data.get("system", {})
        form_models = template_data.get("form_models", [])
        workflows = template_data.get("workflows", [])

        system_code = str(system_data.get("code", "")).strip()
        system_name = str(system_data.get("name", "")).strip()
        if not system_code:
            raise RuntimeError("invalid template: system.code is required")
        if not system_name:
            raise RuntimeError("invalid template: system.name is required")

        if not form_models:
            raise RuntimeError("invalid template: form_models is required")

        if not isinstance(workflows, list) or not workflows:
            raise RuntimeError("invalid template: workflows is required")

        return {
            "system_code": system_code,
        }

    @staticmethod
    def _extract_workflow_keys_from_template(template_data) -> list:
        """从模板配置中提取 workflow keys（与 _build_workflow_key_map 中的逻辑一致）"""
        workflows = template_data.get("workflows", [])
        workflow_keys = []
        for workflow_item in workflows:
            workflow = workflow_item.get("workflow", {})
            key = str(workflow.get("key", "")).strip()
            if key:
                workflow_keys.append(key)

        if not workflow_keys:
            raise RuntimeError("invalid template: no workflow keys found in template")

        return workflow_keys

    @staticmethod
    def _normalize_workflow_key(workflow_key: str) -> str:
        workflow_key = str(workflow_key or "").strip()
        if workflow_key.startswith("$Workflow"):
            return workflow_key[len("$Workflow") :]
        return workflow_key

    @staticmethod
    def _build_workflow_key_map(template_data, workflow_keys):
        normalized_workflow_keys = [
            Command._normalize_workflow_key(key) for key in workflow_keys if Command._normalize_workflow_key(key)
        ]
        if not normalized_workflow_keys:
            raise RuntimeError("invalid system_migrate response: workflow_keys is empty")

        workflow_key_name_map = {}
        for workflow_item in template_data.get("workflows", []):
            workflow = workflow_item.get("workflow", {})
            workflow_key = Command._normalize_workflow_key(workflow.get("key", ""))
            workflow_name = str(workflow.get("name", "")).strip()
            if not workflow_key:
                raise RuntimeError("invalid template: workflow.key is required")
            if not workflow_name:
                raise RuntimeError(f"invalid template: workflow.name is required for workflow_key={workflow_key}")
            if workflow_key in workflow_key_name_map:
                raise RuntimeError(f"invalid template: duplicate workflow.key found: {workflow_key}")
            workflow_key_name_map[workflow_key] = workflow_name

        expected_keys = set(workflow_key_name_map.keys())
        actual_keys = set(normalized_workflow_keys)
        if expected_keys != actual_keys:
            raise RuntimeError(
                f"workflow keys mismatch between template and migrate response: "
                f"template={sorted(expected_keys)}, response={sorted(actual_keys)}"
            )

        non_mcp_workflow_keys = [
            workflow_key
            for workflow_key, workflow_name in workflow_key_name_map.items()
            if "mcp" not in workflow_name.lower()
        ]
        if len(non_mcp_workflow_keys) != 1:
            raise RuntimeError(
                "invalid workflow mapping: exactly one non-mcp workflow is required for gateway/resource dimensions, "
                f"current={non_mcp_workflow_keys}"
            )

        mcp_workflow_keys = [
            workflow_key
            for workflow_key, workflow_name in workflow_key_name_map.items()
            if "mcp" in workflow_name.lower()
        ]
        if len(mcp_workflow_keys) > 1:
            raise RuntimeError(
                f"invalid workflow mapping: at most one mcp workflow is supported, current={mcp_workflow_keys}"
            )

        workflow_key_map = {
            "gateway": non_mcp_workflow_keys[0],
            "resource": non_mcp_workflow_keys[0],
        }
        if mcp_workflow_keys:
            workflow_key_map["mcp_server"] = mcp_workflow_keys[0]

        return workflow_key_map

    @staticmethod
    def _load_existing_config(system_code: str):
        try:
            return ItsmSystemConfig.objects.filter(system_code=system_code).first()
        except (OperationalError, ProgrammingError):
            logger.warning("skip loading ItsmSystemConfig, table is not ready", exc_info=True)
            return None

    @staticmethod
    def _can_fallback_to_existing_config(config: ItsmSystemConfig) -> bool:
        if not (config and config.is_registered and config.itsm_system_id):
            return False

        workflow_key_map = config.workflow_key_map or {}
        return bool(
            workflow_key_map.get("gateway") and workflow_key_map.get("resource") and workflow_key_map.get("mcp_server")
        )

    @staticmethod
    def _is_idempotent_migrate_error(err: Exception) -> bool:
        message = str(err)
        lowered_message = message.lower()
        keywords = [
            "dictionary changed size during iteration",
            "duplicate entry",
            "already exists",
            "名称不唯一",
            "已存在",
        ]
        return any(keyword in lowered_message for keyword in keywords)
