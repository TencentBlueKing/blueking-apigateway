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
from datetime import timedelta

import pytest
from django_dynamic_fixture import G

from apigateway.apps.support.constants import (
    SDKArtifactStatusEnum,
    SDKGenerationItemStatusEnum,
    SDKGenerationTaskStatusEnum,
    SDKNativePublicationStatusEnum,
)
from apigateway.apps.support.models import GatewaySDK, SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import ResourceVersion
from apigateway.tests.utils.testing import dummy_time


class TestGatewaySDKListCreateApi:
    def test_list_unifies_legacy_and_authoritative_generation_rows(
        self, request_view, fake_gateway, fake_admin_user, django_assert_num_queries
    ):
        legacy_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        legacy_sdk = G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=legacy_version,
            language="python",
            name="legacy-sdk",
            version_number="1.0.0",
            _config=json.dumps({"python": {"is_uploaded_to_pypi": True}}),
            schema=SchemaFactory().get_api_sdk_schema(),
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
            url="https://legacy.example/sdk.tar.gz",
        )
        pending_version = G(ResourceVersion, gateway=fake_gateway, version="1.1.0")
        pending_task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=pending_version)
        pending_item = G(SDKGenerationItem, task=pending_task, language="javascript")
        failed_version = G(ResourceVersion, gateway=fake_gateway, version="1.2.0")
        failed_task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=failed_version)
        failed_item = G(
            SDKGenerationItem,
            task=failed_task,
            language="python",
            status=SDKGenerationItemStatusEnum.FAILED.value,
            error_code="build_failed",
            error_message="wheel build failed",
        )
        success_version = G(ResourceVersion, gateway=fake_gateway, version="1.3.0")
        success_task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=success_version)
        success_sdk = G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=success_version,
            language="go",
            name="go-sdk",
            version_number="v1.3.0",
            schema=SchemaFactory().get_api_sdk_schema(),
            created_time=dummy_time.time,
            updated_time=dummy_time.time,
        )
        success_item = G(
            SDKGenerationItem,
            task=success_task,
            language="go",
            status=SDKGenerationItemStatusEnum.SUCCESS.value,
            gateway_sdk=success_sdk,
        )
        success_artifact = G(
            SDKArtifact,
            item=success_item,
            artifact_type="go_zip",
            filename="go-sdk.zip",
            url="https://repo.example/go-sdk.zip",
            status=SDKArtifactStatusEnum.SUCCESS.value,
        )
        native_version = G(ResourceVersion, gateway=fake_gateway, version="1.4.0")
        native_task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=native_version)
        native_item = G(
            SDKGenerationItem,
            task=native_task,
            language="java",
            status=SDKGenerationItemStatusEnum.SUCCESS.value,
            native_status=SDKNativePublicationStatusEnum.FAILED.value,
            native_error_code="registry_unavailable",
            native_error_message="publication failed",
        )
        native_artifact = G(
            SDKArtifact,
            item=native_item,
            artifact_type="distribution_zip",
            filename="java-sdk.zip",
            url="https://repo.example/java-sdk.zip",
            status=SDKArtifactStatusEnum.SUCCESS.value,
        )
        G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=failed_version,
            language="python",
            name="stale-projection",
            version_number="1.2.0",
            schema=SchemaFactory().get_api_sdk_schema(),
        )

        with django_assert_num_queries(4):
            resp = request_view(
                method="GET",
                view_name="gateway.sdk.list_create",
                gateway=fake_gateway,
                user=fake_admin_user,
                path_params={"gateway_id": fake_gateway.id},
            )
            rows = resp.json()["data"]["results"]

        assert len(rows) == 5
        rows_by_version = {row["version_number"]: row for row in rows}
        assert rows_by_version["1.0.0"] == {
            "id": legacy_sdk.id,
            "generation_task_id": None,
            "generation_item_id": None,
            "resource_version": {"id": legacy_version.id, "version": "1.0.0"},
            "version_number": "1.0.0",
            "language": "python",
            "name": "legacy-sdk",
            "status": "success",
            "native_status": "not_required",
            "error": None,
            "native_error": None,
            "download_url": "https://legacy.example/sdk.tar.gz",
            "created_by": None,
            "created_time": dummy_time.str,
            "updated_time": dummy_time.str,
        }
        assert rows_by_version["1.1.0"]["generation_item_id"] == pending_item.id
        assert rows_by_version["1.1.0"]["status"] == "pending"
        assert rows_by_version["1.1.0"]["id"] is None
        assert rows_by_version["1.2.0"]["generation_item_id"] == failed_item.id
        assert rows_by_version["1.2.0"]["name"] != "stale-projection"
        assert rows_by_version["1.2.0"]["error"] == {
            "code": "build_failed",
            "message": "wheel build failed",
        }
        assert rows_by_version["v1.3.0"]["id"] == success_sdk.id
        assert rows_by_version["v1.3.0"]["download_url"] == success_artifact.url
        assert rows_by_version["1.4.0"]["generation_item_id"] == native_item.id
        assert rows_by_version["1.4.0"]["status"] == "success"
        assert rows_by_version["1.4.0"]["native_error"] == {
            "code": "registry_unavailable",
            "message": "publication failed",
        }
        assert rows_by_version["1.4.0"]["download_url"] == native_artifact.url

    def test_list_filters_legacy_and_generation_rows_together(self, request_view, fake_gateway, fake_admin_user):
        legacy_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        G(
            GatewaySDK,
            gateway=fake_gateway,
            resource_version=legacy_version,
            language="python",
            version_number="1.0.0",
            schema=SchemaFactory().get_api_sdk_schema(),
        )
        generated_version = G(ResourceVersion, gateway=fake_gateway, version="2.0.0")
        task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=generated_version)
        item = G(
            SDKGenerationItem,
            task=task,
            language="javascript",
            config_snapshot={"project_name": "@bkapi/openapi-demo", "package_version": "2.0.0"},
        )

        response = request_view(
            method="GET",
            view_name="gateway.sdk.list_create",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id},
            data={"language": "javascript", "version_number": "2.0", "keyword": "openapi-demo"},
        )

        rows = response.json()["data"]["results"]
        assert len(rows) == 1
        assert rows[0]["generation_item_id"] == item.id

    def test_create_returns_stable_async_task(
        self,
        request_view,
        fake_gateway,
        fake_admin_user,
        settings,
        mocker,
        django_capture_on_commit_callbacks,
    ):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        settings.SDK_GENERATION_ENABLED = True
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
        tasks = list(SDKGenerationTask.objects.filter(resource_version=resource_version).order_by("id"))
        assert len(tasks) == 1
        assert [response.json()["data"]["id"] for response in responses] == [tasks[0].id, tasks[0].id]
        assert set(tasks[0].items.values_list("language", flat=True)) == {"python", "go"}
        assert enqueue.call_count == 2

    def test_create_rejects_resource_version_from_another_gateway(
        self, request_view, fake_gateway, fake_admin_user, settings
    ):
        other_gateway = G(type(fake_gateway), name="other-gateway")
        resource_version = G(ResourceVersion, gateway=other_gateway, version="1.0.1")
        settings.SDK_GENERATION_ENABLED = True

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
        settings.SDK_GENERATION_ENABLED = True
        settings.BK_SDK_LANGUAGES = ["python"]

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

    def test_create_rejects_when_generation_is_disabled(
        self, request_view, fake_gateway, fake_admin_user, settings, mocker
    ):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        settings.SDK_GENERATION_ENABLED = False
        create = mocker.patch("apigateway.apis.web.sdk.views.create_or_resume_generation")

        response = request_view(
            method="POST",
            view_name="gateway.sdk.list_create",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id},
            data={"resource_version_id": resource_version.id, "languages": ["python"]},
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
        create.assert_not_called()


