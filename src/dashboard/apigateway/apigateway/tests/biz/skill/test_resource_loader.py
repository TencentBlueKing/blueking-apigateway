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
from django.utils.translation import override

from apigateway.biz.skill.resource_loader import ReleasedResourceProvider, SkillResourceUnavailableError
from apigateway.biz.skill.schema_converter import ResourceParam, ResponseField
from apigateway.core.constants import GatewayStatusEnum, ResourceKindEnum, StageStatusEnum
from apigateway.core.models import Stage
from apigateway.tests.biz.skill.conftest import release_resources

pytestmark = pytest.mark.django_db

NO_REQUEST = "OpenAPI schema 未定义请求参数"
NO_RESPONSE = "OpenAPI schema 的响应未定义字段"

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


def _assert_unavailable(gateway: str, stage: str, resource: str, reason: str) -> None:
    with pytest.raises(SkillResourceUnavailableError) as err:
        ReleasedResourceProvider().get_resource(gateway, stage, resource)
    assert str(err.value) == reason


class TestReleasedResourceProvider:
    def test_from_schema(self):
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert (definition.data.method, definition.data.path, definition.data.description) == (
            "GET",
            "/get_task_status/{task_id}/",
            "查询任务状态",
        )
        assert (
            definition.data.verified_app_required,
            definition.data.verified_user_required,
            definition.data.resource_perm_required,
            definition.data.oauth2_public_client_enabled,
            definition.data.oauth2_personal_client_enabled,
        ) == (True, True, True, False, False)
        assert definition.params == [
            ResourceParam(name="task_id", location="path", type="integer", required=True, schema={"type": "integer"})
        ]
        assert definition.responses == [ResponseField(field="result", type="boolean")]
        assert definition.warnings == []
        assert definition.errors == []

    def test_no_schema(self):
        release_resources("bk-sops", "prod", [RESOURCE])

        with pytest.raises(SkillResourceUnavailableError) as err:
            ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert str(err.value) == f"{NO_REQUEST}; {NO_RESPONSE}"

    @pytest.mark.parametrize(
        "schema, reason",
        [
            pytest.param({}, f"{NO_REQUEST}; {NO_RESPONSE}", id="empty"),
            pytest.param({"none_schema": True}, NO_RESPONSE, id="no-request-params-no-response"),
            pytest.param({"parameters": SCHEMA["parameters"]}, NO_RESPONSE, id="request-only"),
            pytest.param({"responses": SCHEMA["responses"]}, NO_REQUEST, id="response-only"),
            pytest.param(
                {"parameters": SCHEMA["parameters"], "responses": {"204": {"description": "ok"}}},
                NO_RESPONSE,
                id="response-without-fields",
            ),
        ],
    )
    def test_requires_request_and_response(self, schema, reason):
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": schema})

        with pytest.raises(SkillResourceUnavailableError) as err:
            ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert str(err.value) == reason

    def test_declared_no_request_params_with_response(self):
        schema = {"none_schema": True, "responses": SCHEMA["responses"]}
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": schema})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert definition.params == []
        assert definition.responses == [ResponseField(field="result", type="boolean")]
        assert definition.errors == []

    def test_oauth2_clients_from_auth_config(self):
        resource = {
            **RESOURCE,
            "auth": {**RESOURCE["auth"], "oauth2_public_client_enabled": True, "oauth2_personal_client_enabled": True},
        }
        release_resources("bk-sops", "prod", [resource], schemas={"get_task_status": SCHEMA})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert definition.data.oauth2_public_client_enabled is True
        assert definition.data.oauth2_personal_client_enabled is True

    def test_not_public_warning(self):
        release_resources("bk-sops", "prod", [{**RESOURCE, "is_public": False}], schemas={"get_task_status": SCHEMA})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert definition.warnings == ["bk-sops.get_task_status：资源未公开，调用方无法申请权限"]

    def test_non_json_request_body_is_error(self):
        schema = {
            "parameters": [{"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
            "requestBody": {
                "content": {
                    "multipart/form-data": {"schema": {"type": "object", "properties": {"file": {"type": "string"}}}}
                }
            },
            "responses": SCHEMA["responses"],
        }
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": schema})

        definition = ReleasedResourceProvider().get_resource("bk-sops", "prod", "get_task_status")

        assert definition.warnings == []
        assert definition.errors == [
            "bk-sops.get_task_status：请求体不是 application/json，SKILL.md 只能描述 JSON 请求体"
        ]

    @pytest.mark.parametrize(
        "gateway, stage, resource, reason",
        [
            ("bk-other", "prod", "get_task_status", "网关 bk-other 不存在"),
            ("bk-sops", "test", "get_task_status", "环境 test 不存在"),
            ("bk-sops", "prod", "get_task_list", "当前发布版本中没有资源 get_task_list"),
        ],
    )
    def test_missing(self, gateway, stage, resource, reason):
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})

        _assert_unavailable(gateway, stage, resource, reason)

    def test_stage_without_release(self):
        gateway = release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})
        G(Stage, gateway=gateway, name="test", status=StageStatusEnum.ACTIVE.value)

        _assert_unavailable("bk-sops", "test", "get_task_status", "环境 test 未发布")

    def test_inactive_gateway(self):
        gateway = release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})
        gateway.status = GatewayStatusEnum.INACTIVE.value
        gateway.save(update_fields=["status"])

        _assert_unavailable("bk-sops", "prod", "get_task_status", "网关 bk-sops 未启用")

    def test_inactive_stage(self):
        gateway = release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})
        Stage.objects.filter(gateway=gateway, name="prod").update(status=StageStatusEnum.INACTIVE.value)

        _assert_unavailable("bk-sops", "prod", "get_task_status", "环境 prod 未启用")

    def test_ai_resource(self):
        release_resources(
            "bk-sops", "prod", [{**RESOURCE, "kind": ResourceKindEnum.AI.value}], schemas={"get_task_status": SCHEMA}
        )

        _assert_unavailable("bk-sops", "prod", "get_task_status", "资源是 AI 资源，不能编排")

    def test_disabled_stage(self):
        release_resources(
            "bk-sops", "prod", [{**RESOURCE, "disabled_stages": ["prod"]}], schemas={"get_task_status": SCHEMA}
        )

        _assert_unavailable("bk-sops", "prod", "get_task_status", "资源在环境 prod 已禁用")

    def test_reason_translated(self):
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})

        with override("en"):
            _assert_unavailable(
                "bk-sops", "prod", "get_task_list", "resource get_task_list is not in the currently released version"
            )

    def test_cached_per_stage(self, django_assert_num_queries):
        release_resources("bk-sops", "prod", [RESOURCE], schemas={"get_task_status": SCHEMA})
        provider = ReleasedResourceProvider()
        provider.get_resource("bk-sops", "prod", "get_task_status")
        with pytest.raises(SkillResourceUnavailableError):
            provider.get_resource("bk-sops", "test", "get_task_status")

        with django_assert_num_queries(0):
            provider.get_resource("bk-sops", "prod", "get_task_status")
            with pytest.raises(SkillResourceUnavailableError, match="get_task_list"):
                provider.get_resource("bk-sops", "prod", "get_task_list")
            with pytest.raises(SkillResourceUnavailableError, match="环境 test 不存在"):
                provider.get_resource("bk-sops", "test", "get_task_list")
