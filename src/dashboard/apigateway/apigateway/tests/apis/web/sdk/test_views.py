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

from django_dynamic_fixture import G

from apigateway.apps.support.constants import SDKGenerationStatusEnum
from apigateway.apps.support.models import GatewaySDK, SDKGenerationTask
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import ResourceVersion
from apigateway.tests.utils.testing import dummy_time


class TestGatewaySDKListCreateApi:
    def test_list(self, request_view, fake_gateway, settings):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        sdk_1 = G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=resource_version,
            language="python",
            name="bkapigw-test",
            version_number="12345",
            _config=json.dumps({"python": {"is_uploaded_to_pypi": True}}),
            schema=SchemaFactory().get_api_sdk_schema(),
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
            url="http://bking.com/pypi/bkapigw-test/12345/bkapigw-test-12345.tar.gz",
        )

        sdk_2 = G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=resource_version,
            language="python",
            name="bkapigw-test",
            version_number="1234512",
            _config=json.dumps({"python": {"is_uploaded_to_pypi": False}}),
            schema=SchemaFactory().get_api_sdk_schema(),
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
        )

        data = [
            {
                "gateway": fake_gateway,
                "params": {
                    "language": "python",
                    "resource_version_id": resource_version.id,
                },
                "expected": {
                    "count": 2,
                    "results": [
                        {
                            "id": sdk_2.id,
                            "language": "python",
                            "name": "bkapigw-test",
                            "version_number": "1234512",
                            "created_time": dummy_time.str,
                            "updated_time": dummy_time.str,
                            "created_by": None,
                            "download_url": "",
                            "resource_version": {
                                "id": resource_version.id,
                                "version": resource_version.version,
                            },
                        },
                        {
                            "id": sdk_1.id,
                            "language": "python",
                            "name": "bkapigw-test",
                            "version_number": "12345",
                            "created_time": dummy_time.str,
                            "created_by": None,
                            "updated_time": dummy_time.str,
                            "download_url": "http://bking.com/pypi/bkapigw-test/12345/bkapigw-test-12345.tar.gz",
                            "resource_version": {
                                "id": resource_version.id,
                                "version": resource_version.version,
                            },
                        },
                    ],
                },
            },
        ]

        for test in data:
            resp = request_view(
                method="GET",
                view_name="gateway.sdk.list_create",
                gateway=fake_gateway,
                path_params={"gateway_id": fake_gateway.id},
                data=test["params"],
            )

            result = resp.json()

            assert result["data"] == test["expected"]

    def test_create_returns_reusable_async_task(
        self,
        request_view,
        fake_gateway,
        fake_admin_user,
        settings,
        mocker,
        django_capture_on_commit_callbacks,
    ):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        settings.BKREPO_ENDPOINT_URL = "https://repo"
        settings.BKREPO_USERNAME = "user"
        settings.BKREPO_PASSWORD = "password"
        settings.BKREPO_PROJECT = "project"
        settings.BKREPO_GENERIC_BUCKET = "generic"
        enqueue = mocker.patch("apigateway.apis.web.sdk.views.enqueue_generation_items")

        with django_capture_on_commit_callbacks(execute=True):
            responses = [
                request_view(
                    method="POST",
                    view_name="gateway.sdk.list_create",
                    gateway=fake_gateway,
                    user=fake_admin_user,
                    path_params={"gateway_id": fake_gateway.id},
                    data={"resource_version_id": resource_version.id, "languages": ["python", "go"]},
                )
                for _ in range(2)
            ]

        assert [response.status_code for response in responses] == [202, 202]
        assert responses[0].json()["data"] == responses[1].json()["data"]
        task = SDKGenerationTask.objects.get(resource_version=resource_version)
        assert responses[0].json()["data"] == {
            "id": task.id,
            "status": "pending",
            "status_url": f"/backend/gateways/{fake_gateway.id}/sdks/tasks/{task.id}/",
        }
        assert set(task.items.values_list("language", flat=True)) == {"python", "go"}
        assert enqueue.call_count == 2

    def test_create_rejects_resource_version_from_another_gateway(self, request_view, fake_gateway, fake_admin_user):
        other_gateway = G(type(fake_gateway), name="other-gateway")
        resource_version = G(ResourceVersion, gateway=other_gateway, version="1.0.1")

        response = request_view(
            method="POST",
            view_name="gateway.sdk.list_create",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id},
            data={"resource_version_id": resource_version.id, "languages": ["python"]},
        )

        assert response.status_code == 404

    def test_create_rejects_disabled_language(self, request_view, fake_gateway, fake_admin_user, settings):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        settings.SDK_GENERATION = {**settings.SDK_GENERATION, "enabled_languages": ["python"]}
        settings.BKREPO_ENDPOINT_URL = "https://repo"
        settings.BKREPO_USERNAME = "user"
        settings.BKREPO_PASSWORD = "password"
        settings.BKREPO_PROJECT = "project"
        settings.BKREPO_GENERIC_BUCKET = "generic"

        response = request_view(
            method="POST",
            view_name="gateway.sdk.list_create",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id},
            data={"resource_version_id": resource_version.id, "languages": ["java"]},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_ARGUMENT"

    def test_create_rejects_legacy_sdk_coordinate(self, request_view, fake_gateway, fake_admin_user, settings):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=resource_version,
            language="python",
            version_number="1.0.1",
            schema=None,
        )
        settings.BKREPO_ENDPOINT_URL = "https://repo"
        settings.BKREPO_USERNAME = "user"
        settings.BKREPO_PASSWORD = "password"
        settings.BKREPO_PROJECT = "project"
        settings.BKREPO_GENERIC_BUCKET = "generic"

        response = request_view(
            method="POST",
            view_name="gateway.sdk.list_create",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id},
            data={"resource_version_id": resource_version.id, "languages": ["python"]},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "FAILED_PRECONDITION"


