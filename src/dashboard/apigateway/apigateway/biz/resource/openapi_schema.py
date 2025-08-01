#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2025 Tencent. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
from typing import Optional

from apigateway.apps.openapi.models import (
    OpenAPIResourceSchema,
    OpenAPIResourceSchemaVersion,
)
from apigateway.core.models import ResourceVersion


class ResourceOpenAPISchemaVersionHandler:
    @staticmethod
    def make_new_version(resource_version: ResourceVersion):
        """
        创建resource schema version
        """
        resource_ids = [resource["id"] for resource in resource_version.data if "id" in resource]

        # 查询资源所有的schema
        resource_schemas = OpenAPIResourceSchema.objects.filter(resource_id__in=resource_ids)

        schema_list = [
            {
                "resource_id": resource_schema.resource.id,
                "schema": resource_schema.schema,
            }
            for resource_schema in resource_schemas
        ]
        if len(schema_list) > 0:
            OpenAPIResourceSchemaVersion.objects.create(
                resource_version=resource_version,
                schema=schema_list,
            )


class ResourceOpenAPISchemaHandler:
    @staticmethod
    def has_openapi_schem(schema: Optional[dict] = None) -> bool:
        if not schema:
            return False
        if "none_schema" in schema and schema["none_schema"] is True:
            # 对于确认过没有 schema 的资源，直接返回 True
            return True

            # currently, the schema.responses is initialized during import openapi file
            # so, we can't judge whether the schema has configured the schema or not
        if "requestBody" in schema or "parameters" in schema:
            return True

        return False
