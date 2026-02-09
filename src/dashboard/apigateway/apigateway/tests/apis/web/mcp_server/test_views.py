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
    FEATURED_MCP_CATEGORY_NAME,
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerExtendTypeEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermission,
    MCPServerAppPermissionApply,
    MCPServerCategory,
    MCPServerExtend,
)
from apigateway.core.models import Stage
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
def fake_categories():
    """创建测试分类"""
    # 先清理已有的分类数据（可能由迁移文件创建）
    MCPServerCategory.objects.all().delete()

    official_category = G(
        MCPServerCategory,
        name=OFFICIAL_MCP_CATEGORY_NAME,
        display_name="官方",
        description="官方提供的 MCP Server",
        sort_order=1,
        is_active=True,
    )

    devops_category = G(
        MCPServerCategory,
        name="DevOps",
        display_name="运维工具",
        description="运维相关的工具和服务",
        sort_order=3,
        is_active=True,
    )

    return {
        "official": official_category,
        "devops": devops_category,
    }


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

        # 验证返回的数据中包含分类相关字段
        mcp_server_data = next(
            (item for item in result["data"]["results"] if item["id"] == fake_mcp_server.id),
            None,
        )
        assert mcp_server_data is not None
        assert "updated_time" in mcp_server_data
        assert "created_time" in mcp_server_data
        assert "categories" in mcp_server_data
        assert "is_official" in mcp_server_data
        assert "is_featured" in mcp_server_data

    def test_list_with_prompts_count(self, request_view, fake_gateway, fake_mcp_server):
        """测试列表接口返回 prompts_count"""
        # 给 fake_mcp_server 添加 prompts
        G(
            MCPServerExtend,
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([{"id": 1, "name": "prompt1"}, {"id": 2, "name": "prompt2"}]),
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] >= 1

        # 找到 fake_mcp_server 对应的数据
        mcp_server_data = next(
            (item for item in result["data"]["results"] if item["id"] == fake_mcp_server.id),
            None,
        )
        assert mcp_server_data is not None
        assert mcp_server_data["prompts_count"] == 2

    def test_list_with_categories(self, request_view, fake_gateway, fake_mcp_server, fake_categories):
        """测试列表接口返回分类信息"""
        # 给 mcp_server 添加分类
        fake_mcp_server.categories.add(fake_categories["official"], fake_categories["devops"])

        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200

        # 找到对应的数据
        mcp_server_data = next(
            (item for item in result["data"]["results"] if item["id"] == fake_mcp_server.id),
            None,
        )
        assert mcp_server_data is not None
        assert len(mcp_server_data["categories"]) == 2
        assert mcp_server_data["is_official"] is True
        assert mcp_server_data["is_featured"] is False

        # 验证分类信息
        category_names = [cat["name"] for cat in mcp_server_data["categories"]]
        assert OFFICIAL_MCP_CATEGORY_NAME in category_names
        assert "DevOps" in category_names

    def test_list_with_status_filter(self, request_view, fake_gateway, fake_mcp_server, fake_mcp_server_inactive):
        """测试列表接口按状态筛选"""
        # 筛选启用状态
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"status": MCPServerStatusEnum.ACTIVE.value},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        # 验证只返回启用状态的 MCPServer
        for item in result["data"]["results"]:
            assert item["status"] == MCPServerStatusEnum.ACTIVE.value

        # 筛选停用状态
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"status": MCPServerStatusEnum.INACTIVE.value},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        # 验证只返回停用状态的 MCPServer
        for item in result["data"]["results"]:
            assert item["status"] == MCPServerStatusEnum.INACTIVE.value

    def test_list_with_keyword_search(self, request_view, fake_gateway, fake_stage):
        """测试列表接口关键词搜索"""
        # 创建测试数据
        server1 = G(
            MCPServer,
            name="test_search_server",
            title="搜索测试服务",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            description="这是一个测试描述",
        )
        G(
            MCPServer,
            name="other_server",
            title="其他服务",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            description="另一个描述",
        )

        # 按名称搜索
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"keyword": "test_search"},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["name"] == server1.name

        # 按标题搜索
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"keyword": "搜索测试"},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["id"] == server1.id

    def test_list_with_order_by(self, request_view, fake_gateway, fake_stage):
        """测试列表接口排序功能"""
        # 创建测试数据
        server_a = G(
            MCPServer,
            name="aaa_server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server_z = G(
            MCPServer,
            name="zzz_server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.INACTIVE.value,
        )

        # 按名称正序排序
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"order_by": "name"},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        names = [item["name"] for item in result["data"]["results"]]
        assert names.index("aaa_server") < names.index("zzz_server")

        # 按名称倒序排序
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"order_by": "-name"},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        names = [item["name"] for item in result["data"]["results"]]
        assert names.index("zzz_server") < names.index("aaa_server")

        # 按更新时间排序
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"order_by": "-updated_time"},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["results"]) >= 2

    def test_list_with_stage_filter(self, request_view, fake_gateway, fake_stage):
        """测试列表接口按环境筛选"""
        # 创建另一个环境
        other_stage = G(Stage, gateway=fake_gateway, name="other_stage")

        # 创建两个不同环境的 MCPServer
        server1 = G(
            MCPServer,
            name="server_stage1",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        G(
            MCPServer,
            name="server_stage2",
            gateway=fake_gateway,
            stage=other_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 按环境筛选
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"stage_id": fake_stage.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        # 验证只返回指定环境的 MCPServer
        for item in result["data"]["results"]:
            assert item["stage"]["id"] == fake_stage.id

    def test_list_with_label_filter(self, request_view, fake_gateway, fake_stage):
        """测试列表接口按标签筛选"""
        # 创建带标签的 MCPServer
        server1 = G(
            MCPServer,
            name="server_with_label",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server1.labels = ["important", "production"]
        server1.save()

        G(
            MCPServer,
            name="server_without_label",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 按标签筛选
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"label": "important"},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["name"] == server1.name

    def test_list_with_category_filter(self, request_view, fake_gateway, fake_stage, fake_categories):
        """测试列表接口按分类筛选"""
        # 创建带分类的 MCPServer
        server1 = G(
            MCPServer,
            name="server_with_category",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server1.categories.add(fake_categories["official"])

        server2 = G(
            MCPServer,
            name="server_devops",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server2.categories.add(fake_categories["devops"])

        # 按分类筛选
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"categories": OFFICIAL_MCP_CATEGORY_NAME},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["name"] == server1.name

        # 筛选另一个分类
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"categories": "DevOps"},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["name"] == server2.name

    def test_list_with_multiple_categories_filter(self, request_view, fake_gateway, fake_stage, fake_categories):
        """测试列表接口按多个分类筛选（逗号分隔）- 包含 Official 时使用 AND 逻辑"""
        # 创建同时属于 official 和 devops 分类的 MCPServer
        server1 = G(
            MCPServer,
            name="server_official_devops",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server1.categories.add(fake_categories["official"])
        server1.categories.add(fake_categories["devops"])

        # 创建只有 devops 分类的 MCPServer
        server2 = G(
            MCPServer,
            name="server_devops",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server2.categories.add(fake_categories["devops"])

        # 创建只有 official 分类的 MCPServer
        server3 = G(
            MCPServer,
            name="server_official",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server3.categories.add(fake_categories["official"])

        # 创建无分类的 MCPServer
        server4 = G(
            MCPServer,
            name="server_no_category",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 筛选多个分类（包含 Official 时使用 AND 逻辑）
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"categories": f"{OFFICIAL_MCP_CATEGORY_NAME},DevOps"},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        # 只有 server1 同时属于 official 和 devops 分类
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["name"] == server1.name

    def test_list_with_multiple_categories_filter_with_spaces(
        self, request_view, fake_gateway, fake_stage, fake_categories
    ):
        """测试列表接口按多个分类筛选（带空格）- 包含 Official 时使用 AND 逻辑"""
        # 创建同时属于 official 和 devops 分类的 MCPServer
        server1 = G(
            MCPServer,
            name="server_official_devops",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server1.categories.add(fake_categories["official"])
        server1.categories.add(fake_categories["devops"])

        # 创建只有 devops 分类的 MCPServer
        server2 = G(
            MCPServer,
            name="server_devops",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server2.categories.add(fake_categories["devops"])

        # 筛选多个分类（带空格，验证空格会被正确处理）- 包含 Official 时使用 AND 逻辑
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"categories": f" {OFFICIAL_MCP_CATEGORY_NAME} , DevOps "},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        # 只有 server1 同时属于 official 和 devops 分类
        assert result["data"]["count"] == 1

    def test_list_with_empty_category_filter(self, request_view, fake_gateway, fake_stage, fake_categories):
        """测试列表接口空分类筛选"""
        # 创建带分类的 MCPServer
        server1 = G(
            MCPServer,
            name="server_official",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server1.categories.add(fake_categories["official"])

        # 空分类应该返回所有结果
        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"categories": ""},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] >= 1

    def test_create_with_categories(self, mocker, request_view, fake_gateway, fake_stage, fake_categories):
        """测试创建 MCPServer 时设置分类"""
        mocker.patch(
            "apigateway.biz.validators.MCPServerHandler.get_valid_resource_names",
            return_value=["resource1", "resource2"],
        )

        data = {
            "name": "test-mcp-server",
            "title": "测试 MCP Server",
            "description": "测试描述",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
            "category_ids": [fake_categories["official"].id, fake_categories["devops"].id],
        }

        resp = request_view(
            method="POST",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
            gateway=fake_gateway,
        )

        assert resp.status_code == 201
        result = resp.json()

        # 验证创建的 MCPServer 有正确的分类
        mcp_server = MCPServer.objects.get(id=result["data"]["id"])
        assert mcp_server.categories.count() == 2
        assert mcp_server.is_official() is True
        assert mcp_server.is_featured() is False

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
            "tool_names": ["resource1", "resource2"],
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
        # mock _fill_prompts_content 避免调用第三方 API
        mocker.patch(
            "apigateway.apis.web.mcp_server.serializers._fill_prompts_content",
            side_effect=lambda x: x,
        )

        data = {
            "name": "test-mcp-server-" + faker.pystr()[:10].lower().replace("_", "-"),
            "description": faker.pystr(),
            "stage_id": fake_stage.id,
            "is_public": True,
            "labels": ["test"],
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
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
        assert "updated_time" in result["data"]

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
            "tool_names": ["tool1", "tool3"],
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


class TestMCPServerConfigListApi:
    def test_retrieve_config_list(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试获取配置列表（默认 AIDEV 关闭）"""
        mocker.patch(
            "apigateway.apis.web.mcp_server.views.render_to_string",
            return_value="# Config Content",
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.config_list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "configs" in result["data"]
        # 默认 AIDEV_ENABLED=False，只有 3 个配置项
        assert len(result["data"]["configs"]) >= 3

        # 验证基本配置项名称
        config_names = [config["name"] for config in result["data"]["configs"]]
        assert "cursor" in config_names
        assert "codebuddy" in config_names
        assert "claude" in config_names

        # 验证每个配置项都有必要的字段
        for config in result["data"]["configs"]:
            assert "name" in config
            assert "display_name" in config
            assert "content" in config
            assert "install_url" in config

        # 验证 Cursor 有 install_url（一键配置链接）
        cursor_config = next((c for c in result["data"]["configs"] if c["name"] == "cursor"), None)
        assert cursor_config is not None
        assert cursor_config["install_url"].startswith("cursor://anysphere.cursor-deeplink/mcp/install")

        # 验证其他工具没有 install_url（暂不支持）
        for config in result["data"]["configs"]:
            if config["name"] != "cursor":
                assert config["install_url"] == ""

    def test_retrieve_config_list_with_aidev_enabled(
        self, mocker, settings, request_view, fake_gateway, fake_mcp_server
    ):
        """测试获取配置列表（配置了 AIDEV_CREATE_URL）"""
        mocker.patch(
            "apigateway.apis.web.mcp_server.views.render_to_string",
            return_value="# Config Content",
        )
        # 模拟配置了 AIDEV_AGENT_CREATE_URL（AIDev 启用）
        settings.MCP_CONFIG_AGENT_CLIENTS = [
            {"name": "codebuddy", "display_name": "CodeBuddy"},
            {"name": "cursor", "display_name": "Cursor"},
            {"name": "claude", "display_name": "Claude"},
            {"name": "aidev", "display_name": "AIDev"},
        ]

        resp = request_view(
            method="GET",
            view_name="mcp_server.config_list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "configs" in result["data"]
        assert len(result["data"]["configs"]) == 4

        # 验证配置项名称包含 aidev
        config_names = [config["name"] for config in result["data"]["configs"]]
        assert "cursor" in config_names
        assert "codebuddy" in config_names
        assert "claude" in config_names
        assert "aidev" in config_names

    def test_retrieve_config_list_display_names(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试配置项显示名称"""
        mocker.patch(
            "apigateway.apis.web.mcp_server.views.render_to_string",
            return_value="# Config Content",
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.config_list",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200

        # 验证显示名称
        config_map = {config["name"]: config["display_name"] for config in result["data"]["configs"]}
        assert config_map["cursor"] == "Cursor"
        assert config_map["codebuddy"] == "CodeBuddy"
        assert config_map["claude"] == "Claude"


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
    def test_list_pending_with_mcp_server_id(self, request_view, fake_gateway, fake_mcp_server):
        """测试按 mcp_server_id 查询"""
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
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"state": "unprocessed", "mcp_server_id": fake_mcp_server.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1

    def test_list_processed_with_mcp_server_id(self, request_view, fake_gateway, fake_mcp_server):
        """测试按 mcp_server_id 查询已处理的审批"""
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
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"state": "processed", "mcp_server_id": fake_mcp_server.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1

    def test_list_all_mcp_servers_without_mcp_server_id(self, request_view, fake_gateway, fake_stage, faker):
        """测试不传 mcp_server_id 查询网关下所有 MCP Server 的审批"""
        # 创建两个 MCP Server（使用 _resource_names 字段存储资源名称）
        mcp_server_1 = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="mcp-server-1",
            _resource_names="resource1",
        )
        mcp_server_2 = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="mcp-server-2",
            _resource_names="resource2",
        )

        # 为两个 MCP Server 分别创建审批记录
        G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server_1,
            bk_app_code="app-1",
            applied_by="user1",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server_2,
            bk_app_code="app-2",
            applied_by="user2",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        # 不传 mcp_server_id，查询所有
        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission-apply.list",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"state": "unprocessed"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 2
        bk_app_codes = {item["bk_app_code"] for item in result["data"]["results"]}
        assert bk_app_codes == {"app-1", "app-2"}


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
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"state": "unprocessed", "mcp_server_id": fake_mcp_server.id, "bk_app_code": "target-app"},
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
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"state": "unprocessed", "mcp_server_id": fake_mcp_server.id, "applied_by": "target-user"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["applied_by"] == "target-user"

    def test_list_filter_by_bk_app_code_without_mcp_server_id(self, request_view, fake_gateway, fake_stage, faker):
        """测试不传 mcp_server_id 时按 bk_app_code 过滤"""
        mcp_server_1 = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="mcp-server-1",
            _resource_names="resource1",
        )
        mcp_server_2 = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="mcp-server-2",
            _resource_names="resource2",
        )

        G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server_1,
            bk_app_code="target-app",
            applied_by="user1",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server_2,
            bk_app_code="other-app",
            applied_by="user2",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        # 不传 mcp_server_id，只按 bk_app_code 过滤
        resp = request_view(
            method="GET",
            view_name="mcp_server.app-permission-apply.list",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"state": "unprocessed", "bk_app_code": "target-app"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "target-app"


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
            "apigateway.apis.web.mcp_server.views.get_user_credentials_from_request",
            return_value=mocker.MagicMock(),
        )
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

    def test_list_empty(self, mocker, request_view, fake_gateway):
        mocker.patch(
            "apigateway.apis.web.mcp_server.views.get_user_credentials_from_request",
            return_value=mocker.MagicMock(),
        )
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

    def test_update_invalid_prompts_missing_name(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试更新时缺少必填字段 name"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )

        data = {
            "description": fake_mcp_server.description,
            "prompts": [
                {
                    "id": 1,
                    "code": "prompt_001",
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

        assert resp.status_code == 400


class TestMCPServerPromptsApi:
    """测试 MCPServer Prompts 更新 API"""

    def test_update_prompts(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试更新 prompts"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        # mock _fill_prompts_content 避免调用第三方 API
        mocker.patch(
            "apigateway.apis.web.mcp_server.serializers._fill_prompts_content",
            side_effect=lambda x: x,
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

    def test_update_prompts_fill_content_from_remote(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试更新 prompts 时自动从第三方获取 content"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        # mock fetch_remote_prompts_by_ids 返回带 content 的数据
        mocker.patch(
            "apigateway.biz.mcp_server.prompt.MCPServerPromptHandler.fetch_remote_prompts_by_ids",
            return_value=[
                {"id": 1, "content": "远程获取的内容1"},
                {"id": 2, "content": "远程获取的内容2"},
            ],
        )

        data = {
            "description": fake_mcp_server.description,
            "prompts": [
                {
                    "id": 1,
                    "name": "Prompt 1",
                    "code": "prompt_001",
                    "content": "",  # 空 content
                },
                {
                    "id": 2,
                    "name": "Prompt 2",
                    "code": "prompt_002",
                    "content": "本地已有内容",  # 有 content，但也会被远程覆盖
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

        # 验证 content 已被远程数据覆盖
        extend = MCPServerExtend.objects.get(
            mcp_server_id=fake_mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )
        saved_prompts = json.loads(extend.content)
        assert len(saved_prompts) == 2
        assert saved_prompts[0]["content"] == "远程获取的内容1"
        assert saved_prompts[1]["content"] == "远程获取的内容2"


class TestMCPServerProtocolType:
    """测试 MCPServer 协议类型相关功能"""

    def test_create_with_default_protocol_type(self, mocker, request_view, fake_gateway, fake_stage, faker):
        """测试创建 MCPServer 时默认协议类型为 SSE"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        # mock _fill_prompts_content 避免调用第三方 API
        mocker.patch(
            "apigateway.apis.web.mcp_server.serializers._fill_prompts_content",
            side_effect=lambda x: x,
        )

        data = {
            "name": "test-mcp-server-" + faker.pystr()[:10].lower().replace("_", "-"),
            "description": faker.pystr(),
            "stage_id": fake_stage.id,
            "is_public": True,
            "labels": ["test"],
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["tool1", "tool2"],
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
        mcp_server = MCPServer.objects.get(id=result["data"]["id"])
        assert mcp_server.protocol_type == MCPServerProtocolTypeEnum.SSE.value

    def test_create_with_streamable_http_protocol_type(self, mocker, request_view, fake_gateway, fake_stage, faker):
        """测试创建 MCPServer 时指定 Streamable HTTP 协议类型"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        # mock _fill_prompts_content 避免调用第三方 API
        mocker.patch(
            "apigateway.apis.web.mcp_server.serializers._fill_prompts_content",
            side_effect=lambda x: x,
        )

        data = {
            "name": "test-mcp-server-" + faker.pystr()[:10].lower().replace("_", "-"),
            "description": faker.pystr(),
            "stage_id": fake_stage.id,
            "is_public": True,
            "labels": ["test"],
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["tool1", "tool2"],
            "protocol_type": MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value,
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
        mcp_server = MCPServer.objects.get(id=result["data"]["id"])
        assert mcp_server.protocol_type == MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value

    def test_update_protocol_type(self, mocker, request_view, fake_gateway, fake_mcp_server, faker):
        """测试更新 MCPServer 协议类型"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )

        # 确保初始协议类型为 SSE
        fake_mcp_server.protocol_type = MCPServerProtocolTypeEnum.SSE.value
        fake_mcp_server.save()

        data = {
            "description": faker.pystr(),
            "protocol_type": MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value,
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
        assert fake_mcp_server.protocol_type == MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value

    def test_list_returns_protocol_type(self, request_view, fake_gateway, fake_mcp_server):
        """测试列表接口返回 protocol_type"""
        fake_mcp_server.protocol_type = MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value
        fake_mcp_server.save()

        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        mcp_server_data = next(
            (item for item in result["data"]["results"] if item["id"] == fake_mcp_server.id),
            None,
        )
        assert mcp_server_data is not None
        assert mcp_server_data["protocol_type"] == MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value

    def test_retrieve_returns_protocol_type(self, request_view, fake_gateway, fake_mcp_server):
        """测试详情接口返回 protocol_type"""
        fake_mcp_server.protocol_type = MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value
        fake_mcp_server.save()

        resp = request_view(
            method="GET",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["protocol_type"] == MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value

    def test_guideline_returns_correct_url_for_sse(self, mocker, request_view, fake_gateway, fake_mcp_server):
        """测试 guideline 接口返回正确的 SSE URL"""
        fake_mcp_server.protocol_type = MCPServerProtocolTypeEnum.SSE.value
        fake_mcp_server.save()

        mock_render = mocker.patch(
            "apigateway.apis.web.mcp_server.views.render_to_string",
            return_value="# Guideline Content",
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.guideline_retrieve",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )

        assert resp.status_code == 200
        # 验证传递给模板的 protocol_type 参数
        call_args = mock_render.call_args
        context = call_args[1]["context"]
        assert context["protocol_type"] == MCPServerProtocolTypeEnum.SSE.value
        assert "/sse/" in context["url"]

    def test_guideline_returns_correct_url_for_streamable_http(
        self, mocker, request_view, fake_gateway, fake_mcp_server
    ):
        """测试 guideline 接口返回正确的 Streamable HTTP URL"""
        fake_mcp_server.protocol_type = MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value
        fake_mcp_server.save()

        mock_render = mocker.patch(
            "apigateway.apis.web.mcp_server.views.render_to_string",
            return_value="# Guideline Content",
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.guideline_retrieve",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )

        assert resp.status_code == 200
        # 验证传递给模板的 protocol_type 参数
        call_args = mock_render.call_args
        context = call_args[1]["context"]
        assert context["protocol_type"] == MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value
        assert "/mcp/" in context["url"]


class TestMCPServerRemotePromptsBatchApi:
    """测试批量获取第三方平台 Prompts 内容的 API"""

    def test_batch_get_prompts(self, mocker, request_view, fake_gateway):
        """测试批量获取 prompts 内容"""
        mock_prompts = [
            {
                "id": 1,
                "name": "代码审查助手",
                "code": "prompt_001",
                "content": "你是一个代码审查专家...",
                "updated_time": "2025-12-15T10:00:00Z",
                "labels": ["代码", "审查"],
                "is_public": True,
            },
            {
                "id": 2,
                "name": "API 文档生成器",
                "code": "prompt_002",
                "content": "请根据以下代码生成 API 文档...",
                "updated_time": "2025-12-14T15:30:00Z",
                "labels": ["文档", "API"],
                "is_public": True,
            },
        ]

        mocker.patch(
            "apigateway.biz.mcp_server.prompt.MCPServerPromptHandler.fetch_remote_prompts_by_ids",
            return_value=mock_prompts,
        )

        resp = request_view(
            method="POST",
            view_name="mcp_server.remote_prompts_batch",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"ids": [1, 2]},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["prompts"]) == 2
        assert result["data"]["prompts"][0]["id"] == 1
        assert result["data"]["prompts"][0]["content"] == "你是一个代码审查专家..."
        assert result["data"]["prompts"][1]["id"] == 2

    def test_batch_get_prompts_empty_ids(self, mocker, request_view, fake_gateway):
        """测试空 ID 列表返回错误"""
        resp = request_view(
            method="POST",
            view_name="mcp_server.remote_prompts_batch",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"ids": []},
        )

        assert resp.status_code == 400

    def test_batch_get_prompts_partial_found(self, mocker, request_view, fake_gateway):
        """测试部分 ID 找到的情况"""
        mock_prompts = [
            {
                "id": 1,
                "name": "代码审查助手",
                "code": "prompt_001",
                "content": "你是一个代码审查专家...",
            },
        ]

        mocker.patch(
            "apigateway.biz.mcp_server.prompt.MCPServerPromptHandler.fetch_remote_prompts_by_ids",
            return_value=mock_prompts,
        )

        resp = request_view(
            method="POST",
            view_name="mcp_server.remote_prompts_batch",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={"ids": [1, 999]},  # 999 不存在
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["prompts"]) == 1
        assert result["data"]["prompts"][0]["id"] == 1


class TestMCPServerCategoriesListApi:
    """测试 MCPServer 分类列表 API"""

    def test_list_categories_success(self, request_view, fake_gateway):
        """测试成功获取分类列表"""
        # 先清理已有的分类数据（可能由迁移文件创建）
        MCPServerCategory.objects.all().delete()

        # 创建不同类型的分类
        G(
            MCPServerCategory,
            name=OFFICIAL_MCP_CATEGORY_NAME,
            display_name="官方",
            is_active=True,
            sort_order=1,
        )
        G(
            MCPServerCategory,
            name=FEATURED_MCP_CATEGORY_NAME,
            display_name="精选",
            is_active=True,
            sort_order=2,
        )
        G(
            MCPServerCategory,
            name="DevOps",
            display_name="运维工具",
            is_active=True,
            sort_order=3,
        )
        G(
            MCPServerCategory,
            name="Monitoring",
            display_name="监控告警",
            is_active=True,
            sort_order=4,
        )
        # 创建一个非活跃的分类
        G(
            MCPServerCategory,
            name="Inactive",
            display_name="非活跃",
            is_active=False,
            sort_order=5,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.categories_list",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "data" in result

        # 应该只返回活跃的且非官方/精选的分类
        categories = result["data"]
        assert len(categories) == 2  # 只有 DevOps 和 Monitoring

        # 验证返回的分类不包含官方和精选
        category_names = [cat["name"] for cat in categories]
        assert OFFICIAL_MCP_CATEGORY_NAME not in category_names
        assert FEATURED_MCP_CATEGORY_NAME not in category_names
        assert "DevOps" in category_names
        assert "Monitoring" in category_names

        # 验证排序
        assert categories[0]["name"] == "DevOps"
        assert categories[1]["name"] == "Monitoring"

        # 验证字段完整性
        for category in categories:
            assert "id" in category
            assert "name" in category
            assert "display_name" in category
            assert "description" in category
            assert "sort_order" in category

    def test_list_categories_empty(self, request_view, fake_gateway):
        """测试没有可用分类时的情况"""
        # 先清理已有的分类数据（可能由迁移文件创建）
        MCPServerCategory.objects.all().delete()

        # 只创建官方和精选分类
        G(
            MCPServerCategory,
            name=OFFICIAL_MCP_CATEGORY_NAME,
            display_name="官方",
            is_active=True,
        )
        G(
            MCPServerCategory,
            name=FEATURED_MCP_CATEGORY_NAME,
            display_name="精选",
            is_active=True,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.categories_list",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "data" in result
        assert len(result["data"]) == 0  # 应该为空


class TestMCPServerFilterOptionsApi:
    """测试 MCPServer 筛选选项接口"""

    def test_filter_options_success(self, request_view, fake_gateway, fake_stage, fake_mcp_server):
        """测试成功获取筛选选项"""
        # 先清理已有的分类数据
        MCPServerCategory.objects.all().delete()

        # 创建分类
        G(
            MCPServerCategory,
            name=OFFICIAL_MCP_CATEGORY_NAME,
            display_name="官方",
            is_active=True,
            sort_order=1,
        )
        G(
            MCPServerCategory,
            name="DevOps",
            display_name="运维工具",
            is_active=True,
            sort_order=2,
        )

        # 给 MCPServer 添加标签
        fake_mcp_server.labels = ["tag1", "tag2", "tag3"]
        fake_mcp_server.save()

        resp = request_view(
            method="GET",
            view_name="mcp_server.filter_options",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "data" in result

        data = result["data"]

        # 验证环境列表
        assert "stages" in data
        assert len(data["stages"]) >= 1
        stage_ids = [s["id"] for s in data["stages"]]
        assert fake_stage.id in stage_ids

        # 验证标签列表
        assert "labels" in data
        assert "tag1" in data["labels"]
        assert "tag2" in data["labels"]
        assert "tag3" in data["labels"]

        # 验证分类列表（包含所有分类，包括官方）
        assert "categories" in data
        category_names = [c["name"] for c in data["categories"]]
        assert OFFICIAL_MCP_CATEGORY_NAME in category_names
        assert "DevOps" in category_names

    def test_filter_options_empty_labels(self, request_view, fake_gateway, fake_stage):
        """测试没有标签时返回空列表"""
        # 创建一个没有标签的 MCPServer
        G(
            MCPServer,
            name="no_labels_server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _labels="",  # 没有标签
        )

        resp = request_view(
            method="GET",
            view_name="mcp_server.filter_options",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "data" in result
        # labels 应该为空或只包含其他 MCPServer 的标签
        assert "labels" in result["data"]

    def test_filter_options_multiple_mcp_servers(self, request_view, fake_gateway, fake_stage):
        """测试多个 MCPServer 的标签合并"""
        # 创建多个 MCPServer，每个有不同的标签
        server1 = G(
            MCPServer,
            name="server1",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server1.labels = ["tag1", "tag2"]
        server1.save()

        server2 = G(
            MCPServer,
            name="server2",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server2.labels = ["tag2", "tag3"]
        server2.save()

        resp = request_view(
            method="GET",
            view_name="mcp_server.filter_options",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        labels = result["data"]["labels"]

        # 验证标签被正确合并和去重
        assert "tag1" in labels
        assert "tag2" in labels
        assert "tag3" in labels
        # 验证标签按字母顺序排序
        assert labels == sorted(labels)


# ========== OAuth2 认证相关测试 ==========


class TestMCPServerOAuth2Enabled:
    """测试 MCPServer OAuth2 认证相关功能"""

    def test_create_with_oauth2_enabled(self, mocker, request_view, fake_gateway, fake_stage, faker):
        """测试创建 MCPServer 时开启 OAuth2 认证"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        mock_sync_oauth2 = mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_oauth2_permissions",
            return_value=None,
        )

        data = {
            "name": "test-mcp-oauth2-" + faker.pystr()[:10].lower().replace("_", "-"),
            "description": faker.pystr(),
            "stage_id": fake_stage.id,
            "is_public": True,
            "labels": ["test"],
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
            "oauth2_enabled": True,
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
        mcp_server = MCPServer.objects.get(id=result["data"]["id"])
        assert mcp_server.oauth2_enabled is True

        # 验证 sync_oauth2_permissions 被调用（传入的是 MCPServer 实例）
        mock_sync_oauth2.assert_called_once()
        assert mock_sync_oauth2.call_args[0][0].id == mcp_server.id

    def test_create_with_oauth2_disabled(self, mocker, request_view, fake_gateway, fake_stage, faker):
        """测试创建 MCPServer 时不开启 OAuth2 认证"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        mock_sync_oauth2 = mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_oauth2_permissions",
            return_value=None,
        )

        data = {
            "name": "test-mcp-no-oauth2-" + faker.pystr()[:10].lower().replace("_", "-"),
            "description": faker.pystr(),
            "stage_id": fake_stage.id,
            "is_public": True,
            "labels": ["test"],
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
            "oauth2_enabled": False,
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
        mcp_server = MCPServer.objects.get(id=result["data"]["id"])
        assert mcp_server.oauth2_enabled is False

        # 验证 sync_oauth2_permissions 未被调用
        mock_sync_oauth2.assert_not_called()

    def test_create_default_oauth2_disabled(self, mocker, request_view, fake_gateway, fake_stage, faker):
        """测试创建 MCPServer 时默认 OAuth2 认证关闭"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        mock_sync_oauth2 = mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_oauth2_permissions",
            return_value=None,
        )

        data = {
            "name": "test-mcp-default-" + faker.pystr()[:10].lower().replace("_", "-"),
            "description": faker.pystr(),
            "stage_id": fake_stage.id,
            "is_public": True,
            "labels": ["test"],
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
            # 不传 oauth2_enabled，默认应为 False
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
        mcp_server = MCPServer.objects.get(id=result["data"]["id"])
        assert mcp_server.oauth2_enabled is False

        # 验证 sync_oauth2_permissions 未被调用
        mock_sync_oauth2.assert_not_called()

    def test_update_enable_oauth2(self, mocker, request_view, fake_gateway, fake_mcp_server, faker):
        """测试更新 MCPServer 时开启 OAuth2 认证"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )
        mock_sync_oauth2 = mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_oauth2_permissions",
            return_value=None,
        )

        # 确保初始状态未开启
        fake_mcp_server.oauth2_enabled = False
        fake_mcp_server.save()

        data = {
            "description": faker.pystr(),
            "oauth2_enabled": True,
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
        assert fake_mcp_server.oauth2_enabled is True

        # 验证 sync_oauth2_permissions 被调用（传入的是 MCPServer 实例）
        mock_sync_oauth2.assert_called_once()
        assert mock_sync_oauth2.call_args[0][0].id == fake_mcp_server.id

    def test_update_disable_oauth2(self, mocker, request_view, fake_gateway, fake_mcp_server, faker):
        """测试更新 MCPServer 时关闭 OAuth2 认证"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )
        mock_sync_oauth2 = mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_oauth2_permissions",
            return_value=None,
        )

        # 初始状态开启 OAuth2
        fake_mcp_server.oauth2_enabled = True
        fake_mcp_server.save()

        data = {
            "description": faker.pystr(),
            "oauth2_enabled": False,
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
        assert fake_mcp_server.oauth2_enabled is False

        # 关闭 OAuth2 时也应调用 sync_oauth2_permissions（用于撤销 public 权限）
        mock_sync_oauth2.assert_called_once()
        assert mock_sync_oauth2.call_args[0][0].id == fake_mcp_server.id

    def test_update_full_with_oauth2_enabled(self, mocker, request_view, fake_gateway, fake_mcp_server, faker):
        """测试全量更新 MCPServer 时开启 OAuth2 认证"""
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_valid_resource_names",
            return_value={"resource1", "resource2"},
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_permissions",
            return_value=None,
        )
        mock_sync_oauth2 = mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.sync_oauth2_permissions",
            return_value=None,
        )

        data = {
            "description": faker.pystr(),
            "is_public": True,
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
            "oauth2_enabled": True,
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
        assert fake_mcp_server.oauth2_enabled is True

        # 验证 sync_oauth2_permissions 被调用（传入的是 MCPServer 实例）
        mock_sync_oauth2.assert_called_once()
        assert mock_sync_oauth2.call_args[0][0].id == fake_mcp_server.id

    def test_list_returns_oauth2_enabled(self, request_view, fake_gateway, fake_mcp_server):
        """测试列表接口返回 oauth2_enabled 字段"""
        fake_mcp_server.oauth2_enabled = True
        fake_mcp_server.save()

        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        mcp_server_data = next(
            (item for item in result["data"]["results"] if item["id"] == fake_mcp_server.id),
            None,
        )
        assert mcp_server_data is not None
        assert mcp_server_data["oauth2_enabled"] is True

    def test_list_returns_oauth2_disabled(self, request_view, fake_gateway, fake_mcp_server):
        """测试列表接口返回 oauth2_enabled=False"""
        fake_mcp_server.oauth2_enabled = False
        fake_mcp_server.save()

        resp = request_view(
            method="GET",
            view_name="mcp_server.list_create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        mcp_server_data = next(
            (item for item in result["data"]["results"] if item["id"] == fake_mcp_server.id),
            None,
        )
        assert mcp_server_data is not None
        assert mcp_server_data["oauth2_enabled"] is False

    def test_retrieve_returns_oauth2_enabled(self, request_view, fake_gateway, fake_mcp_server):
        """测试详情接口返回 oauth2_enabled 字段"""
        fake_mcp_server.oauth2_enabled = True
        fake_mcp_server.save()

        resp = request_view(
            method="GET",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["oauth2_enabled"] is True

    def test_retrieve_returns_oauth2_disabled(self, request_view, fake_gateway, fake_mcp_server):
        """测试详情接口返回 oauth2_enabled=False"""
        fake_mcp_server.oauth2_enabled = False
        fake_mcp_server.save()

        resp = request_view(
            method="GET",
            view_name="mcp_server.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "mcp_server_id": fake_mcp_server.id},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["oauth2_enabled"] is False
