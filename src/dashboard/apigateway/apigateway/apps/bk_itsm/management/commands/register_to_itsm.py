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
import copy
import json
import logging
import os

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError, ProgrammingError

from apigateway.apps.bk_itsm.models import ItsmSystemConfig
from apigateway.components.bkitsm import form_models_update, system_migrate, system_workflow_list

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
        parser.add_argument(
            "--update-form-model",
            action="store_true",
            default=False,
            help="Update existing ITSM form model fields from template instead of skipping registered systems",
        )
        parser.add_argument(
            "--form-model-key",
            type=str,
            default="",
            help="Existing ITSM form model key. Defaults to normalized form_models[0].key from template",
        )

    def handle(self, *args, **options):
        template_file = options["template_file"]
        strict_mode = options["strict"]
        update_form_model = options["update_form_model"]
        form_model_key = options["form_model_key"]

        template_data = self._load_template(template_file)
        template_data = self._normalize_template_for_migrate(template_data)
        template_defaults = self._extract_defaults_from_template(template_data)

        system_code = template_defaults["system_code"]

        self.stdout.write(f"Start register_to_itsm, system_code={system_code}")

        workflow_list_resp = self._get_system_workflow_list(system_code)

        # 先查询 ITSM 侧该系统是否已注册过流程，避免重复 migrate 导致 400 报错
        if self._is_system_registered_response(workflow_list_resp):
            if update_form_model:
                self._update_form_model_from_template(
                    system_code=system_code,
                    template_data=template_data,
                    workflow_list_resp=workflow_list_resp,
                    form_model_key=form_model_key,
                )
                self._ensure_config_from_template(system_code, template_data)
                return

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
        return Command._is_system_registered_response(Command._get_system_workflow_list(system_code))

    @staticmethod
    def _get_system_workflow_list(system_code: str):
        try:
            return system_workflow_list(system_id=system_code)
        except Exception:
            logger.warning("failed to query system_workflow_list, assume not registered", exc_info=True)
            return {}

    @staticmethod
    def _is_system_registered_response(resp) -> bool:
        return resp.get("count", 0) > 0

    def _update_form_model_from_template(
        self, system_code: str, template_data, workflow_list_resp, form_model_key: str
    ):
        payload = self._build_form_model_update_payload(system_code, template_data, form_model_key)
        missing_field_keys = self._get_missing_form_model_field_keys(workflow_list_resp, payload["meta"]["fields"])
        if not missing_field_keys:
            self.stdout.write(self.style.SUCCESS("ITSM form model already contains all template fields, skip update"))
            return

        self.stdout.write(f"Start updating ITSM form model, key={payload['key']}, missing_fields={missing_field_keys}")
        resp = form_models_update(**payload)
        self._validate_form_model_update_response(resp, missing_field_keys)
        self.stdout.write(self.style.SUCCESS(f"ITSM form model updated: key={payload['key']}"))
        self.stdout.write(
            self.style.WARNING(
                "form_models_update only updates form model fields; form_canvas_data/styleCode/layout are not updated."
            )
        )

    @staticmethod
    def _build_form_model_update_payload(system_code: str, template_data, form_model_key: str = ""):
        form_models = template_data.get("form_models", [])
        if not form_models:
            raise RuntimeError("invalid template: form_models is required")

        form_model = form_models[0]
        key = form_model_key or Command._normalize_form_model_key(form_model.get("key", ""))
        if not key:
            raise RuntimeError("invalid form model key, please provide --form-model-key")

        meta = copy.deepcopy(form_model.get("meta") or {})
        fields = meta.get("fields")
        if not isinstance(fields, dict) or not fields:
            raise RuntimeError("invalid template: form_models[0].meta.fields is required")

        return {
            "key": key,
            "name": form_model.get("name", ""),
            "desc": form_model.get("desc", ""),
            "app_id": form_model.get("app_id", ""),
            "system_id": system_code,
            "meta": meta,
        }

    @staticmethod
    def _normalize_form_model_key(form_model_key: str) -> str:
        form_model_key = str(form_model_key or "").strip()
        if form_model_key.startswith("$FormModel"):
            return form_model_key[len("$FormModel") :]
        return form_model_key

    @staticmethod
    def _get_missing_form_model_field_keys(workflow_list_resp, template_fields) -> list:
        remote_field_keys = Command._extract_form_schema_field_keys(workflow_list_resp)
        if not remote_field_keys:
            return sorted(template_fields.keys())

        return sorted(set(template_fields.keys()) - remote_field_keys)

    @staticmethod
    def _extract_form_schema_field_keys(workflow_list_resp) -> set:
        workflow_items = Command._extract_workflow_items(workflow_list_resp)
        field_keys: set[str] = set()
        for item in workflow_items:
            form_schema = item.get("form_schema") or {}
            properties = form_schema.get("properties") or {}
            field_keys.update(properties.keys())
        return field_keys

    @staticmethod
    def _extract_workflow_items(resp) -> list:
        if not isinstance(resp, dict):
            return []

        items = []
        if isinstance(resp.get("form_schema"), dict):
            items.append(resp)

        for key in ("results", "items"):
            value = resp.get(key)
            if isinstance(value, list):
                items.extend([item for item in value if isinstance(item, dict)])

        data = resp.get("data")
        if isinstance(data, list):
            items.extend([item for item in data if isinstance(item, dict)])
        elif isinstance(data, dict):
            if isinstance(data.get("form_schema"), dict):
                items.append(data)
            for key in ("results", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    items.extend([item for item in value if isinstance(item, dict)])

        return items

    @staticmethod
    def _validate_form_model_update_response(resp, missing_field_keys):
        if isinstance(resp, dict) and resp.get("result") is False:
            raise RuntimeError(f"form_models_update failed: {resp}")

        updated_fields = (
            ((resp or {}).get("data") or {}).get("meta", {}).get("fields", {}) if isinstance(resp, dict) else {}
        )
        if not updated_fields:
            return

        still_missing = sorted(set(missing_field_keys) - set(updated_fields.keys()))
        if still_missing:
            raise RuntimeError(f"form_models_update response missing fields: {still_missing}")

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
        except OperationalError, ProgrammingError:
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
