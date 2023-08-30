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
from django.db import transaction
from django.http import Http404
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.resource_version import serializers
from apigateway.apps.support.models import APISDK, ResourceDoc, ResourceDocVersion
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.biz.resource_version_diff import ResourceDifferHandler
from apigateway.core.models import Release, Resource, ResourceVersion
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ResourceVersionListOutputSLZ(many=True)},
        tags=["WebAPI.ResourceVersion"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.ResourceVersionInfoSLZ,
        tags=["WebAPI.ResourceVersion"],
    ),
)
class ResourceVersionListCreateApi(generics.ListCreateAPIView):
    serializer_class = serializers.ResourceVersionInfoSLZ
    lookup_field = "id"

    def get_queryset(self):
        return ResourceVersion.objects.filter(gateway=self.request.gateway).order_by("-id")

    def list(self, request, *args, **kwargs):
        data = (
            ResourceVersion.objects.filter(gateway=request.gateway)
            .values("id", "version", "name", "title", "comment", "created_time")
            .order_by("-id")
        )

        page = self.paginate_queryset(data)
        resource_version_ids = [rv["id"] for rv in page]

        slz = serializers.ResourceVersionListOutputSLZ(
            page,
            many=True,
            context={
                "released_stages": Release.objects.get_released_stages(request.gateway, resource_version_ids),
                "resource_version_ids_has_sdk": APISDK.objects.filter_resource_version_ids_has_sdk(
                    request.gateway.id,
                    resource_version_ids,
                ),
            },
        )
        return OKJsonResponse(data=self.paginator.get_paginated_data(slz.data))

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # manager = ResourceVersionManager()
        # instance = manager.create_resource_version(request.gateway, request.data, request.user.username)
        instance = ResourceVersionHandler().create_resource_version(
            request.gateway, request.data, request.user.username
        )

        # 创建文档版本
        if ResourceDoc.objects.doc_exists(request.gateway.id):
            ResourceDocVersion.objects.create(
                gateway=self.request.gateway,
                resource_version=instance,
                data=ResourceDocVersion.objects.make_version(request.gateway.id),
            )

        return OKJsonResponse(data={"id": instance.id})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(tags=["WebAPI.ResourceVersion"]),
)
class ResourceVersionRetrieveApi(generics.RetrieveAPIView):
    serializer_class = serializers.ResourceVersionInfoSLZ
    lookup_field = "id"

    def get_queryset(self):
        return ResourceVersion.objects.filter(gateway=self.request.gateway).order_by("-id")

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)

        data = slz.data

        # 补充资源文档的更新时间
        resource_doc_updated_time = ResourceDocVersion.objects.get_doc_updated_time(request.gateway.id, instance.id)
        for item in data["data"]:
            item["doc_updated_time"] = resource_doc_updated_time.get(item["id"], {})

        return OKJsonResponse(data=data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.NeedNewVersionOutputSLZ()}, tags=["WebAPI.ResourceVersion"]
    ),
)
class ResourceVersionNeedNewVersionRetrieveApi(generics.RetrieveAPIView):
    def get_queryset(self):
        return ResourceVersion.objects.filter(gateway=self.request.gateway).order_by("-id")

    def get(self, request, *args, **kwargs):
        resource_version_exist = ResourceVersion.objects.filter(gateway_id=request.gateway.id).exists()
        resource_exist = Resource.objects.filter(api_id=request.gateway.id).exists()
        if not (resource_version_exist or resource_exist):
            return FailJsonResponse(status=status.HTTP_404_NOT_FOUND, code="UNKNOWN", message="请先创建资源，然后再发布版本。")

        if ResourceVersionHandler().need_new_version(request.gateway.id):
            return OKJsonResponse(
                data={"need_new_version": True, "msg": "资源有更新，需生成新版本并发布到指定环境，才能生效。"},
            )

        if ResourceDocVersion.objects.need_new_version(request.gateway.id):
            return OKJsonResponse(
                data={"need_new_version": True, "msg": "资源文档有更新，需生成新版本并发布到任一环境，才能生效。"},
            )

        return OKJsonResponse(data={"need_new_version": False})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.ResourceVersionDiffQueryInputSLZ(),
        responses={status.HTTP_200_OK: serializers.ResourceVersionDiffOutputSLZ()},
        tags=["WebAPI.ResourceVersion"],
    ),
)
class ResourceVersionDiffRetrieveApi(generics.RetrieveAPIView):
    def get_queryset(self):
        return ResourceVersion.objects.filter(gateway=self.request.gateway).order_by("-id")

    def get(self, request, *args, **kwargs):
        """
        版本对比
        """
        slz = serializers.ResourceVersionDiffQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        try:
            source_resource_data = ResourceVersionHandler().get_data_by_id_or_new(
                request.gateway, data.get("source_resource_version_id")
            )
            target_resource_data = ResourceVersionHandler().get_data_by_id_or_new(
                request.gateway, data.get("target_resource_version_id")
            )
        except ResourceVersion.DoesNotExist:
            raise Http404

        return OKJsonResponse(
            data=ResourceDifferHandler.diff_resource_version_data(
                source_resource_data,
                target_resource_data,
                source_resource_doc_updated_time=ResourceDocVersion.objects.get_doc_updated_time(
                    request.gateway.id, data.get("source_resource_version_id")
                ),
                target_resource_doc_updated_time=ResourceDocVersion.objects.get_doc_updated_time(
                    request.gateway.id, data.get("target_resource_version_id")
                ),
            ),
        )
