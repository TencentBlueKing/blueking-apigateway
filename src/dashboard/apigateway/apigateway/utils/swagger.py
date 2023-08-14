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
from collections import OrderedDict

from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from rest_framework import serializers as drf_serializers

from apigateway.utils.serializers import CustomFieldsSerializer


class ResponseSerializer(CustomFieldsSerializer):
    pass
    # code = drf_serializers.IntegerField()
    # result = drf_serializers.BooleanField()
    # message = drf_serializers.CharField()


class PaginatedDataSerializer(CustomFieldsSerializer):
    count = drf_serializers.IntegerField()
    has_next = drf_serializers.BooleanField()
    has_previous = drf_serializers.BooleanField()


def get_response_serializer(data_field=None):
    """
    用于 drf-yasg swagger_auto_schema 获取标准的 response serializer
    """
    add_fields = {"data": data_field} if data_field else {}
    return ResponseSerializer(add_fields=add_fields)


def get_paginated_response_serializer(results_field=None):
    """
    用于 drf-yasg swagger_auto_schema 获取标准翻页的 response serializer
    """
    add_fields = {"results": results_field} if results_field else {}
    paginated_data_slz = PaginatedDataSerializer(add_fields=add_fields)
    return ResponseSerializer(add_fields={"data": paginated_data_slz})


class GenericResponseSwaggerAutoSchema(SwaggerAutoSchema):
    """定义了标准的响应格式，包括 code, result, message, data"""

    def _get_data_schema(self, response) -> openapi.Schema:
        return openapi.Schema(type=openapi.TYPE_OBJECT, description="响应结果", default=None)

    def get_response_schemas(self, response_serializers):
        responses = super().get_response_schemas(response_serializers)
        new_responses = OrderedDict()
        for sc, response in responses.items():
            new_responses[sc] = openapi.Response(
                description=response.get("description", ""),
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties=OrderedDict(
                        (
                            # ("code", openapi.Schema(type=openapi.TYPE_INTEGER, description="响应码")),
                            # ("result", openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否包含结果")),
                            # ("message", openapi.Schema(type=openapi.TYPE_STRING, description="消息")),
                            ("data", self._get_data_schema(response)),
                        )
                    ),
                ),
            )
        return new_responses


class ResponseSwaggerAutoSchema(GenericResponseSwaggerAutoSchema):
    """把 serializer 的结果嵌入到 data 字段中"""

    def _get_data_schema(self, response) -> openapi.Schema:
        return response.get("schema")


class PaginatedResponseSwaggerAutoSchema(GenericResponseSwaggerAutoSchema):
    """把 serializer 转换成分页形式"""

    def _get_data_schema(self, response) -> openapi.Schema:
        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties=OrderedDict(
                (
                    ("count", openapi.Schema(type=openapi.TYPE_INTEGER)),
                    ("has_next", openapi.Schema(type=openapi.TYPE_BOOLEAN)),
                    ("has_previous", openapi.Schema(type=openapi.TYPE_BOOLEAN)),
                    ("results", response.get("schema")),
                )
            ),
        )
