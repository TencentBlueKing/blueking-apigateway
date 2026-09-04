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
from functools import partial
from typing import Any, cast

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.views import APIView

from apigateway.apis.web.sdk import serializers
from apigateway.apps.support.constants import (
    SDKArtifactStatusEnum,
    SDKArtifactTypeEnum,
    SDKGenerationItemStatusEnum,
    SDKNativePublicationStatusEnum,
)
from apigateway.apps.support.models import GatewaySDK, SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk.config import get_sdk_generation_policy
from apigateway.biz.sdk.orchestrator import (
    create_or_resume_generation,
    refresh_task_status,
    serialize_generation_task,
)
from apigateway.biz.sdk.tasks import enqueue_generation_items, enqueue_native_publications
from apigateway.common.error_codes import error_codes
from apigateway.core.models import ResourceVersion
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse

PREFERRED_ARTIFACT_TYPES = {
    "python": SDKArtifactTypeEnum.WHEEL.value,
    "java": SDKArtifactTypeEnum.DISTRIBUTION_ZIP.value,
    "go": SDKArtifactTypeEnum.GO_ZIP.value,
    "javascript": SDKArtifactTypeEnum.NPM_TGZ.value,
}


def _serialize_error(code: str, message: str) -> dict[str, str] | None:
    return {"code": code, "message": message} if code or message else None


def _serialize_generation_item(item: SDKGenerationItem) -> dict[str, Any]:
    resource_version = item.task.resource_version
    gateway_sdk = item.gateway_sdk if item.gateway_sdk_id else None
    artifacts = item.successful_artifacts
    preferred = next(
        (artifact for artifact in artifacts if artifact.artifact_type == PREFERRED_ARTIFACT_TYPES[item.language]),
        artifacts[0] if artifacts else None,
    )
    return {
        "id": gateway_sdk.id if gateway_sdk else None,
        "generation_task_id": item.task_id,
        "generation_item_id": item.id,
        "resource_version": {"id": resource_version.id, "version": resource_version.version},
        "version_number": resource_version.version,
        "language": item.language,
        "name": (
            gateway_sdk.name
            if gateway_sdk
            else item.config_snapshot.get("project_name", f"bkapi-openapi-{item.task.gateway.name}")
        ),
        "status": item.status,
        "native_status": item.native_status,
        "error": _serialize_error(item.error_code, item.error_message),
        "native_error": _serialize_error(item.native_error_code, item.native_error_message),
        "download_url": preferred.url if preferred else (gateway_sdk.url if gateway_sdk else None),
        "created_by": item.created_by,
        "created_time": item.created_time,
        "updated_time": item.updated_time,
    }


def _serialize_legacy_sdk(sdk: GatewaySDK) -> dict[str, Any]:
    return {
        "id": sdk.id,
        "generation_task_id": None,
        "generation_item_id": None,
        "resource_version": {"id": sdk.resource_version_id, "version": sdk.resource_version.version},
        "version_number": sdk.version_number,
        "language": sdk.language,
        "name": sdk.name,
        "status": SDKGenerationItemStatusEnum.SUCCESS.value,
        "native_status": SDKNativePublicationStatusEnum.NOT_REQUIRED.value,
        "error": None,
        "native_error": None,
        "download_url": sdk.url,
        "created_by": sdk.created_by,
        "created_time": sdk.created_time,
        "updated_time": sdk.updated_time,
    }


