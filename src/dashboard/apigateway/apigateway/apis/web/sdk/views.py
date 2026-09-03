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
import logging
from typing import cast

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.views import APIView

from apigateway.apis.web.sdk import serializers
from apigateway.apps.support.models import GatewaySDK, SDKGenerationItem, SDKGenerationTask
from apigateway.biz.sdk import SDKFactory
from apigateway.biz.sdk.exceptions import LegacySDKVersionConflict, SDKRepoConfigError
from apigateway.biz.sdk.orchestrator import (
    create_or_resume_generation,
    retry_generation_task,
    serialize_generation_task,
)
from apigateway.biz.sdk.tasks import enqueue_generation_items
from apigateway.common.error_codes import error_codes
from apigateway.core.models import ResourceVersion
from apigateway.utils.responses import OKJsonResponse

logger = logging.getLogger(__name__)


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

        queryset = self._filter_sdk(
            gateway=self.request.gateway,
            language=slz.validated_data.get("language"),
            version_number=slz.validated_data.get("version_number"),
            resource_version_id=slz.validated_data.get("resource_version_id"),
            order_by="-id",
            fuzzy=True,
            keyword=slz.validated_data.get("keyword"),
        )

        page = self.paginate_queryset(queryset)

        sdks = [SDKFactory.create(model=i) for i in page]
        slz = self.get_serializer(sdks, many=True)
        return self.get_paginated_response(slz.data)

    def _filter_sdk(
        self,
        gateway,
        language=None,
        order_by=None,
        version_number="",
        resource_version_id=None,
        fuzzy=False,
        keyword=None,
    ):
        queryset = GatewaySDK.objects.filter(gateway=gateway)

        if keyword:
            queryset = queryset.filter(
                Q(language__icontains=keyword)
                | Q(version_number__contains=keyword)
                | Q(resource_version__version__contains=keyword)
            )

        if language:
            queryset = queryset.filter(language=language)

        if version_number:
            if fuzzy:
                queryset = queryset.filter(version_number__contains=version_number)
            else:
                queryset = queryset.filter(version_number=version_number)

        if resource_version_id is not None:
            queryset = queryset.filter(resource_version_id=resource_version_id)

        if order_by:
            queryset = queryset.order_by(order_by)

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

        data = cast("dict", slz.validated_data)
        resource_version = get_object_or_404(ResourceVersion, gateway=request.gateway, id=data["resource_version_id"])
        try:
            task = create_or_resume_generation(
                resource_version,
                data["languages"],
                getattr(request.user, "username", None),
                enqueue_generation_items,
            )
        except LegacySDKVersionConflict as error:
            raise error_codes.FAILED_PRECONDITION.format(str(error), replace=True)
        except SDKRepoConfigError as error:
            logger.exception("SDK generation configuration is invalid")
            raise error_codes.INTERNAL.format("SDK generation is unavailable", replace=True) from error
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
        Prefetch("items", queryset=SDKGenerationItem.objects.order_by("id").prefetch_related("artifacts"))
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


class SDKGenerationTaskRetryApi(APIView):
    def post(self, request, gateway_id, task_id):
        task = get_object_or_404(_generation_task_queryset(), id=task_id, gateway=request.gateway)
        retry_generation_task(task, enqueue_generation_items)
        task.refresh_from_db()
        return OKJsonResponse(status=status.HTTP_202_ACCEPTED, data=serialize_generation_task(task))
