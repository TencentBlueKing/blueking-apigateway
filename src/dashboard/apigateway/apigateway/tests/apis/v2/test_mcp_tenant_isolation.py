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
from unittest import mock

import pytest
from django_dynamic_fixture import G

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.biz.mcp_server import MCPServerHandler, MCPServerPermissionHandler
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Stage

TENANT_HEADER = {"HTTP_X_BK_TENANT_ID": "tenant-a"}
TARGET_APP_CODE = "tenant-isolation-app"


@pytest.fixture
def tenant_mcp_servers(settings):
    settings.ENABLE_MULTI_TENANT_MODE = True

    result = {}
    for key, tenant_mode, tenant_id in [
        ("global", TenantModeEnum.GLOBAL.value, ""),
        ("same", TenantModeEnum.SINGLE.value, "tenant-a"),
        ("other", TenantModeEnum.SINGLE.value, "tenant-b"),
    ]:
        gateway = G(
            Gateway,
            name=f"tenant-isolation-{key}-gateway",
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
            tenant_mode=tenant_mode,
            tenant_id=tenant_id,
        )
        stage = G(Stage, gateway=gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        result[key] = G(
            MCPServer,
            gateway=gateway,
            stage=stage,
            name=f"tenant-isolation-{key}-mcp",
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )

    return result


def _create_permissions(tenant_mcp_servers):
    return {
        key: G(
            MCPServerAppPermission,
            bk_app_code=TARGET_APP_CODE,
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
        )
        for key, mcp_server in tenant_mcp_servers.items()
    }


def _create_apply_records(tenant_mcp_servers):
    return {
        key: G(
            MCPServerAppPermissionApply,
            bk_app_code=TARGET_APP_CODE,
            mcp_server=mcp_server,
            applied_by="test-user",
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )
        for key, mcp_server in tenant_mcp_servers.items()
    }


class TestOpenMCPServerTenantIsolation:
    def test_list_filters_by_gateway_tenant(self, request_view, tenant_mcp_servers):
        response = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 200
        assert {item["name"] for item in response.json()["data"]["results"]} == {
            tenant_mcp_servers["global"].name,
            tenant_mcp_servers["same"].name,
        }

    def test_retrieve_hides_cross_tenant_mcp_server(self, request_view, tenant_mcp_servers, mocker):
        build_context = mocker.patch.object(
            MCPServerHandler,
            "build_retrieve_context",
            side_effect=AssertionError("cross-tenant MCP Server reached serialization"),
        )

        response = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.retrieve",
            path_params={"mcp_server_id": tenant_mcp_servers["other"].id},
            user=mock.MagicMock(username="test-user"),
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 404
        build_context.assert_not_called()

    def test_permission_list_hides_cross_tenant_mcp_server(self, request_view, tenant_mcp_servers):
        _create_permissions(tenant_mcp_servers)

        response = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.permissions.list",
            path_params={"mcp_server_id": tenant_mcp_servers["other"].id},
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 404

    def test_app_permission_list_filters_by_gateway_tenant(self, request_view, tenant_mcp_servers):
        _create_permissions(tenant_mcp_servers)

        response = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.app.permissions.list",
            data={"bk_app_code": TARGET_APP_CODE},
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 200
        assert {item["mcp_server"]["name"] for item in response.json()["data"]["results"]} == {
            tenant_mcp_servers["global"].name,
            tenant_mcp_servers["same"].name,
        }

    def test_apply_record_list_filters_by_gateway_tenant(self, request_view, tenant_mcp_servers):
        _create_apply_records(tenant_mcp_servers)

        response = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.app.permissions.apply-records.list",
            data={"bk_app_code": TARGET_APP_CODE},
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 200
        assert {item["mcp_server"]["name"] for item in response.json()["data"]["results"]} == {
            tenant_mcp_servers["global"].name,
            tenant_mcp_servers["same"].name,
        }

    def test_apply_record_lookup_filters_by_gateway_tenant(self, request_view, tenant_mcp_servers):
        records = _create_apply_records(tenant_mcp_servers)

        response = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.app.permissions.apply-records.lookup",
            data={
                "bk_app_code": TARGET_APP_CODE,
                "ids": ",".join(str(record.id) for record in records.values()),
            },
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 200
        assert {item["id"] for item in response.json()["data"]} == {
            records["global"].id,
            records["same"].id,
        }

    def test_user_list_filters_by_gateway_tenant(self, request_view, tenant_mcp_servers):
        response = request_view(
            method="GET",
            view_name="openapi.v2.open.user.mcp_server.list",
            user=mock.MagicMock(username="test-user"),
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 200
        assert {item["name"] for item in response.json()["data"]["results"]} == {
            tenant_mcp_servers["global"].name,
            tenant_mcp_servers["same"].name,
        }

    def test_apply_rejects_cross_tenant_mcp_server(self, request_view, tenant_mcp_servers, mocker):
        create_tickets = mocker.patch.object(MCPServerPermissionHandler, "_create_itsm_tickets_for_applies")

        response = request_view(
            method="POST",
            view_name="openapi.v2.open.mcp_server.app.permissions.apply",
            data={
                "bk_app_code": TARGET_APP_CODE,
                "mcp_server_ids": [tenant_mcp_servers["other"].id],
                "applied_by": "test-user",
                "reason": "tenant isolation",
            },
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 404
        assert not MCPServerAppPermissionApply.objects.filter(bk_app_code=TARGET_APP_CODE).exists()
        create_tickets.assert_not_called()


class TestInnerMCPServerTenantIsolation:
    def test_permission_list_filters_by_gateway_tenant(self, request_view, tenant_mcp_servers):
        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.list",
            data={"target_app_code": TARGET_APP_CODE},
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 200
        assert {item["mcp_server"]["name"] for item in response.json()["data"]} == {
            tenant_mcp_servers["global"].name,
            tenant_mcp_servers["same"].name,
        }

    def test_app_permission_list_filters_by_gateway_tenant(self, request_view, tenant_mcp_servers):
        _create_permissions(tenant_mcp_servers)

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.app-permissions",
            data={"target_app_code": TARGET_APP_CODE},
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 200
        assert {item["mcp_server"]["name"] for item in response.json()["data"]} == {
            tenant_mcp_servers["global"].name,
            tenant_mcp_servers["same"].name,
        }

    def test_apply_record_list_filters_by_gateway_tenant(self, request_view, tenant_mcp_servers):
        _create_apply_records(tenant_mcp_servers)

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.apply-records",
            data={"target_app_code": TARGET_APP_CODE},
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 200
        assert {item["mcp_server"]["name"] for item in response.json()["data"]} == {
            tenant_mcp_servers["global"].name,
            tenant_mcp_servers["same"].name,
        }

    def test_apply_record_detail_hides_cross_tenant_record(self, request_view, tenant_mcp_servers):
        records = _create_apply_records(tenant_mcp_servers)

        response = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.apply-record-detail",
            path_params={"record_id": records["other"].id},
            data={"target_app_code": TARGET_APP_CODE},
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 404

    def test_apply_rejects_cross_tenant_mcp_server(self, request_view, tenant_mcp_servers, mocker):
        create_tickets = mocker.patch.object(MCPServerPermissionHandler, "_create_itsm_tickets_for_applies")

        response = request_view(
            method="POST",
            view_name="openapi.v2.inner.mcp_server.permission.apply",
            data={
                "target_app_code": TARGET_APP_CODE,
                "mcp_server_ids": [tenant_mcp_servers["other"].id],
                "applied_by": "test-user",
                "reason": "tenant isolation",
            },
            app=mock.MagicMock(app_code="test"),
            **TENANT_HEADER,
        )

        assert response.status_code == 404
        assert not MCPServerAppPermissionApply.objects.filter(bk_app_code=TARGET_APP_CODE).exists()
        create_tickets.assert_not_called()
