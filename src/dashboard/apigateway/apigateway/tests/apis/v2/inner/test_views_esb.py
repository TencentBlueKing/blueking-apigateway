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
from unittest import mock

import pytest
from ddf import G

from apigateway.apps.esb.bkcore.models import AppPermissionApplyRecord, ComponentSystem

pytestmark = pytest.mark.django_db


class TestEsbAppPermissionApplyRecordListApi:
    """测试组件权限申请记录列表 API 分页响应"""

    @pytest.fixture
    def fake_system(self):
        return G(ComponentSystem, name="test-system", description="Test System", board="default")

    def test_list_with_pagination(self, request_view, fake_system, mocker):
        """测试组件权限申请记录列表返回分页参数"""
        # Mock patch_permission_apply_records
        mocker.patch(
            "apigateway.apis.v2.inner.views_esb.ComponentPermissionManager.get_manager",
            return_value=mock.MagicMock(patch_permission_apply_records=mock.MagicMock()),
        )

        # 创建申请记录
        AppPermissionApplyRecord.objects.create_record(
            board="default",
            bk_app_code="test-app",
            applied_by="test-user",
            system=fake_system,
            component_ids=[1, 2, 3],
            status="pending",
            reason="test",
            expire_days=180,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.esb.permission.apply-records",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 验证分页参数存在
        assert "count" in result["data"]
        assert "results" in result["data"]
        # 验证数据
        assert result["data"]["count"] == 1
        assert len(result["data"]["results"]) == 1

    def test_list_empty_with_pagination(self, request_view, mocker):
        """测试空列表返回分页参数"""
        # Mock patch_permission_apply_records
        mocker.patch(
            "apigateway.apis.v2.inner.views_esb.ComponentPermissionManager.get_manager",
            return_value=mock.MagicMock(patch_permission_apply_records=mock.MagicMock()),
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.esb.permission.apply-records",
            data={"target_app_code": "non-existent-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 验证分页参数存在
        assert result["data"]["count"] == 0
        assert result["data"]["results"] == []
