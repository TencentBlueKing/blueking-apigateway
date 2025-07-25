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
import pytest
from ddf import G
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import DateTimeField

from apigateway.apis.web.gateway.serializers import (
    GatewayAPIDocMaintainerSLZ,
    GatewayCreateInputSLZ,
    GatewayListOutputSLZ,
    GatewayRetrieveOutputSLZ,
    GatewayUpdateInputSLZ,
    GatewayUpdateStatusInputSLZ,
    ProgrammableGatewayGitInfoSLZ,
)
from apigateway.biz.gateway import GatewayHandler
from apigateway.core.constants import GatewayTypeEnum
from apigateway.core.models import Gateway, Resource, Stage
from apigateway.service.contexts import GatewayAuthConfig
from apigateway.service.gateway_jwt import GatewayJWTHandler
from apigateway.utils.crypto import calculate_fingerprint


class TestGatewayListOutputSLZ:
    def test_to_representation(self):
        gateway_1 = G(Gateway, created_by="admin", status=1, is_public=True, tenant_mode="single", tenant_id="default")
        gateway_2 = G(
            Gateway, created_by="admin", status=0, is_public=False, tenant_mode="single", tenant_id="default"
        )

        stage_1 = G(Stage, gateway=gateway_1, name="prod")
        stage_2 = G(Stage, gateway=gateway_1, name="test")

        G(Resource, gateway=gateway_1)
        G(Resource, gateway=gateway_1)

        expected = [
            {
                "id": gateway_1.id,
                "name": gateway_1.name,
                "description": gateway_1.description,
                "created_by": gateway_1.created_by,
                "stages": [
                    {
                        "id": stage_1.id,
                        "name": stage_1.name,
                        "released": False,
                    },
                    {
                        "id": stage_2.id,
                        "name": stage_2.name,
                        "released": False,
                    },
                ],
                "resource_count": 2,
                "tenant_mode": "single",
                "tenant_id": "default",
                "status": 1,
                "kind": 0,
                "is_public": True,
                "is_official": True,
                "created_time": DateTimeField().to_representation(gateway_1.created_time),
                "updated_time": DateTimeField().to_representation(gateway_1.updated_time),
                "extra_info": {},
            },
            {
                "id": gateway_2.id,
                "name": gateway_2.name,
                "description": gateway_2.description,
                "created_by": gateway_2.created_by,
                "stages": [],
                "resource_count": 0,
                "tenant_mode": "single",
                "tenant_id": "default",
                "status": 0,
                "kind": 0,
                "is_public": False,
                "is_official": False,
                "created_time": DateTimeField().to_representation(gateway_2.created_time),
                "updated_time": DateTimeField().to_representation(gateway_2.updated_time),
                "extra_info": {},
            },
        ]
        gateways = Gateway.objects.filter(id__in=[gateway_1.id, gateway_2.id])
        gateway_ids = [gateway_1.id, gateway_2.id]
        slz = GatewayListOutputSLZ(
            gateways,
            many=True,
            context={
                "resource_count": GatewayHandler.get_resource_count(gateway_ids),
                "stages": GatewayHandler.get_stages_with_release_status(gateway_ids),
                "gateway_auth_configs": {
                    gateway_1.id: GatewayAuthConfig(GatewayTypeEnum.OFFICIAL_API.value),
                    gateway_2.id: GatewayAuthConfig(GatewayTypeEnum.CLOUDS_API.value),
                },
            },
        )
        assert slz.data == expected


