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
from django.db import transaction
from django.db.models import Count
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apigateway.apps.esb.bkcore.models import ComponentSystem, DocCategory, SystemDocCategory
from apigateway.apps.esb.constants import DataTypeEnum
from apigateway.apps.esb.doc_category import serializers
from apigateway.apps.esb.permissions import UserAccessESBPermission
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import OKJsonResponse


class DocCategoryViewSet(viewsets.ModelViewSet):
    queryset = DocCategory.objects.all()
    serializer_class = serializers.DocCategorySLZ
    permission_classes = [IsAuthenticated, UserAccessESBPermission]
    lookup_field = "id"

    @swagger_auto_schema(
        response_serializer=serializers.DocCategorySLZ(many=True),
        tags=["ESB.DocCategory"],
    )
    def list(self, request, *args, **kwargs):
        queryset = DocCategory.objects.all().order_by("-priority", "name")

        # only get the system not hidden
        system_ids = ComponentSystem.objects.exclude(data_type=DataTypeEnum.OFFICIAL_HIDDEN.value).values_list(
            "id", flat=True
        )
        q = (
            SystemDocCategory.objects.filter(system_id__in=system_ids)
            .values("doc_category_id")
            .annotate(count=Count("doc_category_id"))
        )
        counts = {i["doc_category_id"]: i["count"] for i in q}

        slz = self.get_serializer_class()(
            queryset,
            many=True,
            context={"system_counts": counts},
        )

        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(
        response_serializer=serializers.DocCategorySLZ,
        tags=["ESB.DocCategory"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(
        request_body=serializers.DocCategorySLZ,
        tags=["ESB.DocCategory"],
    )
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            data_type=DataTypeEnum.CUSTOM.value,
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return OKJsonResponse(data={"id": slz.instance.id})

    @swagger_auto_schema(
        request_body=serializers.DocCategorySLZ,
        tags=["ESB.DocCategory"],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
        )

        return OKJsonResponse()

    @swagger_auto_schema(tags=["ESB.DocCategory"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        allow, message = DocCategory.objects.allow_delete([instance.id])
        if not allow:
            raise error_codes.FAILED_PRECONDITION.format(message=message, replace=True)

        DocCategory.objects.delete_custom_doc_category(instance.id)

        return OKJsonResponse()
