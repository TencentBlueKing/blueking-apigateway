# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import pytest
from django_dynamic_fixture import G

from apigateway.apps.openapi.models import OpenAPIResourceSchema
from apigateway.biz.resource import ResourceOpenAPISchemaHandler
from apigateway.core.models import Gateway, Resource


class TestResourceOpenAPISchemaHandler:
    @pytest.mark.parametrize(
        "schema, expected",
        [
            ({"version": "3.0.1", "none_schema": False, "parameters": [{"name": "id", "in": "query"}]}, True),
            ({"version": "3.0.1", "requestBody": {"content": {}}}, True),
            ({"none_schema": True}, True),
            # 导入 openapi 文件时会初始化 responses，仅有 responses 不算已配置
            ({"version": "3.0.1", "responses": {"200": {"description": "ok"}}}, False),
        ],
    )
    def test_get_resource_ids_with_openapi_schema(self, fake_gateway, schema, expected):
        """数据库筛选与 has_openapi_schema 判定一致"""
        resource = G(Resource, gateway=fake_gateway)
        G(OpenAPIResourceSchema, resource=resource, schema=schema)

        result = set(ResourceOpenAPISchemaHandler.get_resource_ids_with_openapi_schema(fake_gateway.id))

        assert (resource.id in result) is expected
        assert ResourceOpenAPISchemaHandler.has_openapi_schema(schema) is expected

    def test_get_resource_ids_with_openapi_schema_scope(self, fake_gateway):
        resource = G(Resource, gateway=fake_gateway)
        G(OpenAPIResourceSchema, resource=resource, schema={"none_schema": True})

        # 没有 schema 记录
        G(Resource, gateway=fake_gateway)

        # 其他网关的资源
        other_resource = G(Resource, gateway=G(Gateway))
        G(OpenAPIResourceSchema, resource=other_resource, schema={"none_schema": True})

        result = set(ResourceOpenAPISchemaHandler.get_resource_ids_with_openapi_schema(fake_gateway.id))

        assert result == {resource.id}