class TestSDKGenerationTaskApi:
    def test_list_is_paginated_and_prefetches_items(
        self,
        request_view,
        django_assert_num_queries,
        fake_gateway,
        fake_admin_user,
    ):
        for index in range(3):
            resource_version = G(ResourceVersion, gateway=fake_gateway, version=f"1.0.{index}")
            task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=resource_version)
            G(SDKGenerationItem, task=task, language="python")

        with django_assert_num_queries(5):
            listing = request_view(
                method="GET",
                view_name="gateway.sdk.generation_task_list",
                gateway=fake_gateway,
                user=fake_admin_user,
                path_params={"gateway_id": fake_gateway.id},
            )
            data = listing.json()["data"]

        assert data["count"] == 3
        assert len(data["results"]) == 3

    def test_detail_remains_available_when_generation_is_disabled(
        self,
        request_view,
        fake_gateway,
        fake_admin_user,
        settings,
    ):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=resource_version)
        G(SDKGenerationItem, task=task, language="python")
        settings.SDK_GENERATION_ENABLED = False

        detail = request_view(
            method="GET",
            view_name="gateway.sdk.generation_task_detail",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id, "task_id": task.id},
        )

        assert detail.status_code == 200
        assert detail.json()["data"]["resource_version"] == {"id": resource_version.id, "version": "1.0.1"}

    def test_retry_resets_and_enqueues_only_failed_generation_item(
        self,
        request_view,
        fake_gateway,
        fake_admin_user,
        mocker,
        django_capture_on_commit_callbacks,
    ):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=resource_version, status="failed")
        item = G(
            SDKGenerationItem,
            task=task,
            language="python",
            status=SDKGenerationItemStatusEnum.FAILED.value,
            lease_token="expired-claim",
            lease_expires_at=dummy_time.time - timedelta(minutes=1),
            attempt_count=7,
            attempt_cycle_count=3,
            next_attempt_at=dummy_time.time + timedelta(minutes=1),
            error_code="build_failed",
            error_message="wheel build failed",
            error_retryable=False,
            finished_at=dummy_time.time,
            native_status=SDKNativePublicationStatusEnum.FAILED.value,
            native_error_code="native_failed",
            native_error_message="keep this error",
        )
        enqueue = mocker.patch("apigateway.apis.web.sdk.views.enqueue_generation_items")

        with django_capture_on_commit_callbacks(execute=True):
            retry = request_view(
                method="POST",
                view_name="gateway.sdk.generation_item_retry",
                gateway=fake_gateway,
                user=fake_admin_user,
                path_params={"gateway_id": fake_gateway.id, "task_id": task.id, "item_id": item.id},
            )

        assert retry.status_code == 202
        item.refresh_from_db()
        task.refresh_from_db()
        assert item.status == SDKGenerationItemStatusEnum.PENDING.value
        assert item.attempt_count == 7
        assert item.attempt_cycle_count == 0
        assert item.lease_token == ""
        assert item.lease_expires_at is None
        assert item.next_attempt_at is None
        assert item.finished_at is None
        assert item.error_code == ""
        assert item.error_message == ""
        assert item.error_retryable is False
        assert item.native_status == SDKNativePublicationStatusEnum.FAILED.value
        assert item.native_error_code == "native_failed"
        assert item.native_error_message == "keep this error"
        assert task.status == SDKGenerationTaskStatusEnum.PENDING.value
        enqueue.assert_called_once_with([item.id])

    @pytest.mark.parametrize(
        "item_status", [SDKGenerationItemStatusEnum.RUNNING.value, SDKGenerationItemStatusEnum.SUCCESS.value]
    )
    def test_retry_rejects_non_failed_generation_item(self, item_status, request_view, fake_gateway, fake_admin_user):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.1")
        task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=resource_version)
        item = G(SDKGenerationItem, task=task, language="python", status=item_status)

        response = request_view(
            method="POST",
            view_name="gateway.sdk.generation_item_retry",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id, "task_id": task.id, "item_id": item.id},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_ARGUMENT"

    def test_retry_rejects_item_from_another_gateway(self, request_view, fake_gateway, fake_admin_user):
        other_gateway = G(type(fake_gateway), name="other-gateway")
        resource_version = G(ResourceVersion, gateway=other_gateway, version="1.0.1")
        task = G(SDKGenerationTask, gateway=other_gateway, resource_version=resource_version)
        item = G(SDKGenerationItem, task=task, language="python", status=SDKGenerationItemStatusEnum.FAILED.value)

        response = request_view(
            method="POST",
            view_name="gateway.sdk.generation_item_retry",
            gateway=fake_gateway,
            user=fake_admin_user,
            path_params={"gateway_id": fake_gateway.id, "task_id": task.id, "item_id": item.id},
        )

        assert response.status_code == 404
