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

from django.test import Client
from django.urls import reverse


class TestUserApplicationListApi:
    def test_list_without_login(self):
        response = Client().get(reverse("me.applications.list"))

        assert response.status_code == 401

    def test_list_passes_user_tenant_id_to_paas_component(self, mocker, request_view, settings):
        settings.ENABLE_MULTI_TENANT_MODE = True
        user = mocker.MagicMock(username="alice", tenant_id="tenant-a", is_authenticated=True)
        mock_get_apps = mocker.patch(
            "apigateway.apis.web.user_application.views.get_paas_apps_by_username",
            return_value=[
                {
                    "code": "app-001",
                    "name": "App 001",
                    "logo_url": "https://example.com/logo.png",
                }
            ],
        )

        response = request_view(
            method="GET",
            view_name="me.applications.list",
            user=user,
        )

        assert response.status_code == 200
        assert response.json()["data"] == [
            {
                "bk_app_code": "app-001",
                "name": "App 001",
                "logo_url": "https://example.com/logo.png",
            }
        ]
        mock_get_apps.assert_called_once_with("alice", "tenant-a")