def _matches_text_filters(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    version_number = filters.get("version_number")
    if version_number and version_number not in row["version_number"]:
        return False
    keyword = filters.get("keyword")
    if not keyword:
        return True
    keyword = keyword.lower()
    return any(
        keyword in value.lower()
        for value in (row["language"], row["name"], row["version_number"], row["resource_version"]["version"])
    )


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.GatewaySDKQueryInputSLZ(),
        responses={status.HTTP_200_OK: serializers.GatewaySDKListOutputSLZ(many=True)},
        tags=["WebAPI.SDK"],
        operation_description="sdk列表查询接口",
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        responses={status.HTTP_202_ACCEPTED: ""},
        request_body=serializers.GatewaySDKGenerateInputSLZ,
        tags=["WebAPI.SDK"],
        operation_description="sdk创建接口",
    ),
)
class GatewaySDKListCreateApi(generics.ListCreateAPIView):
    serializer_class = serializers.GatewaySDKListOutputSLZ
    lookup_field = "id"

    def list(self, request, *args, **kwargs):
        slz = serializers.GatewaySDKQueryInputSLZ(data=request.query_params, context={"request": request})
        slz.is_valid(raise_exception=True)

        filters = cast("dict[str, Any]", slz.validated_data)
        items = list(
            self._filter_generation_items(self.request.gateway, filters)
            .select_related("task", "task__gateway", "task__resource_version", "gateway_sdk")
            .prefetch_related(
                Prefetch(
                    "artifacts",
                    queryset=SDKArtifact.objects.filter(status=SDKArtifactStatusEnum.SUCCESS.value).exclude(
                        artifact_type=SDKArtifactTypeEnum.MANIFEST.value
                    ),
                    to_attr="successful_artifacts",
                )
            )
        )
        authoritative_keys = {(item.task.resource_version_id, item.language) for item in items}
        legacy_sdks = self._filter_legacy_sdks(self.request.gateway, filters).select_related("resource_version")

        rows = []
        for item in items:
            row = _serialize_generation_item(item)
            if _matches_text_filters(row, filters):
                rows.append(row)
        seen_legacy_keys: set[tuple[int | None, str]] = set()
        for sdk in legacy_sdks.order_by("-id"):
            key = (sdk.resource_version_id, sdk.language)
            if key in authoritative_keys or key in seen_legacy_keys:
                continue
            row = _serialize_legacy_sdk(sdk)
            if _matches_text_filters(row, filters):
                rows.append(row)
            seen_legacy_keys.add(key)
        rows.sort(key=lambda row: (row["created_time"], row["generation_item_id"] or row["id"] or 0), reverse=True)

        page = self.paginate_queryset(rows)
        slz = self.get_serializer(page, many=True)
        return self.get_paginated_response(slz.data)

    def _filter_generation_items(self, gateway, filters: dict[str, Any]):
        queryset = SDKGenerationItem.objects.filter(task__gateway=gateway)
        language = filters.get("language")
        resource_version_id = filters.get("resource_version_id")
        if language:
            queryset = queryset.filter(language=language)
        if resource_version_id is not None:
            queryset = queryset.filter(task__resource_version_id=resource_version_id)
        return queryset

    def _filter_legacy_sdks(self, gateway, filters: dict[str, Any]):
        queryset = GatewaySDK.objects.filter(gateway=gateway)
        language = filters.get("language")
        resource_version_id = filters.get("resource_version_id")
        if language:
            queryset = queryset.filter(language=language)
        if resource_version_id is not None:
            queryset = queryset.filter(resource_version_id=resource_version_id)
        return queryset

    def create(self, request, gateway_id):
        """
        生成 SDK
        """
        slz = serializers.GatewaySDKGenerateInputSLZ(
            data=request.data,
            context={
                "request": request,
            },
        )
        slz.is_valid(raise_exception=True)
        if not get_sdk_generation_policy().enabled:
            return FailJsonResponse(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                code="SERVICE_UNAVAILABLE",
                message="SDK generation is unavailable",
            )

        data = cast("dict", slz.validated_data)
        resource_version = get_object_or_404(ResourceVersion, gateway=request.gateway, id=data["resource_version_id"])
        try:
            task = create_or_resume_generation(
                resource_version,
                data["languages"],
                getattr(request.user, "username", None),
                enqueue_generation_items,
            )
        except ValueError as error:
            raise error_codes.INVALID_ARGUMENT.format(str(error), replace=True)

        status_url = reverse(
            "gateway.sdk.generation_task_detail",
            kwargs={"gateway_id": request.gateway.id, "task_id": task.id},
        )
        return OKJsonResponse(
            status=status.HTTP_202_ACCEPTED,
            data={"id": task.id, "status": task.status, "status_url": status_url},
        )


