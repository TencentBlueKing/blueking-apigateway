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
from django.urls import NoReverseMatch, reverse

pytestmark = pytest.mark.django_db


@pytest.fixture()
def has_related_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.open.permission.views.OpenAPIGatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


@pytest.fixture(autouse=True)
def enable_sdk_generation(settings):
    settings.SDK_GENERATION_ENABLED = True


class TestSDKGenerateViewSet:
    def test_generate(
        self,
        has_related_app_permission,
        mocker,
        fake_gateway,
        fake_resource_version,
        rf,
        request_to_view,
    ):
        create_task = mocker.patch("apigateway.apis.open.support.views.create_or_resume_generation")

        request = rf.post(
            "",
            data={
                "resource_version": fake_resource_version.version,
                "version": "9.9.9",
            },
        )
        request.gateway = fake_gateway

        response = request_to_view(
            request=request,
            view_name="openapi.support.sdk.generate",
            path_params={"gateway_name": fake_gateway.name},
        )
        assert create_task.call_args.args[:2] == (fake_resource_version, ["python"])
        assert create_task.call_args.args[2] is None

        assert response.status_code == 200
        assert json.loads(response.content) == {
            "code": 0,
            "message": "SDK generation started",
            "result": True,
            "data": [],
        }

    @pytest.mark.parametrize("error", [ValueError("disabled")])
    def test_generate_maps_expected_domain_errors_to_v1_failure(
        self,
        error,
        has_related_app_permission,
        mocker,
        fake_gateway,
        fake_resource_version,
        rf,
        request_to_view,
    ):
        mocker.patch("apigateway.apis.open.support.views.create_or_resume_generation", side_effect=error)
        request = rf.post("", data={"resource_version": fake_resource_version.version})
        request.gateway = fake_gateway

        response = request_to_view(
            request=request,
            view_name="openapi.support.sdk.generate",
            path_params={"gateway_name": fake_gateway.name},
        )

        assert response.status_code == 400
        assert json.loads(response.content)["result"] is False

    def test_disabled_generation_keeps_legacy_success_without_enqueue(
        self,
        settings,
        has_related_app_permission,
        mocker,
        fake_gateway,
        fake_resource_version,
        rf,
        request_to_view,
    ):
        settings.SDK_GENERATION_ENABLED = False
        create = mocker.patch("apigateway.apis.open.support.views.create_or_resume_generation")
        request = rf.post("", data={"resource_version": fake_resource_version.version})
        request.gateway = fake_gateway

        response = request_to_view(
            request=request,
            view_name="openapi.support.sdk.generate",
            path_params={"gateway_name": fake_gateway.name},
        )

        assert response.status_code == 200
        assert json.loads(response.content)["data"] == []
        create.assert_not_called()

    def test_v1_has_no_generation_task_detail_route(self):
        with pytest.raises(NoReverseMatch):
            reverse("openapi.support.sdk.generation_task_detail", kwargs={"gateway_name": "demo", "task_id": 1})
