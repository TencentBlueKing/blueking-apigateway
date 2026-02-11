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
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

from django_dynamic_fixture import G

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, Stage
from apigateway.tests.utils.testing import get_response_json


class TestGatewayListApi:
    def test_list(self, request_view, fake_gateway, mocker):
        g1 = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=False)
        G(Release, gateway=g1)
        g2 = G(Gateway, status=GatewayStatusEnum.INACTIVE.value, is_public=True)
        G(Release, gateway=g2)

        _ = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=True)

        # released
        g4 = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=True)
        G(Release, gateway=g4)
        G(Release, gateway=fake_gateway)

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.gateway.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()
        assert resp.status_code == 200
        assert len(result["data"]) == 2


class TestGatewayRetrieveApi:
    def test_retrieve(self, request_to_view, request_factory, fake_gateway):
        request = request_factory.get("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")
        response = request_to_view(
            request,
            view_name="openapi.v2.open.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["data"]["name"] == fake_gateway.name


class TestMCPServerAppPermissionApplyCreateApi:
    def test_create_returns_approval_url(self, request_view, fake_gateway, settings):
        """测试创建 MCP Server 权限申请时返回 approval_url"""
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/{gateway_id}/mcp/permission?serverId={mcp_server_id}"
        )

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )

        resp = request_view(
            method="POST",
            view_name="openapi.v2.open.mcp_server.app.permissions.apply",
            app=mock.MagicMock(app_code="test"),
            data={
                "bk_app_code": "test_app",
                "mcp_server_ids": [mcp_server.id],
                "reason": "test reason",
                "applied_by": "test_user",
            },
        )

        assert resp.status_code == 200
        result = resp.json()
        assert "data" in result
        assert len(result["data"]) > 0
        # 验证返回的数据包含 approval_url
        for item in result["data"]:
            assert "approval_url" in item
            assert f"/{fake_gateway.id}/mcp/permission?serverId={mcp_server.id}" in item["approval_url"]


class TestMCPServerAppPermissionRecordListApi:
    def test_list_returns_approval_url(self, request_view, fake_gateway, settings):
        """测试获取 MCP Server 权限申请记录时返回 approval_url"""
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/{gateway_id}/mcp/permission?serverId={mcp_server_id}"
        )

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test_app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="test_user",
            reason="test reason",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.app.permissions.apply-records.list",
            app=mock.MagicMock(app_code="test"),
            data={
                "bk_app_code": "test_app",
            },
        )

        assert resp.status_code == 200
        result = resp.json()
        assert "data" in result
        assert len(result["data"]) > 0
        # 验证返回的数据包含 approval_url
        for item in result["data"]:
            assert "approval_url" in item
            assert f"/{fake_gateway.id}/mcp/permission?serverId={mcp_server.id}" in item["approval_url"]


class TestGetDatetimeApi:
    def test_get_datetime_with_default_timezone(self, request_view, settings):
        """测试使用默认时区获取当前时间"""
        settings.TIME_ZONE = "Asia/Shanghai"

        with mock.patch("apigateway.apis.v2.open.views.datetime") as mock_datetime:
            # Mock datetime.now to return a fixed time
            mock_now = datetime(2025, 1, 7, 15, 30, 45, tzinfo=ZoneInfo("Asia/Shanghai"))
            mock_datetime.now.return_value = mock_now
            # Keep the original strptime for other uses
            mock_datetime.strptime = datetime.strptime

            resp = request_view(
                method="GET",
                view_name="openapi.v2.open.tools.time.get_datetime",
                app=mock.MagicMock(app_code="test"),
            )

            assert resp.status_code == 200
            result = resp.json()
            assert "data" in result
            assert "datetime" in result["data"]
            assert result["data"]["datetime"] == "2025-01-07 15:30:45"

    def test_get_datetime_with_custom_timezone(self, request_view):
        """测试使用自定义时区获取当前时间"""
        with mock.patch("apigateway.apis.v2.open.views.datetime") as mock_datetime:
            # Mock datetime.now to return a fixed time in UTC
            mock_now = datetime(2025, 1, 7, 10, 30, 45, tzinfo=ZoneInfo("UTC"))
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime = datetime.strptime

            resp = request_view(
                method="GET",
                view_name="openapi.v2.open.tools.time.get_datetime",
                app=mock.MagicMock(app_code="test"),
                data={"tz_name": "UTC"},
            )

            assert resp.status_code == 200
            result = resp.json()
            assert "data" in result
            assert "datetime" in result["data"]
            assert result["data"]["datetime"] == "2025-01-07 10:30:45"

    def test_get_datetime_with_invalid_timezone(self, request_view):
        """测试使用无效时区时返回错误"""
        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.tools.time.get_datetime",
            app=mock.MagicMock(app_code="test"),
            data={"tz_name": "Invalid/Timezone"},
        )

        assert resp.status_code == 400
        result = resp.json()
        assert "error" in result or "message" in result