class TestSDKGenerationTaskApi:
    def test_list_detail_and_retry(
        self,
        request_view,
        fake_gateway,
        fake_admin_user,
        settings,
        mocker,
        django_capture_on_commit_callbacks,
    ):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        settings.BKREPO_ENDPOINT_URL = "https://repo"
        settings.BKREPO_USERNAME = "user"
        settings.BKREPO_PASSWORD = "password"
        settings.BKREPO_PROJECT = "project"
        settings.BKREPO_GENERIC_BUCKET = "generic"
        mocker.patch("apigateway.apis.web.sdk.views.enqueue_generation_items")
        create = request_view(
            method="POST",
            view_name="gateway.sdk.list_create",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id},
            data={"resource_version_id": resource_version.id, "languages": ["python", "go"]},
        )
        task = SDKGenerationTask.objects.get(id=create.json()["data"]["id"])
        task.items.filter(language="python").update(status=SDKGenerationStatusEnum.FAILED.value)
        task.items.filter(language="go").update(status=SDKGenerationStatusEnum.SUCCESS.value)
        enqueue = mocker.patch("apigateway.apis.web.sdk.views.enqueue_generation_items")

        listing = request_view(
            method="GET",
            view_name="gateway.sdk.generation_task_list",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id},
        )
        detail = request_view(
            method="GET",
            view_name="gateway.sdk.generation_task_detail",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id, "task_id": task.id},
        )
        with django_capture_on_commit_callbacks(execute=True):
            retry = request_view(
                method="POST",
                view_name="gateway.sdk.generation_task_retry",
                gateway=fake_gateway,
                user=fake_admin_user,
                path_params={"gateway_id": fake_gateway.id, "task_id": task.id},
            )

        assert listing.json()["data"][0]["id"] == task.id
        assert detail.json()["data"]["resource_version"] == {"id": resource_version.id, "version": "1.0.1"}
        assert retry.status_code == 202
        enqueue.assert_called_once_with([task.items.get(language="python").id])
