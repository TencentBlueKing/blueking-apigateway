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
from django.test import Client
from django.urls import reverse

from apigateway.apps.permission.constants import (
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
    PermissionApplyExpireDaysEnum,
)
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord, AppResourcePermission
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.constants import GatewayStatusEnum

pytestmark = pytest.mark.django_db


class TestGatewayPermissionApplyCreateApi:
    def test_create_without_login(self, fake_gateway):
        response = Client().post(
            reverse("docs.gateway.permission.apply", kwargs={"gateway_name": fake_gateway.name}),
            data={
                "bk_app_code": "test-app",
                "resource_name": "test-resource",
                "reason": "",
            },
        )

        assert response.status_code == 401

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("is_public", False),
            ("status", GatewayStatusEnum.INACTIVE.value),
        ],
    )
    def test_create_rejects_unavailable_gateway(
        self,
        field,
        value,
        mocker,
        request_view,
        fake_gateway,
    ):
        setattr(fake_gateway, field, value)
        fake_gateway.save(update_fields=[field])
        get_apps = mocker.patch("apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username")

        response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "bk_app_code": "test-app",
                "resource_name": "test-resource",
                "reason": "",
            },
        )

        assert response.status_code == 404
        get_apps.assert_not_called()

    def test_create(
        self,
        settings,
        mocker,
        request_view,
        fake_gateway,
        fake_resource1,
        fake_release,
    ):
        settings.ENABLE_ITSM4_PERMISSION_APPLY = False
        get_apps = mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username",
            return_value=[{"code": "test-app"}],
        )
        apply_async_on_commit = mocker.patch("apigateway.biz.permission.manager.apply_async_on_commit")
        build_ticket_url = mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.ItsmPermissionApplyHelper.build_ticket_url",
            return_value="https://example.com/tickets/1",
        )

        response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "bk_app_code": "test-app",
                "resource_name": fake_resource1.name,
                "reason": "for test",
            },
        )
        result = response.json()

        assert response.status_code == 201
        record = AppPermissionRecord.objects.get(id=result["data"]["record_id"])
        apply = AppPermissionApply.objects.get(apply_record_id=record.id)
        assert result["data"] == {
            "record_id": record.id,
            "bk_app_code": "test-app",
            "gateway_name": fake_gateway.name,
            "resource_name": fake_resource1.name,
            "itsm_ticket_id": "",
            "itsm_ticket_url": "https://example.com/tickets/1",
        }
        assert record.resource_ids == [fake_resource1.id]
        assert record.grant_dimension == GrantDimensionEnum.RESOURCE.value
        assert record.expire_days == PermissionApplyExpireDaysEnum.FOREVER.value
        assert record.applied_by == "admin"
        assert apply.status == ApplyStatusEnum.PENDING.value
        assert apply.resource_ids == [fake_resource1.id]
        assert apply.reason == "for test"
        get_apps.assert_called_once_with("admin", "default")
        apply_async_on_commit.assert_called_once()
        build_ticket_url.assert_called_once_with("")

    def test_create_does_not_send_mail_when_itsm_ticket_exists(
        self,
        mocker,
        request_view,
        fake_gateway,
        fake_resource1,
        fake_release,
    ):
        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username",
            return_value=[{"code": "test-app"}],
        )
        manager = mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.PermissionDimensionManager.get_manager"
        ).return_value
        manager.apply_permission.return_value = mocker.Mock(id=1, itsm_ticket_id="ticket-1")
        apply_async_on_commit = mocker.patch("apigateway.biz.permission.manager.apply_async_on_commit")
        build_ticket_url = mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.ItsmPermissionApplyHelper.build_ticket_url",
            return_value="https://example.com/tickets/1",
        )

        response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "bk_app_code": "test-app",
                "resource_name": fake_resource1.name,
                "reason": "",
            },
        )

        assert response.status_code == 201
        assert response.json()["data"]["itsm_ticket_id"] == "ticket-1"
        assert response.json()["data"]["itsm_ticket_url"] == "https://example.com/tickets/1"
        apply_async_on_commit.assert_not_called()
        build_ticket_url.assert_called_once_with("ticket-1")

    def test_create_rejects_app_without_user_permission(
        self,
        mocker,
        request_view,
        fake_gateway,
        fake_resource1,
        fake_release,
    ):
        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username",
            return_value=[{"code": "other-app"}],
        )

        response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "bk_app_code": "test-app",
                "resource_name": fake_resource1.name,
                "reason": "",
            },
        )

        assert response.status_code == 400
        assert not AppPermissionApply.objects.filter(bk_app_code="test-app").exists()

    def test_create_rejects_app_from_another_tenant(
        self,
        settings,
        mocker,
        request_view,
        fake_gateway,
        fake_resource1,
        fake_release,
    ):
        settings.ENABLE_MULTI_TENANT_MODE = True
        fake_gateway.tenant_mode = TenantModeEnum.SINGLE.value
        fake_gateway.tenant_id = "tenant-a"
        fake_gateway.save(update_fields=["tenant_mode", "tenant_id"])
        user = mocker.MagicMock(username="admin", tenant_id="tenant-a", is_authenticated=True)
        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username",
            return_value=[{"code": "test-app"}],
        )
        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_app_tenant_info",
            return_value=(TenantModeEnum.SINGLE.value, "tenant-b"),
        )

        response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "bk_app_code": "test-app",
                "resource_name": fake_resource1.name,
                "reason": "",
            },
            user=user,
        )

        assert response.status_code == 403
        assert not AppPermissionApply.objects.filter(bk_app_code="test-app").exists()

    def test_create_rejects_unreleased_resource(
        self,
        mocker,
        request_view,
        fake_gateway,
        fake_resource1,
    ):
        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username",
            return_value=[{"code": "test-app"}],
        )

        response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "bk_app_code": "test-app",
                "resource_name": fake_resource1.name,
                "reason": "",
            },
        )

        assert response.status_code == 404
        assert not AppPermissionApply.objects.filter(bk_app_code="test-app").exists()

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("allow_apply_permission", False),
            ("app_verified_required", False),
            ("resource_perm_required", False),
        ],
    )
    def test_create_rejects_resource_not_applicable(
        self,
        field,
        value,
        mocker,
        request_view,
        fake_gateway,
        fake_resource1,
    ):
        resource_data = {
            "id": fake_resource1.id,
            "name": fake_resource1.name,
            "allow_apply_permission": True,
            "app_verified_required": True,
            "resource_perm_required": True,
        }
        resource_data[field] = value

        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username",
            return_value=[{"code": "test-app"}],
        )
        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.ResourceVersionHandler.get_released_public_resources",
            return_value=[resource_data],
        )

        response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "bk_app_code": "test-app",
                "resource_name": fake_resource1.name,
                "reason": "",
            },
        )

        assert response.status_code == 404
        assert not AppPermissionApply.objects.filter(bk_app_code="test-app").exists()

    def test_create_rejects_existing_pending_apply(
        self,
        settings,
        mocker,
        request_view,
        fake_gateway,
        fake_resource1,
        fake_release,
    ):
        settings.ENABLE_ITSM4_PERMISSION_APPLY = False
        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username",
            return_value=[{"code": "test-app"}],
        )
        mocker.patch("apigateway.biz.permission.manager.apply_async_on_commit")
        request_data = {
            "bk_app_code": "test-app",
            "resource_name": fake_resource1.name,
            "reason": "",
        }

        first_response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data=request_data,
        )
        second_response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data=request_data,
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 409
        assert second_response.json()["error"]["code"] == "CONFLICT"
        assert AppPermissionApply.objects.filter(bk_app_code="test-app").count() == 1

    def test_create_rejects_existing_unexpired_permission(
        self,
        mocker,
        request_view,
        fake_gateway,
        fake_resource1,
        fake_release,
    ):
        mocker.patch(
            "apigateway.apis.web.docs.gateway.permission.views.get_paas_apps_by_username",
            return_value=[{"code": "test-app"}],
        )
        G(
            AppResourcePermission,
            bk_app_code="test-app",
            gateway=fake_gateway,
            resource_id=fake_resource1.id,
            expires=None,
            grant_type=GrantTypeEnum.APPLY.value,
        )

        response = request_view(
            method="POST",
            view_name="docs.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "bk_app_code": "test-app",
                "resource_name": fake_resource1.name,
                "reason": "",
            },
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CONFLICT"
        assert not AppPermissionApply.objects.filter(bk_app_code="test-app").exists()