class TestGetCurrentUnixTimestampApi:
    def test_get_current_unix_timestamp(self, request_view):
        """测试获取当前Unix时间戳"""
        with mock.patch("apigateway.apis.v2.open.views.time.time") as mock_time:
            mock_time.return_value = 1704628245.123

            resp = request_view(
                method="GET",
                view_name="openapi.v2.open.tools.time.get_current_unix_timestamp",
                app=mock.MagicMock(app_code="test"),
            )

            assert resp.status_code == 200
            result = resp.json()
            assert "data" in result
            assert "unix_timestamp" in result["data"]
            assert result["data"]["unix_timestamp"] == 1704628245

    def test_get_current_unix_timestamp_returns_integer(self, request_view):
        """测试返回的时间戳是整数类型"""
        with mock.patch("apigateway.apis.v2.open.views.time.time") as mock_time:
            mock_time.return_value = 1704628245.999

            resp = request_view(
                method="GET",
                view_name="openapi.v2.open.tools.time.get_current_unix_timestamp",
                app=mock.MagicMock(app_code="test"),
            )

            assert resp.status_code == 200
            result = resp.json()
            assert isinstance(result["data"]["unix_timestamp"], int)
            assert result["data"]["unix_timestamp"] == 1704628245


class TestParseDatetimeStrToTimestampApi:
    def test_parse_datetime_with_default_format(self, request_view):
        """测试使用默认格式解析时间字符串"""
        with mock.patch("apigateway.apis.v2.open.views.time.mktime") as mock_mktime:
            mock_mktime.return_value = 1704628245.0

            resp = request_view(
                method="POST",
                view_name="openapi.v2.open.tools.time.parse_datetime_str_to_timestamp",
                app=mock.MagicMock(app_code="test"),
                data={
                    "datetime": "2025-01-07 15:30:45",
                },
            )

            assert resp.status_code == 200
            result = resp.json()
            assert "data" in result
            assert "timestamp" in result["data"]
            assert result["data"]["timestamp"] == 1704628245

    def test_parse_datetime_with_custom_format(self, request_view):
        """测试使用自定义格式解析时间字符串"""
        with mock.patch("apigateway.apis.v2.open.views.time.mktime") as mock_mktime:
            mock_mktime.return_value = 1704628245.0

            resp = request_view(
                method="POST",
                view_name="openapi.v2.open.tools.time.parse_datetime_str_to_timestamp",
                app=mock.MagicMock(app_code="test"),
                data={
                    "datetime": "2025/01/07 15:30:45",
                    "datetime_format": "%Y/%m/%d %H:%M:%S",
                },
            )

            assert resp.status_code == 200
            result = resp.json()
            assert "data" in result
            assert "timestamp" in result["data"]
            assert result["data"]["timestamp"] == 1704628245

    def test_parse_datetime_with_invalid_format(self, request_view):
        """测试时间字符串格式不匹配时返回错误"""
        resp = request_view(
            method="POST",
            view_name="openapi.v2.open.tools.time.parse_datetime_str_to_timestamp",
            app=mock.MagicMock(app_code="test"),
            data={
                "datetime": "2025-01-07 15:30:45",
                "datetime_format": "%Y/%m/%d",
            },
        )

        assert resp.status_code == 400
        result = resp.json()
        assert "error" in result or "message" in result

    def test_parse_datetime_with_invalid_string(self, request_view):
        """测试无效的时间字符串时返回错误"""
        resp = request_view(
            method="POST",
            view_name="openapi.v2.open.tools.time.parse_datetime_str_to_timestamp",
            app=mock.MagicMock(app_code="test"),
            data={
                "datetime": "invalid-datetime-string",
                "datetime_format": "%Y-%m-%d %H:%M:%S",
            },
        )

        assert resp.status_code == 400
        result = resp.json()
        assert "error" in result or "message" in result


