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
from unittest.mock import ANY, patch

import pytest
from django_dynamic_fixture import G

from apigateway.apps.audit.constants import OpObjectTypeEnum
from apigateway.apps.audit.models import AuditEventLog
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.apps.gateway.models import GatewayAppBinding
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.biz.gateway import GatewayHandler
from apigateway.core.constants import GatewayKindEnum, GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import JWT, Gateway, GatewayRelatedApp, Release, ResourceVersion, Stage
from apigateway.service.gateway_jwt import GatewayJWTHandler


class TestGatewayListCreateApi:
    def test_list(self, request_view, fake_gateway):
        resp = request_view(
            method="GET",
            view_name="gateways.list_create",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) >= 1

    def test_create(self, request_view, faker, unique_gateway_name, default_data_plane):
        data = {
            "name": unique_gateway_name,
            "description": faker.pystr(),
            "maintainers": ["admin"],
            "is_public": False,
            "bk_app_codes": ["app1"],
            "tenant_mode": "single",
            "tenant_id": "default",
            "kind": GatewayKindEnum.NORMAL.value,
        }

        resp = request_view(
            method="POST",
            view_name="gateways.list_create",
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 201

        gateway = Gateway.objects.get(name=unique_gateway_name)
        assert result["data"]["id"] == gateway.id
        assert Stage.objects.filter(gateway=gateway).exists()
        assert JWT.objects.filter(gateway=gateway).count() == 1
        assert GatewayAppBinding.objects.filter(gateway=gateway).count() == 1
        assert gateway.kind == GatewayKindEnum.NORMAL.value

        auth_config = GatewayHandler.get_gateway_auth_config(gateway.id)
        assert auth_config["allow_auth_from_params"] is False
        assert auth_config["allow_delete_sensitive_params"] is False

        assert GatewayDataPlaneBinding.objects.filter(gateway=gateway, data_plane=default_data_plane).exists()

    def test_create_and_filter_ai_gateway(self, request_view, unique_gateway_name, default_data_plane):
        response = request_view(
            method="POST",
            view_name="gateways.list_create",
            data={
                "name": unique_gateway_name,
                "description": "AI gateway",
                "maintainers": ["admin"],
                "is_public": False,
                "kind": GatewayKindEnum.AI.value,
                "tenant_mode": "single",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 201
        gateway = Gateway.objects.get(name=unique_gateway_name)
        assert gateway.kind == GatewayKindEnum.AI.value

        response = request_view(
            method="GET",
            view_name="gateways.list_create",
            data={"kind": GatewayKindEnum.AI.value},
        )

        assert response.status_code == 200
        assert [item["id"] for item in response.json()["data"]["results"]] == [gateway.id]

    def test_create_ai_gateway_rejects_older_default_data_plane(
        self, request_view, unique_gateway_name, default_data_plane
    ):
        DataPlane.objects.filter(id=default_data_plane.id).update(apisix_version="3.13")

        response = request_view(
            method="POST",
            view_name="gateways.list_create",
            data={
                "name": unique_gateway_name,
                "description": "AI gateway",
                "maintainers": ["admin"],
                "is_public": False,
                "kind": GatewayKindEnum.AI.value,
                "tenant_mode": "single",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 400
        assert "APISIX 3.16 or later" in response.json()["error"]["message"]
        assert not Gateway.objects.filter(name=unique_gateway_name).exists()

    def test_create_programmable_gateway_without_repo_authorization__non_te(
        self,
        request_view,
        faker,
        mocker,
    ):
        name = f"pgw-{faker.pyint(min_value=10000, max_value=99999)}"
        data = {
            "name": name,
            "description": faker.pystr(),
            "maintainers": ["admin"],
            "is_public": False,
            "tenant_mode": "single",
            "tenant_id": "default",
            "kind": GatewayKindEnum.PROGRAMMABLE.value,
            "extra_info": {
                "language": "python",
                "repository": f"https://git.example.com/bkapps/{name}.git",
            },
        }
        mocker.patch("apigateway.apis.web.gateway.views.settings.EDITION", "ce")
        mocker.patch("apigateway.apis.web.gateway.validators.is_app_code_occupied", return_value=False)
        mock_create_paas_app = mocker.patch("apigateway.apis.web.gateway.views.create_paas_app")
        mocker.patch(
            "apigateway.apis.web.gateway.views.get_paas_repo_authorization",
            return_value={
                "authorized": False,
                "message": "用户未关联 oauth 授权",
                "address": "https://git.example.com/oauth/authorize",
                "auth_docs": "http://docs.example.com/tc_git_oauth",
            },
        )

        resp = request_view(
            method="POST",
            view_name="gateways.list_create",
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 403
        assert result["error"]["message"] == "用户未关联 oauth 授权"
        assert result["error"]["data"]["address"] == "https://git.example.com/oauth/authorize"
        assert not Gateway.objects.filter(name=name).exists()
        mock_create_paas_app.assert_not_called()

    def test_create_programmable_gateway_skip_repo_authorization_in_te(
        self,
        request_view,
        faker,
        mocker,
        default_data_plane,
    ):
        name = f"pgw-{faker.pyint(min_value=10000, max_value=99999)}"
        data = {
            "name": name,
            "description": faker.pystr(),
            "maintainers": ["admin"],
            "is_public": False,
            "tenant_mode": "single",
            "tenant_id": "default",
            "kind": GatewayKindEnum.PROGRAMMABLE.value,
            "extra_info": {
                "language": "python",
                "repository": f"https://git.example.com/bkapps/{name}.git",
            },
        }
        mocker.patch("apigateway.apis.web.gateway.views.settings.EDITION", "te")
        mocker.patch("apigateway.apis.web.gateway.validators.is_app_code_occupied", return_value=False)
        mock_repo_authorization = mocker.patch(
            "apigateway.apis.web.gateway.views.get_paas_repo_authorization",
            return_value={
                "authorized": False,
                "message": "用户未关联 oauth 授权",
                "address": "https://git.example.com/oauth/authorize",
                "auth_docs": "http://docs.example.com/tc_git_oauth",
            },
        )
        mock_create_paas_app = mocker.patch("apigateway.apis.web.gateway.views.create_paas_app", return_value=True)
        mock_update_app_maintainers = mocker.patch("apigateway.apis.web.gateway.views.update_app_maintainers")

        resp = request_view(
            method="POST",
            view_name="gateways.list_create",
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 201
        gateway = Gateway.objects.get(name=name)
        assert result["data"]["id"] == gateway.id
        assert gateway.kind == GatewayKindEnum.PROGRAMMABLE.value
        assert GatewayDataPlaneBinding.objects.filter(gateway=gateway, data_plane=default_data_plane).exists()
        mock_repo_authorization.assert_not_called()
        mock_create_paas_app.assert_called_once_with(
            app_code=name,
            language="python",
            git_info=None,
            user_credentials=ANY,
        )
        mock_update_app_maintainers.assert_called_once_with(name, ["admin"], user_credentials=ANY)

    @pytest.mark.parametrize(
        "data, expected_status_code, expected_error",
        [
            (
                {
                    "name": "test1",
                    "description": "test description",
                    "maintainers": ["admin"],
                    "is_public": False,
                    "bk_app_codes": ["app1"],
                    "tenant_mode": "global",
                    "tenant_id": "",
                },
                403,
                "只有运营租户下的用户才能创建全租户网关。",
            ),
            (
                {
                    "name": "test2",
                    "description": "test description",
                    "maintainers": ["admin"],
                    "is_public": False,
                    "bk_app_codes": ["app1"],
                    "tenant_mode": "single",
                    "tenant_id": "invalid_tenant",
                },
                403,
                "普通租户（非运营租户）只能创建当前用户租户下的单租户网关。",
            ),
            (
                {
                    "name": "test3",
                    "description": "test description",
                    "maintainers": ["admin"],
                    "is_public": False,
                    "bk_app_codes": ["app1"],
                    "tenant_mode": "single",
                    "tenant_id": "valid_tenant_id",
                },
                201,
                None,
            ),
        ],
    )
    @patch("apigateway.apis.web.gateway.views.settings.ENABLE_MULTI_TENANT_MODE", True)
    def test_create_with_multi_tenant_mode(
        self,
        request_view,
        faker,
        unique_gateway_name,
        default_data_plane,
        data,
        expected_status_code,
        expected_error,
    ):
        with patch("apigateway.apis.web.gateway.views.get_user_tenant_id", return_value="valid_tenant_id"):
            resp = request_view(
                method="POST",
                view_name="gateways.list_create",
                data=data,
            )
            result = resp.json()

            assert resp.status_code == expected_status_code
            if expected_error:
                assert expected_error in result["error"]["message"]
            else:
                gateway = Gateway.objects.get(name=data["name"])
                assert result["data"]["id"] == gateway.id
                assert Stage.objects.filter(gateway=gateway).exists()
                assert JWT.objects.filter(gateway=gateway).count() == 1
                assert GatewayAppBinding.objects.filter(gateway=gateway).count() == 1

                auth_config = GatewayHandler.get_gateway_auth_config(gateway.id)
                assert auth_config["allow_auth_from_params"] is False
                assert auth_config["allow_delete_sensitive_params"] is False

                assert GatewayDataPlaneBinding.objects.filter(gateway=gateway, data_plane=default_data_plane).exists()


class TestGatewayRetrieveUpdateDestroyApi:
    def test_retrieve(self, request_view, fake_gateway):
        GatewayJWTHandler.create_jwt(fake_gateway)
        GatewayHandler.save_auth_config(fake_gateway.id, "default")

        resp = request_view(
            method="GET",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == fake_gateway.id

    def test_update(self, request_view, faker, fake_gateway):
        data = {
            "description": faker.pystr(),
            "maintainers": ["admin"],
            "doc_maintainers": {
                "type": "user",
                "contacts": ["admin1", "admin2", "admin3"],
                "service_account": {
                    "name": "",
                    "link": "",
                },
            },
            "is_public": faker.random_element([True, False]),
            "bk_app_codes": ["app1"],
            "related_app_codes": ["app2"],
        }
        resp = request_view(
            method="PUT",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        gateway = Gateway.objects.get(id=fake_gateway.id)

        assert resp.status_code == 204
        assert gateway.description == data["description"]
        assert gateway.is_public is data["is_public"]
        assert GatewayAppBinding.objects.filter(gateway=gateway).count() == 1
        assert GatewayRelatedApp.objects.filter(gateway=gateway).count() == 1

        auth_config = GatewayHandler.get_gateway_auth_config(gateway.id)
        assert "allow_auth_from_params" not in auth_config
        assert "allow_delete_sensitive_params" not in auth_config

    def test_destroy(self, request_view, fake_gateway):
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()

        resp = request_view(
            method="DELETE",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )

        assert resp.status_code == 204
        assert fake_gateway.id is not None
        assert not Gateway.objects.filter(id=fake_gateway.id).exists()

    def test_destroy__failed(self, request_view, fake_gateway):
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        resp = request_view(
            method="DELETE",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )

        assert resp.status_code == 400


class TestGatewayUpdateStatusApi:
    def test_update(self, request_view, faker, fake_gateway):
        data = {
            "status": faker.random_element(GatewayStatusEnum.get_values()),
        }
        resp = request_view(
            method="PUT",
            view_name="gateways.update_status",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        gateway = Gateway.objects.get(id=fake_gateway.id)

        assert resp.status_code == 204
        assert gateway.status == data["status"]

    @pytest.mark.parametrize(
        "old_gateway_status, new_gateway_status, expected_comment",
        [
            (GatewayStatusEnum.INACTIVE.value, GatewayStatusEnum.ACTIVE.value, "发布环境"),
            (GatewayStatusEnum.ACTIVE.value, GatewayStatusEnum.INACTIVE.value, "下架环境"),
        ],
    )
    @patch("apigateway.apis.web.gateway.views.trigger_gateway_publish")
    def test_update_record_stage_audit(
        self,
        mock_trigger_gateway_publish,
        request_view,
        fake_gateway,
        old_gateway_status,
        new_gateway_status,
        expected_comment,
    ):
        fake_gateway.status = old_gateway_status
        fake_gateway.save()
        stage = G(Stage, gateway=fake_gateway, name="prod", status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=stage, status=MCPServerStatusEnum.ACTIVE.value)
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        G(Release, gateway=fake_gateway, stage=stage, resource_version=resource_version)

        resp = request_view(
            method="PUT",
            view_name="gateways.update_status",
            path_params={"gateway_id": fake_gateway.id},
            data={"status": new_gateway_status},
        )

        assert resp.status_code == 204
        mock_trigger_gateway_publish.assert_called_once()
        assert AuditEventLog.objects.filter(
            op_object_id=str(stage.id),
            op_object=stage.name,
            comment=expected_comment,
        ).exists()
        if new_gateway_status == GatewayStatusEnum.INACTIVE.value:
            mcp_server.refresh_from_db()
            assert mcp_server.status == MCPServerStatusEnum.INACTIVE.value
            mcp_server_audit_log = AuditEventLog.objects.get(
                op_object_type=OpObjectTypeEnum.MCP_SERVER.value,
                op_object_id=mcp_server.id,
            )
            assert mcp_server_audit_log.comment == "网关停用，同步停用其 MCP Server"


class TestGatewayCheckNameAvailableApi:
    def test_check_name_available__true(self, request_view, unique_gateway_name):
        """Test when gateway name is available (doesn't exist)"""
        resp = request_view(
            method="GET",
            view_name="gateways.check_name_available",
            data={"name": unique_gateway_name},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["is_available"] is True

    def test_check_name_available__false(self, request_view, fake_gateway):
        """Test when gateway name is not available (already exists)"""
        resp = request_view(
            method="GET",
            view_name="gateways.check_name_available",
            data={"name": fake_gateway.name},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["is_available"] is False


class TestGatewayRepoAuthorizationApi:
    def test_retrieve(self, request_view, mocker):
        mocker.patch(
            "apigateway.apis.web.gateway.views.get_paas_repo_authorization",
            return_value={
                "authorized": False,
                "message": "用户未关联 oauth 授权",
                "address": "https://git.example.com/oauth/authorize",
                "auth_docs": "http://docs.example.com/tc_git_oauth",
            },
        )

        resp = request_view(
            method="GET",
            view_name="gateways.repo_authorization",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"] == {
            "authorized": False,
            "message": "用户未关联 oauth 授权",
            "address": "https://git.example.com/oauth/authorize",
            "auth_docs": "http://docs.example.com/tc_git_oauth",
        }
