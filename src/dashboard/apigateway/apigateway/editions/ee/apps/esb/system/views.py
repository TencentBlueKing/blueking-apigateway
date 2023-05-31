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
import logging

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apigateway.apps.esb.bkcore.models import ComponentSystem, ESBChannel, SystemDocCategory
from apigateway.apps.esb.constants import DataTypeEnum
from apigateway.apps.esb.permissions import UserAccessESBPermission
from apigateway.apps.esb.system import serializers
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import OKJsonResponse

logger = logging.getLogger(__name__)


class SystemViewSet(viewsets.ModelViewSet):
    queryset = ComponentSystem.objects.all()
    serializer_class = serializers.SystemSLZ
    permission_classes = [IsAuthenticated, UserAccessESBPermission]
    lookup_field = "id"

    @swagger_auto_schema(
        response_serializer=serializers.SystemSLZ(many=True),
        tags=["ESB.System"],
    )
    def list(self, request, *args, **kwargs):
        # 去除官方隐藏系统，不展示给用户
        queryset = ComponentSystem.objects.exclude(data_type=DataTypeEnum.OFFICIAL_HIDDEN.value).order_by("name")

        slz = self.get_serializer_class()(
            queryset,
            many=True,
            context={
                "system_id_to_doc_category_map": SystemDocCategory.objects.get_system_id_to_doc_category_map(),
                "system_id_to_channel_count_map": ESBChannel.objects.calculate_channel_count_per_system(),
            },
        )

        return OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        response_serializer=serializers.SystemSLZ,
        tags=["ESB.System"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer_class()(
            instance,
            context={
                "system_id_to_doc_category_map": SystemDocCategory.objects.get_system_id_to_doc_category_map(
                    [instance.id],
                ),
            },
        )
        return OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        request_body=serializers.SystemSLZ,
        tags=["ESB.System"],
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        # 1. save system
        slz.save(
            data_type=DataTypeEnum.CUSTOM.value,
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        # 2. save system doc-category
        SystemDocCategory.objects.create(
            board=data["board"],
            doc_category=data["doc_category"],
            system=slz.instance,
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return OKJsonResponse("OK", data={"id": slz.instance.id})

    @swagger_auto_schema(
        request_body=serializers.SystemSLZ,
        tags=["ESB.System"],
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        # 1. save system
        slz.save(
            updated_by=request.user.username,
        )

        # 2. save system doc-category
        if data.get("doc_category"):
            SystemDocCategory.objects.filter(system=instance).update(
                doc_category=data["doc_category"],
                updated_by=request.user.username,
            )

        return OKJsonResponse("OK")

    @swagger_auto_schema(tags=["ESB.System"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        allow, message = ComponentSystem.objects.allow_delete([instance.id])
        if not allow:
            raise error_codes.FORBIDDEN.format(message=message, replace=True)

        ComponentSystem.objects.delete_custom_systems([instance.id])

        return OKJsonResponse("OK")
