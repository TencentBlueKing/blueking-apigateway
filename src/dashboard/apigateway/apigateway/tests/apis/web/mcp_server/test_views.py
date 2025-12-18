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
import json

import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerExtendTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermission,
    MCPServerAppPermissionApply,
    MCPServerExtend,
)
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


@pytest.fixture
def fake_mcp_server(fake_gateway, fake_stage, faker):
    return G(
        MCPServer,
        name=faker.pystr()[:20],
        gateway=fake_gateway,
        stage=fake_stage,
        status=MCPServerStatusEnum.ACTIVE.value,
        description=faker.pystr(),
        is_public=True,
        _resource_names="resource1;resource2",
    )


@pytest.fixture
def fake_mcp_server_inactive(fake_gateway, fake_stage, faker):
    return G(
        MCPServer,
        name=faker.pystr()[:20],
        gateway=fake_gateway,
        stage=fake_stage,
        status=MCPServerStatusEnum.INACTIVE.value,
        description=faker.pystr(),
    )


class TestMCPServerListCreateApi:
    def test_list(self, request_view, fake_gateway, fake_mcp_server):
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] >= 1

    def test_create(self, mocker, request_view, fake_gateway, fake_stage, faker):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )

        # name 只能包含小写字母、数字和短横线
        data = {
            "name": "test-mcp-server-" + faker.pystr()[:10].lower().replace("_", "-"),
            "description": faker.pystr(),
            "stage_id": fake_stage.id,
            "is_public": True,
            "labels": ["test"],
            "resource_names": ["resource1", "resource2"],
        }

        resp = request_view(
            method="POST",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 201
        assert "id" in result["data"]

        mcp_server = MCPServer.objects.get(id=result["data"]["id"])
        assert mcp_server.name == data["name"]
        assert mcp_server.description == data["description"]

    def test_create_with_prompts(self, mocker, request_view, fake_gateway, fake_stage, faker):
        """测试创建 MCPServer 时同时创建 prompts"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )

        data = {
            "name": "test-mcp-server-" + faker.pystr()[:10].lower().replace("_", "-"),
            "description": faker.pystr(),
            "stage_id": fake_stage.id,
            "is_public": True,
            "labels": ["test"],
            "resource_names": ["resource1", "resource2"],
            "prompts": [
                {
                    "id": 1,
                    "name": "代码审查助手",
                    "code": "prompt_001",
                    "content": "你是一个代码审查专家...",
                    "labels": ["代码"],
                    "is_public": True,
                },
            ],
        }

        resp = request_view(
            method="POST",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 201
        assert "id" in result["data"]

        mcp_server_id = result["data"]["id"]

        # 验证 prompts 已保存
        extend = MCPServerExtend.objects.get(
            mcp_server_id=mcp_server_id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )
        saved_prompts = json.loads(extend.content)
        assert len(saved_prompts) == 1
        assert saved_prompts[0]["id"] == 1
        assert saved_prompts[0]["code"] == "prompt_001"


class TestMCPServerRetrieveUpdateDestroyApi:
    def test_retrieve(self, request_view, fake_gateway, fake_mcp_server):
        resp = request_view(
            method="GET",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == fake_mcp_server.id
        assert result["data"]["name"] == fake_mcp_server.name

    def test_update(self, mocker, request_view, fake_gateway, fake_mcp_server, faker):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2", "resource3"},
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )

        data = {
            "description": faker.pystr(),
            "is_public": False,
            "labels": ["new-label"],
            "resource_names": ["resource1", "resource3"],
        }

        resp = request_view(
            method="PUT",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        fake_mcp_server.refresh_from_db()
        assert fake_mcp_server.description == data["description"]
        assert fake_mcp_server.is_public == data["is_public"]

    def test_destroy_active_failed(self, request_view, fake_gateway, fake_mcp_server):
        resp = request_view(
            method="DELETE",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )

        assert resp.status_code == 400

    def test_destroy_inactive_success(self, request_view, fake_gateway, fake_mcp_server_inactive):
        resp = request_view(
            method="DELETE",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server_inactive.id},
            gateway=fake_gateway,
        )

        assert resp.status_code == 204
        assert not MCPServer.objects.filter(id=fake_mcp_server_inactive.id).exists()


class TestMCPServerUpdateStatusApi:
    def test_update_status(self, request_view, fake_gateway, fake_mcp_server):
        data = {
            "status": MCPServerStatusEnum.INACTIVE.value,
        }

        resp = request_view(
            method="PATCH",
            view_name="mcp_server.update_status",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        fake_mcp_server.refresh_from_db()
        assert fake_mcp_server.status == MCPServerStatusEnum.INACTIVE.value


class TestMCPServerUpdateLabelsApi:
    def test_update_labels(self, request_view, fake_gateway, fake_mcp_server):
        data = {
            "labels": ["label1", "label2"],
        }

        resp = request_view(
            method="PATCH",
            view_name="mcp_server.update_labels",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        fake_mcp_server.refresh_from_db()
        assert fake_mcp_server.labels == data["labels"]


class TestMCPServerToolsListApi:
    def test_list(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_tools_resources_and_labels",
            return_value=([], {}),
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.tools_list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )

        assert resp.status_code == 200


class TestMCPServerGuidelineRetrieveApi:
    def test_retrieve(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.apis.web.mcp_server.views.render_to_string",
            return_value="# Guideline Content",
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.guideline_retrieve",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "content" in result["data"]


class TestMCPServerToolDocRetrieveApi:
    def test_retrieve(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_tool_doc",
            return_value={
                "type": "markdown",
                "content": "# Tool Doc",
                "updated_time": now_datetime(),
                "schema": {},
            },
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.tool_doc_retrieve",
            path_params={
                "gateway_id": fake_gateway.id,
                "mcp_server_id": fake_mcp_server.id,
                "tool_name": "resource1",
            },
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "content" in result["data"]


class TestMCPServerUserCustomDocApi:
    def test_retrieve_empty(self, request_view, fake_gateway, fake_mcp_server):
        resp = request_view(
            method="GET",
            view_name="mcp_server.user_custom_doc",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["content"] == ""

    def test_retrieve_with_content(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerExtend,
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
            content="# Custom Doc",
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.user_custom_doc",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["content"] == "# Custom Doc"

    def test_create(self, request_view, fake_gateway, fake_mcp_server):
        data = {
            "content": "# New Custom Doc",
        }

        resp = request_view(
            method="POST",
            view_name="mcp_server.user_custom_doc",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 201

        extend = MCPServerExtend.objects.get(
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
        )
        assert extend.content == data["content"]

    def test_create_already_exists(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerExtend,
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
            content="# Existing Doc",
        )

        data = {
            "content": "# New Custom Doc",
        }

        resp = request_view(
            method="POST",
            view_name="mcp_server.user_custom_doc",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 400

    def test_update(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerExtend,
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
            content="# Old Doc",
        )

        data = {
            "content": "# Updated Custom Doc",
        }

        resp = request_view(
            method="PUT",
            view_name="mcp_server.user_custom_doc",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        extend = MCPServerExtend.objects.get(
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
        )
        assert extend.content == data["content"]

    def test_update_not_exists(self, request_view, fake_gateway, fake_mcp_server):
        data = {
            "content": "# New Custom Doc",
        }

        resp = request_view(
            method="PUT",
            view_name="mcp_server.user_custom_doc",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 404

    def test_destroy(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerExtend,
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
            content="# Custom Doc",
        )

        resp = request_view(
            method="DELETE",
            view_name="mcp_server.user_custom_doc",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )

        assert resp.status_code == 204
        assert not MCPServerExtend.objects.filter(
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
        ).exists()


class TestMCPServerStageReleaseCheckApi:
    def test_check_no_mcp_servers(self, request_view, fake_gateway, fake_stage):
        resp = request_view(
            method="GET",
            view_name="mcp_server.stage_release_check",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_version_id": 1,
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["has_related_changes"] is False

    def test_check_with_mcp_servers(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.biz.resource_version.ResourceVersionHandler.get_resource_names_set",
            return_value={"resource1"},
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.stage_release_check",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_mcp_server.stage.id,
                "resource_version_id": 1,
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["has_related_changes"] is True
        assert result["data"]["deleted_resource_count"] == 1


class TestMCPServerAppPermissionListCreateApi:
    def test_list(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerAppPermission,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission.list_create",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1

    def test_list_with_filter(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerAppPermission,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
        )
        G(
            MCPServerAppPermission,
            mcp_server=fake_mcp_server,
            bk_app_code="another-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission.list_create",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data={"bk_app_code": "test"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1

    def test_create(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )

        data = {
            "bk_app_code": "new-app",
        }

        resp = request_view(
            method="POST",
            view_name="mcp_server.app-permission.list_create",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 201
        assert MCPServerAppPermission.objects.filter(
            mcp_server=fake_mcp_server,
            bk_app_code="new-app",
        ).exists()


class TestMCPServerAppPermissionDestroyApi:
    def test_destroy(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )

        permission = G(
            MCPServerAppPermission,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
        )

        resp = request_view(
            method="DELETE",
            view_name="mcp_server.app-permission.destroy",
            path_params={
                "gateway_id": fake_gateway.id,
                "mcp_server_id": fake_mcp_server.id,
                "id": permission.id,
            },
            gateway=fake_gateway,
        )

        assert resp.status_code == 204
        assert not MCPServerAppPermission.objects.filter(id=permission.id).exists()


class TestMCPServerAppPermissionApplyListApi:
    def test_list_pending(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            applied_by="admin",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission-apply.list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data={"state": "unprocessed"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1

    def test_list_processed(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            applied_by="admin",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission-apply.list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data={"state": "processed"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1


class TestMCPServerAppPermissionApplyApplicantListApi:
    def test_list(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            applied_by="user1",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app2",
            applied_by="user2",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission-apply.applicant_list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["applicants"]) == 2


class TestMCPServerAppPermissionApplyUpdateStatusApi:
    def test_approve(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )

        apply = G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            applied_by="admin",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        data = {
            "status": MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            "comment": "approved",
        }

        resp = request_view(
            method="PATCH",
            view_name="mcp_server.app-permission-apply.update_status",
            path_params={
                "gateway_id": fake_gateway.id,
                "mcp_server_id": fake_mcp_server.id,
                "id": apply.id,
            },
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        apply.refresh_from_db()
        assert apply.status == MCPServerAppPermissionApplyStatusEnum.APPROVED.value

        assert MCPServerAppPermission.objects.filter(
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
        ).exists()

    def test_reject(self, request_view, fake_gateway, fake_mcp_server):
        apply = G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            applied_by="admin",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        data = {
            "status": MCPServerAppPermissionApplyStatusEnum.REJECTED.value,
            "comment": "rejected",
        }

        resp = request_view(
            method="PATCH",
            view_name="mcp_server.app-permission-apply.update_status",
            path_params={
                "gateway_id": fake_gateway.id,
                "mcp_server_id": fake_mcp_server.id,
                "id": apply.id,
            },
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        apply.refresh_from_db()
        assert apply.status == MCPServerAppPermissionApplyStatusEnum.REJECTED.value


class TestMCPServerRetrieveUpdateDestroyApiPartialUpdate:
    """测试 PATCH 部分更新"""

    def test_partial_update(self, mocker, request_view, fake_gateway, fake_mcp_server, faker):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )

        original_is_public = fake_mcp_server.is_public
        new_description = faker.pystr()

        data = {
            "description": new_description,
        }

        resp = request_view(
            method="PATCH",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        fake_mcp_server.refresh_from_db()
        assert fake_mcp_server.description == new_description
        # 确保其他字段未被修改
        assert fake_mcp_server.is_public == original_is_public


class TestMCPServerAppPermissionListCreateApiWithGrantTypeFilter:
    """测试按 grant_type 过滤"""

    def test_list_filter_by_grant_type(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerAppPermission,
            mcp_server=fake_mcp_server,
            bk_app_code="grant-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
        )
        G(
            MCPServerAppPermission,
            mcp_server=fake_mcp_server,
            bk_app_code="apply-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission.list_create",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data={"grant_type": MCPServerAppPermissionGrantTypeEnum.GRANT.value},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "grant-app"


class TestMCPServerAppPermissionApplyListApiWithFilters:
    """测试按 bk_app_code 和 applied_by 过滤"""

    def test_list_filter_by_bk_app_code(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="target-app",
            applied_by="user1",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="other-app",
            applied_by="user2",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission-apply.list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data={"state": "unprocessed", "bk_app_code": "target-app"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "target-app"

    def test_list_filter_by_applied_by(self, request_view, fake_gateway, fake_mcp_server):
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app1",
            applied_by="target-user",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app2",
            applied_by="other-user",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission-apply.list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data={"state": "unprocessed", "applied_by": "target-user"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["applied_by"] == "target-user"


class TestMCPServerStageReleaseCheckApiNoChanges:
    """测试环境发布检查无变更的情况"""

    def test_check_no_changes(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.biz.resource_version.ResourceVersionHandler.get_resource_names_set",
            return_value={"resource1", "resource2"},  # 包含所有 mcp_server 的资源
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.stage_release_check",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_mcp_server.stage.id,
                "resource_version_id": 1,
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["has_related_changes"] is False


class TestMCPServerAppPermissionDestroyApiWithApprovedApply:
    """测试删除权限时同时更新已通过的申请记录"""

    def test_destroy_with_approved_apply(self, mocker, request_view, fake_gateway, fake_mcp_server):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )

        permission = G(
            MCPServerAppPermission,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
        )

        apply_record = G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="test-app",
            applied_by="admin",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            is_deleted=False,
        )

        resp = request_view(
            method="DELETE",
            view_name="mcp_server.app-permission.destroy",
            path_params={
                "gateway_id": fake_gateway.id,
                "mcp_server_id": fake_mcp_server.id,
                "id": permission.id,
            },
            gateway=fake_gateway,
        )

        assert resp.status_code == 204
        assert not MCPServerAppPermission.objects.filter(id=permission.id).exists()

        # 验证申请记录被标记为已删除
        apply_record.refresh_from_db()
        assert apply_record.is_deleted is True


class TestMCPServerUserCustomDocApiDestroyNonExistent:
    """测试删除不存在的自定义文档"""

    def test_destroy_non_existent(self, request_view, fake_gateway, fake_mcp_server):
        # 没有创建 MCPServerExtend 记录

        resp = request_view(
            method="DELETE",
            view_name="mcp_server.user_custom_doc",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )

        # 删除不存在的记录应该成功（幂等）
        assert resp.status_code == 204


# ========== Prompts 相关 API 测试 ==========


class TestMCPServerRemotePromptsListApi:
    """测试从第三方平台获取 Prompts 列表"""

    def test_list(self, mocker, request_view, fake_gateway):
        mock_prompts = [
            {
                "id": 1,
                "name": "代码审查助手",
                "code": "prompt_001",
                "content": "你是一个代码审查专家...",
                "updated_time": "2025-12-15T10:00:00Z",
                "labels": ["代码", "审查"],
                "is_public": True,
                "space_code": "devops",
            },
            {
                "id": 2,
                "name": "API 文档生成器",
                "code": "prompt_002",
                "content": "请根据以下代码生成 API 文档...",
                "updated_time": "2025-12-14T15:30:00Z",
                "labels": ["文档", "API"],
                "is_public": True,
                "space_code": "devops",
            },
        ]

        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.fetch_remote_prompts",
            return_value=mock_prompts,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.remote_prompts_list",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["prompts"]) == 2
        assert result["data"]["prompts"][0]["id"] == 1
        assert result["data"]["prompts"][0]["name"] == "代码审查助手"
        assert result["data"]["prompts"][0]["code"] == "prompt_001"

    def test_list_with_keyword(self, mocker, request_view, fake_gateway):
        mock_prompts = [
            {
                "id": 1,
                "name": "代码审查助手",
                "code": "prompt_001",
                "content": "你是一个代码审查专家...",
                "updated_time": "2025-12-15T10:00:00Z",
                "labels": ["代码"],
                "is_public": True,
                "space_code": "devops",
            },
        ]

        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.fetch_remote_prompts",
            return_value=mock_prompts,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.remote_prompts_list",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"keyword": "代码"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["prompts"]) == 1

    def test_list_empty(self, mocker, request_view, fake_gateway):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.fetch_remote_prompts",
            return_value=[],
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.remote_prompts_list",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["prompts"]) == 0

    def test_update_invalid_prompts_missing_name(self, request_view, fake_gateway, fake_mcp_server):
        """测试更新时缺少必填字段 name"""
        data = {
            "prompts": [
                {
                    "id": 1,
                    "code": "prompt_001",
                },
            ],
        }

        resp = request_view(
            method="PUT",
            view_name="mcp_server.prompts",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 400


class TestMCPServerPromptsApi:
    """测试 MCPServer Prompts 更新 API"""

    def test_update_prompts(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试更新 prompts"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )

        data = {
            "description": fake_mcp_server.description,
            "prompts": [
                {
                    "id": 1,
                    "name": "代码审查助手",
                    "code": "prompt_001",
                    "content": "你是一个代码审查专家...",
                    "updated_time": "2025-12-15T10:00:00Z",
                    "updated_by": "admin",
                    "labels": ["代码", "审查"],
                    "is_public": True,
                    "space_code": "devops",
                    "space_name": "DevOps",
                },
                {
                    "id": 2,
                    "name": "API 文档生成器",
                    "code": "prompt_002",
                    "content": "请根据以下代码生成 API 文档...",
                    "updated_time": "2025-12-14T15:30:00Z",
                    "updated_by": "developer",
                    "labels": ["文档", "API"],
                    "is_public": True,
                    "space_code": "devops",
                    "space_name": "DevOps",
                },
            ],
        }

        resp = request_view(
            method="PUT",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        # 验证 prompts 已保存
        extend = MCPServerExtend.objects.get(
            mcp_server_id=fake_mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )
        saved_prompts = json.loads(extend.content)
        assert len(saved_prompts) == 2
        assert saved_prompts[0]["id"] == 1
        assert saved_prompts[0]["name"] == "代码审查助手"
        assert saved_prompts[0]["space_name"] == "DevOps"
        assert saved_prompts[1]["id"] == 2
        assert saved_prompts[1]["updated_by"] == "developer"

    def test_update_prompts_clear(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试清空 prompts"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )

        # 先创建一些 prompts
        G(
            MCPServerExtend,
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([{"id": 1, "name": "test", "code": "test_001"}]),
        )

        data = {
            "description": fake_mcp_server.description,
            "prompts": [],
        }

        resp = request_view(
            method="PUT",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        # 验证 prompts 已清空
        extend = MCPServerExtend.objects.get(
            mcp_server_id=fake_mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )
        saved_prompts = json.loads(extend.content)
        assert len(saved_prompts) == 0

    def test_update_prompts_partial(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试部分更新不传 prompts 字段，不影响已有 prompts"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )

        # 先创建一些 prompts
        original_prompts = [{"id": 1, "name": "test", "code": "test_001"}]
        G(
            MCPServerExtend,
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps(original_prompts),
        )

        # 只更新 description，不传 prompts
        data = {
            "description": "new description",
        }

        resp = request_view(
            method="PATCH",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
            data=data,
        )

        assert resp.status_code == 204

        # 验证 prompts 未被修改
        extend = MCPServerExtend.objects.get(
            mcp_server_id=fake_mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )
        saved_prompts = json.loads(extend.content)
        assert len(saved_prompts) == 1
        assert saved_prompts[0]["id"] == 1
