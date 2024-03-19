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

# FIXME: 将 views 挪到 apis.web 模块
from apigateway.biz.resource.importer import ResourceDataConvertor, ResourceImportValidator
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Gateway, ResourceVersion
from apigateway.utils.django import get_object_or_None
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse

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

        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(response_serializer=serializers.ESBChannelDetailSLZ, tags=["ESB.Component"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.ESBChannelDetailSLZ(instance)
        return OKJsonResponse(data=slz.data)

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

        return OKJsonResponse(data={"id": slz.instance.id})

    @swagger_auto_schema(request_body=serializers.ESBChannelSLZ, tags=["ESB.Component"])
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = self.get_serializer(instance, request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
        )

        return OKJsonResponse()

    @swagger_auto_schema(tags=["ESB.Component"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        allow, message = ESBChannel.objects.allow_delete([instance.id])
        if not allow:
            raise error_codes.FAILED_PRECONDITION.format(message, replace=True)

        ESBChannel.objects.delete_custom_channels([instance.id])

        return OKJsonResponse()


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
            raise error_codes.FAILED_PRECONDITION.format(message, replace=True)

        ESBChannel.objects.delete_custom_channels(slz.validated_data["ids"])

        return OKJsonResponse()


class ComponentSyncViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, UserAccessESBPermission]

    @swagger_auto_schema(tags=["ESB.Component"])
    def need_new_release(self, request, *args, **kwargs):
        if ComponentReleaseHistory.objects.need_new_release():
            return OKJsonResponse(
                # _("组件配置有更新，新增组件或更新组件请求方法、请求路径、权限级别，需同步到网关才能生效。"),
                data={
                    "need_new_release": True,
                },
            )

        return OKJsonResponse(data={"need_new_release": False})

    @swagger_auto_schema(tags=["ESB.Component"])
    def get_release_status(self, request, *args, **kwargs):
        """获取组件的发布状态"""
        release_lock = get_release_lock()
        locked = release_lock.locked()
        return OKJsonResponse(data={"is_releasing": locked})

    @swagger_auto_schema(tags=["ESB.Component"])
    def retrieve_esb_gateway(self, request, *args, **kwargs):
        """获取 ESB 组件对应网关的信息"""
        esb_gateway = self._get_esb_gateway()
        return OKJsonResponse(data={"gateway_id": esb_gateway.id, "gateway_name": esb_gateway.name})

    @swagger_auto_schema(tags=["ESB.Component"])
    def sync_check(self, request, *args, **kwargs):
        esb_gateway = self._get_esb_gateway()

        synchronizer = ComponentSynchronizer()
        importing_resources = synchronizer.get_importing_resources()

        resource_data_list = ResourceDataConvertor(esb_gateway, importing_resources).convert()
        validator = ResourceImportValidator(
            gateway=esb_gateway,
            resource_data_list=resource_data_list,
            need_delete_unspecified_resources=True,
        )
        validator.validate()
        unspecified_resources = validator.get_unspecified_resources()

        resources = unspecified_resources + [
            resource_data.snapshot_for_checking() for resource_data in resource_data_list
        ]
        slz = serializers.ComponentResourceBindingSLZ(resources, many=True)
        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(tags=["ESB.Component"])
    def sync_and_release(self, request, *args, **kwargs):
        esb_gateway = self._get_esb_gateway()

        # 检查锁状态，防止多个同步任务同时进行
        release_lock = get_release_lock()
        if release_lock.locked():
            return FailJsonResponse(
                status=status.HTTP_400_BAD_REQUEST,
                code="FAILED_PRECONDITION",
                message=_("当前已有同步任务正在执行，请稍后重试。"),
                data={"is_releasing": True},
            )

        # 因同步及发布任务耗时较长，因此采用异步方式处理
        apply_async_on_commit(
            sync_and_release_esb_components,
            args=(esb_gateway.id, request.user.username, False),
            expires=ESB_RELEASE_TASK_EXPIRES,
        )

        return OKJsonResponse(data={"is_releasing": True})

    def _get_esb_gateway(self) -> Gateway:
        gateway = get_object_or_None(Gateway, name=settings.BK_ESB_GATEWAY_NAME)
        if not gateway:
            raise error_codes.INTERNAL.format(api_name=settings.BK_ESB_GATEWAY_NAME)
        return gateway


class ComponentReleaseHistoryViewSet(viewsets.ModelViewSet):
    queryset = ComponentReleaseHistory.objects.all()
    serializer_class = serializers.ComponentReleaseHistorySLZ
    permission_classes = [IsAuthenticated, UserAccessESBPermission]
    lookup_field = "id"

    @swagger_auto_schema(
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
        return self.get_paginated_response(slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ComponentResourceBindingSLZ(many=True)},
        tags=["ESB.Component"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.ComponentResourceBindingSLZ(instance.data, many=True)
        return OKJsonResponse(data=slz.data)