def _generation_task_queryset():
    return SDKGenerationTask.objects.select_related("resource_version").prefetch_related(
        Prefetch(
            "items",
            queryset=SDKGenerationItem.objects.select_related("gateway_sdk")
            .order_by("id")
            .prefetch_related("artifacts"),
        )
    )


class SDKGenerationTaskListApi(generics.GenericAPIView):
    def get(self, request, gateway_id):
        tasks = _generation_task_queryset().filter(gateway=request.gateway).order_by("-id")
        page = self.paginate_queryset(tasks)
        return self.get_paginated_response([serialize_generation_task(task) for task in page])


class SDKGenerationTaskDetailApi(APIView):
    def get(self, request, gateway_id, task_id):
        task = get_object_or_404(_generation_task_queryset(), id=task_id, gateway=request.gateway)
        return OKJsonResponse(data=serialize_generation_task(task))


class SDKGenerationItemRetryApi(APIView):
    @transaction.atomic
    def post(self, request, gateway_id, task_id, item_id):
        if not get_sdk_generation_policy().enabled:
            return FailJsonResponse(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                code="SERVICE_UNAVAILABLE",
                message="SDK generation is unavailable",
            )

        task = get_object_or_404(SDKGenerationTask.objects.select_for_update(), id=task_id, gateway=request.gateway)
        item = get_object_or_404(SDKGenerationItem.objects.select_for_update(), id=item_id, task=task)
        generation_failed = item.status == SDKGenerationItemStatusEnum.FAILED.value
        native_failed = (
            item.status == SDKGenerationItemStatusEnum.SUCCESS.value
            and item.native_status == SDKNativePublicationStatusEnum.FAILED.value
        )
        if not generation_failed and not native_failed:
            raise error_codes.INVALID_ARGUMENT.format(
                "Only failed SDK generation or native publication items can be retried", replace=True
            )

        if native_failed:
            item.native_status = SDKNativePublicationStatusEnum.PENDING.value
            item.native_lease_token = ""
            item.native_lease_expires_at = None
            item.native_next_attempt_at = None
            item.native_attempt_cycle_count = 0
            item.native_error_code = ""
            item.native_error_message = ""
            item.save(
                update_fields=[
                    "native_status",
                    "native_lease_token",
                    "native_lease_expires_at",
                    "native_next_attempt_at",
                    "native_attempt_cycle_count",
                    "native_error_code",
                    "native_error_message",
                    "updated_time",
                ]
            )
            transaction.on_commit(partial(enqueue_native_publications, [item.id]))
            return OKJsonResponse(
                status=status.HTTP_202_ACCEPTED,
                data={"id": item.id, "status": SDKGenerationItemStatusEnum.SUCCESS.value},
            )

        item.status = SDKGenerationItemStatusEnum.PENDING.value
        item.lease_token = ""
        item.lease_expires_at = None
        item.next_attempt_at = None
        item.attempt_cycle_count = 0
        item.finished_at = None
        item.error_code = ""
        item.error_message = ""
        item.error_retryable = False
        item.save(
            update_fields=[
                "status",
                "lease_token",
                "lease_expires_at",
                "next_attempt_at",
                "attempt_cycle_count",
                "finished_at",
                "error_code",
                "error_message",
                "error_retryable",
                "updated_time",
            ]
        )
        refresh_task_status(task.id)
        transaction.on_commit(partial(enqueue_generation_items, [item.id]))
        return OKJsonResponse(
            status=status.HTTP_202_ACCEPTED,
            data={"id": item.id, "status": SDKGenerationItemStatusEnum.PENDING.value},
        )
