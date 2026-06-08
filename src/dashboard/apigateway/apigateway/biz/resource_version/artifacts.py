#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from typing import Any, Dict

from django.db import transaction

from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion
from apigateway.apps.support.models import ResourceDoc, ResourceDocVersion
from apigateway.core.models import Gateway, ResourceVersion
from apigateway.service.resource_version import OpenAPIExportManager

from .resource_doc_version import ResourceDocVersionHandler
from .resource_version import ResourceVersionHandler


class ResourceVersionArtifactHandler:
    @classmethod
    @transaction.atomic
    def create_resource_version_with_artifacts(
        cls,
        gateway: Gateway,
        data: Dict[str, Any],
        username: str = "",
    ) -> ResourceVersion:
        resource_version = ResourceVersionHandler.create_resource_version(gateway, data, username)

        if ResourceDoc.objects.filter(gateway=gateway).exists():
            ResourceDocVersion.objects.create(
                gateway=gateway,
                resource_version=resource_version,
                data=ResourceDocVersionHandler().make_version(gateway.id),
            )

        exporter = OpenAPIExportManager(
            api_version=resource_version.version,
            title=f"the openapi of {gateway.name}",
        )
        OpenAPIFileResourceSchemaVersion.objects.create(
            gateway=gateway,
            resource_version=resource_version,
            schema=exporter.export_resource_version_openapi(resource_version),
        )

        return resource_version
