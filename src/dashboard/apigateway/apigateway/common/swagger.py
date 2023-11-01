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
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.inspectors import SwaggerAutoSchema
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from rest_framework import status


class BkStandardResponseSwaggerAutoSchema(SwaggerAutoSchema):
    """定义了蓝鲸标准的响应格式，包括 data, error"""

    def get_response_schemas(self, response_serializers):
        responses = super().get_response_schemas(response_serializers)
        new_responses = OrderedDict()
        for sc, response in responses.items():
            # 失败情况
            if sc.isdigit() and status.is_success(int(sc)):
                # 成功
                data = self._get_successful_schema(response)
                properties = OrderedDict((("data", data),))
            else:
                properties = OrderedDict(
                    (("error", response.get("schema") or openapi.Schema(type=openapi.TYPE_OBJECT)),)
                )

            new_responses[sc] = openapi.Response(
                description=response.get("description", ""),
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties=properties),
            )

        return new_responses

    def _get_successful_schema(self, response) -> openapi.Schema:
        """获取成功情况下的 Schema"""
        # 无需分页，直接返回
        if not self.should_page():
            return response.get("schema") or openapi.Schema(type=openapi.TYPE_OBJECT)

        # 处理分页情况
        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties=OrderedDict(
                (
                    ("count", openapi.Schema(type=openapi.TYPE_INTEGER)),
                    ("results", response.get("schema")),
                )
            ),
            required=["count", "results"],
        )


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


# add drf-yasg automatically generated documents
schema_view = get_schema_view(
    openapi.Info(
        title="APIGateway-Dashboard API",
        default_version="v1",
        description="APIGateway-Dashboard API Document",
        terms_of_service="http://example.com",
        contact=openapi.Contact(email="blueking@tencent.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    generator_class=BothHttpAndHttpsSchemaGenerator,
    permission_classes=(permissions.AllowAny,),
)
