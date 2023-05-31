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
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.resource_version import serializers
from apigateway.apps.resource_version.diff_helpers import ResourceDiffer
from apigateway.apps.support.models import APISDK, ResourceDoc, ResourceDocVersion
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.core.models import Release, Resource, ResourceVersion
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class ResourceVersionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ResourceVersionSLZ
    lookup_field = "id"

    def get_queryset(self):
        return ResourceVersion.objects.filter(api=self.request.gateway).order_by("-id")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.ResourceVersionSLZ, tags=["ResourceVersion"]
    )
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
                api=self.request.gateway,
                resource_version=instance,
                data=ResourceDocVersion.objects.make_version(request.gateway.id),
            )

        return OKJsonResponse("OK", data={"id": instance.id})

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: serializers.ResourceVersionListSLZ(many=True)},
        tags=["ResourceVersion"],
    )
    def list(self, request, *args, **kwargs):
        data = (
            ResourceVersion.objects.filter(api=request.gateway)
            .values("id", "version", "name", "title", "comment", "created_time")
            .order_by("-id")
        )

        page = self.paginate_queryset(data)
        resource_version_ids = [rv["id"] for rv in page]

        slz = serializers.ResourceVersionListSLZ(
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
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(tags=["ResourceVersion"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)

        data = slz.data

        # 补充资源文档的更新时间
        resource_doc_updated_time = ResourceDocVersion.objects.get_doc_updated_time(request.gateway.id, instance.id)
        for item in data["data"]:
            item["doc_updated_time"] = resource_doc_updated_time.get(item["id"], {})

        return OKJsonResponse("OK", data=data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.ResourceVersionUpdateSLZ, tags=["ResourceVersion"]
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.ResourceVersionUpdateSLZ(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(updated_by=request.user.username)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.RESOURCE_VERSION.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.name,
            comment=_("更新版本"),
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(responses={status.HTTP_200_OK: serializers.NeedNewVersionSLZ}, tags=["ResourceVersion"])
    def need_new_version(self, request, *args, **kwargs):
        resource_version_exist = ResourceVersion.objects.filter(api_id=request.gateway.id).exists()
        resource_exist = Resource.objects.filter(api_id=request.gateway.id).exists()
        if not (resource_version_exist or resource_exist):
            return FailJsonResponse(_("请先创建资源，然后再发布版本。"))

        if ResourceVersionHandler().need_new_version(request.gateway.id):
            return OKJsonResponse(
                _("资源有更新，需生成新版本并发布到指定环境，才能生效。"),
                data={
                    "need_new_version": True,
                },
            )

        if ResourceDocVersion.objects.need_new_version(request.gateway.id):
            return OKJsonResponse(
                _("资源文档有更新，需生成新版本并发布到任一环境，才能生效。"),
                data={
                    "need_new_version": True,
                },
            )

        return OKJsonResponse("OK", data={"need_new_version": False})


class ResourceVersionDiffViewSet(ResourceVersionViewSet):
    @swagger_auto_schema(
        query_serializer=serializers.ResourceVersionDiffQuerySLZ,
        responses={status.HTTP_200_OK: serializers.ResourceVersionDiffSLZ},
        tags=["ResourceVersion"],
    )
    def diff(self, request, *args, **kwargs):
        """
        版本对比
        """
        slz = serializers.ResourceVersionDiffQuerySLZ(data=request.query_params)
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
            "OK",
            data=self._diff_resource_version_data(
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

    def _diff_resource_version_data(
        self,
        source_data: list,
        target_data: list,
        source_resource_doc_updated_time: dict,
        target_resource_doc_updated_time: dict,
    ) -> dict:
        source_data_map = {}
        target_data_map = {}
        for item in source_data:
            resource_id = item["id"]
            # 添加文档更新时间
            item["doc_updated_time"] = source_resource_doc_updated_time.get(resource_id, {})
            source_data_map[resource_id] = item
        for item in target_data:
            resource_id = item["id"]
            # 添加文档更新时间
            item["doc_updated_time"] = target_resource_doc_updated_time.get(resource_id, {})
            target_data_map[resource_id] = item

        resource_add = []
        resource_delete = []
        resource_update = []

        for resource_id, source_resource_data in source_data_map.items():
            source_resource_differ = ResourceDiffer.parse_obj(source_resource_data)
            target_resource_data = target_data_map.pop(resource_id, None)

            # 目标版本中资源不存在，资源被删除
            if not target_resource_data:
                resource_delete.append(source_resource_differ.dict())
                continue

            target_resource_differ = ResourceDiffer.parse_obj(target_resource_data)
            source_diff_value, target_diff_value = source_resource_differ.diff(target_resource_differ)

            # 资源无变化，忽略此资源
            if not source_diff_value and not target_diff_value:
                continue

            # 资源有变化，记录资源差异
            source_resource_data = source_resource_differ.dict()
            target_resource_data = target_resource_differ.dict()
            source_resource_data["diff"] = source_diff_value
            target_resource_data["diff"] = target_diff_value
            resource_update.append(
                {
                    "source": source_resource_data,
                    "target": target_resource_data,
                }
            )

        # 目标版本中，新增的资源
        if target_data_map:
            for target_resource_data in target_data_map.values():
                target_resource_differ = ResourceDiffer.parse_obj(target_resource_data)
                resource_add.append(target_resource_differ.dict())

        return {
            "add": sorted(resource_add, key=lambda x: x["path"]),
            "delete": sorted(resource_delete, key=lambda x: x["path"]),
            "update": sorted(resource_update, key=lambda x: x["target"]["path"]),
        }
