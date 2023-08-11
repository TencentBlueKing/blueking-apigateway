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

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated

from apigateway.apps.esb.bkcore.models import ComponentReleaseHistory, ESBChannel
from apigateway.apps.esb.component import serializers
from apigateway.apps.esb.component.constants import ESB_RELEASE_TASK_EXPIRES
from apigateway.apps.esb.component.helpers import get_release_lock
from apigateway.apps.esb.component.sync import ComponentSynchronizer
from apigateway.apps.esb.component.tasks import sync_and_release_esb_components
from apigateway.apps.esb.constants import DataTypeEnum
from apigateway.apps.esb.permissions import UserAccessESBPermission
from apigateway.apps.resource.importer import ResourcesImporter
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Gateway, ResourceVersion
from apigateway.utils.access_token import get_user_access_token_from_request
from apigateway.utils.django import get_object_or_None
from apigateway.utils.responses import V1FailJsonResponse, V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema

logger = logging.getLogger(__name__)


class ESBChannelViewSet(viewsets.ModelViewSet):
    queryset = ESBChannel.objects.all()
    serializer_class = serializers.ESBChannelSLZ
    permission_classes = [IsAuthenticated, UserAccessESBPermission]
    lookup_field = "id"

    @swagger_auto_schema(response_serializer=serializers.ESBChannelSLZ(many=True), tags=["ESB.Component"])
    def list(self, request, *args, **kwargs):
        queryset = ESBChannel.objects.exclude(system__data_type=DataTypeEnum.OFFICIAL_HIDDEN.value).order_by(
            "-is_active", "system__name", "path"
        )

        slz = serializers.ESBChannelSLZ(
            queryset,
            many=True,
            context={
                "latest_release_time": ComponentReleaseHistory.objects.get_latest_release_time(),
            },
        )

        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(response_serializer=serializers.ESBChannelDetailSLZ, tags=["ESB.Component"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.ESBChannelDetailSLZ(instance)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(request_body=serializers.ESBChannelSLZ, tags=["ESB.Component"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        slz.save(
            board=data["system"].board,
            data_type=DataTypeEnum.CUSTOM.value,
            is_public=True,
            created_by=request.user.username,
            updated_by=request.user.username,
            config={},
        )

        return V1OKJsonResponse("OK", data={"id": slz.instance.id})

    @swagger_auto_schema(request_body=serializers.ESBChannelSLZ, tags=["ESB.Component"])
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = self.get_serializer(instance, request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
        )

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(tags=["ESB.Component"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        allow, message = ESBChannel.objects.allow_delete([instance.id])
        if not allow:
            raise error_codes.FORBIDDEN.format(message, replace=True)

        ESBChannel.objects.delete_custom_channels([instance.id])

        return V1OKJsonResponse("OK")


class ESBChannelBatchViewSet(viewsets.ModelViewSet):
    queryset = ESBChannel.objects.all()
    serializer_class = serializers.ESBChannelBatchSLZ
    permission_classes = [IsAuthenticated, UserAccessESBPermission]
    lookup_field = "id"

    @swagger_auto_schema(request_body=serializers.ESBChannelBatchSLZ, tags=["ESB.Component"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        allow, message = ESBChannel.objects.allow_delete(slz.validated_data["ids"])
        if not allow:
            raise error_codes.FORBIDDEN.format(message, replace=True)

        ESBChannel.objects.delete_custom_channels(slz.validated_data["ids"])

        return V1OKJsonResponse("OK")


class ComponentSyncViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, UserAccessESBPermission]

    @swagger_auto_schema(tags=["ESB.Component"])
    def need_new_release(self, request, *args, **kwargs):
        if ComponentReleaseHistory.objects.need_new_release():
            return V1OKJsonResponse(
                _("组件配置有更新，新增组件或更新组件请求方法、请求路径、权限级别，需同步到网关才能生效。"),
                data={
                    "need_new_release": True,
                },
            )

        return V1OKJsonResponse("OK", data={"need_new_release": False})

    @swagger_auto_schema(tags=["ESB.Component"])
    def get_release_status(self, request, *args, **kwargs):
        """获取组件的发布状态"""
        release_lock = get_release_lock()
        locked = release_lock.locked()
        return V1OKJsonResponse("OK", data={"is_releasing": locked})

    @swagger_auto_schema(tags=["ESB.Component"])
    def retrieve_esb_gateway(self, request, *args, **kwargs):
        """获取 ESB 组件对应网关的信息"""
        esb_gateway = self._get_esb_gateway()
        return V1OKJsonResponse("OK", data={"gateway_id": esb_gateway.id, "gateway_name": esb_gateway.name})

    @swagger_auto_schema(tags=["ESB.Component"])
    def sync_check(self, request, *args, **kwargs):
        esb_gateway = self._get_esb_gateway()

        synchronizer = ComponentSynchronizer()
        importing_resources = synchronizer.get_importing_resources()

        resources_importer = ResourcesImporter(
            gateway=esb_gateway,
            allow_overwrite=True,
            need_delete_unspecified_resources=True,
            username=request.user.username,
        )
        resources_importer.set_importing_resources(importing_resources)
        unspecified_resources = resources_importer.get_unspecified_resources()

        slz = serializers.ComponentResourceBindingSLZ(unspecified_resources + importing_resources, many=True)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(tags=["ESB.Component"])
    def sync_and_release(self, request, *args, **kwargs):
        esb_gateway = self._get_esb_gateway()

        # 检查锁状态，防止多个同步任务同时进行
        release_lock = get_release_lock()
        if release_lock.locked():
            return V1FailJsonResponse(_("当前已有同步任务正在执行，请稍后重试。"), data={"is_releasing": True})

        # 因同步及发布任务耗时较长，因此采用异步方式处理
        apply_async_on_commit(
            sync_and_release_esb_components,
            args=(esb_gateway.id, request.user.username, get_user_access_token_from_request(request), False),
            expires=ESB_RELEASE_TASK_EXPIRES,
        )

        return V1OKJsonResponse("OK", data={"is_releasing": True})

    def _get_esb_gateway(self) -> Gateway:
        gateway = get_object_or_None(Gateway, name=settings.BK_ESB_GATEWAY_NAME)
        if not gateway:
            raise error_codes.COMPONENT_GATEWAY_NOT_FOUND.format(api_name=settings.BK_ESB_GATEWAY_NAME)
        return gateway


class ComponentReleaseHistoryViewSet(viewsets.ModelViewSet):
    queryset = ComponentReleaseHistory.objects.all()
    serializer_class = serializers.ComponentReleaseHistorySLZ
    permission_classes = [IsAuthenticated, UserAccessESBPermission]
    lookup_field = "id"

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.QueryComponentReleaseHistorySLZ,
        responses={status.HTTP_200_OK: serializers.ComponentReleaseHistorySLZ(many=True)},
        tags=["ESB.Component"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.QueryComponentReleaseHistorySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = ComponentReleaseHistory.objects.get_histories(
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
            order_by="-id",
        )
        page = self.paginate_queryset(queryset)
        slz = serializers.ComponentReleaseHistorySLZ(
            page,
            many=True,
            context={
                "resource_version_id_to_fields": ResourceVersion.objects.get_id_to_fields_map(
                    resource_version_ids=[history["resource_version_id"] for history in page],
                ),
            },
        )
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ComponentResourceBindingSLZ(many=True)},
        tags=["ESB.Component"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.ComponentResourceBindingSLZ(instance.data, many=True)
        return V1OKJsonResponse("OK", data=slz.data)
