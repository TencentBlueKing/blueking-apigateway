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
from typing import Dict, List, Tuple

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Gateway

from .released_resource import ReleasedResourceData, ReleasedResourceHandler
from .released_resource_doc import ReleasedResourceDocHandler
from .released_resource_doc.generators import DocGenerator
from .resource_doc import ResourceDocHandler
from .resource_label import ResourceLabelHandler


class MCPServerHandler:
    @staticmethod
    def get_tools_resources_and_labels(
        gateway_id: int, stage_name: str, resource_names: List[str]
    ) -> Tuple[List[ReleasedResourceData], Dict[int, List]]:
        tool_resource_names = set(resource_names)

        stage_released_resources = ReleasedResourceHandler.get_public_released_resource_data_list(
            gateway_id,
            stage_name,
            False,
        )

        # only need the resources in the resource_names
        tool_resources: List[ReleasedResourceData] = [
            r for r in stage_released_resources if r.name in tool_resource_names
        ]

        label_ids = list({label_id for resource in tool_resources for label_id in resource.gateway_labels})
        labels = ResourceLabelHandler.get_labels_by_ids(label_ids)

        return tool_resources, labels

    @staticmethod
    def get_tool_doc(gateway_id: int, stage_name: str, tool_name: str) -> Dict:
        resource_data, doc_data = ReleasedResourceDocHandler.get_released_resource_doc_data(
            gateway_id=gateway_id,
            stage_name=stage_name,
            resource_name=tool_name,
            language=ResourceDocHandler.get_doc_language(get_current_language_code()),
        )
        if not (resource_data and doc_data):
            raise error_codes.NOT_FOUND

        gateway = Gateway.objects.get(id=gateway_id)

        generator = DocGenerator(
            gateway=gateway,
            stage_name=stage_name,
            resource_data=resource_data,
            doc_data=doc_data,
            language=ResourceDocHandler.get_doc_language(get_current_language_code()),
        )

        return generator.get_doc()

    @staticmethod
    def disable_servers(gateway_id: int, stage_id: int = 0) -> None:
        """set the status of the servers to inactive
        e.g. gateway inactivated, stage offline, etc.

        Args:
            gateway_id (int): the id of the gateway
            stage_id (int, optional): the id of the stage. Defaults to 0.
        """
        queryset = MCPServer.objects.filter(gateway_id=gateway_id)
        if stage_id:
            queryset = queryset.filter(stage_id=stage_id)

        queryset.update(status=MCPServerStatusEnum.INACTIVE.value)
