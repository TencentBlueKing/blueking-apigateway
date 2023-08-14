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

from apigateway.apps.stage_item.config import serializers
from apigateway.core.models import Stage, StageItem, StageItemConfig
from apigateway.utils.django import get_object_or_None
from apigateway.utils.responses import V1OKJsonResponse


class StageItemConfigViewSet(viewsets.ModelViewSet):
    lookup_field = "id"
    serializer_class = serializers.StageItemConfigSLZ

    def get_queryset(self):
        return StageItem.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(tags=["StageItem"])
    def retrieve(self, request, gateway_id: int, stage_id: int, stage_item_id: int, *args, **kwargs):
        stage = get_object_or_404(Stage, api=self.request.gateway, id=stage_id)
        stage_item = get_object_or_404(StageItem, api=self.request.gateway, id=stage_item_id)
        instance = get_object_or_None(
            StageItemConfig, api=self.request.gateway, stage=stage, stage_item_id=stage_item.id
        )
        stage_item.config = instance and instance.config or {}

        slz = self.get_serializer(stage_item)
        return V1OKJsonResponse(data=slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["StageItem"],
    )
    @transaction.atomic
    def update(self, request, gateway_id: int, stage_id: int, stage_item_id: int, *args, **kwargs):
        stage = get_object_or_404(Stage, api=self.request.gateway, id=stage_id)
        stage_item = get_object_or_404(StageItem, api=self.request.gateway, id=stage_item_id)
        instance = get_object_or_None(
            StageItemConfig, api=self.request.gateway, stage=stage, stage_item_id=stage_item.id
        )

        slz = serializers.StageItemConfigSLZ(
            instance,
            data=request.data,
            context={"api": self.request.gateway, "stage": stage, "stage_item": stage_item},
        )
        slz.is_valid(raise_exception=True)

        slz.save(created_by=request.user.username, updated_by=request.user.username)

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["StageItem"])
    @transaction.atomic
    def destroy(self, request, gateway_id: int, stage_id: int, stage_item_id: int, *args, **kwargs):
        stage = get_object_or_404(Stage, api=self.request.gateway, id=stage_id)
        stage_item = get_object_or_404(StageItem, api=self.request.gateway, id=stage_item_id)

        # 直接清空环境中，配置项的配置内容，该清空操作不能直接生效到云 API 服务
        StageItemConfig.objects.filter(api=self.request.gateway, stage=stage, stage_item_id=stage_item.id).delete()

        return V1OKJsonResponse()