class TestGatewayCreateInputSLZ:
    @pytest.mark.parametrize(
        "check_reserved_gateway_name, data, expected",
        [
            # ok
            (
                False,
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["guest"],
                    "developers": ["t1", "t2"],
                    "is_public": True,
                    "bk_app_codes": ["app1", "app2"],
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["guest", "admin"],
                    "developers": ["t1", "t2"],
                    "is_public": True,
                    "bk_app_codes": ["app1", "app2"],
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
            ),
            # ok, default value
            (
                False,
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["guest"],
                    "is_public": True,
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["guest", "admin"],
                    "developers": [],
                    "is_public": True,
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
            ),
            # name length < 3
            (
                False,
                {
                    "name": "ab",
                    "description": "test",
                    "maintainers": ["admin"],
                    "is_public": True,
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
                None,
            ),
            # name length > 32
            (
                False,
                {
                    "name": "a" * 50,
                    "description": "test",
                    "maintainers": ["admin"],
                    "is_public": True,
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
                None,
            ),
            # name contains invalid character
            (
                False,
                {
                    "name": "a_b_c",
                    "description": "test",
                    "maintainers": ["admin"],
                    "is_public": True,
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
                None,
            ),
            # name ends with invalid character
            (
                False,
                {
                    "name": "test-",
                    "description": "test",
                    "maintainers": ["admin"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "ieod",
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
                None,
            ),
            # name exists
            (
                False,
                {
                    "name": "create-test-exists",
                    "description": "test",
                    "maintainers": ["admin"],
                    "is_public": True,
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
                None,
            ),
            # name startswith bk-
            (
                True,
                {
                    "name": "bk-test",
                    "description": "test",
                    "maintainers": ["admin", "guest"],
                    "status": 1,
                    "is_public": True,
                    "tenant_mode": "single",
                    "tenant_id": "default",
                },
                None,
            ),
        ],
    )
    def test_validate(self, settings, check_reserved_gateway_name, data, expected):
        settings.CHECK_RESERVED_GATEWAY_NAME = check_reserved_gateway_name

        G(Gateway, name="create-test-exists")
        slz = GatewayCreateInputSLZ(data=data, context={"created_by": "admin"})
        slz.is_valid()
        if expected is None:
            assert slz.errors
            return

        assert slz.validated_data == expected


class TestGatewayRetrieveOutputSLZ:
    def test_to_representation(self, fake_gateway, fake_release, mocker):
        mocker.patch(
            "apigateway.apis.web.gateway.serializers.GatewayHandler.get_api_domain",
            return_value="http://bkapi.demo.com",
        )
        mocker.patch(
            "apigateway.apis.web.gateway.serializers.GatewayHandler.get_docs_url",
            return_value="http://apigw.demo.com/docs/",
        )

        slz = GatewayRetrieveOutputSLZ(
            instance=fake_gateway,
            context={
                "auth_config": GatewayAuthConfig(
                    gateway_type=GatewayTypeEnum.CLOUDS_API.value,
                    allow_update_gateway_auth=True,
                ),
                "bk_app_codes": [],
                "related_app_codes": [],
            },
        )
        jwt = GatewayJWTHandler.create_jwt(fake_gateway)

        expected = {
            "id": fake_gateway.id,
            "name": fake_gateway.name,
            "description": fake_gateway.description,
            "maintainers": fake_gateway.maintainers,
            "doc_maintainers": fake_gateway.doc_maintainers,
            "developers": fake_gateway.developers,
            "status": fake_gateway.status,
            "kind": fake_gateway.kind,
            "is_public": fake_gateway.is_public,
            "created_by": fake_gateway.created_by,
            "created_time": DateTimeField().to_representation(fake_gateway.created_time),
            "updated_time": DateTimeField().to_representation(fake_gateway.updated_time),
            "public_key": jwt.public_key,
            "allow_update_gateway_auth": True,
            "api_domain": "http://bkapi.demo.com",
            "docs_url": "http://apigw.demo.com/docs/",
            "public_key_fingerprint": calculate_fingerprint(jwt.public_key),
            "is_official": False,
            "bk_app_codes": [],
            "related_app_codes": [],
            "tenant_id": "default",
            "tenant_mode": "single",
            "extra_info": {},
            "links": {},
        }

        assert slz.data == expected

    def test_valid_maintainers(self, fake_gateway, fake_release):
        fake_gateway._maintainers = "admin;guest;;,,"
        fake_gateway.save()

        slz = GatewayRetrieveOutputSLZ(
            instance=fake_gateway,
            context={
                "auth_config": GatewayAuthConfig(
                    gateway_type=GatewayTypeEnum.CLOUDS_API.value,
                    allow_update_gateway_auth=True,
                ),
                "bk_app_codes": [],
                "related_app_codes": [],
            },
        )
        GatewayJWTHandler.create_jwt(fake_gateway)

        assert slz.data["maintainers"] == ["admin", "guest"]


class TestGatewayAPIDocMaintainerSLZ:
    @pytest.mark.parametrize(
        "data, expected, will_error",
        [
            (
                {
                    "type": "",
                    "contacts": [],
                    "service_account": {
                        "name": "",
                        "link": "",
                    },
                },
                {
                    "type": "",
                    "contacts": [],
                    "service_account": {
                        "name": "",
                        "link": "",
                    },
                },
                False,
            ),
            (
                {
                    "type": "user",
                    "contacts": ["admin1", "admin2", "admin3"],
                    "service_account": {
                        "name": "",
                        "link": "",
                    },
                },
                {
                    "type": "user",
                    "contacts": ["admin1", "admin2", "admin3"],
                    "service_account": {
                        "name": "",
                        "link": "",
                    },
                },
                False,
            ),
            (
                {
                    "type": "service_account",
                    "contacts": [],
                    "service_account": {
                        "name": "admin1",
                        "link": "wxwork://message?xxx",
                    },
                },
                {
                    "type": "service_account",
                    "contacts": [],
                    "service_account": {
                        "name": "admin1",
                        "link": "wxwork://message?xxx",
                    },
                },
                False,
            ),
            (
                {
                    "type": "user",
                    "contacts": [],
                    "service_account": {
                        "name": "",
                        "link": "",
                    },
                },
                None,
                True,
            ),
            (
                {
                    "type": "service_account",
                    "contacts": [],
                    "service_account": {
                        "name": "",
                        "link": "wxwork://message?xxx",
                    },
                },
                None,
                True,
            ),
            (
                {
                    "type": "service_account",
                    "contacts": [],
                    "service_account": {
                        "name": "admin",
                        "link": "",
                    },
                },
                None,
                True,
            ),
            (
                {
                    "type": "service_account",
                    "contacts": [],
                    "service_account": {
                        "name": "admin",
                        "link": "wxxxwork://message?xxx",
                    },
                },
                None,
                True,
            ),
        ],
    )
    def test_validate(self, data, expected, will_error):
        slz = GatewayAPIDocMaintainerSLZ(data=data)

        if not will_error:
            slz.is_valid(raise_exception=True)
            assert slz.validated_data == expected
            return

        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)


class TestGatewayUpdateInputSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "maintainers": ["admin"],
                    "doc_maintainers": {
                        "type": "user",
                        "contacts": ["admin1", "admin2", "admin3"],
                        "service_account": {
                            "name": "",
                            "link": "",
                        },
                    },
                    "developers": ["foo"],
                    "description": "test",
                    "is_public": True,
                    "bk_app_codes": ["app1", "app2"],
                    "related_app_codes": ["app1", "app2"],
                },
                {
                    "maintainers": ["admin"],
                    "doc_maintainers": {
                        "type": "user",
                        "contacts": ["admin1", "admin2", "admin3"],
                        "service_account": {
                            "name": "",
                            "link": "",
                        },
                    },
                    "developers": ["foo"],
                    "description": "test",
                    "is_public": True,
                    "bk_app_codes": ["app1", "app2"],
                    "related_app_codes": ["app1", "app2"],
                },
            ),
            (
                {
                    "maintainers": ["admin"],
                    "doc_maintainers": {
                        "type": "service_account",
                        "contacts": [],
                        "service_account": {
                            "name": "admin1",
                            "link": "wxwork://message?xxx",
                        },
                    },
                    "developers": ["foo"],
                    "description": "test",
                    "is_public": True,
                    "bk_app_codes": ["app1", "app2"],
                    "related_app_codes": ["app1", "app2"],
                },
                {
                    "maintainers": ["admin"],
                    "doc_maintainers": {
                        "type": "service_account",
                        "contacts": [],
                        "service_account": {
                            "name": "admin1",
                            "link": "wxwork://message?xxx",
                        },
                    },
                    "developers": ["foo"],
                    "description": "test",
                    "is_public": True,
                    "bk_app_codes": ["app1", "app2"],
                    "related_app_codes": ["app1", "app2"],
                },
            ),
            # input include status
            (
                {
                    "maintainers": ["admin"],
                    "doc_maintainers": {
                        "type": "user",
                        "contacts": ["admin1", "admin2", "admin3"],
                        "service_account": {
                            "name": "",
                            "link": "",
                        },
                    },
                    "description": "test",
                    "is_public": True,
                    "status": 1,
                },
                {
                    "maintainers": ["admin"],
                    "doc_maintainers": {
                        "type": "user",
                        "contacts": ["admin1", "admin2", "admin3"],
                        "service_account": {
                            "name": "",
                            "link": "",
                        },
                    },
                    "developers": [],
                    "description": "test",
                    "is_public": True,
                },
            ),
        ],
    )
    def test_validate(self, fake_gateway, data, expected):
        slz = GatewayUpdateInputSLZ(instance=fake_gateway, data=data)
        slz.is_valid(raise_exception=True)

        assert slz.validated_data == expected


class TestGatewayUpdateStatusInputSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "status": 0,
                },
                {
                    "status": 0,
                },
            ),
            # input include is_public
            (
                {
                    "status": 1,
                    "is_public": True,
                },
                {
                    "status": 1,
                },
            ),
            # status invalid
            (
                {
                    "status": 100,
                },
                None,
            ),
        ],
    )
    def test_validate(self, data, expected):
        slz = GatewayUpdateStatusInputSLZ(data=data)
        slz.is_valid()

        if expected is None:
            assert slz.errors
            return

        assert slz.validated_data == expected


class TestProgrammableGatewayGitInfoSLZ:
    def test_valid_http_git_repo(self):
        data = {"repository": "http://github.com/user/repo.git", "account": "user", "password": "pass"}
        slz = ProgrammableGatewayGitInfoSLZ(data=data)
        assert slz.is_valid()

    def test_missing_git_suffix(self):
        data = {"repository": "https://github.com/user/repo", "account": "user", "password": "pass"}
        slz = ProgrammableGatewayGitInfoSLZ(data=data)
        with pytest.raises(ValidationError) as e:
            slz.is_valid(raise_exception=True)
        assert "必须以 .git 结尾" in str(e.value)
