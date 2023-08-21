# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

from apigateway.apis.open.support import views
from apigateway.apps.support.api_sdk.helper import SDKInfo
from apigateway.apps.support.models import APISDK
from apigateway.core.models import Gateway, ResourceVersion
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json

pytestmark = pytest.mark.django_db


@pytest.fixture()
def has_related_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.open.permission.views.GatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


class TestAPISDKV1ViewSet:
    def test_list_latest_sdk(self, mocker, request_factory, faker):
        fake_gateway = G(Gateway, is_public=True, status=1)
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        sdk = G(
            APISDK,
            gateway=fake_gateway,
            resource_version=resource_version,
            language="python",
            is_recommended=True,
            url=faker.url(),
            _config="{}",
        )

        mocker.patch(
            "apigateway.apis.open.support.views.Gateway.objects.filter_id_object_map",
            return_value={
                fake_gateway.id: fake_gateway,
            },
        )
        mocker.patch(
            "apigateway.apis.open.support.views.GatewayAuthContext.filter_scope_id_config_map",
            return_value={
                fake_gateway.id: {
                    "user_auth_type": "test",
                }
            },
        )
        mocker.patch(
            "apigateway.apis.open.support.views.Release.objects.get_released_stages",
            return_value={
                resource_version.id: [
                    {
                        "id": 1,
                        "name": "prod",
                    },
                ]
            },
        )
        mocker.patch(
            "apigateway.apis.open.support.views.ResourceVersion.objects.get_id_to_fields_map",
            return_value={
                resource_version.id: {
                    "id": resource_version.id,
                    "name": "test",
                    "title": "title",
                    "version": "1.0.1",
                },
            },
        )

        request = request_factory.get(
            "/api/v1/apis/latest-sdks/",
            data={
                "api_id": fake_gateway.id,
                "language": "python",
            },
        )

        view = views.APISDKV1ViewSet.as_view({"get": "list_latest_sdks"})
        response = view(request)

        result = get_response_json(response)
        assert result["code"] == 0

        result = result["data"][0]
        assert result == {
            "api_id": fake_gateway.id,
            "api_name": fake_gateway.name,
            "api_description": fake_gateway.description,
            "user_auth_type": "test",
            "language": "python",
            "version_number": sdk.version_number,
            "download_url": sdk.url,
            "sdk_version_number": sdk.version_number,
            "sdk_download_url": sdk.url,
            "sdk_name": sdk.name,
            "sdk_created_time": result["sdk_created_time"],
            "sdk_install_command": "",
            "resource_version_name": "test",
            "resource_version_title": "title",
            "resource_version_display": "1.0.1(title)",
            "released_stages": [
                {
                    "id": 1,
                    "name": "prod",
                },
            ],
        }


class TestResourceDocImportViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, faker):
        self.factory = APIRequestFactory()
        self.gateway = create_gateway(name=faker.uuid4())

    def test_import_by_archive(self, has_related_app_permission, mocker, fake_zip_file):
        mocker.patch(
            "apigateway.apis.open.support.views.ArchiveImportDocManager.import_docs",
            return_value=None,
        )

        request = self.factory.post(
            "",
            data={"file": fake_zip_file},
            format="multipart",
        )
        request.gateway = self.gateway

        view = views.ResourceDocImportViewSet.as_view({"post": "import_by_archive"})
        response = view(request, gateway_name=self.gateway.name)

        result = get_response_json(response)
        assert result["code"] == 0, result

    def test_import_by_swagger(self, has_related_app_permission, mocker, faker):
        mocker.patch(
            "apigateway.apis.open.support.views.SwaggerImportDocManager.import_docs",
            return_value=None,
        )

        request = self.factory.post(
            "",
            data={"language": "zh", "swagger": faker.pystr()},
        )
        request.gateway = self.gateway

        view = views.ResourceDocImportViewSet.as_view({"post": "import_by_swagger"})
        response = view(request, gateway_name=self.gateway.name)

        result = get_response_json(response)
        assert result["code"] == 0


class TestSDKGenerateViewSet:
    def test_generate(
        self,
        has_related_app_permission,
        mocker,
        fake_gateway,
        fake_resource_version,
        fake_sdk,
        rf,
        request_to_view,
    ):
        MockSDKHelper = mocker.patch("apigateway.apis.open.support.views.SDKHelper")
        helper = MockSDKHelper.return_value.__enter__.return_value

        request = rf.post(
            "",
            data={
                "languages": ["python"],
                "resource_version": fake_resource_version.version,
            },
        )
        request.gateway = fake_gateway
        helper.create.return_value = SDKInfo(
            context=mocker.MagicMock(),
            sdk=fake_sdk,
        )

        response = request_to_view(
            request=request,
            view_name="openapi.support.sdk.generate",
            path_params={"gateway_name": fake_gateway.name},
        )
        helper.create.assert_called_with(
            language="python",
            include_private_resources=False,
            is_public=True,
            version=fake_resource_version.version,
            operator=None,
        )

        assert response.status_code == 200
