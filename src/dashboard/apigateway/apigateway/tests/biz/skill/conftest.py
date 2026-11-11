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
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage
from apigateway.tests.biz.skill.static_provider import (
    StaticResourceProvider,
    fixture_resource_schema,
    released_resource_payload,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
DECLARATIONS_DIR = FIXTURES_DIR / "declarations"
EXPECTED_DIR = FIXTURES_DIR / "expected"
GOLDEN_NAMES = sorted(path.stem for path in DECLARATIONS_DIR.glob("*.yaml"))


def load_declaration_data(name: str) -> dict:
    return yaml.safe_load((DECLARATIONS_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def set_version(data: dict, version: str) -> dict:
    """改 version，changelog 换成只有这个版本的一条，满足「第一条是当前版本」"""
    data["version"] = version
    data["changelog"] = [{"version": version, "date": "2026-11-12", "content": f"发布 {version}"}]
    return data


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
        data = released_resource_payload(item, index)
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
    schemas = {item["resource"]: fixture_resource_schema(item) for item in resources}
    release_resources(gateway_name, stage_name, resources, schemas)
    return resources


@pytest.fixture
def resources_data() -> dict:
    return json.loads((FIXTURES_DIR / "resources.json").read_text(encoding="utf-8"))


@pytest.fixture
def static_provider(resources_data) -> StaticResourceProvider:
    return StaticResourceProvider.from_dict(resources_data)


@pytest.fixture
def job_plan_data() -> dict:
    """三步编排：run-plan -> wait-result（说明里写轮询）-> collect-log（说明里写执行条件，with 用 `[]` 逐个调用）。规则测试都改这一份"""
    return load_declaration_data("job-plan-run-and-log")
