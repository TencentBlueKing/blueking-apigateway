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
import pytest
from ddf import G

from apigateway.biz.skill.resource_definition import ResourceParam, ResponseField
from apigateway.biz.skill.resource_loader import ReleasedResourceProvider
from apigateway.core.constants import GatewayStatusEnum, ResourceKindEnum, StageStatusEnum
from apigateway.core.models import Stage
from apigateway.tests.biz.skill.conftest import release_resources, write_snapshots

pytestmark = pytest.mark.django_db

RESOURCE = {
    "resource": "get_task_status",
    "method": "GET",
    "path": "/get_task_status/{task_id}/",
    "description": "查询任务状态",
    "auth": {"app_verified_required": True, "user_verified_required": True, "resource_perm_required": True},
}
SCHEMA = {
    "parameters": [{"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
    "responses": {
        "200": {
            "description": "ok",
            "content": {
                "application/json": {"schema": {"type": "object", "properties": {"result": {"type": "boolean"}}}}
            },
        }
    },
}
SNAPSHOT_RESOURCE = {
    "gateway": "bk-sops",
    "resource": "get_task_status",
    "params": [{"name": "task_id", "in": "path", "type": "string", "required": True}],
    "response": [{"field": "data.state", "type": "string"}],
}


class TestReleasedResourceProvider:
    def test_from_schema(self):
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert (definition.method, definition.path, definition.description) == (
            "GET",
            "/get_task_status/{task_id}/",
            "查询任务状态",
        )
        assert (
            definition.app_verified_required,
            definition.user_verified_required,
            definition.resource_perm_required,
        ) == (True, True, True)
        assert definition.params == [ResourceParam(name="task_id", location="path", type="integer", required=True)]
        assert definition.responses == [ResponseField(field="result", type="boolean")]
        assert definition.warnings == []

    def test_no_schema_no_snapshot(self):
        release_resources("bk-sops", "prod", [RESOURCE])

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert definition.params == []
        assert definition.warnings == ["bk-sops.get_task_status：资源无 schema、无快照，参数和响应字段无法核对"]

    def test_snapshot_fills_missing_schema(self, tmp_path):
        release_resources("bk-sops", "prod", [RESOURCE])
        snapshot_dir = write_snapshots(tmp_path, [SNAPSHOT_RESOURCE])

        definition = ReleasedResourceProvider(snapshot_dir=snapshot_dir).get_resource(
            "bk-sops", "prod", "get_task_status"
        )

        assert definition.params == [ResourceParam(name="task_id", location="path", type="string", required=True)]
        assert definition.responses == [ResponseField(field="data.state", type="string")]
        assert definition.warnings == []

    def test_snapshot_wins_over_schema_with_warning(self, tmp_path):
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})
        snapshot_dir = write_snapshots(tmp_path, [SNAPSHOT_RESOURCE])

        definition = ReleasedResourceProvider(snapshot_dir=snapshot_dir).get_resource(
            "bk-sops", "prod", "get_task_status"
        )

        assert definition.responses == [ResponseField(field="data.state", type="string")]
        assert definition.warnings == [
            "bk-sops.get_task_status：资源已有 schema，核对后删除 resources/bk-sops.yaml 里的这条快照"
        ]

    def test_not_public_warning(self):
        release_resources("bk-sops", "prod", [{**RESOURCE, "is_public": False}], schemas={"get_task_status": SCHEMA})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert definition.warnings == ["bk-sops.get_task_status：资源未公开，调用方无法申请权限"]

    def test_non_json_request_body_warns_without_rejecting(self):
        schema = {
            "parameters": [{"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
            "requestBody": {
                "content": {
                    "multipart/form-data": {"schema": {"type": "object", "properties": {"file": {"type": "string"}}}}
                }
            },
        }
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": schema})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert definition.params == [ResourceParam(name="task_id", location="path", type="integer", required=True)]
        assert definition.definition_unverified is False
        assert definition.warnings == ["bk-sops.get_task_status：请求体不是 application/json，未转换为 body 参数"]

    def test_non_json_request_body_only_is_not_unverified(self):
        schema = {
            "requestBody": {
                "content": {
                    "multipart/form-data": {"schema": {"type": "object", "properties": {"file": {"type": "string"}}}}
                }
            }
        }
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": schema})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert definition.params == []
        assert definition.definition_unverified is False
        assert definition.warnings == ["bk-sops.get_task_status：请求体不是 application/json，未转换为 body 参数"]

    @pytest.mark.parametrize(
        "gateway, stage, resource",
        [
            ("bk-other", "prod", "get_task_status"),
            ("bk-sops", "test", "get_task_status"),
            ("bk-sops", "prod", "get_task_list"),
        ],
    )
    def test_missing(self, gateway, stage, resource):
        release_resources("bk-sops", "prod", [RESOURCE])

        assert ReleasedResourceProvider().get_resource(gateway, stage, resource) is None

    def test_stage_without_release(self):
        gateway = release_resources("bk-sops", "prod", [RESOURCE])
        G(Stage, gateway=gateway, name="test", status=StageStatusEnum.ACTIVE.value)

        assert ReleasedResourceProvider().get_resource("bk-sops", "test", "get_task_status") is None

    def test_inactive_gateway(self):
        gateway = release_resources("bk-sops", "prod", [RESOURCE])
        gateway.status = GatewayStatusEnum.INACTIVE.value
        gateway.save(update_fields=["status"])

        assert ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status") is None

    def test_inactive_stage(self):
        gateway = release_resources("bk-sops", "prod", [RESOURCE])
        Stage.objects.filter(gateway=gateway, name="prod").update(status=StageStatusEnum.INACTIVE.value)

        assert ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status") is None

    def test_ai_resource(self):
        release_resources("bk-sops", "prod", [{**RESOURCE, "kind": ResourceKindEnum.AI.value}])

        assert ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status") is None

    def test_disabled_stage(self):
        release_resources("bk-sops", "prod", [{**RESOURCE, "disabled_stages": ["prod"]}])

        assert ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status") is None

    def test_cached_per_stage(self, django_assert_num_queries):
        release_resources("bk-sops", "prod", [RESOURCE])
        provider = ReleasedResourceProvider()
        provider.get_resource("bk-sops", "prod", "get_task_status")

        with django_assert_num_queries(0):
            provider.get_resource("bk-sops", "prod", "get_task_status")
            provider.get_resource("bk-sops", "prod", "get_task_list")
