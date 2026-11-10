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
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml
from ddf import G

from apigateway.apps.openapi.models import OpenAPIResourceSchemaVersion
from apigateway.core.constants import GatewayStatusEnum, ResourceKindEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage
from apigateway.tests.biz.skill.static_provider import StaticResourceProvider

FIXTURES_DIR = Path(__file__).parent / "fixtures"
DECLARATIONS_DIR = FIXTURES_DIR / "declarations"
EXPECTED_DIR = FIXTURES_DIR / "expected"
GOLDEN_NAMES = sorted(path.stem for path in DECLARATIONS_DIR.glob("*.yaml"))


def load_declaration_data(name: str) -> dict:
    return yaml.safe_load((DECLARATIONS_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def release_resources(
    gateway_name: str,
    stage_name: str,
    resources: List[Dict[str, Any]],
    schemas: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Gateway:
    """建网关、环境、资源版本和发布，并写入 ReleasedResource 投影；schemas 按资源名给 OpenAPI schema"""
    gateway = Gateway.objects.filter(name=gateway_name).first() or G(
        Gateway, name=gateway_name, status=GatewayStatusEnum.ACTIVE.value
    )
    gateway.status = GatewayStatusEnum.ACTIVE.value
    gateway.save(update_fields=["status"])
    stage = G(Stage, gateway=gateway, name=stage_name, status=StageStatusEnum.ACTIVE.value)
    resource_version = G(ResourceVersion, gateway=gateway)
    G(Release, gateway=gateway, stage=stage, resource_version=resource_version)

    schema_items = []
    for index, item in enumerate(resources, start=1):
        auth = item.get("auth", {})
        auth_config = {
            "app_verified_required": auth.get("app_verified_required", True),
            "auth_verified_required": auth.get("user_verified_required", False),
            "resource_perm_required": auth.get("resource_perm_required", True),
        }
        data = {
            "id": index,
            "name": item["resource"],
            "method": item["method"],
            "path": item["path"],
            "description": item.get("description", ""),
            "is_public": item.get("is_public", True),
            "kind": item.get("kind") or ResourceKindEnum.STANDARD.value,
            "disabled_stages": item.get("disabled_stages", []),
            "contexts": {"resource_auth": {"config": json.dumps(auth_config)}},
            "api_labels": [],
        }
        G(
            ReleasedResource,
            gateway=gateway,
            resource_version_id=resource_version.id,
            resource_id=index,
            resource_name=item["resource"],
            resource_method=item["method"],
            resource_path=item["path"],
            is_public=data["is_public"],
            data=data,
        )
        if schemas and item["resource"] in schemas:
            schema_items.append({"resource_id": index, "schema": schemas[item["resource"]]})

    if schema_items:
        G(OpenAPIResourceSchemaVersion, resource_version=resource_version, schema=schema_items)
    return gateway


def release_fixture_gateway(resources_data: dict, gateway_name: str, stage_name: str = "prod") -> List[dict]:
    """把 resources.json 里该网关的资源及其 OpenAPI schema 发布到数据库。"""
    resources = [item for item in resources_data["resources"] if item["gateway"] == gateway_name]
    schemas = {item["resource"]: _fixture_resource_schema(item) for item in resources}
    release_resources(gateway_name, stage_name, resources, schemas)
    return resources


def _fixture_resource_schema(resource: Dict[str, Any]) -> Dict[str, Any]:
    parameters = []
    body_properties = {}
    body_required = []
    for item in resource.get("params", []):
        param_schema = _fixture_type_schema(item.get("type") or "")
        if item.get("description"):
            param_schema["description"] = item["description"]
        if item["in"] == "body":
            body_properties[item["name"]] = param_schema
            if item.get("required"):
                body_required.append(item["name"])
            continue
        parameters.append(
            {
                "name": item["name"],
                "in": item["in"],
                "required": bool(item.get("required")),
                "description": item.get("description") or "",
                "schema": param_schema,
            }
        )

    schema: Dict[str, Any] = {"parameters": parameters}
    if body_properties:
        schema["requestBody"] = {
            "required": bool(body_required),
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": body_properties,
                        "required": body_required,
                    }
                }
            },
        }

    response_schema: Dict[str, Any] = {"type": "object", "properties": {}}
    for item in resource.get("response", []):
        _add_fixture_response_field(response_schema, item)
    if response_schema["properties"]:
        schema["responses"] = {
            "200": {
                "description": "ok",
                "content": {"application/json": {"schema": response_schema}},
            }
        }
    return schema


def _fixture_type_schema(type_text: str) -> Dict[str, Any]:
    if type_text.startswith("array<") and type_text.endswith(">"):
        return {"type": "array", "items": _fixture_type_schema(type_text[6:-1])}
    if "|" in type_text:
        return {"type": type_text.split("|")}
    return {"type": type_text} if type_text else {}


def _add_fixture_response_field(root: Dict[str, Any], field: Dict[str, Any]) -> None:
    current = root
    parts = field["field"].split(".")
    for index, raw_part in enumerate(parts):
        is_array = raw_part.endswith("[]")
        name = raw_part[:-2] if is_array else raw_part
        is_last = index == len(parts) - 1
        properties = current.setdefault("properties", {})
        if is_last:
            value_schema = _fixture_type_schema(field.get("type") or "")
            if field.get("description"):
                value_schema["description"] = field["description"]
            properties[name] = {"type": "array", "items": value_schema} if is_array else value_schema
            return
        if is_array:
            item_schema = properties.setdefault(
                name, {"type": "array", "items": {"type": "object", "properties": {}}}
            )["items"]
            current = item_schema
        else:
            current = properties.setdefault(name, {"type": "object", "properties": {}})


@pytest.fixture
def resources_data() -> dict:
    return json.loads((FIXTURES_DIR / "resources.json").read_text(encoding="utf-8"))


@pytest.fixture
def static_provider(resources_data) -> StaticResourceProvider:
    return StaticResourceProvider.from_dict(resources_data)


@pytest.fixture
def job_plan_data() -> dict:
    """三步编排：run-plan -> wait-result（说明里写轮询）-> collect-log（带 if，说明里写逐个调用）。规则测试都改这一份"""
    return load_declaration_data("job-plan-run-and-log")
