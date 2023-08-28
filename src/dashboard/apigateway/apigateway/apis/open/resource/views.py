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
from rest_framework import generics

from apigateway.apis.web.resource.serializers import ResourceImportInputSLZ
from apigateway.biz.resource.importer.importers import ResourcesImporter
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.models import Resource, Stage
from apigateway.utils.responses import V1OKJsonResponse


class ResourceSyncApi(generics.CreateAPIView):
    permission_classes = [GatewayRelatedAppPermission]

    def get_queryset(self):
        return Resource.objects.filter(api=self.request.gateway)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = ResourceImportInputSLZ(data=request.data, context={"stages": Stage.objects.filter(api=request.gateway)})
        slz.is_valid(raise_exception=True)

        importer = ResourcesImporter.from_resources(
            gateway=request.gateway,
            resources=slz.validated_data["resources"],
            # 同步全部资源
            selected_resources=None,
            need_delete_unspecified_resources=slz.validated_data.get("delete", False),
            username=request.user.username,
        )
        importer.import_resources()

        # 分析出已创建或更新的资源
        added_resources = []
        updated_resources = []
        for resource_data in importer.get_selected_resource_data_list():
            if resource_data.metadata.get("is_created"):
                added_resources.append({"id": resource_data.resource.id})
            else:
                updated_resources.append({"id": resource_data.resource.id})

        return V1OKJsonResponse(
            data={
                "added": added_resources,
                "updated": updated_resources,
                "deleted": importer.get_deleted_resources(),
            },
        )
