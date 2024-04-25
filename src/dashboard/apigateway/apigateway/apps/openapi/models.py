#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from django.db import models

from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Resource, ResourceVersion


class OpenAPIResourceSchema(TimestampedModelMixin, OperatorModelMixin):
    """
    openapi_resource_schema: resource 接口协议表
    """

    resource = models.OneToOneField(Resource, on_delete=models.CASCADE)
    schema = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = "openapi_resource_schema"

    def __str__(self):
        return f"<OpenAPIResourceSchema: {self.id}/{self.resource.name}>"


class OpenAPIResourceSchemaVersion(TimestampedModelMixin, OperatorModelMixin):
    """
    openapi_resource_schema_version: resource 接口协议版本表
    """

    resource_version = models.OneToOneField(ResourceVersion, on_delete=models.PROTECT)
    schema = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = "openapi_resource_schema_version"

    def __str__(self):
        return f"<OpenAPIResourceSchemaVersion: {self.id}/{self.resource_version.version}>"