class TestMCPServerListApiOAuth2:
    """测试 MCPServer 列表接口返回 oauth2_enabled 字段"""

    def test_list_returns_oauth2_enabled(self, request_view, fake_gateway, settings):
        """测试 MCPServer 列表接口正确返回 oauth2_enabled 字段"""
        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
            oauth2_enabled=True,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )

        assert resp.status_code == 200
        result = resp.json()
        mcp_data = next(
            (item for item in result["data"]["results"] if item["id"] == mcp_server.id),
            None,
        )
        assert mcp_data is not None
        assert mcp_data["oauth2_enabled"] is True

    def test_list_returns_oauth2_disabled(self, request_view, fake_gateway, settings):
        """测试 MCPServer 列表接口返回 oauth2_enabled=False"""
        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
            oauth2_enabled=False,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )

        assert resp.status_code == 200
        result = resp.json()
        mcp_data = next(
            (item for item in result["data"]["results"] if item["id"] == mcp_server.id),
            None,
        )
        assert mcp_data is not None
        assert mcp_data["oauth2_enabled"] is False


class TestOAuthProtectedResourceApi:
    def test_get_oauth_protected_resource_success(self, request_view, settings):
        """测试成功获取 OAuth 保护资源元数据"""
        settings.BK_AUTH_SERVER_URL = "https://bkauth.example.com"
        resource_url = "https://api.example.com/resource"

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.well_known.oauth_protected_resource",
            data={"resource": resource_url},
        )

        assert resp.status_code == 200
        result = resp.json()
        assert result["resource"] == resource_url
        assert result["authorization_servers"] == ["https://bkauth.example.com"]
        assert result["bearer_methods_supported"] == ["header"]

    def test_get_oauth_protected_resource_returns_settings_auth_url(self, request_view, settings):
        """测试返回的 authorization_servers 使用 settings.BK_AUTH_SERVER_URL"""
        settings.BK_AUTH_SERVER_URL = "https://custom-auth.example.com"
        resource_url = "https://api.example.com/another-resource"

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.well_known.oauth_protected_resource",
            data={"resource": resource_url},
        )

        assert resp.status_code == 200
        result = resp.json()
        assert result["authorization_servers"] == ["https://custom-auth.example.com"]

    def test_get_oauth_protected_resource_missing_resource_param(self, request_view, settings):
        """测试缺少 resource 参数时返回错误"""
        settings.BK_AUTH_SERVER_URL = "https://bkauth.example.com"

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.well_known.oauth_protected_resource",
            data={},
        )

        assert resp.status_code == 400

    def test_get_oauth_protected_resource_empty_resource_param(self, request_view, settings):
        """测试 resource 参数为空时返回错误"""
        settings.BK_AUTH_SERVER_URL = "https://bkauth.example.com"

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.well_known.oauth_protected_resource",
            data={"resource": ""},
        )

        assert resp.status_code == 400
