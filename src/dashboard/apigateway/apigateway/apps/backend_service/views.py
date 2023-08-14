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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.backend_service import serializers
from apigateway.common.exceptions import InstanceDeleteError
from apigateway.core.models import BackendService
from apigateway.utils.responses import V1FailJsonResponse, V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class BackendServiceViewSet(viewsets.ModelViewSet):
    lookup_field = "id"
    serializer_class = serializers.BackendServiceSLZ

    def get_queryset(self):
        return BackendService.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.QueryBackendServiceSLZ,
        responses={status.HTTP_200_OK: serializers.ListBackendServiceSLZ(many=True)},
        tags=["BackendService"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.QueryBackendServiceSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        if data.get("query"):
            queryset = queryset.filter(name__contains=data["query"])
        queryset = queryset.order_by(data.get("order_by") or "-updated_time")

        page = self.paginate_queryset(queryset)

        slz = serializers.ListBackendServiceSLZ(page, many=True)
        return V1OKJsonResponse(data=self.paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(tags=["BackendService"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return V1OKJsonResponse(data=slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.BackendServiceSLZ,
        tags=["BackendService"],
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = serializers.BackendServiceSLZ(data=request.data, context={"api": self.request.gateway})
        slz.is_valid(raise_exception=True)

        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return V1OKJsonResponse(data={"id": slz.instance.id})

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["BackendService"],
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = serializers.BackendServiceSLZ(instance, data=request.data, context={"api": self.request.gateway})
        slz.is_valid(raise_exception=True)

        slz.save(updated_by=request.user.username)

        return V1OKJsonResponse("OK")

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["BackendService"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            BackendService.objects.delete_backend_service(instance.id)
        except InstanceDeleteError as err:
            return V1FailJsonResponse(str(err))

        return V1OKJsonResponse()
