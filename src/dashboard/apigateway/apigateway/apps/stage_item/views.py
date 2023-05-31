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
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.stage_item import serializers
from apigateway.common.exceptions import InstanceDeleteError
from apigateway.core.models import Stage, StageItem, StageItemConfig
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse


class StageItemViewSet(viewsets.ModelViewSet):
    lookup_field = "id"
    serializer_class = serializers.StageItemSLZ

    def get_queryset(self):
        return StageItem.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ListStageItemSLZ(many=True)},
        tags=["StageItem"],
    )
    def list(self, request, gateway_id: int, *args, **kwargs):
        items_queryset = self.get_queryset()

        slz = serializers.ListStageItemSLZ(
            items_queryset,
            many=True,
            context={
                "stage_item_id_to_configured_stages": StageItemConfig.objects.get_stage_item_id_to_configured_stages(
                    gateway_id=self.request.gateway.id,
                ),
                "stage_item_id_to_reference_instances": StageItem.objects.get_reference_instances(
                    self.request.gateway.id
                ),
                "stage_id_to_fields": Stage.objects.get_id_to_fields(
                    gateway_id=self.request.gateway.id, fields=["id", "name"]
                ),
            },
        )

        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(tags=["StageItem"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        stage_item_configs = StageItemConfig.objects.get_configs(self.request.gateway.id, instance.id)

        slz = serializers.StageItemSLZ(
            instance=instance,
            context={
                "stage_item_configs": stage_item_configs,
            },
        )
        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.StageItemSLZ,
        tags=["StageItem"],
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = serializers.StageItemSLZ(data=request.data, context={"api": self.request.gateway})
        slz.is_valid(raise_exception=True)
        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return OKJsonResponse(data={"id": slz.instance.id})

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["StageItem"],
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = serializers.StageItemSLZ(instance, data=request.data, context={"api": self.request.gateway})
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        return OKJsonResponse()

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["StageItem"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            StageItem.objects.delete_stage_item(instance.id)
        except InstanceDeleteError as err:
            return FailJsonResponse(str(err))

        return OKJsonResponse()


class StageItemForStageViewSet(viewsets.ModelViewSet):
    lookup_field = "id"
    serializer_class = serializers.StageItemSLZ

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ListStageItemForStageSLZ(many=True)},
        tags=["StageItem"],
    )
    def list(self, request, gateway_id: int, stage_id: int, *args, **kwargs):
        items_queryset = StageItem.objects.filter(api=self.request.gateway)
        stage = get_object_or_404(Stage, api=self.request.gateway, id=stage_id)

        slz = serializers.ListStageItemForStageSLZ(
            items_queryset,
            many=True,
            context={
                "configured_item_ids": StageItemConfig.objects.get_configured_item_ids(
                    gateway_id=self.request.gateway.id,
                    stage_id=stage.id,
                )
            },
        )

        return OKJsonResponse(data=slz.data)
