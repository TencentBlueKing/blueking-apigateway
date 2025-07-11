# -*- coding: utf-8 -*-
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
import json

from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, serializers, status

from apigateway.apis.open.permissions import (
    OpenAPIGatewayRelatedAppPermission,
)
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource.importer import ResourcesImporter
from apigateway.biz.resource.importer.openapi import OpenAPIImportManager
from apigateway.biz.resource_doc.importer import DocImporter
from apigateway.biz.resource_doc.importer.parsers import OpenAPIParser
from apigateway.core.models import Resource
from apigateway.utils.responses import V1OKJsonResponse

from .serializers import ResourceImportInputSLZ, ResourceSyncOutputSLZ


class ResourceSyncApi(generics.CreateAPIView):
    permission_classes = [OpenAPIGatewayRelatedAppPermission]

    def get_queryset(self):
        return Resource.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(
        request_body=ResourceImportInputSLZ,
        responses={status.HTTP_200_OK: ResourceSyncOutputSLZ()},
        tags=["OpenAPI.V1"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = ResourceImportInputSLZ(
            data=request.data,
            context={
                "gateway": request.gateway,
            },
        )
        slz.is_valid(raise_exception=True)

        try:
            openapi_manager = OpenAPIImportManager.load_from_content(
                request.gateway,
                slz.validated_data["content"],
                need_delete_unspecified_resources=slz.validated_data["delete"],
            )
        except Exception as err:  # pylint: disable=broad-except
            raise serializers.ValidationError(
                {"content": _("导入内容为无效的 json/yaml 数据，{err}。").format(err=err)}
            )

        validate_err_list = openapi_manager.validate()
        if len(validate_err_list) != 0:
            error_dicts = [error.to_dict() for error in validate_err_list]
            raise serializers.ValidationError(
                {
                    "content": _("validate err {err}。").format(
                        err=json.dumps(error_dicts, ensure_ascii=False, indent=4)
                    )
                }
            )

        importer = ResourcesImporter.from_resources(
            gateway=request.gateway,
            resources=openapi_manager.get_resource_list(),
            username=request.user.username,
            selected_resources=None,
            need_delete_unspecified_resources=slz.validated_data["delete"],
        )
        importer.import_resources()

        # 如果生成文档还要再生成文档
        if slz.validated_data.get("doc_language"):
            parser = OpenAPIParser(gateway_id=request.gateway.id)
            docs = parser.parse(
                swagger=slz.validated_data["content"],
                language=DocLanguageEnum(slz.validated_data["doc_language"]),
            )
            doc_importer = DocImporter(
                gateway_id=request.gateway.id,
            )
            doc_importer.import_docs(docs=docs)

        # 分析出已创建或更新的资源
        added = []
        updated = []
        for resource_data in importer.get_selected_resource_data_list():
            if resource_data.metadata.get("is_created"):
                added.append({"id": resource_data.resource.id})
            else:
                updated.append({"id": resource_data.resource.id})

        slz = ResourceSyncOutputSLZ(
            {
                "added": added,
                "updated": updated,
                "deleted": importer.get_deleted_resources(),
            }
        )

        return V1OKJsonResponse(data=slz.data)
